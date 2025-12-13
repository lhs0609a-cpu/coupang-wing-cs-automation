"""
Return Log Model
반품 처리 로그 데이터베이스 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Numeric
from sqlalchemy.sql import func
from ..database import Base


class ReturnLog(Base):
    """반품 처리 로그"""
    __tablename__ = "return_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 쿠팡 정보
    coupang_receipt_id = Column(Integer, nullable=False, index=True, comment="쿠팡 반품 접수 번호")
    coupang_order_id = Column(String(100), nullable=False, index=True, comment="쿠팡 주문 번호")
    coupang_payment_id = Column(String(100), nullable=True, comment="쿠팡 결제 번호")
    coupang_created_at = Column(DateTime(timezone=True), nullable=True, comment="쿠팡 반품 접수 시간")
    coupang_modified_at = Column(DateTime(timezone=True), nullable=True, comment="쿠팡 반품 상태 최종 변경 시간")

    # 상품 정보
    product_name = Column(String(500), nullable=False, comment="상품명")
    vendor_item_id = Column(String(100), nullable=True, comment="옵션 ID")
    vendor_item_package_id = Column(String(100), nullable=True, comment="딜 번호")
    vendor_item_package_name = Column(String(500), nullable=True, comment="딜명")
    seller_product_id = Column(String(100), nullable=True, comment="업체등록상품번호")
    seller_product_name = Column(String(500), nullable=True, comment="업체등록상품명")
    cancel_count = Column(Integer, default=1, comment="취소/반품 수량")
    cancel_count_sum = Column(Integer, nullable=True, comment="총 취소 수량")
    purchase_count = Column(Integer, nullable=True, comment="주문 수량")
    shipment_box_id = Column(String(100), nullable=True, comment="원 배송번호")
    release_status = Column(String(10), nullable=True, comment="상품출고여부 (Y:출고됨, N:미출고, S:출고중지됨, A:이미출고됨)")

    # 수령인/회수지 정보
    receiver_name = Column(String(100), nullable=True, comment="반품 신청인 이름")
    receiver_phone = Column(String(50), nullable=True, comment="반품 신청인 전화번호(안심번호)")
    receiver_real_phone = Column(String(50), nullable=True, comment="반품 신청인 실전화번호")
    receiver_address = Column(String(500), nullable=True, comment="반품 회수지 주소")
    receiver_address_detail = Column(String(500), nullable=True, comment="반품 회수지 상세주소")
    receiver_zipcode = Column(String(20), nullable=True, comment="반품 회수지 우편번호")

    # 반품 상태
    receipt_type = Column(String(50), nullable=False, comment="RETURN or CANCEL")
    receipt_status = Column(
        String(100),
        nullable=False,
        index=True,
        comment="RELEASE_STOP_UNCHECKED, RETURNS_UNCHECKED, etc."
    )
    release_stop_status = Column(String(50), nullable=True, comment="출고중지처리상태")

    # 반품 사유
    cancel_reason_category1 = Column(String(200), nullable=True, comment="반품 사유 카테고리 1")
    cancel_reason_category2 = Column(String(200), nullable=True, comment="반품 사유 카테고리 2")
    cancel_reason = Column(Text, nullable=True, comment="상세 취소 사유")
    reason_code = Column(String(100), nullable=True, index=True, comment="반품 사유 코드")
    reason_code_text = Column(String(500), nullable=True, comment="반품 사유 설명")

    # 귀책 및 환불 정보
    fault_by_type = Column(String(50), nullable=True, index=True, comment="귀책타입 (COUPANG, VENDOR, CUSTOMER, WMS, GENERAL)")
    pre_refund = Column(Boolean, nullable=True, comment="선환불 여부")
    return_shipping_charge = Column(Numeric(10, 2), nullable=True, comment="예상 반품배송비 (양수: 셀러부담, 음수: 고객부담)")
    return_shipping_charge_currency = Column(String(10), nullable=True, comment="반품배송비 통화 코드")
    enclose_price = Column(Numeric(10, 2), nullable=True, comment="동봉배송비")
    enclose_price_currency = Column(String(10), nullable=True, comment="동봉배송비 통화 코드")

    # 배송 정보
    return_delivery_id = Column(String(100), nullable=True, comment="반품 배송 번호")
    return_delivery_type = Column(String(50), nullable=True, comment="회수종류 (전담택배, 연동택배, 수기관리)")
    return_delivery_dtos = Column(JSON, nullable=True, comment="회수 운송장 정보 [{deliveryCompanyCode, deliveryInvoiceNo}]")

    # 완료 확인 정보
    complete_confirm_type = Column(String(50), nullable=True, comment="완료 확인 종류 (VENDOR_CONFIRM, UNDEFINED, CS_CONFIRM, CS_LOSS_CONFIRM)")
    complete_confirm_date = Column(DateTime(timezone=True), nullable=True, comment="완료 확인 시간")
    cancel_complete_user = Column(String(100), nullable=True, comment="주문취소처리 담당자")

    # 네이버 처리 정보
    naver_processed = Column(Boolean, default=False, index=True, comment="네이버 처리 완료 여부")
    naver_processed_at = Column(DateTime(timezone=True), nullable=True, comment="네이버 처리 완료 시간")
    naver_process_type = Column(
        String(50),
        nullable=True,
        comment="RETURN_REQUEST or ORDER_CANCEL"
    )
    naver_result = Column(Text, nullable=True, comment="네이버 처리 결과")
    naver_error = Column(Text, nullable=True, comment="네이버 처리 오류 메시지")

    # 처리 상태
    status = Column(
        String(50),
        default="pending",
        index=True,
        comment="pending, processing, completed, failed"
    )

    # 원본 데이터 (JSON)
    raw_data = Column(JSON, nullable=True, comment="쿠팡 API 원본 데이터")

    # 메타 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정 시간")
    processed_by = Column(String(100), nullable=True, comment="처리자")
    notes = Column(Text, nullable=True, comment="메모")

    def __repr__(self):
        return f"<ReturnLog(id={self.id}, coupang_order_id={self.coupang_order_id}, status={self.status})>"
