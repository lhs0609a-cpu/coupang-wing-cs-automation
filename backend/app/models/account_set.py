"""
Account Set Model
쿠팡 + 네이버 계정을 하나의 세트로 관리
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class AccountSet(Base):
    """계정 세트 모델 - 쿠팡과 네이버 계정을 묶어서 관리"""
    __tablename__ = "account_sets"

    id = Column(Integer, primary_key=True, index=True)

    # 세트 정보
    name = Column(String(200), nullable=False, comment="계정 세트 이름 (예: 기본 계정, 회사 계정)")
    description = Column(String(500), nullable=True, comment="세트 설명")

    # 연결된 계정들
    coupang_account_id = Column(Integer, ForeignKey("coupang_accounts.id"), nullable=True)
    naver_account_id = Column(Integer, ForeignKey("naver_accounts.id"), nullable=True)

    # Relationships
    coupang_account = relationship("CoupangAccount", foreign_keys=[coupang_account_id])
    naver_account = relationship("NaverAccount", foreign_keys=[naver_account_id])

    # 상태
    is_default = Column(Boolean, default=False, comment="기본 세트 여부")
    is_active = Column(Boolean, default=True, comment="활성화 여부")
    last_used_at = Column(DateTime, nullable=True, comment="마지막 사용 시간")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성 시간")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정 시간")

    def to_dict(self, include_account_details: bool = True):
        """
        Convert to dictionary

        Args:
            include_account_details: 연결된 계정의 상세 정보 포함 여부
        """
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "coupang_account_id": self.coupang_account_id,
            "naver_account_id": self.naver_account_id,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_account_details:
            # 쿠팡 계정 정보
            if self.coupang_account:
                data["coupang_account"] = self.coupang_account.to_dict(include_keys=True)
            else:
                data["coupang_account"] = None

            # 네이버 계정 정보
            if self.naver_account:
                data["naver_account"] = self.naver_account.to_dict(include_secrets=True)
            else:
                data["naver_account"] = None

        return data

    def __repr__(self):
        return f"<AccountSet(id={self.id}, name={self.name}, is_default={self.is_default})>"
