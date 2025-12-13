"""
자동 반품 처리 실행 로그 모델
자동화 실행 내역과 성능을 추적하기 위한 로그
"""
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Text
from sqlalchemy.sql import func
from ..database import Base


class AutoReturnExecutionLog(Base):
    """자동 반품 처리 실행 로그"""
    __tablename__ = "auto_return_execution_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 실행 정보
    execution_type = Column(String, nullable=False, index=True, comment="FETCH 또는 PROCESS")
    status = Column(String, nullable=False, index=True, comment="success, failed, partial")

    # 시작/종료 시간
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True, comment="실행 시간(초)")

    # 실행 결과
    total_items = Column(Integer, default=0, comment="전체 아이템 수")
    success_count = Column(Integer, default=0, comment="성공 개수")
    failed_count = Column(Integer, default=0, comment="실패 개수")

    # 상세 정보
    details = Column(JSON, nullable=True, comment="상세 실행 정보")
    error_message = Column(Text, nullable=True, comment="에러 메시지")

    # 메타데이터
    triggered_by = Column(String, nullable=True, comment="scheduler, manual, api 등")
    config_snapshot = Column(JSON, nullable=True, comment="실행 시점의 설정 스냅샷")

    def __repr__(self):
        return f"<AutoReturnExecutionLog(id={self.id}, type={self.execution_type}, status={self.status})>"

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "execution_type": self.execution_type,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "total_items": self.total_items,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "details": self.details,
            "error_message": self.error_message,
            "triggered_by": self.triggered_by,
        }
