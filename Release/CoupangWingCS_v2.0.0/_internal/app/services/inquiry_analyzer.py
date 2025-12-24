"""
Inquiry Analyzer Service
Analyzes and classifies customer inquiries
"""
import re
import json
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from loguru import logger

from ..models import Inquiry
from ..config import settings


class InquiryAnalyzer:
    """
    Analyzes customer inquiries to classify category, extract keywords,
    assess risk, and determine if human intervention is needed
    """

    # Category keywords mapping
    CATEGORY_KEYWORDS = {
        "shipping": ["배송", "발송", "택배", "운송", "도착", "언제", "늦", "빠르", "배달"],
        "refund": ["환불", "취소", "반품", "돌려", "취소하", "환불받"],
        "exchange": ["교환", "바꿔", "다른", "변경", "다시"],
        "product": ["상품", "제품", "물건", "품질", "불량", "파손", "다름", "설명"],
        "payment": ["결제", "결제", "돈", "금액", "가격", "할인", "쿠폰", "포인트"],
        "delivery_address": ["주소", "주소지", "받는", "수령"],
        "size_color": ["사이즈", "크기", "색상", "컬러", "치수"],
        "stock": ["재고", "품절", "입고", "수량"],
        "receipt": ["영수증", "증빙", "거래명세서"],
        "complaint": ["불만", "항의", "화", "짜증", "답답", "실망"]
    }

    # High-risk keywords
    HIGH_RISK_KEYWORDS = [
        "소송", "법", "변호사", "고소", "신고", "소비자원", "공정위",
        "피해", "사기", "거짓", "기만", "언론", "보도"
    ]

    # Urgent keywords
    URGENT_KEYWORDS = [
        "급", "빨리", "긴급", "당장", "바로", "즉시", "시급"
    ]

    # Negative sentiment keywords
    NEGATIVE_KEYWORDS = [
        "실망", "화", "짜증", "최악", "엉망", "불만", "항의",
        "불친절", "무시", "답답", "어이없", "황당"
    ]

    def __init__(self, db: Session):
        self.db = db

    def analyze_inquiry(self, inquiry: Inquiry) -> Dict[str, any]:
        """
        Perform complete analysis on an inquiry

        Args:
            inquiry: Inquiry object to analyze

        Returns:
            Analysis results dictionary
        """
        logger.info(f"Analyzing inquiry {inquiry.id}")

        text = inquiry.inquiry_text.lower()

        # Classify category
        category, confidence = self._classify_category(text)

        # Extract keywords
        keywords = self._extract_keywords(text)

        # Assess risk level
        risk_level = self._assess_risk_level(text, inquiry)

        # Check sentiment
        sentiment = self._analyze_sentiment(text)

        # Calculate complexity
        complexity = self._calculate_complexity(text, inquiry)

        # Determine if human review needed
        requires_human = self._requires_human_review(
            text, inquiry, risk_level, confidence, complexity
        )

        # Check urgency
        is_urgent = self._check_urgency(text)

        # Update inquiry with analysis results
        inquiry.classified_category = category
        inquiry.confidence_score = confidence
        inquiry.risk_level = risk_level
        inquiry.keywords = json.dumps(keywords, ensure_ascii=False)
        inquiry.sentiment = sentiment
        inquiry.complexity_score = complexity
        inquiry.requires_human = requires_human
        inquiry.is_urgent = is_urgent

        self.db.commit()

        result = {
            "category": category,
            "confidence": confidence,
            "risk_level": risk_level,
            "keywords": keywords,
            "sentiment": sentiment,
            "complexity": complexity,
            "requires_human": requires_human,
            "is_urgent": is_urgent
        }

        logger.info(f"Analysis complete: {result}")
        return result

    def _classify_category(self, text: str) -> Tuple[str, float]:
        """
        Classify inquiry category based on keywords

        Args:
            text: Inquiry text (lowercase)

        Returns:
            Tuple of (category, confidence_score)
        """
        scores = {}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[category] = score

        if not scores:
            return "unknown", 0.0

        # Get category with highest score
        max_category = max(scores, key=scores.get)
        max_score = scores[max_category]

        # Calculate confidence (0-100)
        total_keywords = len(self.CATEGORY_KEYWORDS[max_category])
        confidence = min(100, (max_score / total_keywords) * 100 + 50)

        # If multiple categories have similar scores, reduce confidence
        high_scores = [s for s in scores.values() if s >= max_score * 0.7]
        if len(high_scores) > 1:
            confidence *= 0.7

        return max_category, round(confidence, 2)

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from text

        Args:
            text: Inquiry text

        Returns:
            List of keywords
        """
        keywords = []

        # Extract from all category keywords
        for category, category_keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in category_keywords:
                if keyword in text:
                    keywords.append(keyword)

        # Remove duplicates and limit
        keywords = list(set(keywords))[:10]

        return keywords

    def _assess_risk_level(self, text: str, inquiry: Inquiry) -> str:
        """
        Assess risk level of inquiry

        Args:
            text: Inquiry text
            inquiry: Inquiry object

        Returns:
            Risk level: 'low', 'medium', 'high'
        """
        risk_score = 0

        # Check for high-risk keywords
        high_risk_count = sum(1 for keyword in self.HIGH_RISK_KEYWORDS if keyword in text)
        if high_risk_count > 0:
            risk_score += 50

        # Check for negative sentiment
        negative_count = sum(1 for keyword in self.NEGATIVE_KEYWORDS if keyword in text)
        if negative_count >= 3:
            risk_score += 30
        elif negative_count >= 1:
            risk_score += 10

        # Check for financial mentions
        if re.search(r'\d+만원|\d+원|금액|돈|환불', text):
            risk_score += 20

        # Check text length (very long = complex = risky)
        if len(text) > 500:
            risk_score += 15

        # Check for multiple questions
        question_count = text.count('?') + text.count('???')
        if question_count > 3:
            risk_score += 10

        # Determine risk level
        if risk_score >= 50:
            return "high"
        elif risk_score >= 20:
            return "medium"
        else:
            return "low"

    def _analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of inquiry

        Args:
            text: Inquiry text

        Returns:
            Sentiment: 'positive', 'neutral', 'negative'
        """
        negative_count = sum(1 for keyword in self.NEGATIVE_KEYWORDS if keyword in text)

        # Simple sentiment analysis
        if negative_count >= 2:
            return "negative"
        elif negative_count == 1:
            return "neutral"
        else:
            return "neutral"  # Default to neutral for safety

    def _calculate_complexity(self, text: str, inquiry: Inquiry) -> float:
        """
        Calculate complexity score of inquiry

        Args:
            text: Inquiry text
            inquiry: Inquiry object

        Returns:
            Complexity score (0-100)
        """
        complexity = 0

        # Text length factor
        if len(text) > 500:
            complexity += 30
        elif len(text) > 200:
            complexity += 15

        # Number of questions
        questions = text.count('?')
        complexity += min(20, questions * 5)

        # Multiple categories mentioned
        categories_mentioned = sum(
            1 for keywords in self.CATEGORY_KEYWORDS.values()
            if any(k in text for k in keywords)
        )
        if categories_mentioned > 2:
            complexity += 25

        # Numbers and specific details
        if re.search(r'\d{4,}', text):  # Order numbers, etc.
            complexity += 10

        return min(100, complexity)

    def _requires_human_review(
        self,
        text: str,
        inquiry: Inquiry,
        risk_level: str,
        confidence: float,
        complexity: float
    ) -> bool:
        """
        Determine if inquiry requires human review

        Args:
            text: Inquiry text
            inquiry: Inquiry object
            risk_level: Risk level
            confidence: Classification confidence
            complexity: Complexity score

        Returns:
            True if human review required
        """
        # High risk always requires human
        if risk_level == "high":
            return True

        # Low confidence requires human
        if confidence < 60:
            return True

        # High complexity requires human
        if complexity > 70:
            return True

        # Legal/lawsuit mentions
        if any(keyword in text for keyword in ["소송", "법", "변호사", "고소"]):
            return True

        # Exception requests
        exception_keywords = ["예외", "특별", "사정", "양해"]
        if any(keyword in text for keyword in exception_keywords):
            return True

        # Very negative sentiment
        negative_count = sum(1 for keyword in self.NEGATIVE_KEYWORDS if keyword in text)
        if negative_count >= 3:
            return True

        return False

    def _check_urgency(self, text: str) -> bool:
        """
        Check if inquiry is urgent

        Args:
            text: Inquiry text

        Returns:
            True if urgent
        """
        return any(keyword in text for keyword in self.URGENT_KEYWORDS)

    def get_analysis_summary(self, inquiry_id: int) -> Dict[str, any]:
        """
        Get analysis summary for an inquiry

        Args:
            inquiry_id: Inquiry ID

        Returns:
            Analysis summary
        """
        inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
        if not inquiry:
            return None

        return {
            "inquiry_id": inquiry.id,
            "category": inquiry.classified_category,
            "confidence": inquiry.confidence_score,
            "risk_level": inquiry.risk_level,
            "sentiment": inquiry.sentiment,
            "complexity": inquiry.complexity_score,
            "requires_human": inquiry.requires_human,
            "is_urgent": inquiry.is_urgent,
            "keywords": json.loads(inquiry.keywords) if inquiry.keywords else []
        }
