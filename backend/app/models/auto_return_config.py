"""
자동 반품 처리 설정 모델
"""
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from ..database import Base


class AutoReturnConfig(Base):
    """자동 반품 처리 설정"""
    __tablename__ = "auto_return_configs"

    id = Column(Integer, primary_key=True, index=True)

    # 자동화 활성화 여부
    enabled = Column(Boolean, default=False, nullable=False, comment="자동화 활성화")

    # 수집 설정
    fetch_enabled = Column(Boolean, default=True, nullable=False, comment="자동 수집 활성화")
    fetch_interval_minutes = Column(Integer, default=15, nullable=False, comment="수집 주기(분)")
    fetch_lookback_hours = Column(Integer, default=1, nullable=False, comment="조회할 과거 시간(시간)")

    # 처리 설정
    process_enabled = Column(Boolean, default=True, nullable=False, comment="자동 처리 활성화")
    process_interval_minutes = Column(Integer, default=20, nullable=False, comment="처리 주기(분)")
    process_batch_size = Column(Integer, default=50, nullable=False, comment="한 번에 처리할 최대 개수")

    # 상태 필터링
    auto_process_statuses = Column(JSON, default=list, nullable=False, comment="자동 처리할 상태 목록")
    exclude_statuses = Column(JSON, default=list, nullable=False, comment="제외할 상태 목록")

    # 재시도 설정
    max_retry_count = Column(Integer, default=3, nullable=False, comment="최대 재시도 횟수")
    retry_delay_seconds = Column(JSON, default=list, nullable=False, comment="재시도 간격(초) 배열")

    # 알림 설정
    notify_on_failure = Column(Boolean, default=True, nullable=False, comment="실패 시 알림")
    notify_on_success = Column(Boolean, default=False, nullable=False, comment="성공 시 알림")
    notification_email = Column(String, nullable=True, comment="알림 받을 이메일")

    # 네이버 계정 설정
    use_headless = Column(Boolean, default=True, nullable=False, comment="헤드리스 모드 사용")
    selenium_timeout = Column(Integer, default=30, nullable=False, comment="Selenium 타임아웃(초)")

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
    created_by = Column(String, nullable=True, comment="생성자")
    updated_by = Column(String, nullable=True, comment="수정자")

    # 마지막 실행 정보
    last_fetch_at = Column(DateTime(timezone=True), nullable=True, comment="마지막 수집 시간")
    last_process_at = Column(DateTime(timezone=True), nullable=True, comment="마지막 처리 시간")
    last_fetch_count = Column(Integer, default=0, nullable=False, comment="마지막 수집 개수")
    last_process_count = Column(Integer, default=0, nullable=False, comment="마지막 처리 개수")
    last_error = Column(String, nullable=True, comment="마지막 에러 메시지")

    def __repr__(self):
        return f"<AutoReturnConfig(id={self.id}, enabled={self.enabled})>"

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "enabled": self.enabled,
            "fetch_enabled": self.fetch_enabled,
            "fetch_interval_minutes": self.fetch_interval_minutes,
            "fetch_lookback_hours": self.fetch_lookback_hours,
            "process_enabled": self.process_enabled,
            "process_interval_minutes": self.process_interval_minutes,
            "process_batch_size": self.process_batch_size,
            "auto_process_statuses": self.auto_process_statuses,
            "exclude_statuses": self.exclude_statuses,
            "max_retry_count": self.max_retry_count,
            "retry_delay_seconds": self.retry_delay_seconds,
            "notify_on_failure": self.notify_on_failure,
            "notify_on_success": self.notify_on_success,
            "notification_email": self.notification_email,
            "use_headless": self.use_headless,
            "selenium_timeout": self.selenium_timeout,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "last_fetch_at": self.last_fetch_at.isoformat() if self.last_fetch_at else None,
            "last_process_at": self.last_process_at.isoformat() if self.last_process_at else None,
            "last_fetch_count": self.last_fetch_count,
            "last_process_count": self.last_process_count,
            "last_error": self.last_error,
        }

    @classmethod
    def get_default_config(cls):
        """기본 설정값 반환"""
        return {
            "enabled": False,
            "fetch_enabled": True,
            "fetch_interval_minutes": 15,
            "fetch_lookback_hours": 1,
            "process_enabled": True,
            "process_interval_minutes": 20,
            "process_batch_size": 50,
            "auto_process_statuses": [
                "RELEASE_STOP_UNCHECKED",
                "RETURNS_UNCHECKED",
                "VENDOR_WAREHOUSE_CONFIRM"
            ],
            "exclude_statuses": [
                "REQUEST_COUPANG_CHECK",
                "RETURNS_COMPLETED"
            ],
            "max_retry_count": 3,
            "retry_delay_seconds": [60, 300, 900],  # 1분, 5분, 15분
            "notify_on_failure": True,
            "notify_on_success": False,
            "notification_email": None,
            "use_headless": True,
            "selenium_timeout": 30,
        }
