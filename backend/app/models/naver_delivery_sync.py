"""
Naver Delivery Sync Model
네이버 배송 정보 → 쿠팡 송장 동기화 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class NaverDeliveryInfo(Base):
    """네이버에서 수집한 배송 정보"""
    __tablename__ = "naver_delivery_info"

    id = Column(Integer, primary_key=True, index=True)

    # 네이버 정보
    naver_account_id = Column(Integer, ForeignKey("naver_accounts.id"), nullable=True)
    store_name = Column(String(200))  # 판매자 스토어명 (메디프라, 삼원농산 등)
    naver_order_id = Column(String(100))  # 네이버 주문번호

    # 배송 정보 (네이버에서 파싱)
    receiver_name = Column(String(100), nullable=False)  # 수취인 이름
    courier_name = Column(String(100))  # 택배사 이름 (네이버 표기)
    courier_code = Column(String(50))  # 쿠팡 택배사 코드
    tracking_number = Column(String(100))  # 송장번호
    product_name = Column(String(500))  # 상품명

    # 쿠팡 매칭 정보
    coupang_account_id = Column(Integer, ForeignKey("coupang_accounts.id"), nullable=True)
    coupang_order_id = Column(String(100))  # 쿠팡 주문번호
    coupang_shipment_box_id = Column(String(100))  # 쿠팡 배송번호
    coupang_vendor_item_id = Column(String(100))  # 쿠팡 옵션ID
    is_matched = Column(Boolean, default=False)  # 매칭 여부
    match_confidence = Column(Integer, default=0)  # 매칭 신뢰도 (0-100)

    # 송장 등록 상태
    status = Column(String(50), default="pending")  # pending, matched, uploaded, failed
    upload_result = Column(JSON)  # 업로드 결과
    error_message = Column(Text)  # 에러 메시지
    uploaded_at = Column(DateTime)  # 송장 등록 시간

    # 타임스탬프
    collected_at = Column(DateTime, default=datetime.utcnow)  # 수집 시간
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "naver_account_id": self.naver_account_id,
            "store_name": self.store_name,
            "naver_order_id": self.naver_order_id,
            "receiver_name": self.receiver_name,
            "courier_name": self.courier_name,
            "courier_code": self.courier_code,
            "tracking_number": self.tracking_number,
            "product_name": self.product_name,
            "coupang_account_id": self.coupang_account_id,
            "coupang_order_id": self.coupang_order_id,
            "coupang_shipment_box_id": self.coupang_shipment_box_id,
            "coupang_vendor_item_id": self.coupang_vendor_item_id,
            "is_matched": self.is_matched,
            "match_confidence": self.match_confidence,
            "status": self.status,
            "upload_result": self.upload_result,
            "error_message": self.error_message,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<NaverDeliveryInfo {self.id}: {self.receiver_name} - {self.tracking_number}>"


class CoupangPendingOrder(Base):
    """쿠팡 발송 대기 주문 (상품준비중)"""
    __tablename__ = "coupang_pending_orders"

    id = Column(Integer, primary_key=True, index=True)

    # 쿠팡 계정
    coupang_account_id = Column(Integer, ForeignKey("coupang_accounts.id"), nullable=True)

    # 주문 정보
    shipment_box_id = Column(String(100), nullable=False, unique=True)  # 배송번호
    order_id = Column(String(100), nullable=False)  # 주문번호
    vendor_item_id = Column(String(100))  # 옵션ID

    # 수취인 정보
    receiver_name = Column(String(100))  # 수취인 이름
    receiver_phone = Column(String(50))  # 수취인 전화 (안심번호)
    receiver_address = Column(Text)  # 배송지 주소

    # 주문 상세
    product_name = Column(String(500))  # 상품명
    shipping_count = Column(Integer, default=1)  # 수량
    order_price = Column(Integer)  # 주문 금액
    ordered_at = Column(DateTime)  # 주문 시간

    # 상태
    status = Column(String(50), default="INSTRUCT")  # INSTRUCT: 상품준비중
    is_invoice_uploaded = Column(Boolean, default=False)  # 송장 등록 여부

    # 타임스탬프
    fetched_at = Column(DateTime, default=datetime.utcnow)  # 조회 시간
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "coupang_account_id": self.coupang_account_id,
            "shipment_box_id": self.shipment_box_id,
            "order_id": self.order_id,
            "vendor_item_id": self.vendor_item_id,
            "receiver_name": self.receiver_name,
            "receiver_phone": self.receiver_phone,
            "receiver_address": self.receiver_address,
            "product_name": self.product_name,
            "shipping_count": self.shipping_count,
            "order_price": self.order_price,
            "ordered_at": self.ordered_at.isoformat() if self.ordered_at else None,
            "status": self.status,
            "is_invoice_uploaded": self.is_invoice_uploaded,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<CoupangPendingOrder {self.order_id}: {self.receiver_name}>"


# 택배사 코드 매핑 (네이버 → 쿠팡)
NAVER_TO_COUPANG_COURIER = {
    # 주요 택배사
    "우체국택배": "EPOST",
    "우체국": "EPOST",
    "CJ대한통운": "CJGLS",
    "대한통운": "CJGLS",
    "씨제이대한통운": "CJGLS",
    "한진택배": "HANJIN",
    "한진": "HANJIN",
    "롯데택배": "HYUNDAI",
    "롯데글로벌로지스": "HYUNDAI",
    "로젠택배": "KGB",
    "로젠": "KGB",
    "경동택배": "KDEXP",
    "경동": "KDEXP",

    # 기타 택배사
    "대신택배": "DAESIN",
    "일양택배": "ILYANG",
    "일양로지스": "ILYANG",
    "천일택배": "CHUNIL",
    "천일특송": "CHUNIL",
    "합동택배": "HDEXP",
    "CVS택배": "CVS",
    "편의점택배": "CVS",
    "홈픽택배": "HOMEPICK",
    "홈픽": "HOMEPICK",
    "CU택배": "CVS",
    "GS택배": "CVS",

    # 국제 택배
    "DHL": "DHL",
    "UPS": "UPS",
    "FedEx": "FEDEX",
    "페덱스": "FEDEX",
    "EMS": "EMS",
    "우체국EMS": "EMS",

    # 기타
    "건영택배": "KUNYOUNG",
    "세방택배": "SEBANG",
    "농협택배": "NHLOGIS",
}


def get_coupang_courier_code(naver_courier_name: str) -> str:
    """네이버 택배사명을 쿠팡 택배사 코드로 변환"""
    if not naver_courier_name:
        return None

    # 정확한 매칭
    if naver_courier_name in NAVER_TO_COUPANG_COURIER:
        return NAVER_TO_COUPANG_COURIER[naver_courier_name]

    # 부분 매칭
    naver_lower = naver_courier_name.lower().replace(" ", "")
    for name, code in NAVER_TO_COUPANG_COURIER.items():
        if name.lower().replace(" ", "") in naver_lower or naver_lower in name.lower().replace(" ", ""):
            return code

    return None
