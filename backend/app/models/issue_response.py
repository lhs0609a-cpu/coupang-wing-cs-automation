"""
Issue Response Model
쿠팡 판매 관련 문제 대응 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from ..database import Base


class IssueResponse(Base):
    """문제 대응 기록 모델"""
    __tablename__ = "issue_responses"

    id = Column(Integer, primary_key=True, index=True)
    coupang_account_id = Column(Integer, ForeignKey("coupang_accounts.id"), nullable=True)

    # 문제 정보
    issue_type = Column(String(50), nullable=False)  # ip_infringement, reseller, suspension, other
    issue_subtype = Column(String(100))  # 세부 유형 (trademark, copyright, parallel_import 등)
    original_content = Column(Text, nullable=False)  # 원본 메일/알림 내용

    # AI 분석 결과
    ai_analysis = Column(JSON)  # 문제 분석 결과 (JSON)
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    summary = Column(String(500))  # 요약
    deadline = Column(String(50))  # 대응 기한
    recommended_actions = Column(JSON)  # 권장 조치 목록

    # 생성된 답변
    generated_response = Column(Text)  # AI 생성 답변
    response_type = Column(String(20))  # appeal (이의제기), statement (소명서), report (신고답변)
    confidence = Column(Integer)  # AI 신뢰도 (0-100)
    suggestions = Column(JSON)  # 첨부 권장 서류 등 제안사항

    # 상태
    status = Column(String(20), default="draft")  # draft, copied, resolved
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)  # 해결 메모

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "coupang_account_id": self.coupang_account_id,
            "issue_type": self.issue_type,
            "issue_subtype": self.issue_subtype,
            "original_content": self.original_content,
            "ai_analysis": self.ai_analysis,
            "severity": self.severity,
            "summary": self.summary,
            "deadline": self.deadline,
            "recommended_actions": self.recommended_actions,
            "generated_response": self.generated_response,
            "response_type": self.response_type,
            "confidence": self.confidence,
            "suggestions": self.suggestions,
            "status": self.status,
            "is_resolved": self.is_resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<IssueResponse {self.id}: {self.issue_type}/{self.issue_subtype}>"


class IssueTemplate(Base):
    """문제 대응 템플릿 모델"""
    __tablename__ = "issue_templates"

    id = Column(Integer, primary_key=True, index=True)

    # 분류
    issue_type = Column(String(50), nullable=False)  # ip_infringement, reseller, suspension, other
    issue_subtype = Column(String(100))  # 세부 유형
    response_type = Column(String(20), nullable=False)  # appeal, statement, report

    # 템플릿 내용
    name = Column(String(200), nullable=False)  # 템플릿 이름
    description = Column(Text)  # 템플릿 설명
    template_content = Column(Text, nullable=False)  # 템플릿 본문

    # 메타데이터
    is_default = Column(Boolean, default=False)  # 기본 템플릿 여부
    use_count = Column(Integer, default=0)  # 사용 횟수

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "issue_type": self.issue_type,
            "issue_subtype": self.issue_subtype,
            "response_type": self.response_type,
            "name": self.name,
            "description": self.description,
            "template_content": self.template_content,
            "is_default": self.is_default,
            "use_count": self.use_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<IssueTemplate {self.id}: {self.name}>"
