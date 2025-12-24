"""
NaverPay 배송 정보 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.sql import func
from ..database import Base


class NaverPayDelivery(Base):
    """네이버페이 배송 정보 테이블"""
    __tablename__ = "naverpay_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient = Column(String(100), nullable=False, comment="수령인명")
    courier = Column(String(50), nullable=False, comment="택배사명")
    tracking_number = Column(String(50), nullable=False, comment="송장번호")
    product_name = Column(String(500), nullable=True, comment="상품명")
    order_date = Column(String(20), nullable=True, comment="주문일자")
    collected_at = Column(DateTime, default=func.now(), comment="수집 시각")
    collected_date = Column(String(10), nullable=False, comment="수집 날짜 (YYYY-MM-DD)")

    __table_args__ = (
        Index('idx_tracking_date', 'tracking_number', 'collected_date', unique=True),
        Index('idx_collected_at', 'collected_at'),
        Index('idx_courier', 'courier'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "recipient": self.recipient,
            "courier": self.courier,
            "tracking_number": self.tracking_number,
            "product_name": self.product_name,
            "order_date": self.order_date,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "collected_date": self.collected_date
        }


class NaverPayDeliveryHistory(Base):
    """네이버페이 배송 정보 이력 테이블"""
    __tablename__ = "naverpay_delivery_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient = Column(String(100), nullable=False)
    courier = Column(String(50), nullable=False)
    tracking_number = Column(String(50), nullable=False)
    product_name = Column(String(500), nullable=True)
    order_date = Column(String(20), nullable=True)
    collected_at = Column(DateTime, nullable=False)
    collected_date = Column(String(10), nullable=False)
    archived_at = Column(DateTime, default=func.now(), comment="보관 시각")
    archived_date = Column(String(10), nullable=False, comment="보관 날짜")

    def to_dict(self):
        return {
            "id": self.id,
            "recipient": self.recipient,
            "courier": self.courier,
            "tracking_number": self.tracking_number,
            "product_name": self.product_name,
            "order_date": self.order_date,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "collected_date": self.collected_date,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "archived_date": self.archived_date
        }


class NaverPaySchedule(Base):
    """네이버페이 수집 스케줄 테이블"""
    __tablename__ = "naverpay_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(50), unique=True, nullable=False, comment="스케줄 작업 ID")
    schedule_type = Column(String(20), nullable=False, comment="interval 또는 cron")
    interval_minutes = Column(Integer, nullable=True, comment="간격(분)")
    cron_expression = Column(String(100), nullable=True, comment="크론 표현식")
    is_active = Column(Integer, default=1, comment="활성화 여부")
    created_at = Column(DateTime, default=func.now())
    last_run_at = Column(DateTime, nullable=True, comment="마지막 실행 시각")
    next_run_at = Column(DateTime, nullable=True, comment="다음 실행 예정 시각")

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "schedule_type": self.schedule_type,
            "interval_minutes": self.interval_minutes,
            "cron_expression": self.cron_expression,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None
        }


class NaverPayScheduleHistory(Base):
    """네이버페이 스케줄 실행 이력 테이블"""
    __tablename__ = "naverpay_schedule_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    executed_at = Column(DateTime, default=func.now(), comment="실행 시각")
    total_found = Column(Integer, default=0, comment="발견된 배송 건수")
    new_saved = Column(Integer, default=0, comment="신규 저장 건수")
    status = Column(String(20), default="success", comment="실행 상태 (success, failed, skipped)")
    error_message = Column(Text, nullable=True, comment="에러 메시지")

    __table_args__ = (
        Index('idx_naverpay_history_executed_at', 'executed_at'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "total_found": self.total_found,
            "new_saved": self.new_saved,
            "status": self.status,
            "error_message": self.error_message
        }
