"""
Naver Delivery Sync Service
네이버 배송 정보를 쿠팡 송장으로 자동 등록하는 통합 서비스
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
from loguru import logger
from sqlalchemy.orm import Session

from .naverpay_scraper import NaverPayScraper, get_scraper, scrape_logger
from .coupang_shipment_service import CoupangShipmentService
from ..models.naver_delivery_sync import (
    NaverDeliveryInfo,
    CoupangPendingOrder,
    get_coupang_courier_code
)


class NaverDeliverySyncService:
    """네이버 배송 → 쿠팡 송장 동기화 서비스"""

    def __init__(
        self,
        db: Session,
        coupang_access_key: str = None,
        coupang_secret_key: str = None,
        coupang_vendor_id: str = None
    ):
        self.db = db
        self.coupang_access_key = coupang_access_key
        self.coupang_secret_key = coupang_secret_key
        self.coupang_vendor_id = coupang_vendor_id
        self._scraper: Optional[NaverPayScraper] = None
        self._coupang_service: Optional[CoupangShipmentService] = None

    async def get_scraper(self) -> NaverPayScraper:
        """스크래퍼 인스턴스 가져오기"""
        if self._scraper is None:
            self._scraper = await get_scraper()
        return self._scraper

    def get_coupang_service(self) -> CoupangShipmentService:
        """쿠팡 서비스 인스턴스 가져오기"""
        if self._coupang_service is None:
            self._coupang_service = CoupangShipmentService(
                db=self.db,
                access_key=self.coupang_access_key,
                secret_key=self.coupang_secret_key,
                vendor_id=self.coupang_vendor_id
            )
        return self._coupang_service

    async def sync_deliveries(
        self,
        auto_upload: bool = False,
        naver_account_id: int = None,
        coupang_account_id: int = None
    ) -> AsyncGenerator[Dict, None]:
        """
        네이버 배송 정보 수집 및 쿠팡 주문 매칭 (스트리밍)

        Args:
            auto_upload: True면 매칭된 송장 자동 업로드
            naver_account_id: 네이버 계정 ID
            coupang_account_id: 쿠팡 계정 ID

        Yields:
            진행 상황 및 결과
        """
        try:
            yield {"type": "status", "message": "동기화 시작..."}

            # 1. 네이버 로그인 상태 확인
            scraper = await self.get_scraper()
            if not scraper.is_logged_in:
                logged_in = await scraper.ensure_logged_in()
                if not logged_in:
                    yield {"type": "error", "message": "네이버 로그인이 필요합니다"}
                    return

            yield {"type": "status", "message": "네이버 배송 정보 수집 중..."}

            # 2. 네이버에서 배송 정보 수집
            collected_deliveries = []
            async for result in scraper.scrape_deliveries():
                yield result  # 진행 상황 그대로 전달

                if result["type"] == "delivery":
                    delivery_data = result["data"]
                    collected_deliveries.append(delivery_data)

                    # DB에 저장
                    await self._save_delivery_info(
                        delivery_data,
                        naver_account_id=naver_account_id
                    )

            if not collected_deliveries:
                yield {"type": "status", "message": "수집된 배송 정보가 없습니다"}
                return

            yield {"type": "status", "message": f"{len(collected_deliveries)}건 수집 완료, 쿠팡 주문 매칭 중..."}

            # 3. 쿠팡 발주서 조회
            if self.coupang_access_key and self.coupang_secret_key and self.coupang_vendor_id:
                coupang_service = self.get_coupang_service()

                # 쿠팡 발주서 조회 (API)
                yield {"type": "status", "message": "쿠팡 발주서 조회 중..."}
                pending_orders = coupang_service.get_pending_orders(hours_back=24)
                yield {"type": "status", "message": f"쿠팡 발주서 {len(pending_orders)}건 조회됨"}

                # 4. 매칭 및 업로드
                matched_count = 0
                uploaded_count = 0

                for delivery in collected_deliveries:
                    # 수취인 이름으로 매칭
                    match_result = coupang_service.match_delivery_with_orders(
                        receiver_name=delivery["recipient"]
                    )

                    if match_result["matched"]:
                        matched_count += 1
                        matched_order = match_result["order"]

                        # DB 업데이트
                        await self._update_delivery_match(
                            tracking_number=delivery["tracking_number"],
                            coupang_order=matched_order,
                            confidence=match_result["confidence"],
                            coupang_account_id=coupang_account_id
                        )

                        yield {
                            "type": "matched",
                            "data": {
                                "naver_recipient": delivery["recipient"],
                                "coupang_recipient": matched_order.get("receiver_name"),
                                "tracking_number": delivery["tracking_number"],
                                "courier": delivery["courier"],
                                "confidence": match_result["confidence"],
                                "order_id": matched_order.get("order_id")
                            }
                        }

                        # 자동 업로드
                        if auto_upload:
                            courier_code = get_coupang_courier_code(delivery["courier"])
                            if courier_code:
                                upload_result = coupang_service.upload_invoice(
                                    shipment_box_id=matched_order["shipment_box_id"],
                                    order_id=matched_order["order_id"],
                                    vendor_item_id=matched_order["vendor_item_id"],
                                    courier_code=courier_code,
                                    tracking_number=delivery["tracking_number"]
                                )

                                if upload_result["success"]:
                                    uploaded_count += 1
                                    await self._update_delivery_uploaded(
                                        tracking_number=delivery["tracking_number"],
                                        result=upload_result
                                    )

                                yield {
                                    "type": "uploaded",
                                    "data": {
                                        "tracking_number": delivery["tracking_number"],
                                        "success": upload_result["success"],
                                        "error": upload_result.get("error")
                                    }
                                }
                            else:
                                yield {
                                    "type": "warning",
                                    "message": f"택배사 코드를 찾을 수 없음: {delivery['courier']}"
                                }

                yield {
                    "type": "complete",
                    "data": {
                        "collected": len(collected_deliveries),
                        "matched": matched_count,
                        "uploaded": uploaded_count if auto_upload else 0
                    }
                }
            else:
                yield {
                    "type": "warning",
                    "message": "쿠팡 API 키가 설정되지 않아 매칭을 건너뜁니다"
                }

                yield {
                    "type": "complete",
                    "data": {
                        "collected": len(collected_deliveries),
                        "matched": 0,
                        "uploaded": 0
                    }
                }

        except Exception as e:
            logger.error(f"동기화 오류: {e}")
            yield {"type": "error", "message": str(e)}

    async def _save_delivery_info(
        self,
        delivery_data: Dict,
        naver_account_id: int = None
    ):
        """배송 정보 DB 저장"""
        try:
            tracking_number = delivery_data.get("tracking_number")
            if not tracking_number:
                return

            # 기존 레코드 확인
            existing = self.db.query(NaverDeliveryInfo).filter(
                NaverDeliveryInfo.tracking_number == tracking_number
            ).first()

            if existing:
                # 업데이트
                existing.updated_at = datetime.utcnow()
            else:
                # 새로 생성
                courier_code = get_coupang_courier_code(delivery_data.get("courier", ""))

                new_info = NaverDeliveryInfo(
                    naver_account_id=naver_account_id,
                    receiver_name=delivery_data.get("recipient", ""),
                    courier_name=delivery_data.get("courier", ""),
                    courier_code=courier_code,
                    tracking_number=tracking_number,
                    product_name=delivery_data.get("product_name", ""),
                    status="pending"
                )
                self.db.add(new_info)

            self.db.commit()

        except Exception as e:
            logger.error(f"배송 정보 저장 오류: {e}")
            self.db.rollback()

    async def _update_delivery_match(
        self,
        tracking_number: str,
        coupang_order: Dict,
        confidence: int,
        coupang_account_id: int = None
    ):
        """매칭 정보 업데이트"""
        try:
            delivery_info = self.db.query(NaverDeliveryInfo).filter(
                NaverDeliveryInfo.tracking_number == tracking_number
            ).first()

            if delivery_info:
                delivery_info.coupang_account_id = coupang_account_id
                delivery_info.coupang_order_id = coupang_order.get("order_id")
                delivery_info.coupang_shipment_box_id = coupang_order.get("shipment_box_id")
                delivery_info.coupang_vendor_item_id = coupang_order.get("vendor_item_id")
                delivery_info.is_matched = True
                delivery_info.match_confidence = confidence
                delivery_info.status = "matched"
                delivery_info.updated_at = datetime.utcnow()

                self.db.commit()

        except Exception as e:
            logger.error(f"매칭 정보 업데이트 오류: {e}")
            self.db.rollback()

    async def _update_delivery_uploaded(
        self,
        tracking_number: str,
        result: Dict
    ):
        """업로드 결과 업데이트"""
        try:
            delivery_info = self.db.query(NaverDeliveryInfo).filter(
                NaverDeliveryInfo.tracking_number == tracking_number
            ).first()

            if delivery_info:
                delivery_info.status = "uploaded" if result["success"] else "failed"
                delivery_info.upload_result = result
                delivery_info.uploaded_at = datetime.utcnow() if result["success"] else None
                delivery_info.error_message = result.get("error")
                delivery_info.updated_at = datetime.utcnow()

                self.db.commit()

        except Exception as e:
            logger.error(f"업로드 결과 업데이트 오류: {e}")
            self.db.rollback()

    def get_pending_deliveries(self) -> List[Dict]:
        """매칭 대기 중인 배송 정보 조회"""
        deliveries = self.db.query(NaverDeliveryInfo).filter(
            NaverDeliveryInfo.status == "pending"
        ).order_by(NaverDeliveryInfo.created_at.desc()).all()

        return [d.to_dict() for d in deliveries]

    def get_matched_deliveries(self, uploaded: bool = None) -> List[Dict]:
        """매칭된 배송 정보 조회"""
        query = self.db.query(NaverDeliveryInfo).filter(
            NaverDeliveryInfo.is_matched == True
        )

        if uploaded is True:
            query = query.filter(NaverDeliveryInfo.status == "uploaded")
        elif uploaded is False:
            query = query.filter(NaverDeliveryInfo.status == "matched")

        deliveries = query.order_by(NaverDeliveryInfo.created_at.desc()).all()
        return [d.to_dict() for d in deliveries]

    def get_delivery_stats(self) -> Dict:
        """배송 동기화 통계"""
        from sqlalchemy import func

        total = self.db.query(func.count(NaverDeliveryInfo.id)).scalar() or 0
        pending = self.db.query(func.count(NaverDeliveryInfo.id)).filter(
            NaverDeliveryInfo.status == "pending"
        ).scalar() or 0
        matched = self.db.query(func.count(NaverDeliveryInfo.id)).filter(
            NaverDeliveryInfo.status == "matched"
        ).scalar() or 0
        uploaded = self.db.query(func.count(NaverDeliveryInfo.id)).filter(
            NaverDeliveryInfo.status == "uploaded"
        ).scalar() or 0
        failed = self.db.query(func.count(NaverDeliveryInfo.id)).filter(
            NaverDeliveryInfo.status == "failed"
        ).scalar() or 0

        return {
            "total": total,
            "pending": pending,
            "matched": matched,
            "uploaded": uploaded,
            "failed": failed
        }

    def manual_upload_invoice(
        self,
        delivery_id: int
    ) -> Dict[str, Any]:
        """수동 송장 업로드"""
        try:
            delivery_info = self.db.query(NaverDeliveryInfo).filter(
                NaverDeliveryInfo.id == delivery_id
            ).first()

            if not delivery_info:
                return {"success": False, "error": "배송 정보를 찾을 수 없습니다"}

            if not delivery_info.is_matched:
                return {"success": False, "error": "매칭된 쿠팡 주문이 없습니다"}

            if delivery_info.status == "uploaded":
                return {"success": False, "error": "이미 업로드된 송장입니다"}

            coupang_service = self.get_coupang_service()

            result = coupang_service.upload_invoice(
                shipment_box_id=delivery_info.coupang_shipment_box_id,
                order_id=delivery_info.coupang_order_id,
                vendor_item_id=delivery_info.coupang_vendor_item_id,
                courier_code=delivery_info.courier_code,
                tracking_number=delivery_info.tracking_number
            )

            # 결과 업데이트
            delivery_info.status = "uploaded" if result["success"] else "failed"
            delivery_info.upload_result = result
            delivery_info.uploaded_at = datetime.utcnow() if result["success"] else None
            delivery_info.error_message = result.get("error")
            delivery_info.updated_at = datetime.utcnow()

            self.db.commit()

            return result

        except Exception as e:
            logger.error(f"수동 업로드 오류: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def manual_match(
        self,
        delivery_id: int,
        shipment_box_id: str,
        order_id: str,
        vendor_item_id: str
    ) -> Dict[str, Any]:
        """수동 매칭"""
        try:
            delivery_info = self.db.query(NaverDeliveryInfo).filter(
                NaverDeliveryInfo.id == delivery_id
            ).first()

            if not delivery_info:
                return {"success": False, "error": "배송 정보를 찾을 수 없습니다"}

            delivery_info.coupang_shipment_box_id = shipment_box_id
            delivery_info.coupang_order_id = order_id
            delivery_info.coupang_vendor_item_id = vendor_item_id
            delivery_info.is_matched = True
            delivery_info.match_confidence = 100  # 수동 매칭은 100%
            delivery_info.status = "matched"
            delivery_info.updated_at = datetime.utcnow()

            self.db.commit()

            return {"success": True, "message": "매칭 완료"}

        except Exception as e:
            logger.error(f"수동 매칭 오류: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
