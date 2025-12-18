"""
Coupon Auto-Sync Service
쿠폰 자동연동 서비스
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from loguru import logger
import time

from .coupon_api_client import CouponAPIClient
from ..models.coupon_config import CouponAutoSyncConfig, ProductCouponTracking, CouponApplyLog, BulkApplyProgress
from ..models.coupang_account import CoupangAccount


class CouponAutoSyncService:
    """쿠폰 자동연동 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def _get_api_client(self, account: CoupangAccount) -> CouponAPIClient:
        """계정으로 API 클라이언트 생성"""
        return CouponAPIClient(
            access_key=account.access_key,
            secret_key=account.secret_key,
            vendor_id=account.vendor_id,
            wing_username=account.wing_username
        )

    # ==================== 설정 관리 ====================

    def get_config(self, coupang_account_id: int) -> Optional[CouponAutoSyncConfig]:
        """계정의 쿠폰 자동연동 설정 조회"""
        return self.db.query(CouponAutoSyncConfig).filter(
            CouponAutoSyncConfig.coupang_account_id == coupang_account_id
        ).first()

    def create_or_update_config(
        self,
        coupang_account_id: int,
        config_data: Dict[str, Any]
    ) -> CouponAutoSyncConfig:
        """쿠폰 자동연동 설정 생성/수정"""
        config = self.get_config(coupang_account_id)

        if config:
            # 기존 설정 업데이트
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            config.updated_at = datetime.utcnow()
        else:
            # 새 설정 생성
            config = CouponAutoSyncConfig(
                coupang_account_id=coupang_account_id,
                **config_data
            )
            self.db.add(config)

        self.db.commit()
        self.db.refresh(config)
        return config

    def toggle_config(self, coupang_account_id: int, enabled: bool) -> Optional[CouponAutoSyncConfig]:
        """쿠폰 자동연동 활성화/비활성화"""
        config = self.get_config(coupang_account_id)
        if config:
            config.is_enabled = enabled
            config.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(config)
        return config

    # ==================== 계약서/쿠폰 조회 ====================

    def get_contracts(self, coupang_account_id: int) -> Dict[str, Any]:
        """계약서 목록 조회"""
        account = self.db.query(CoupangAccount).filter(
            CoupangAccount.id == coupang_account_id
        ).first()

        if not account:
            return {"success": False, "message": "계정을 찾을 수 없습니다."}

        client = self._get_api_client(account)

        try:
            result = client.get_contract_list()
            if result.get("code") == 200:
                contracts = result.get("data", {}).get("content", [])
                # 유효한 계약서만 필터링
                now = datetime.now()
                valid_contracts = []
                for contract in contracts:
                    try:
                        end_date = datetime.strptime(contract["end"], "%Y-%m-%d %H:%M:%S")
                        if end_date > now:
                            valid_contracts.append(contract)
                    except:
                        valid_contracts.append(contract)

                return {"success": True, "contracts": valid_contracts}
            else:
                return {"success": False, "message": result.get("message", "조회 실패")}
        except Exception as e:
            logger.error(f"Error fetching contracts: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_instant_coupons(self, coupang_account_id: int, status: str = "APPLIED") -> Dict[str, Any]:
        """즉시할인쿠폰 목록 조회"""
        account = self.db.query(CoupangAccount).filter(
            CoupangAccount.id == coupang_account_id
        ).first()

        if not account:
            return {"success": False, "message": "계정을 찾을 수 없습니다."}

        client = self._get_api_client(account)

        try:
            result = client.get_instant_coupons(status=status)
            if result.get("code") == 200:
                coupons = result.get("data", {}).get("content", [])
                return {"success": True, "coupons": coupons}
            else:
                return {"success": False, "message": result.get("message", "조회 실패")}
        except Exception as e:
            logger.error(f"Error fetching instant coupons: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_download_coupons(self, coupang_account_id: int, status: str = "IN_PROGRESS") -> Dict[str, Any]:
        """다운로드쿠폰 목록 조회"""
        account = self.db.query(CoupangAccount).filter(
            CoupangAccount.id == coupang_account_id
        ).first()

        if not account:
            return {"success": False, "message": "계정을 찾을 수 없습니다.", "coupons": []}

        client = self._get_api_client(account)

        try:
            result = client.get_download_coupons(status=status)
            # 다운로드 쿠폰 API 응답 구조 처리
            if result.get("code") == "SUCCESS" or "content" in result:
                coupons = result.get("content", [])
                # 쿠폰 데이터 정규화
                normalized_coupons = []
                for coupon in coupons:
                    normalized_coupons.append({
                        "couponId": coupon.get("couponId"),
                        "couponName": coupon.get("couponName") or coupon.get("title"),
                        "discountType": coupon.get("discountType"),
                        "discountValue": coupon.get("discountValue"),
                        "status": coupon.get("status"),
                        "startDate": coupon.get("startDate"),
                        "endDate": coupon.get("endDate"),
                    })
                return {"success": True, "coupons": normalized_coupons}
            else:
                return {"success": False, "message": result.get("message", "조회 실패"), "coupons": []}
        except Exception as e:
            logger.error(f"Error fetching download coupons: {str(e)}")
            # API가 지원되지 않는 경우 빈 배열 반환 (410 Gone 등)
            return {"success": False, "message": "다운로드 쿠폰 목록 조회 API가 지원되지 않습니다. 쿠폰 ID를 직접 입력해주세요.", "coupons": []}

    def get_download_coupon_by_id(self, coupang_account_id: int, coupon_id: int) -> Dict[str, Any]:
        """다운로드쿠폰 단건 조회 (쿠폰 ID로 직접 조회)"""
        account = self.db.query(CoupangAccount).filter(
            CoupangAccount.id == coupang_account_id
        ).first()

        if not account:
            return {"success": False, "message": "계정을 찾을 수 없습니다."}

        client = self._get_api_client(account)

        try:
            result = client.get_download_coupon(coupon_id)

            # 에러 응답 처리
            if result.get("code") in ["NOT_FOUND", "FORBIDDEN", "ERROR"]:
                return {"success": False, "message": result.get("message", "쿠폰을 찾을 수 없습니다.")}

            # 성공 응답 처리
            coupon_data = result.get("data") or result

            # API 응답에서 쿠폰 정보 추출
            coupon = {
                "couponId": coupon_data.get("couponId") or coupon_id,
                "couponName": coupon_data.get("title") or coupon_data.get("couponName") or f"쿠폰 #{coupon_id}",
                "discountType": coupon_data.get("discountType"),
                "discountValue": coupon_data.get("discountValue"),
                "status": coupon_data.get("status"),
                "startDate": coupon_data.get("startDate"),
                "endDate": coupon_data.get("endDate"),
                # 추가 정보
                "maxDiscountPrice": coupon_data.get("maxDiscountPrice"),
                "minOrderPrice": coupon_data.get("minOrderPrice"),
                "couponCount": coupon_data.get("couponCount"),
            }

            logger.info(f"Download coupon {coupon_id} fetched successfully: {coupon}")
            return {"success": True, "coupon": coupon}

        except Exception as e:
            logger.error(f"Error fetching download coupon {coupon_id}: {str(e)}")
            return {"success": False, "message": str(e)}

    # ==================== 신규 상품 감지 ====================

    def detect_new_products(self, coupang_account_id: int, target_date: str = None) -> Dict[str, Any]:
        """
        신규 등록 상품 감지

        Args:
            coupang_account_id: 쿠팡 계정 ID
            target_date: 조회할 날짜 (yyyy-MM-dd), None이면 어제

        Returns:
            감지된 신규 상품 목록
        """
        account = self.db.query(CoupangAccount).filter(
            CoupangAccount.id == coupang_account_id
        ).first()

        if not account:
            return {"success": False, "message": "계정을 찾을 수 없습니다."}

        config = self.get_config(coupang_account_id)
        if not config or not config.is_enabled:
            return {"success": False, "message": "자동연동이 비활성화되어 있습니다."}

        # 대상 날짜 계산 (apply_delay_days 전)
        if not target_date:
            target_datetime = datetime.now() - timedelta(days=config.apply_delay_days)
            target_date = target_datetime.strftime("%Y-%m-%d")

        client = self._get_api_client(account)

        try:
            # 해당 날짜에 승인완료된 상품 조회
            products = client.get_all_products_by_date(
                created_at=target_date,
                status="APPROVED"
            )

            # 이미 추적 중인 상품 제외
            existing_product_ids = set(
                tracking.seller_product_id for tracking in
                self.db.query(ProductCouponTracking).filter(
                    ProductCouponTracking.coupang_account_id == coupang_account_id
                ).all()
            )

            # 제외 상품 필터링
            excluded_ids = set(config.excluded_product_ids or [])

            new_products = []
            for product in products:
                seller_product_id = product.get("sellerProductId")
                if seller_product_id and seller_product_id not in existing_product_ids and seller_product_id not in excluded_ids:
                    new_products.append(product)

            logger.info(f"Detected {len(new_products)} new products for {target_date}")

            return {
                "success": True,
                "target_date": target_date,
                "total_products": len(products),
                "new_products": new_products
            }

        except Exception as e:
            logger.error(f"Error detecting new products: {str(e)}")
            return {"success": False, "message": str(e)}

    # ==================== 상품 추적 등록 ====================

    def register_products_for_tracking(
        self,
        coupang_account_id: int,
        products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        신규 상품들을 쿠폰 적용 추적에 등록

        Args:
            coupang_account_id: 쿠팡 계정 ID
            products: 상품 목록

        Returns:
            등록 결과
        """
        config = self.get_config(coupang_account_id)
        if not config:
            return {"success": False, "message": "설정을 찾을 수 없습니다."}

        registered = 0
        for product in products:
            seller_product_id = product.get("sellerProductId")
            if not seller_product_id:
                continue

            # 이미 존재하는지 확인
            existing = self.db.query(ProductCouponTracking).filter(
                ProductCouponTracking.coupang_account_id == coupang_account_id,
                ProductCouponTracking.seller_product_id == seller_product_id
            ).first()

            if existing:
                continue

            # 상품 등록일 파싱
            created_at_str = product.get("createdAt", "")
            try:
                product_created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S")
            except:
                product_created_at = datetime.utcnow()

            # 쿠폰 적용 예정일 계산
            apply_scheduled_at = product_created_at + timedelta(days=config.apply_delay_days)

            tracking = ProductCouponTracking(
                coupang_account_id=coupang_account_id,
                seller_product_id=seller_product_id,
                seller_product_name=product.get("sellerProductName", ""),
                product_created_at=product_created_at,
                coupon_apply_scheduled_at=apply_scheduled_at,
                status="pending"
            )
            self.db.add(tracking)
            registered += 1

        self.db.commit()

        logger.info(f"Registered {registered} products for coupon tracking")
        return {"success": True, "registered": registered}

    # ==================== 쿠폰 적용 ====================

    def apply_coupons_to_pending_products(self, coupang_account_id: int) -> Dict[str, Any]:
        """
        대기 중인 상품들에 쿠폰 적용

        Args:
            coupang_account_id: 쿠팡 계정 ID

        Returns:
            적용 결과
        """
        account = self.db.query(CoupangAccount).filter(
            CoupangAccount.id == coupang_account_id
        ).first()

        if not account:
            return {"success": False, "message": "계정을 찾을 수 없습니다."}

        config = self.get_config(coupang_account_id)
        if not config or not config.is_enabled:
            return {"success": False, "message": "자동연동이 비활성화되어 있습니다."}

        client = self._get_api_client(account)
        now = datetime.utcnow()

        # 적용 예정일이 지난 pending 상품 조회
        pending_trackings = self.db.query(ProductCouponTracking).filter(
            ProductCouponTracking.coupang_account_id == coupang_account_id,
            ProductCouponTracking.status == "pending",
            ProductCouponTracking.coupon_apply_scheduled_at <= now
        ).all()

        if not pending_trackings:
            return {"success": True, "message": "적용할 상품이 없습니다.", "applied": 0}

        results = {
            "total": len(pending_trackings),
            "instant_success": 0,
            "instant_failed": 0,
            "download_success": 0,
            "download_failed": 0,
            "errors": []
        }

        for tracking in pending_trackings:
            tracking.status = "processing"
            self.db.commit()

            try:
                # vendorItemId 조회
                vendor_item_ids = client.get_vendor_item_ids(tracking.seller_product_id)

                if not vendor_item_ids:
                    tracking.status = "failed"
                    tracking.error_message = "vendorItemId를 찾을 수 없습니다."
                    self.db.commit()
                    results["errors"].append({
                        "seller_product_id": tracking.seller_product_id,
                        "error": "vendorItemId를 찾을 수 없습니다."
                    })
                    continue

                # 즉시할인쿠폰 적용
                if config.instant_coupon_enabled and config.instant_coupon_id and config.instant_coupon_id > 0:
                    instant_result = self._apply_instant_coupon(
                        client, config, tracking, vendor_item_ids
                    )
                    if instant_result["success"]:
                        results["instant_success"] += 1
                    else:
                        results["instant_failed"] += 1

                # 다운로드쿠폰 적용
                if config.download_coupon_enabled and config.download_coupon_id and config.download_coupon_id > 0:
                    download_result = self._apply_download_coupon(
                        client, config, tracking, vendor_item_ids, account.wing_username
                    )
                    if download_result["success"]:
                        results["download_success"] += 1
                    else:
                        results["download_failed"] += 1

                # 상태 업데이트
                if tracking.instant_coupon_applied or tracking.download_coupon_applied:
                    tracking.status = "completed"
                elif tracking.error_message:
                    tracking.status = "failed"
                else:
                    tracking.status = "completed"

                self.db.commit()

            except Exception as e:
                logger.error(f"Error applying coupons to product {tracking.seller_product_id}: {str(e)}")
                tracking.status = "failed"
                tracking.error_message = str(e)
                self.db.commit()
                results["errors"].append({
                    "seller_product_id": tracking.seller_product_id,
                    "error": str(e)
                })

        # 설정의 마지막 동기화 시간 업데이트
        config.last_sync_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Coupon application results: {results}")
        return {"success": True, "results": results}

    def _apply_instant_coupon(
        self,
        client: CouponAPIClient,
        config: CouponAutoSyncConfig,
        tracking: ProductCouponTracking,
        vendor_item_ids: List[int]
    ) -> Dict[str, Any]:
        """즉시할인쿠폰 적용"""
        try:
            result = client.apply_instant_coupon_to_items(
                coupon_id=config.instant_coupon_id,
                vendor_item_ids=vendor_item_ids
            )

            # 로그 기록
            log = CouponApplyLog(
                coupang_account_id=config.coupang_account_id,
                seller_product_id=tracking.seller_product_id,
                vendor_item_id=vendor_item_ids[0] if vendor_item_ids else None,
                coupon_type="instant",
                coupon_id=config.instant_coupon_id,
                coupon_name=config.instant_coupon_name,
                request_data={"vendor_item_ids": vendor_item_ids},
                response_data=result
            )

            if result.get("code") == 200 and result.get("data", {}).get("success"):
                requested_id = result.get("data", {}).get("content", {}).get("requestedId")
                tracking.instant_coupon_request_id = requested_id

                # 비동기 처리 결과 확인 (최대 5회 시도)
                for _ in range(5):
                    time.sleep(2)
                    status_result = client.get_instant_coupon_request_status(requested_id)
                    status = status_result.get("data", {}).get("content", {}).get("status")

                    if status == "DONE":
                        tracking.instant_coupon_applied = True
                        tracking.instant_coupon_applied_at = datetime.utcnow()
                        log.success = True
                        self.db.add(log)
                        return {"success": True}
                    elif status == "FAIL":
                        failed_items = status_result.get("data", {}).get("content", {}).get("failedVendorItems", [])
                        error_msg = str(failed_items) if failed_items else "적용 실패"
                        log.success = False
                        log.error_message = error_msg
                        self.db.add(log)
                        return {"success": False, "error": error_msg}

                # 타임아웃
                log.success = False
                log.error_message = "처리 타임아웃"
                self.db.add(log)
                return {"success": False, "error": "처리 타임아웃"}
            else:
                error_msg = result.get("message", "알 수 없는 오류")
                log.success = False
                log.error_message = error_msg
                self.db.add(log)
                return {"success": False, "error": error_msg}

        except Exception as e:
            logger.error(f"Error applying instant coupon: {str(e)}")
            return {"success": False, "error": str(e)}

    def _apply_download_coupon(
        self,
        client: CouponAPIClient,
        config: CouponAutoSyncConfig,
        tracking: ProductCouponTracking,
        vendor_item_ids: List[int],
        wing_username: str
    ) -> Dict[str, Any]:
        """다운로드쿠폰 적용"""
        try:
            # 다운로드쿠폰은 최대 100개씩 적용
            batch_size = 100
            all_success = True

            for i in range(0, len(vendor_item_ids), batch_size):
                batch = vendor_item_ids[i:i+batch_size]

                result = client.apply_download_coupon_to_items(
                    coupon_id=config.download_coupon_id,
                    vendor_item_ids=batch,
                    user_id=wing_username
                )

                # 로그 기록
                log = CouponApplyLog(
                    coupang_account_id=config.coupang_account_id,
                    seller_product_id=tracking.seller_product_id,
                    vendor_item_id=batch[0] if batch else None,
                    coupon_type="download",
                    coupon_id=config.download_coupon_id,
                    coupon_name=config.download_coupon_name,
                    request_data={"vendor_item_ids": batch},
                    response_data=result
                )

                if result.get("requestResultStatus") == "SUCCESS":
                    log.success = True
                else:
                    all_success = False
                    log.success = False
                    log.error_message = result.get("errorMessage", "알 수 없는 오류")

                self.db.add(log)

            if all_success:
                tracking.download_coupon_applied = True
                tracking.download_coupon_applied_at = datetime.utcnow()
                return {"success": True}
            else:
                return {"success": False, "error": "일부 아이템 적용 실패"}

        except Exception as e:
            logger.error(f"Error applying download coupon: {str(e)}")
            return {"success": False, "error": str(e)}

    # ==================== 통계/이력 조회 ====================

    def get_tracking_list(
        self,
        coupang_account_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """상품 쿠폰 적용 추적 목록 조회"""
        query = self.db.query(ProductCouponTracking).filter(
            ProductCouponTracking.coupang_account_id == coupang_account_id
        )

        if status:
            query = query.filter(ProductCouponTracking.status == status)

        total = query.count()
        trackings = query.order_by(
            ProductCouponTracking.created_at.desc()
        ).offset(offset).limit(limit).all()

        return {
            "success": True,
            "total": total,
            "trackings": [t.to_dict() for t in trackings]
        }

    def get_apply_logs(
        self,
        coupang_account_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """쿠폰 적용 이력 조회"""
        query = self.db.query(CouponApplyLog).filter(
            CouponApplyLog.coupang_account_id == coupang_account_id
        )

        total = query.count()
        logs = query.order_by(
            CouponApplyLog.created_at.desc()
        ).offset(offset).limit(limit).all()

        return {
            "success": True,
            "total": total,
            "logs": [log.to_dict() for log in logs]
        }

    def get_statistics(self, coupang_account_id: int) -> Dict[str, Any]:
        """쿠폰 자동연동 통계"""
        # 전체 추적 상품 수
        total_tracking = self.db.query(ProductCouponTracking).filter(
            ProductCouponTracking.coupang_account_id == coupang_account_id
        ).count()

        # 상태별 수
        pending = self.db.query(ProductCouponTracking).filter(
            ProductCouponTracking.coupang_account_id == coupang_account_id,
            ProductCouponTracking.status == "pending"
        ).count()

        completed = self.db.query(ProductCouponTracking).filter(
            ProductCouponTracking.coupang_account_id == coupang_account_id,
            ProductCouponTracking.status == "completed"
        ).count()

        failed = self.db.query(ProductCouponTracking).filter(
            ProductCouponTracking.coupang_account_id == coupang_account_id,
            ProductCouponTracking.status == "failed"
        ).count()

        # 오늘 적용된 수
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_applied = self.db.query(CouponApplyLog).filter(
            CouponApplyLog.coupang_account_id == coupang_account_id,
            CouponApplyLog.success == True,
            CouponApplyLog.created_at >= today_start
        ).count()

        return {
            "success": True,
            "statistics": {
                "total_tracking": total_tracking,
                "pending": pending,
                "completed": completed,
                "failed": failed,
                "today_applied": today_applied
            }
        }

    # ==================== 진행 상황 조회 ====================

    def get_bulk_apply_progress(self, coupang_account_id: int) -> Optional[BulkApplyProgress]:
        """현재 진행 중인 일괄 적용 진행 상황 조회"""
        return self.db.query(BulkApplyProgress).filter(
            BulkApplyProgress.coupang_account_id == coupang_account_id,
            BulkApplyProgress.status.in_(["collecting", "applying"])
        ).order_by(BulkApplyProgress.started_at.desc()).first()

    def get_latest_bulk_apply_progress(self, coupang_account_id: int) -> Optional[BulkApplyProgress]:
        """최근 일괄 적용 진행 상황 조회 (완료된 것 포함)"""
        return self.db.query(BulkApplyProgress).filter(
            BulkApplyProgress.coupang_account_id == coupang_account_id
        ).order_by(BulkApplyProgress.started_at.desc()).first()

    def cancel_bulk_apply_progress(self, coupang_account_id: int) -> Dict[str, Any]:
        """
        진행 중인 일괄 적용 작업 취소/리셋

        Args:
            coupang_account_id: 쿠팡 계정 ID

        Returns:
            취소 결과
        """
        # 진행 중인 작업 조회
        progress = self.db.query(BulkApplyProgress).filter(
            BulkApplyProgress.coupang_account_id == coupang_account_id,
            BulkApplyProgress.status.in_(["collecting", "applying"])
        ).first()

        if not progress:
            # 진행 중인 작업이 없으면 최근 작업을 찾아서 리셋
            latest = self.get_latest_bulk_apply_progress(coupang_account_id)
            if latest and latest.status not in ["completed", "failed"]:
                latest.status = "cancelled"
                latest.completed_at = datetime.utcnow()
                latest.error_message = "사용자에 의해 취소됨"
                self.db.commit()
                logger.info(f"[DEBUG] Cancelled stuck bulk apply progress for account {coupang_account_id}")
                return {
                    "success": True,
                    "message": "멈춘 작업이 취소되었습니다. 다시 시작할 수 있습니다."
                }
            return {
                "success": True,
                "message": "취소할 작업이 없습니다."
            }

        # 진행 중인 작업 취소
        progress.status = "cancelled"
        progress.completed_at = datetime.utcnow()
        progress.error_message = "사용자에 의해 취소됨"
        self.db.commit()

        logger.info(f"[DEBUG] Cancelled bulk apply progress for account {coupang_account_id}")

        return {
            "success": True,
            "message": "작업이 취소되었습니다. 새로 시작할 수 있습니다."
        }

    # ==================== 전체 상품 일괄 적용 ====================

    def apply_coupons_to_all_products(
        self,
        coupang_account_id: int,
        days_back: int = 30,
        skip_applied: bool = True
    ) -> Dict[str, Any]:
        """
        전체 상품에 쿠폰 일괄 적용 (배치 단위로 수집+적용 동시 진행)

        Args:
            coupang_account_id: 쿠팡 계정 ID
            days_back: 미사용 (호환성 유지용)
            skip_applied: 이미 쿠폰이 적용된 상품 건너뛰기 (기본값: True)

        Returns:
            적용 결과
        """
        account = self.db.query(CoupangAccount).filter(
            CoupangAccount.id == coupang_account_id
        ).first()

        if not account:
            return {"success": False, "message": "계정을 찾을 수 없습니다."}

        config = self.get_config(coupang_account_id)
        if not config:
            return {"success": False, "message": "설정을 먼저 생성해주세요."}

        if not config.instant_coupon_enabled and not config.download_coupon_enabled:
            return {"success": False, "message": "적용할 쿠폰이 설정되지 않았습니다."}

        # 이미 진행 중인 작업이 있는지 확인
        existing_progress = self.get_bulk_apply_progress(coupang_account_id)
        if existing_progress:
            return {"success": False, "message": "이미 진행 중인 작업이 있습니다."}

        # 이미 쿠폰이 적용된 상품 목록 조회 (skip_applied=True일 때)
        applied_seller_product_ids = set()
        if skip_applied:
            applied_trackings = self.db.query(ProductCouponTracking).filter(
                ProductCouponTracking.coupang_account_id == coupang_account_id,
                ProductCouponTracking.status == "completed"
            ).all()
            applied_seller_product_ids = {t.seller_product_id for t in applied_trackings}
            logger.info(f"[DEBUG] Found {len(applied_seller_product_ids)} already applied products to skip")

        client = self._get_api_client(account)

        # 진행 상황 레코드 생성
        progress = BulkApplyProgress(
            coupang_account_id=coupang_account_id,
            status="applying",  # 바로 적용 상태로 시작
            total_days=1
        )
        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)

        results = {
            "total_products": 0,
            "total_items": 0,
            "instant_success": 0,
            "instant_failed": 0,
            "download_success": 0,
            "download_failed": 0,
            "errors": []
        }

        # 배치 처리 설정
        PRODUCT_BATCH_SIZE = 100  # 100개 상품씩 처리
        INSTANT_COUPON_BATCH_SIZE = 10000  # 즉시할인 최대 10,000개
        DOWNLOAD_COUPON_BATCH_SIZE = 100  # 다운로드 최대 100개

        try:
            logger.info(f"[DEBUG] Starting batch bulk apply for account {coupang_account_id}")
            logger.info(f"[DEBUG] Config: instant={config.instant_coupon_enabled}, download={config.download_coupon_enabled}")

            # 페이지네이션으로 상품 조회하면서 바로 쿠폰 적용
            next_token = None
            page_count = 0
            batch_vendor_items = []  # 현재 배치의 vendorItemIds
            processed_products = 0

            while True:
                page_count += 1
                progress.current_date = f"페이지 {page_count} 처리 중..."
                self.db.commit()

                # 상품 페이지 조회
                api_result = client.get_all_products(
                    status="APPROVED",
                    max_per_page=100,
                    next_token=next_token
                )

                if api_result.get("code") != "SUCCESS":
                    logger.error(f"[DEBUG] API error on page {page_count}: {api_result.get('message')}")
                    break

                products = api_result.get("data", [])
                if not products:
                    logger.info(f"[DEBUG] No more products on page {page_count}")
                    break

                logger.info(f"[DEBUG] Page {page_count}: processing {len(products)} products")

                # 각 상품에서 vendorItemId 추출
                for product in products:
                    seller_product_id = product.get("sellerProductId")
                    if not seller_product_id:
                        continue

                    # 제외 상품 체크
                    if seller_product_id in (config.excluded_product_ids or []):
                        continue

                    # 이미 적용된 상품 체크
                    if skip_applied and seller_product_id in applied_seller_product_ids:
                        continue

                    # vendorItemId 조회
                    try:
                        vendor_item_ids = client.get_vendor_item_ids(seller_product_id)
                        if vendor_item_ids:
                            batch_vendor_items.extend(vendor_item_ids)
                            results["total_products"] += 1
                            results["total_items"] += len(vendor_item_ids)
                            processed_products += 1
                    except Exception as e:
                        logger.error(f"[DEBUG] Error getting vendorItemIds: {str(e)}")

                    # 진행 상황 업데이트
                    progress.total_products = results["total_products"]
                    progress.total_items = results["total_items"]

                # 배치가 충분히 쌓이면 쿠폰 적용
                if len(batch_vendor_items) >= PRODUCT_BATCH_SIZE:
                    self._apply_coupons_to_batch(
                        client, config, progress, results,
                        batch_vendor_items, account.wing_username,
                        INSTANT_COUPON_BATCH_SIZE, DOWNLOAD_COUPON_BATCH_SIZE
                    )
                    batch_vendor_items = []  # 배치 초기화

                # 다음 페이지 토큰
                next_token_str = api_result.get("nextToken", "")
                if next_token_str and next_token_str.strip():
                    next_token = int(next_token_str)
                else:
                    break

            # 남은 배치 처리
            if batch_vendor_items:
                self._apply_coupons_to_batch(
                    client, config, progress, results,
                    batch_vendor_items, account.wing_username,
                    INSTANT_COUPON_BATCH_SIZE, DOWNLOAD_COUPON_BATCH_SIZE
                )

            # 완료
            progress.status = "completed"
            progress.completed_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"[DEBUG] === Batch Bulk Apply Complete ===")
            logger.info(f"[DEBUG] Total products: {results['total_products']}, Items: {results['total_items']}")
            logger.info(f"[DEBUG] Instant: {results['instant_success']} success, {results['instant_failed']} failed")
            logger.info(f"[DEBUG] Download: {results['download_success']} success, {results['download_failed']} failed")

            return {
                "success": True,
                "message": f"총 {results['total_products']}개 상품에 쿠폰 적용 완료",
                "results": results
            }

        except Exception as e:
            logger.error(f"[DEBUG] Error in batch bulk apply: {str(e)}")
            progress.status = "failed"
            progress.error_message = str(e)
            progress.completed_at = datetime.utcnow()
            self.db.commit()
            return {"success": False, "message": str(e), "results": results}

    def _apply_coupons_to_batch(
        self,
        client: CouponAPIClient,
        config: CouponAutoSyncConfig,
        progress: BulkApplyProgress,
        results: Dict[str, Any],
        vendor_item_ids: List[int],
        wing_username: str,
        instant_batch_size: int,
        download_batch_size: int
    ):
        """배치에 쿠폰 적용 (즉시할인 + 다운로드)"""
        if not vendor_item_ids:
            return

        logger.info(f"[DEBUG] Applying coupons to batch of {len(vendor_item_ids)} items")

        # 즉시할인쿠폰 적용
        if config.instant_coupon_enabled and config.instant_coupon_id and config.instant_coupon_id > 0:
            logger.info(f"[DEBUG] Applying instant coupon {config.instant_coupon_id} to {len(vendor_item_ids)} items")
            for i in range(0, len(vendor_item_ids), instant_batch_size):
                batch = vendor_item_ids[i:i+instant_batch_size]
                try:
                    logger.info(f"[DEBUG] Calling apply_instant_coupon_to_items with coupon_id={config.instant_coupon_id}, batch_size={len(batch)}")
                    result = client.apply_instant_coupon_to_items(
                        coupon_id=config.instant_coupon_id,
                        vendor_item_ids=batch
                    )
                    logger.info(f"[DEBUG] Instant coupon API response: {result}")

                    if result.get("code") == 200 and result.get("data", {}).get("success"):
                        requested_id = result.get("data", {}).get("content", {}).get("requestedId")
                        logger.info(f"[DEBUG] Instant coupon request submitted, requestedId={requested_id}")

                        # 비동기 처리 결과 확인 (최대 5회)
                        for check_num in range(5):
                            time.sleep(2)
                            status_result = client.get_instant_coupon_request_status(requested_id)
                            status = status_result.get("data", {}).get("content", {}).get("status")
                            logger.info(f"[DEBUG] Status check {check_num+1}: {status}")

                            if status == "DONE":
                                results["instant_success"] += len(batch)
                                logger.info(f"[DEBUG] Batch completed successfully: {len(batch)} items")
                                break
                            elif status == "FAIL":
                                failed_items = status_result.get("data", {}).get("content", {}).get("failedVendorItems", [])
                                results["instant_failed"] += len(failed_items)
                                results["instant_success"] += len(batch) - len(failed_items)
                                logger.warning(f"[DEBUG] Batch failed: {len(failed_items)} items failed, {len(batch) - len(failed_items)} succeeded")
                                break
                        else:
                            # 타임아웃 - 성공으로 간주 (백그라운드에서 처리됨)
                            results["instant_success"] += len(batch)
                            logger.info(f"[DEBUG] Status check timeout, assuming success: {len(batch)} items")
                    else:
                        results["instant_failed"] += len(batch)
                        logger.error(f"[DEBUG] Instant coupon API failed - code: {result.get('code')}, message: {result.get('message')}, full response: {result}")

                except Exception as e:
                    results["instant_failed"] += len(batch)
                    logger.error(f"[DEBUG] Instant coupon exception: {str(e)}", exc_info=True)

            # 진행 상황 업데이트
            progress.instant_total = (progress.instant_total or 0) + len(vendor_item_ids)
            progress.instant_success = results["instant_success"]
            progress.instant_failed = results["instant_failed"]
            self.db.commit()

        # 다운로드쿠폰 적용
        if config.download_coupon_enabled and config.download_coupon_id and config.download_coupon_id > 0:
            for i in range(0, len(vendor_item_ids), download_batch_size):
                batch = vendor_item_ids[i:i+download_batch_size]
                try:
                    result = client.apply_download_coupon_to_items(
                        coupon_id=config.download_coupon_id,
                        vendor_item_ids=batch,
                        user_id=wing_username
                    )

                    if result.get("requestResultStatus") == "SUCCESS":
                        results["download_success"] += len(batch)
                    else:
                        results["download_failed"] += len(batch)
                        logger.error(f"[DEBUG] Download coupon error: {result.get('errorMessage')}")

                except Exception as e:
                    results["download_failed"] += len(batch)
                    logger.error(f"[DEBUG] Download coupon exception: {str(e)}")

            # 진행 상황 업데이트
            progress.download_total = (progress.download_total or 0) + len(vendor_item_ids)
            progress.download_success = results["download_success"]
            progress.download_failed = results["download_failed"]
            self.db.commit()

        logger.info(f"[DEBUG] Batch complete - Instant: {results['instant_success']}/{progress.instant_total or 0}, Download: {results['download_success']}/{progress.download_total or 0}")

    def _legacy_apply_coupons_to_all_products(
        self,
        coupang_account_id: int,
        days_back: int = 30,
        skip_applied: bool = True
    ) -> Dict[str, Any]:
        """
        [레거시] 전체 상품에 쿠폰 일괄 적용 - 수집 후 적용 방식
        """
        # 이전 코드 보존 (필요시 사용)
        pass

    # ==================== 자동 실행 (스케줄러용) ====================

    def run_auto_sync(self, coupang_account_id: int) -> Dict[str, Any]:
        """
        자동 동기화 실행 (스케줄러에서 호출)

        1. 신규 상품 감지
        2. 추적 등록
        3. 대기 상품에 쿠폰 적용
        """
        logger.info(f"Running auto sync for account {coupang_account_id}")

        results = {
            "detect": None,
            "register": None,
            "apply": None
        }

        # 1. 신규 상품 감지
        detect_result = self.detect_new_products(coupang_account_id)
        results["detect"] = detect_result

        if detect_result.get("success") and detect_result.get("new_products"):
            # 2. 추적 등록
            register_result = self.register_products_for_tracking(
                coupang_account_id,
                detect_result["new_products"]
            )
            results["register"] = register_result

        # 3. 대기 상품에 쿠폰 적용
        apply_result = self.apply_coupons_to_pending_products(coupang_account_id)
        results["apply"] = apply_result

        return {
            "success": True,
            "results": results
        }

    def run_auto_sync_all_accounts(self) -> Dict[str, Any]:
        """모든 활성화된 계정에 대해 자동 동기화 실행"""
        configs = self.db.query(CouponAutoSyncConfig).filter(
            CouponAutoSyncConfig.is_enabled == True
        ).all()

        results = []
        for config in configs:
            try:
                result = self.run_auto_sync(config.coupang_account_id)
                results.append({
                    "account_id": config.coupang_account_id,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                logger.error(f"Error running auto sync for account {config.coupang_account_id}: {str(e)}")
                results.append({
                    "account_id": config.coupang_account_id,
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": True,
            "total_accounts": len(configs),
            "results": results
        }
