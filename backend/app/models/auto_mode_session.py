"""
Auto Mode Session Model - 자동모드 세션 영구 저장
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class AutoModeSession(Base):
    """자동모드 세션 - 영구 저장"""
    __tablename__ = "auto_mode_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True, nullable=False)

    # 계정 정보
    account_id = Column(Integer, ForeignKey("coupang_accounts.id"), nullable=False)
    account_name = Column(String(100))
    vendor_id = Column(String(50))

    # 설정
    interval_minutes = Column(Integer, default=5)
    inquiry_types = Column(JSON, default=["online", "callcenter"])  # ["online", "callcenter"]

    # 상태
    is_active = Column(Boolean, default=True)  # 활성화 여부 (삭제 대신 비활성화)
    status = Column(String(20), default="stopped")  # running, stopped

    # 통계
    total_collected = Column(Integer, default=0)
    total_answered = Column(Integer, default=0)
    total_submitted = Column(Integer, default=0)
    total_confirmed = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    run_count = Column(Integer, default=0)

    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run = Column(DateTime, nullable=True)

    # 관계
    account = relationship("CoupangAccount", backref="auto_mode_sessions")

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "vendor_id": self.vendor_id,
            "interval_minutes": self.interval_minutes,
            "inquiry_types": self.inquiry_types or ["online", "callcenter"],
            "is_active": self.is_active,
            "status": self.status,
            "stats": {
                "total_collected": self.total_collected,
                "total_answered": self.total_answered,
                "total_submitted": self.total_submitted,
                "total_confirmed": self.total_confirmed,
                "total_failed": self.total_failed,
                "run_count": self.run_count
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_run": self.last_run.isoformat() if self.last_run else None
        }
