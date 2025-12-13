"""
Coupon Auto-Sync Configuration Models
쿠폰 자동연동 설정 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class CouponAutoSyncConfig(Base):
    """쿠폰 자동연동 설정 모델"""
    __tablename__ = "coupon_auto_sync_configs"

    id = Column(Integer, primary_key=True, index=True)

    # 연결된 쿠팡 계정
    coupang_account_id = Column(Integer, ForeignKey("coupang_accounts.id"), nullable=False)

    # 활성화 여부
    is_enabled = Column(Boolean, default=False)

    # 즉시할인쿠폰 설정
    instant_coupon_enabled = Column(Boolean, default=False)
    instant_coupon_id = Column(Integer, nullable=True)  # 적용할 즉시할인쿠폰 ID
    instant_coupon_name = Column(String(200), nullable=True)  # 쿠폰명 (표시용)

    # 다운로드쿠폰 설정
    download_coupon_enabled = Column(Boolean, default=False)
    download_coupon_id = Column(Integer, nullable=True)  # 적용할 다운로드쿠폰 ID
    download_coupon_name = Column(String(200), nullable=True)  # 쿠폰명 (표시용)

    # 적용 대기일 (상품 등록 후 며칠 후에 쿠폰 적용할지)
    apply_delay_days = Column(Integer, default=1)  # 기본 1일

    # 계약서 ID (쿠폰 생성에 필요)
    contract_id = Column(Integer, nullable=True)

    # 제외 카테고리 (JSON 배열)
    excluded_categories = Column(JSON, default=list)

    # 제외 상품 ID 목록 (JSON 배열)
    excluded_product_ids = Column(JSON, default=list)

    # 마지막 동기화 시간
    last_sync_at = Column(DateTime, nullable=True)

    # 마지막으로 확인한 상품 등록일
    last_checked_product_date = Column(String(20), nullable=True)  # yyyy-MM-dd 형식

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "coupang_account_id": self.coupang_account_id,
            "is_enabled": self.is_enabled,
            "instant_coupon_enabled": self.instant_coupon_enabled,
            "instant_coupon_id": self.instant_coupon_id,
            "instant_coupon_name": self.instant_coupon_name,
            "download_coupon_enabled": self.download_coupon_enabled,
            "download_coupon_id": self.download_coupon_id,
            "download_coupon_name": self.download_coupon_name,
            "apply_delay_days": self.apply_delay_days,
            "contract_id": self.contract_id,
            "excluded_categories": self.excluded_categories or [],
            "excluded_product_ids": self.excluded_product_ids or [],
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_checked_product_date": self.last_checked_product_date,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ProductCouponTracking(Base):
    """상품별 쿠폰 적용 추적 모델"""
    __tablename__ = "product_coupon_trackings"

    id = Column(Integer, primary_key=True, index=True)

    # 연결된 쿠팡 계정
    coupang_account_id = Column(Integer, ForeignKey("coupang_accounts.id"), nullable=False)

    # 상품 정보
    seller_product_id = Column(Integer, nullable=False, index=True)  # 등록상품ID
    seller_product_name = Column(String(500), nullable=True)  # 등록상품명

    # 상품 등록일
    product_created_at = Column(DateTime, nullable=False)

    # 쿠폰 적용 예정일
    coupon_apply_scheduled_at = Column(DateTime, nullable=False)

    # 상태: pending, processing, completed, failed, skipped
    status = Column(String(50), default="pending", index=True)

    # 즉시할인쿠폰 적용 상태
    instant_coupon_applied = Column(Boolean, default=False)
    instant_coupon_applied_at = Column(DateTime, nullable=True)
    instant_coupon_request_id = Column(String(100), nullable=True)  # 비동기 요청 ID

    # 다운로드쿠폰 적용 상태
    download_coupon_applied = Column(Boolean, default=False)
    download_coupon_applied_at = Column(DateTime, nullable=True)

    # 오류 메시지
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "coupang_account_id": self.coupang_account_id,
            "seller_product_id": self.seller_product_id,
            "seller_product_name": self.seller_product_name,
            "product_created_at": self.product_created_at.isoformat() if self.product_created_at else None,
            "coupon_apply_scheduled_at": self.coupon_apply_scheduled_at.isoformat() if self.coupon_apply_scheduled_at else None,
            "status": self.status,
            "instant_coupon_applied": self.instant_coupon_applied,
            "instant_coupon_applied_at": self.instant_coupon_applied_at.isoformat() if self.instant_coupon_applied_at else None,
            "instant_coupon_request_id": self.instant_coupon_request_id,
            "download_coupon_applied": self.download_coupon_applied,
            "download_coupon_applied_at": self.download_coupon_applied_at.isoformat() if self.download_coupon_applied_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class BulkApplyProgress(Base):
    """일괄 적용 진행 상황"""
    __tablename__ = "bulk_apply_progress"

    id = Column(Integer, primary_key=True, index=True)

    # 연결된 쿠팡 계정
    coupang_account_id = Column(Integer, ForeignKey("coupang_accounts.id"), nullable=False, index=True)

    # 상태: collecting, applying, completed, failed
    status = Column(String(50), default="collecting")

    # 수집 단계 진행률
    total_days = Column(Integer, default=0)  # 조회할 총 일수
    processed_days = Column(Integer, default=0)  # 처리된 일수
    current_date = Column(String(20), nullable=True)  # 현재 처리 중인 날짜

    # 상품/아이템 수
    total_products = Column(Integer, default=0)
    total_items = Column(Integer, default=0)

    # 쿠폰 적용 단계 진행률
    instant_total = Column(Integer, default=0)
    instant_success = Column(Integer, default=0)
    instant_failed = Column(Integer, default=0)

    download_total = Column(Integer, default=0)
    download_success = Column(Integer, default=0)
    download_failed = Column(Integer, default=0)

    # 오류 메시지
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        """Convert to dictionary"""
        # 진행률 계산
        collecting_progress = 0
        if self.total_days > 0:
            collecting_progress = round((self.processed_days / self.total_days) * 100, 1)

        applying_progress = 0
        total_apply = self.instant_total + self.download_total
        applied = self.instant_success + self.instant_failed + self.download_success + self.download_failed
        if total_apply > 0:
            applying_progress = round((applied / total_apply) * 100, 1)

        return {
            "id": self.id,
            "coupang_account_id": self.coupang_account_id,
            "status": self.status,
            "total_days": self.total_days,
            "processed_days": self.processed_days,
            "current_date": self.current_date,
            "collecting_progress": collecting_progress,
            "total_products": self.total_products,
            "total_items": self.total_items,
            "instant_total": self.instant_total,
            "instant_success": self.instant_success,
            "instant_failed": self.instant_failed,
            "download_total": self.download_total,
            "download_success": self.download_success,
            "download_failed": self.download_failed,
            "applying_progress": applying_progress,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class CouponApplyLog(Base):
    """쿠폰 적용 이력 로그"""
    __tablename__ = "coupon_apply_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 연결된 쿠팡 계정
    coupang_account_id = Column(Integer, ForeignKey("coupang_accounts.id"), nullable=False)

    # 상품 정보
    seller_product_id = Column(Integer, nullable=False)
    vendor_item_id = Column(Integer, nullable=True)  # 옵션 ID

    # 쿠폰 정보
    coupon_type = Column(String(50), nullable=False)  # instant, download
    coupon_id = Column(Integer, nullable=False)
    coupon_name = Column(String(200), nullable=True)

    # 결과
    success = Column(Boolean, default=False)
    request_id = Column(String(100), nullable=True)  # 비동기 요청 ID
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # 요청/응답 데이터 (디버깅용)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "coupang_account_id": self.coupang_account_id,
            "seller_product_id": self.seller_product_id,
            "vendor_item_id": self.vendor_item_id,
            "coupon_type": self.coupon_type,
            "coupon_id": self.coupon_id,
            "coupon_name": self.coupon_name,
            "success": self.success,
            "request_id": self.request_id,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
