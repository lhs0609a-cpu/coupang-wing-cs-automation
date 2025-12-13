"""
자동 반품 수집 서비스
쿠팡 API에서 주기적으로 반품 데이터를 가져와 DB에 저장
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from .coupang_api_client import CoupangAPIClient
from ..models.return_log import ReturnLog
from ..models.coupang_account import CoupangAccount
from ..models.auto_return_config import AutoReturnConfig
from ..models.auto_return_log import AutoReturnExecutionLog


logger = logging.getLogger(__name__)


class AutoReturnCollector:
    """자동 반품 수집 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def collect_returns(self, config: Optional[AutoReturnConfig] = None, triggered_by: str = "scheduler") -> Dict:
        """
        쿠팡에서 반품 데이터를 자동으로 수집

        Args:
            config: 자동화 설정 (없으면 DB에서 조회)
            triggered_by: 실행 트리거 (scheduler, manual, api)

        Returns:
            수집 결과 딕셔너리
        """
        # 실행 로그 생성
        execution_log = AutoReturnExecutionLog(
            execution_type="FETCH",
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
                    logger.warning("자동화 설정이 없습니다. 기본 설정으로 생성합니다.")
                    config = self._create_default_config()

            # 자동화가 비활성화되어 있으면 중단
            if not config.enabled or not config.fetch_enabled:
                logger.info("자동 수집이 비활성화되어 있습니다.")
                return {
                    "success": False,
                    "message": "자동 수집이 비활성화되어 있습니다.",
                    "total_fetched": 0,
                    "saved": 0,
                    "updated": 0,
                }

            # 쿠팡 계정 조회
            coupang_account = self.db.query(CoupangAccount).first()
            if not coupang_account:
                raise Exception("쿠팡 계정 정보가 없습니다.")

            # 시간 범위 계산
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=config.fetch_lookback_hours)

            # API 클라이언트 생성
            api_client = CoupangAPIClient(
                vendor_id=coupang_account.vendor_id,
                access_key=coupang_account.get_decrypted_access_key(),
                secret_key=coupang_account.get_decrypted_secret_key()
            )

            # 반품 데이터 수집
            logger.info(f"쿠팡 반품 데이터 수집 시작: {start_date} ~ {end_date}")

            total_fetched = 0
            saved_count = 0
            updated_count = 0

            # RETURN과 CANCEL 타입 모두 수집
            for cancel_type in ["RETURN", "CANCEL"]:
                try:
                    response = api_client.get_return_requests(
                        start_date=start_date.strftime("%Y-%m-%dT%H:%M"),
                        end_date=end_date.strftime("%Y-%m-%dT%H:%M"),
                        cancel_type=cancel_type,
                        search_type="timeFrame"
                    )

                    if not response or "data" not in response:
                        logger.warning(f"{cancel_type} 타입 반품 데이터가 없습니다.")
                        continue

                    return_requests = response["data"]
                    logger.info(f"{cancel_type} 타입 {len(return_requests)}건의 반품 발견")

                    # 각 반품 항목 처리
                    for return_request in return_requests:
                        return_items = return_request.get("returnItems", [])

                        for item in return_items:
                            total_fetched += 1

                            # 기존 레코드 확인
                            existing = self.db.query(ReturnLog).filter(
                                ReturnLog.coupang_receipt_id == return_request.get("receiptId")
                            ).first()

                            if existing:
                                # 업데이트
                                self._update_return_log(existing, return_request, item)
                                updated_count += 1
                            else:
                                # 새로 생성
                                self._create_return_log(return_request, item)
                                saved_count += 1

                except Exception as e:
                    logger.error(f"{cancel_type} 타입 수집 중 오류: {str(e)}")
                    continue

            # DB 커밋
            self.db.commit()

            # 설정 업데이트
            config.last_fetch_at = datetime.now()
            config.last_fetch_count = total_fetched
            config.last_error = None
            self.db.commit()

            # 실행 로그 업데이트
            end_time = datetime.now()
            execution_log.status = "success"
            execution_log.completed_at = end_time
            execution_log.duration_seconds = int((end_time - start_time).total_seconds())
            execution_log.total_items = total_fetched
            execution_log.success_count = saved_count + updated_count
            execution_log.failed_count = 0
            execution_log.details = {
                "saved": saved_count,
                "updated": updated_count,
            }
            execution_log.config_snapshot = config.to_dict()
            self.db.commit()

            result = {
                "success": True,
                "message": f"총 {total_fetched}건 수집 (신규: {saved_count}, 업데이트: {updated_count})",
                "total_fetched": total_fetched,
                "saved": saved_count,
                "updated": updated_count,
                "timestamp": datetime.now().isoformat(),
                "execution_log_id": execution_log.id,
            }

            logger.info(f"수집 완료: {result['message']}")
            return result

        except Exception as e:
            error_msg = f"자동 수집 중 오류 발생: {str(e)}"
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
                "total_fetched": 0,
                "saved": 0,
                "updated": 0,
                "execution_log_id": execution_log.id,
            }

    def _create_default_config(self) -> AutoReturnConfig:
        """기본 설정 생성"""
        default_values = AutoReturnConfig.get_default_config()
        config = AutoReturnConfig(**default_values)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def _create_return_log(self, return_request: Dict, item: Dict) -> ReturnLog:
        """새 반품 로그 생성"""
        from datetime import datetime

        # 수령인 정보 추출
        receiver_name = return_request.get("requesterName")
        receiver_phone = return_request.get("requesterPhoneNumber")
        receiver_real_phone = return_request.get("requesterRealPhoneNumber")
        receiver_address = return_request.get("requesterAddress")
        receiver_address_detail = return_request.get("requesterAddressDetail")
        receiver_zipcode = return_request.get("requesterZipCode")

        # 시간 파싱
        coupang_created_at = None
        coupang_modified_at = None
        try:
            if return_request.get("createdAt"):
                coupang_created_at = datetime.fromisoformat(return_request.get("createdAt").replace("Z", "+00:00"))
            if return_request.get("modifiedAt"):
                coupang_modified_at = datetime.fromisoformat(return_request.get("modifiedAt").replace("Z", "+00:00"))
        except:
            pass

        # 완료 확인 시간 파싱
        complete_confirm_date = None
        try:
            if return_request.get("completeConfirmDate"):
                complete_confirm_date = datetime.fromisoformat(return_request.get("completeConfirmDate").replace("Z", "+00:00"))
        except:
            pass

        # 반품 배송비 파싱
        return_shipping_charge = None
        return_shipping_charge_currency = None
        shipping_charge_obj = return_request.get("returnShippingCharge")
        if shipping_charge_obj:
            try:
                units = shipping_charge_obj.get("units", 0)
                nanos = shipping_charge_obj.get("nanos", 0)
                return_shipping_charge = float(units) + (float(nanos) / 1_000_000_000)
                return_shipping_charge_currency = shipping_charge_obj.get("currencyCode")
            except:
                pass

        # 동봉 배송비 파싱
        enclose_price = None
        enclose_price_currency = None
        enclose_obj = return_request.get("enclosePrice")
        if enclose_obj:
            try:
                units = enclose_obj.get("units", 0)
                nanos = enclose_obj.get("nanos", 0)
                enclose_price = float(units) + (float(nanos) / 1_000_000_000)
                enclose_price_currency = enclose_obj.get("currencyCode")
            except:
                pass

        return_log = ReturnLog(
            # 쿠팡 정보
            coupang_receipt_id=return_request.get("receiptId"),
            coupang_order_id=return_request.get("orderId"),
            coupang_payment_id=return_request.get("paymentId"),
            coupang_created_at=coupang_created_at,
            coupang_modified_at=coupang_modified_at,

            # 상품 정보
            product_name=item.get("vendorItemName") or item.get("vendorItemPackageName", ""),
            vendor_item_id=item.get("vendorItemId"),
            vendor_item_package_id=item.get("vendorItemPackageId"),
            vendor_item_package_name=item.get("vendorItemPackageName"),
            seller_product_id=item.get("sellerProductId"),
            seller_product_name=item.get("sellerProductName"),
            cancel_count=item.get("cancelCount", 1),
            cancel_count_sum=return_request.get("cancelCountSum"),
            purchase_count=item.get("purchaseCount"),
            shipment_box_id=item.get("shipmentBoxId"),
            release_status=item.get("releaseStatus"),

            # 수령인/회수지 정보
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            receiver_real_phone=receiver_real_phone,
            receiver_address=receiver_address,
            receiver_address_detail=receiver_address_detail,
            receiver_zipcode=receiver_zipcode,

            # 반품 상태
            receipt_type=return_request.get("receiptType"),
            receipt_status=return_request.get("receiptStatus"),
            release_stop_status=return_request.get("releaseStopStatus"),

            # 반품 사유
            cancel_reason_category1=return_request.get("cancelReasonCategory1"),
            cancel_reason_category2=return_request.get("cancelReasonCategory2"),
            cancel_reason=return_request.get("cancelReason"),
            reason_code=return_request.get("reasonCode"),
            reason_code_text=return_request.get("reasonCodeText"),

            # 귀책 및 환불 정보
            fault_by_type=return_request.get("faultByType"),
            pre_refund=return_request.get("preRefund"),
            return_shipping_charge=return_shipping_charge,
            return_shipping_charge_currency=return_shipping_charge_currency,
            enclose_price=enclose_price,
            enclose_price_currency=enclose_price_currency,

            # 배송 정보
            return_delivery_id=return_request.get("returnDeliveryId"),
            return_delivery_type=return_request.get("returnDeliveryType"),
            return_delivery_dtos=return_request.get("returnDeliveryDtos"),

            # 완료 확인 정보
            complete_confirm_type=return_request.get("completeConfirmType"),
            complete_confirm_date=complete_confirm_date,
            cancel_complete_user=item.get("cancelCompleteUser"),

            # 네이버 처리 정보
            naver_processed=False,
            status="pending",
            raw_data=return_request,
        )

        self.db.add(return_log)
        return return_log

    def _update_return_log(self, existing: ReturnLog, return_request: Dict, item: Dict):
        """기존 반품 로그 업데이트"""
        from datetime import datetime

        # 상태가 변경된 경우에만 업데이트
        new_status = return_request.get("receiptStatus")
        updated = False

        if existing.receipt_status != new_status:
            logger.info(f"Receipt {existing.coupang_receipt_id} 상태 변경: {existing.receipt_status} -> {new_status}")
            existing.receipt_status = new_status
            updated = True

            # 완료된 상태로 변경되었고 아직 처리되지 않았다면 처리 불필요로 표시
            if new_status == "RETURNS_COMPLETED" and not existing.naver_processed:
                existing.status = "skipped"
                logger.info(f"Receipt {existing.coupang_receipt_id} 이미 완료된 상태로 스킵")

        # 수령인 정보 업데이트 (누락된 정보 보완)
        receiver_name = return_request.get("requesterName")
        receiver_phone = return_request.get("requesterPhoneNumber")
        receiver_real_phone = return_request.get("requesterRealPhoneNumber")
        receiver_address = return_request.get("requesterAddress")
        receiver_address_detail = return_request.get("requesterAddressDetail")
        receiver_zipcode = return_request.get("requesterZipCode")

        if receiver_name and existing.receiver_name != receiver_name:
            existing.receiver_name = receiver_name
            updated = True
        if receiver_phone and existing.receiver_phone != receiver_phone:
            existing.receiver_phone = receiver_phone
            updated = True
        if receiver_real_phone and existing.receiver_real_phone != receiver_real_phone:
            existing.receiver_real_phone = receiver_real_phone
            updated = True
        if receiver_address and existing.receiver_address != receiver_address:
            existing.receiver_address = receiver_address
            updated = True
        if receiver_address_detail and existing.receiver_address_detail != receiver_address_detail:
            existing.receiver_address_detail = receiver_address_detail
            updated = True
        if receiver_zipcode and existing.receiver_zipcode != receiver_zipcode:
            existing.receiver_zipcode = receiver_zipcode
            updated = True

        # 다른 필드들도 업데이트
        if return_request.get("modifiedAt"):
            try:
                coupang_modified_at = datetime.fromisoformat(return_request.get("modifiedAt").replace("Z", "+00:00"))
                if existing.coupang_modified_at != coupang_modified_at:
                    existing.coupang_modified_at = coupang_modified_at
                    updated = True
            except:
                pass

        # 완료 확인 정보 업데이트
        if return_request.get("completeConfirmType") and existing.complete_confirm_type != return_request.get("completeConfirmType"):
            existing.complete_confirm_type = return_request.get("completeConfirmType")
            updated = True

        if return_request.get("completeConfirmDate"):
            try:
                complete_confirm_date = datetime.fromisoformat(return_request.get("completeConfirmDate").replace("Z", "+00:00"))
                if existing.complete_confirm_date != complete_confirm_date:
                    existing.complete_confirm_date = complete_confirm_date
                    updated = True
            except:
                pass

        # 배송 정보 업데이트
        if return_request.get("returnDeliveryDtos") and existing.return_delivery_dtos != return_request.get("returnDeliveryDtos"):
            existing.return_delivery_dtos = return_request.get("returnDeliveryDtos")
            updated = True

        # raw_data는 항상 최신으로 유지
        if updated:
            existing.raw_data = return_request

    def get_pending_returns(
        self,
        config: Optional[AutoReturnConfig] = None,
        limit: Optional[int] = None
    ) -> List[ReturnLog]:
        """
        처리 대기 중인 반품 목록 조회

        Args:
            config: 자동화 설정 (필터링용)
            limit: 최대 개수

        Returns:
            반품 로그 리스트
        """
        query = self.db.query(ReturnLog).filter(
            ReturnLog.status == "pending",
            ReturnLog.naver_processed == False
        )

        # 설정이 있으면 상태 필터링
        if config:
            # 자동 처리할 상태만 포함
            if config.auto_process_statuses:
                query = query.filter(
                    ReturnLog.receipt_status.in_(config.auto_process_statuses)
                )

            # 제외할 상태 필터링
            if config.exclude_statuses:
                query = query.filter(
                    ~ReturnLog.receipt_status.in_(config.exclude_statuses)
                )

        # 생성 시간 순으로 정렬 (오래된 것부터)
        query = query.order_by(ReturnLog.created_at.asc())

        # 개수 제한
        if limit:
            query = query.limit(limit)

        return query.all()

    def get_statistics(self) -> Dict:
        """수집 통계 조회"""
        total = self.db.query(ReturnLog).count()
        pending = self.db.query(ReturnLog).filter(
            ReturnLog.status == "pending",
            ReturnLog.naver_processed == False
        ).count()
        processed = self.db.query(ReturnLog).filter(
            ReturnLog.naver_processed == True
        ).count()
        failed = self.db.query(ReturnLog).filter(
            ReturnLog.status == "failed"
        ).count()

        # 최근 24시간 수집 건수
        yesterday = datetime.now() - timedelta(days=1)
        recent_24h = self.db.query(ReturnLog).filter(
            ReturnLog.created_at >= yesterday
        ).count()

        return {
            "total": total,
            "pending": pending,
            "processed": processed,
            "failed": failed,
            "recent_24h": recent_24h,
        }
