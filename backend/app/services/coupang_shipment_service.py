"""
Coupang Shipment Service
쿠팡 발주서 조회 및 송장 등록 서비스
"""
import hmac
import hashlib
import datetime
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from loguru import logger
from sqlalchemy.orm import Session

from ..models.naver_delivery_sync import CoupangPendingOrder, get_coupang_courier_code


class CoupangShipmentService:
    """쿠팡 발주서/송장 API 서비스"""

    BASE_URL = "https://api-gateway.coupang.com"

    def __init__(
        self,
        db: Session,
        access_key: str,
        secret_key: str,
        vendor_id: str
    ):
        self.db = db
        self.access_key = access_key
        self.secret_key = secret_key
        self.vendor_id = vendor_id

    def _generate_hmac(self, method: str, path: str, query: str = "") -> tuple:
        """HMAC 서명 생성"""
        now = datetime.datetime.utcnow()
        datetime_str = now.strftime('%y%m%d') + 'T' + now.strftime('%H%M%S') + 'Z'

        message = datetime_str + method + path + query

        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature, datetime_str

    def _get_headers(self, method: str, path: str, query: str = "") -> Dict[str, str]:
        """인증 헤더 생성"""
        signature, datetime_str = self._generate_hmac(method, path, query)

        return {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={datetime_str}, signature={signature}"
        }

    def get_pending_orders(
        self,
        hours_back: int = 24,
        status: str = "INSTRUCT"
    ) -> List[Dict]:
        """
        발주서 목록 조회 (상품준비중)

        Args:
            hours_back: 몇 시간 전부터 조회할지 (최대 24시간)
            status: 발주서 상태 (INSTRUCT: 상품준비중)

        Returns:
            발주서 목록
        """
        try:
            # 시간 범위 설정 (KST 기준)
            import pytz
            kst = pytz.timezone('Asia/Seoul')
            now_kst = datetime.datetime.now(kst)
            from_time = now_kst - datetime.timedelta(hours=min(hours_back, 24))

            # ISO 8601 형식 + URL 인코딩
            created_at_from = from_time.strftime('%Y-%m-%dT%H:%M') + '%2B09:00'
            created_at_to = now_kst.strftime('%Y-%m-%dT%H:%M') + '%2B09:00'

            path = f"/v2/providers/openapi/apis/api/v5/vendors/{self.vendor_id}/ordersheets"
            query = f"createdAtFrom={created_at_from}&createdAtTo={created_at_to}&status={status}&searchType=timeFrame"

            url = f"{self.BASE_URL}{path}?{query}"
            headers = self._get_headers("GET", path, query)

            logger.info(f"Fetching pending orders from Coupang: {url}")

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                orders = data.get("data", [])
                logger.success(f"Fetched {len(orders)} pending orders from Coupang")

                # DB에 저장
                self._save_pending_orders(orders)

                return orders
            else:
                logger.error(f"Failed to fetch orders: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error fetching pending orders: {e}")
            return []

    def _save_pending_orders(self, orders: List[Dict]):
        """발주서 DB 저장"""
        for order in orders:
            try:
                shipment_box_id = str(order.get("shipmentBoxId"))

                # 기존 레코드 확인
                existing = self.db.query(CoupangPendingOrder).filter(
                    CoupangPendingOrder.shipment_box_id == shipment_box_id
                ).first()

                if existing:
                    # 업데이트
                    existing.status = order.get("status")
                    existing.updated_at = datetime.datetime.utcnow()
                else:
                    # 새로 생성
                    receiver = order.get("receiver", {})
                    order_items = order.get("orderItems", [])
                    first_item = order_items[0] if order_items else {}

                    new_order = CoupangPendingOrder(
                        shipment_box_id=shipment_box_id,
                        order_id=str(order.get("orderId")),
                        vendor_item_id=str(first_item.get("vendorItemId", "")),
                        receiver_name=receiver.get("name", ""),
                        receiver_phone=receiver.get("safeNumber", ""),
                        receiver_address=f"{receiver.get('addr1', '')} {receiver.get('addr2', '')}",
                        product_name=first_item.get("vendorItemName", ""),
                        shipping_count=first_item.get("shippingCount", 1),
                        order_price=first_item.get("orderPrice", {}).get("units", 0),
                        status=order.get("status"),
                        is_invoice_uploaded=order.get("invoiceNumber") is not None and order.get("invoiceNumber") != ""
                    )

                    # 주문 시간 파싱
                    ordered_at_str = order.get("orderedAt")
                    if ordered_at_str:
                        try:
                            new_order.ordered_at = datetime.datetime.fromisoformat(
                                ordered_at_str.replace('+09:00', '+00:00').replace('-08:00', '+00:00')
                            )
                        except:
                            pass

                    self.db.add(new_order)

                self.db.commit()

            except Exception as e:
                logger.error(f"Error saving pending order {order.get('orderId')}: {e}")
                self.db.rollback()

    def get_pending_orders_from_db(self, only_unuploaded: bool = True) -> List[Dict]:
        """DB에서 발송 대기 주문 조회"""
        query = self.db.query(CoupangPendingOrder).filter(
            CoupangPendingOrder.status == "INSTRUCT"
        )

        if only_unuploaded:
            query = query.filter(CoupangPendingOrder.is_invoice_uploaded == False)

        orders = query.order_by(CoupangPendingOrder.created_at.desc()).all()
        return [order.to_dict() for order in orders]

    def upload_invoice(
        self,
        shipment_box_id: str,
        order_id: str,
        vendor_item_id: str,
        courier_code: str,
        tracking_number: str
    ) -> Dict[str, Any]:
        """
        송장 업로드

        Args:
            shipment_box_id: 배송번호
            order_id: 주문번호
            vendor_item_id: 옵션ID
            courier_code: 쿠팡 택배사 코드 (예: EPOST, CJGLS)
            tracking_number: 송장번호

        Returns:
            업로드 결과
        """
        try:
            path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/orders/invoices"

            body = {
                "vendorId": self.vendor_id,
                "orderSheetInvoiceApplyDtos": [
                    {
                        "shipmentBoxId": int(shipment_box_id),
                        "orderId": int(order_id),
                        "vendorItemId": int(vendor_item_id),
                        "deliveryCompanyCode": courier_code,
                        "invoiceNumber": tracking_number,
                        "splitShipping": False,
                        "preSplitShipped": False,
                        "estimatedShippingDate": ""
                    }
                ]
            }

            url = f"{self.BASE_URL}{path}"
            headers = self._get_headers("POST", path, "")

            logger.info(f"Uploading invoice to Coupang: {tracking_number} for order {order_id}")

            response = requests.post(url, headers=headers, json=body, timeout=30)

            result = {
                "success": False,
                "status_code": response.status_code,
                "response": None,
                "error": None
            }

            if response.status_code == 200:
                data = response.json()
                result["response"] = data

                # 응답 확인
                response_list = data.get("data", {}).get("responseList", [])
                if response_list:
                    first_result = response_list[0]
                    if first_result.get("succeed"):
                        result["success"] = True
                        logger.success(f"Invoice uploaded successfully: {tracking_number}")

                        # DB 업데이트
                        self._mark_invoice_uploaded(shipment_box_id)
                    else:
                        result["error"] = first_result.get("resultMessage") or first_result.get("resultCode")
                        logger.error(f"Invoice upload failed: {result['error']}")
                else:
                    result["success"] = True
                    self._mark_invoice_uploaded(shipment_box_id)
            else:
                result["error"] = response.text
                logger.error(f"Invoice upload HTTP error: {response.status_code} - {response.text}")

            return result

        except Exception as e:
            logger.error(f"Error uploading invoice: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _mark_invoice_uploaded(self, shipment_box_id: str):
        """송장 업로드 완료 표시"""
        try:
            order = self.db.query(CoupangPendingOrder).filter(
                CoupangPendingOrder.shipment_box_id == shipment_box_id
            ).first()

            if order:
                order.is_invoice_uploaded = True
                order.status = "DEPARTURE"
                order.updated_at = datetime.datetime.utcnow()
                self.db.commit()

        except Exception as e:
            logger.error(f"Error marking invoice uploaded: {e}")
            self.db.rollback()

    def upload_invoices_batch(
        self,
        invoices: List[Dict]
    ) -> Dict[str, Any]:
        """
        송장 일괄 업로드

        Args:
            invoices: 송장 정보 리스트
                [{
                    "shipment_box_id": "...",
                    "order_id": "...",
                    "vendor_item_id": "...",
                    "courier_code": "EPOST",
                    "tracking_number": "..."
                }]

        Returns:
            업로드 결과
        """
        results = {
            "total": len(invoices),
            "success": 0,
            "failed": 0,
            "details": []
        }

        for invoice in invoices:
            result = self.upload_invoice(
                shipment_box_id=invoice["shipment_box_id"],
                order_id=invoice["order_id"],
                vendor_item_id=invoice["vendor_item_id"],
                courier_code=invoice["courier_code"],
                tracking_number=invoice["tracking_number"]
            )

            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "order_id": invoice["order_id"],
                "tracking_number": invoice["tracking_number"],
                **result
            })

        return results

    def match_delivery_with_orders(
        self,
        receiver_name: str,
        orders: List[Dict] = None
    ) -> Optional[Dict]:
        """
        수취인 이름으로 주문 매칭

        Args:
            receiver_name: 네이버에서 가져온 수취인 이름
            orders: 쿠팡 발주서 목록 (없으면 DB에서 조회)

        Returns:
            매칭된 주문 정보
        """
        if orders is None:
            orders = self.get_pending_orders_from_db()

        # 정확한 이름 매칭
        for order in orders:
            order_receiver = order.get("receiver_name", "")

            # 마스킹 제거 후 비교 (예: 유*익 → 유병익)
            # 쿠팡은 마스킹된 이름 (신*희)으로 오는 경우가 있음
            if self._names_match(receiver_name, order_receiver):
                return {
                    "matched": True,
                    "confidence": 100,
                    "order": order
                }

        # 부분 매칭 시도
        for order in orders:
            order_receiver = order.get("receiver_name", "")
            if self._partial_name_match(receiver_name, order_receiver):
                return {
                    "matched": True,
                    "confidence": 70,
                    "order": order
                }

        return {
            "matched": False,
            "confidence": 0,
            "order": None
        }

    def _names_match(self, name1: str, name2: str) -> bool:
        """이름 매칭 (마스킹 고려)"""
        if not name1 or not name2:
            return False

        # 완전 일치
        if name1 == name2:
            return True

        # 마스킹 패턴 확인 (예: 신*희)
        if '*' in name2:
            # 첫글자와 마지막 글자 비교
            if len(name1) == len(name2):
                if name1[0] == name2[0] and name1[-1] == name2[-1]:
                    return True

        if '*' in name1:
            if len(name1) == len(name2):
                if name1[0] == name2[0] and name1[-1] == name2[-1]:
                    return True

        return False

    def _partial_name_match(self, name1: str, name2: str) -> bool:
        """부분 이름 매칭"""
        if not name1 or not name2:
            return False

        # 공백 제거
        n1 = name1.replace(" ", "")
        n2 = name2.replace(" ", "").replace("*", "")

        # 한 이름이 다른 이름에 포함되는 경우
        if n1 in n2 or n2 in n1:
            return True

        # 첫 글자와 글자수 비교
        if len(n1) == len(n2) and n1[0] == n2[0]:
            return True

        return False
