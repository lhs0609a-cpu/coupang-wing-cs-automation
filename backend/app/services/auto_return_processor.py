"""
자동 반품 처리 서비스
네이버 스마트스토어에서 반품을 자동으로 처리
"""
import logging
import time
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from .naver_smartstore_automation import NaverSmartStoreAutomation
from .naver_pay_automation import NaverPayAutomation
from ..models.return_log import ReturnLog
from ..models.naver_account import NaverAccount
from ..models.auto_return_config import AutoReturnConfig
from ..models.auto_return_log import AutoReturnExecutionLog
from .auto_return_collector import AutoReturnCollector


logger = logging.getLogger(__name__)


class AutoReturnProcessor:
    """자동 반품 처리 클래스"""

    def __init__(self, db: Session):
        self.db = db
        self.collector = AutoReturnCollector(db)

    def process_pending_returns(self, config: Optional[AutoReturnConfig] = None, triggered_by: str = "scheduler") -> Dict:
        """
        대기 중인 반품을 자동으로 처리

        Args:
            config: 자동화 설정 (없으면 DB에서 조회)
            triggered_by: 실행 트리거 (scheduler, manual, api)

        Returns:
            처리 결과 딕셔너리
        """
        # 실행 로그 생성
        execution_log = AutoReturnExecutionLog(
            execution_type="PROCESS",
            status="running",
            triggered_by=triggered_by,
            started_at=datetime.now()
        )
        self.db.add(execution_log)
        self.db.commit()

        start_time = datetime.now()

        try:
            # 설정 가져오기
            if not config:
                config = self.db.query(AutoReturnConfig).first()
                if not config:
                    logger.warning("자동화 설정이 없습니다.")
                    return {
                        "success": False,
                        "message": "자동화 설정이 없습니다.",
                        "total": 0,
                        "processed": 0,
                        "failed": 0,
                    }

            # 자동화가 비활성화되어 있으면 중단
            if not config.enabled or not config.process_enabled:
                logger.info("자동 처리가 비활성화되어 있습니다.")
                return {
                    "success": False,
                    "message": "자동 처리가 비활성화되어 있습니다.",
                    "total": 0,
                    "processed": 0,
                    "failed": 0,
                }

            # 네이버 계정 조회
            naver_account = self.db.query(NaverAccount).first()
            if not naver_account:
                raise Exception("네이버 계정 정보가 없습니다.")

            # 처리 대기 중인 반품 조회
            pending_returns = self.collector.get_pending_returns(
                config=config,
                limit=config.process_batch_size
            )

            if not pending_returns:
                logger.info("처리할 반품이 없습니다.")
                return {
                    "success": True,
                    "message": "처리할 반품이 없습니다.",
                    "total": 0,
                    "processed": 0,
                    "failed": 0,
                }

            logger.info(f"{len(pending_returns)}건의 반품 처리 시작")

            # 네이버페이 자동화 인스턴스 생성
            automation = None
            try:
                automation = NaverPayAutomation(
                    headless=config.use_headless,
                    timeout=config.selenium_timeout
                )

                # 배치 처리용 데이터 준비
                return_items = []
                for return_log in pending_returns:
                    return_items.append({
                        "product_name": return_log.product_name,
                        "receiver_name": return_log.receiver_name,
                        "return_log": return_log,  # 참조 저장
                    })

                # 로그인 및 일괄 처리
                username = naver_account.get_decrypted_username()
                password = naver_account.get_decrypted_password()

                result = automation.process_return_batch(
                    return_items=return_items,
                    username=username,
                    password=password
                )

                # 결과 반영
                processed_count = result.get("processed", 0)
                failed_count = result.get("failed", 0)
                errors = result.get("errors", [])

                # 각 항목의 상태 업데이트
                for item in return_items:
                    return_log = item["return_log"]

                    # 처리 성공 여부 판단 (간단한 로직)
                    # 실제로는 더 정교한 매칭이 필요할 수 있음
                    if processed_count > 0:
                        return_log.status = "completed"
                        return_log.naver_processed = True
                        return_log.naver_processed_at = datetime.now()
                        return_log.naver_process_type = "NAVERPAY_RETURN"
                        return_log.naver_result = "네이버페이에서 반품 처리 완료"
                    else:
                        return_log.status = "failed"
                        return_log.naver_error = "반품 처리 실패"

                    self.db.commit()

                # 설정 업데이트
                config.last_process_at = datetime.now()
                config.last_process_count = processed_count
                config.last_error = None if not errors else "\n".join(errors[:5])  # 최대 5개 에러만 저장
                self.db.commit()

                # 실행 로그 업데이트
                end_time = datetime.now()
                execution_log.status = "success" if failed_count == 0 else "partial"
                execution_log.completed_at = end_time
                execution_log.duration_seconds = int((end_time - start_time).total_seconds())
                execution_log.total_items = len(pending_returns)
                execution_log.success_count = processed_count
                execution_log.failed_count = failed_count
                execution_log.details = {
                    "errors": errors[:10]  # 최대 10개 에러만 저장
                }
                execution_log.config_snapshot = config.to_dict()
                self.db.commit()

                result = {
                    "success": True,
                    "message": f"총 {len(pending_returns)}건 처리 (성공: {processed_count}, 실패: {failed_count})",
                    "total": len(pending_returns),
                    "processed": processed_count,
                    "failed": failed_count,
                    "errors": errors,
                    "timestamp": datetime.now().isoformat(),
                    "execution_log_id": execution_log.id,
                }

                logger.info(f"처리 완료: {result['message']}")
                return result

            finally:
                # 브라우저 종료
                if automation:
                    try:
                        automation.close()
                    except Exception as e:
                        logger.warning(f"브라우저 종료 중 오류: {str(e)}")

        except Exception as e:
            error_msg = f"자동 처리 중 오류 발생: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # 설정에 에러 기록
            if config:
                config.last_error = error_msg
                self.db.commit()

            # 실행 로그 업데이트
            end_time = datetime.now()
            execution_log.status = "failed"
            execution_log.completed_at = end_time
            execution_log.duration_seconds = int((end_time - start_time).total_seconds())
            execution_log.error_message = error_msg
            self.db.commit()

            return {
                "success": False,
                "message": error_msg,
                "total": 0,
                "processed": 0,
                "failed": 0,
                "execution_log_id": execution_log.id,
            }

    def _process_single_return_with_retry(
        self,
        automation: NaverSmartStoreAutomation,
        return_log: ReturnLog,
        config: AutoReturnConfig
    ) -> bool:
        """
        재시도 로직을 포함한 단일 반품 처리

        Args:
            automation: 네이버 자동화 인스턴스
            return_log: 반품 로그
            config: 자동화 설정

        Returns:
            성공 여부
        """
        max_retry = config.max_retry_count
        retry_delays = config.retry_delay_seconds or [60, 300, 900]

        for attempt in range(max_retry + 1):
            try:
                logger.info(f"Receipt {return_log.coupang_receipt_id} 처리 시도 {attempt + 1}/{max_retry + 1}")

                # 반품 타입에 따라 처리
                if return_log.receipt_status == "RELEASE_STOP_UNCHECKED":
                    # 주문 취소
                    process_type = "ORDER_CANCEL"
                    success = automation.process_order_cancel(
                        product_name=return_log.product_name,
                        cancel_reason=return_log.cancel_reason or "고객 요청"
                    )
                else:
                    # 반품 요청
                    process_type = "RETURN_REQUEST"
                    success = automation.process_return_request(
                        product_name=return_log.product_name,
                        return_reason=return_log.cancel_reason or "고객 요청"
                    )

                if success:
                    # 성공 처리
                    return_log.status = "completed"
                    return_log.naver_processed = True
                    return_log.naver_processed_at = datetime.now()
                    return_log.naver_process_type = process_type
                    return_log.naver_result = f"자동 처리 성공 (시도 {attempt + 1}회)"
                    return_log.naver_error = None
                    self.db.commit()

                    logger.info(f"Receipt {return_log.coupang_receipt_id} 처리 성공")
                    return True
                else:
                    # 실패했지만 재시도 가능
                    if attempt < max_retry:
                        delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                        logger.warning(f"Receipt {return_log.coupang_receipt_id} 처리 실패. {delay}초 후 재시도...")
                        time.sleep(delay)
                        continue
                    else:
                        # 최대 재시도 횟수 초과
                        raise Exception(f"최대 재시도 횟수({max_retry}회) 초과")

            except Exception as e:
                # 에러 발생
                if attempt < max_retry:
                    delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                    logger.warning(f"Receipt {return_log.coupang_receipt_id} 처리 중 에러: {str(e)}. {delay}초 후 재시도...")
                    time.sleep(delay)
                    continue
                else:
                    # 최대 재시도 횟수 초과
                    logger.error(f"Receipt {return_log.coupang_receipt_id} 최종 실패: {str(e)}")
                    return_log.status = "failed"
                    return_log.naver_error = f"최대 재시도 초과: {str(e)}"
                    self.db.commit()
                    return False

        # 여기에 도달하면 실패
        return_log.status = "failed"
        return_log.naver_error = "알 수 없는 오류"
        self.db.commit()
        return False

    def retry_failed_returns(self, max_count: int = 10) -> Dict:
        """
        실패한 반품을 재처리

        Args:
            max_count: 최대 재처리 개수

        Returns:
            처리 결과 딕셔너리
        """
        # 실패 상태인 반품 조회
        failed_returns = self.db.query(ReturnLog).filter(
            ReturnLog.status == "failed",
            ReturnLog.naver_processed == False
        ).order_by(ReturnLog.created_at.desc()).limit(max_count).all()

        if not failed_returns:
            return {
                "success": True,
                "message": "재처리할 실패 건이 없습니다.",
                "total": 0,
                "processed": 0,
                "failed": 0,
            }

        logger.info(f"{len(failed_returns)}건의 실패 건 재처리 시작")

        # 상태를 pending으로 변경
        for return_log in failed_returns:
            return_log.status = "pending"
            return_log.naver_error = None

        self.db.commit()

        # 일반 처리 로직 실행
        return self.process_pending_returns()

    def get_processing_statistics(self) -> Dict:
        """처리 통계 조회"""
        config = self.db.query(AutoReturnConfig).first()

        base_stats = self.collector.get_statistics()

        return {
            **base_stats,
            "config": {
                "enabled": config.enabled if config else False,
                "fetch_enabled": config.fetch_enabled if config else False,
                "process_enabled": config.process_enabled if config else False,
                "last_fetch_at": config.last_fetch_at.isoformat() if config and config.last_fetch_at else None,
                "last_process_at": config.last_process_at.isoformat() if config and config.last_process_at else None,
                "last_fetch_count": config.last_fetch_count if config else 0,
                "last_process_count": config.last_process_count if config else 0,
                "last_error": config.last_error if config else None,
            }
        }
