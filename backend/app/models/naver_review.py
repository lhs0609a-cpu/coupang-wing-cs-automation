"""
Naver Review Automation Models
네이버 리뷰 자동화 데이터 모델
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class NaverReviewTemplate(Base):
    """리뷰 템플릿 모델"""
    __tablename__ = "naver_review_templates"

    id = Column(Integer, primary_key=True, index=True)

    # 리뷰 내용
    star_rating = Column(Integer, default=5, comment="별점 (1-5)")
    review_text = Column(Text, nullable=False, comment="리뷰 텍스트")
    image_paths = Column(String(2000), nullable=True, comment="이미지 경로 (세미콜론 구분)")

    # 상태
    is_active = Column(Boolean, default=True, comment="활성화 여부")
    use_count = Column(Integer, default=0, comment="사용 횟수")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "star_rating": self.star_rating,
            "review_text": self.review_text,
            "image_paths": self.image_paths.split(";") if self.image_paths else [],
            "is_active": self.is_active,
            "use_count": self.use_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class NaverReviewLog(Base):
    """리뷰 작성 로그 모델"""
    __tablename__ = "naver_review_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 세션 정보
    session_id = Column(String(50), nullable=False, index=True, comment="자동화 세션 ID")
    naver_account_id = Column(Integer, ForeignKey("naver_accounts.id"), nullable=True)

    # 상품 정보
    product_name = Column(String(500), nullable=True, comment="상품명")
    point_amount = Column(Integer, default=0, comment="포인트 금액")

    # 리뷰 정보
    review_text = Column(Text, nullable=True, comment="작성된 리뷰")
    star_rating = Column(Integer, default=5, comment="별점")
    image_count = Column(Integer, default=0, comment="첨부된 이미지 수")

    # 결과
    status = Column(String(20), default="pending", comment="상태: pending, success, failed, skipped")
    error_message = Column(Text, nullable=True, comment="에러 메시지")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationship
    naver_account = relationship("NaverAccount", foreign_keys=[naver_account_id])

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "naver_account_id": self.naver_account_id,
            "product_name": self.product_name,
            "point_amount": self.point_amount,
            "review_text": self.review_text,
            "star_rating": self.star_rating,
            "image_count": self.image_count,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class NaverReviewImage(Base):
    """리뷰 이미지 모델"""
    __tablename__ = "naver_review_images"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String(255), nullable=False, comment="파일명")
    original_filename = Column(String(255), nullable=True, comment="원본 파일명")
    file_path = Column(String(500), nullable=False, comment="파일 경로")
    file_size = Column(Integer, default=0, comment="파일 크기 (bytes)")
    mime_type = Column(String(50), nullable=True, comment="MIME 타입")

    # 상태
    is_active = Column(Boolean, default=True)
    use_count = Column(Integer, default=0, comment="사용 횟수")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "is_active": self.is_active,
            "use_count": self.use_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "url": f"/api/naver-review/images/file/{self.filename}"
        }


class NaverReviewStats(Base):
    """일별 리뷰 통계 모델"""
    __tablename__ = "naver_review_stats"

    id = Column(Integer, primary_key=True, index=True)

    date = Column(DateTime, nullable=False, index=True, comment="날짜")
    naver_account_id = Column(Integer, ForeignKey("naver_accounts.id"), nullable=True)

    # 통계
    total_reviews = Column(Integer, default=0, comment="총 리뷰 수")
    success_count = Column(Integer, default=0, comment="성공 수")
    failed_count = Column(Integer, default=0, comment="실패 수")
    skipped_count = Column(Integer, default=0, comment="스킵 수")
    total_points = Column(Integer, default=0, comment="총 획득 포인트")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d") if self.date else None,
            "naver_account_id": self.naver_account_id,
            "total_reviews": self.total_reviews,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "total_points": self.total_points,
            "success_rate": round(self.success_count / self.total_reviews * 100, 1) if self.total_reviews > 0 else 0
        }
