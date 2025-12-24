"""
Response Validator Service
Multi-stage validation system for generated responses
"""
import re
import json
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from loguru import logger

from ..models import Inquiry, Response
from ..config import settings


class ResponseValidator:
    """
    Validates generated responses through multiple stages:
    1. Format validation
    2. Content validation
    3. Risk assessment
    4. Confidence scoring
    """

    # Forbidden words/phrases
    FORBIDDEN_WORDS = [
        "100% 보장", "절대", "반드시", "무조건",
        "확정", "약속", "보증"
    ]

    # High-risk phrases that require human review
    HIGH_RISK_PHRASES = [
        "법적", "소송", "변호사", "고소",
        "불법", "위법", "배상", "손해배상"
    ]

    # Financial keywords
    FINANCIAL_KEYWORDS = [
        "원", "만원", "환불", "보상", "배상", "금액"
    ]

    def __init__(self, db: Session):
        self.db = db

    def validate_response(
        self,
        response: Response,
        inquiry: Optional[Inquiry] = None
    ) -> Dict[str, any]:
        """
        Perform complete validation on a response

        Args:
            response: Response object to validate
            inquiry: Related inquiry object (optional, loaded if not provided)

        Returns:
            Validation result dictionary
        """
        logger.info(f"Validating response {response.id}")

        if not inquiry:
            inquiry = self.db.query(Inquiry).filter(
                Inquiry.id == response.inquiry_id
            ).first()

        # Stage 1: Format validation
        format_result = self._validate_format(response)

        # Stage 2: Content validation
        content_result = self._validate_content(response, inquiry)

        # Stage 3: Risk assessment
        risk_result = self._assess_risk(response, inquiry)

        # Stage 4: Final confidence calculation
        final_confidence = self._calculate_final_confidence(
            response,
            format_result,
            content_result,
            risk_result
        )

        # Compile validation results
        validation_passed = (
            format_result["passed"] and
            content_result["passed"] and
            risk_result["level"] != "critical"
        )

        all_issues = (
            format_result["issues"] +
            content_result["issues"] +
            risk_result["issues"]
        )

        # Update response object
        response.validation_passed = validation_passed
        response.validation_issues = json.dumps(all_issues, ensure_ascii=False)
        response.format_check_passed = format_result["passed"]
        response.content_check_passed = content_result["passed"]
        response.confidence_score = final_confidence
        response.risk_level = risk_result["level"]

        if validation_passed:
            response.status = "pending_approval"
        else:
            response.status = "draft"

        self.db.commit()

        result = {
            "passed": validation_passed,
            "confidence": final_confidence,
            "risk_level": risk_result["level"],
            "issues": all_issues,
            "details": {
                "format": format_result,
                "content": content_result,
                "risk": risk_result
            },
            "requires_human": self._requires_human_approval(
                validation_passed,
                final_confidence,
                risk_result["level"]
            )
        }

        logger.info(f"Validation complete: {result}")
        return result

    def _validate_format(self, response: Response) -> Dict:
        """
        Stage 1: Format validation

        Args:
            response: Response object

        Returns:
            Validation result
        """
        issues = []
        text = response.response_text

        # Check if empty
        if not text or not text.strip():
            issues.append("Response is empty")
            return {"passed": False, "issues": issues}

        # Check length
        if len(text) < 20:
            issues.append("Response is too short (minimum 20 characters)")

        if len(text) > settings.MAX_RESPONSE_LENGTH:
            issues.append(f"Response exceeds maximum length ({settings.MAX_RESPONSE_LENGTH})")

        # Check for greeting
        if not any(greeting in text for greeting in ["안녕하세요", "고객님"]):
            issues.append("Missing proper greeting")

        # Check for closing
        if not any(closing in text for closing in ["감사합니다", "감사드립니다"]):
            issues.append("Missing proper closing")

        # Check for excessive line breaks
        if text.count('\n\n\n') > 0:
            issues.append("Excessive line breaks detected")

        # Check for forbidden words
        for word in self.FORBIDDEN_WORDS:
            if word in text:
                issues.append(f"Contains forbidden word: '{word}'")

        # Check for proper JSON encoding (for API submission)
        try:
            json.dumps({"content": text})
        except Exception as e:
            issues.append(f"Text contains characters that cannot be JSON-encoded: {str(e)}")

        # Check grammar issues (basic)
        if text.count('??') > 0:
            issues.append("Contains double question marks")

        return {
            "passed": len(issues) == 0,
            "issues": issues
        }

    def _validate_content(self, response: Response, inquiry: Inquiry) -> Dict:
        """
        Stage 2: Content validation

        Args:
            response: Response object
            inquiry: Inquiry object

        Returns:
            Validation result
        """
        issues = []
        text = response.response_text.lower()
        inquiry_text = inquiry.inquiry_text.lower()

        # Check relevance - should mention customer's inquiry topic
        keywords = json.loads(inquiry.keywords) if inquiry.keywords else []
        keyword_mentioned = any(keyword in text for keyword in keywords)

        if keywords and not keyword_mentioned:
            issues.append("Response may not be relevant to inquiry")

        # Check for placeholder text
        placeholders = [
            "{{", "}}", "TODO", "xxx", "___", "[내용]", "[여기]"
        ]
        for placeholder in placeholders:
            if placeholder.lower() in text:
                issues.append(f"Contains placeholder text: '{placeholder}'")

        # Check for policy compliance based on category
        if inquiry.classified_category == "refund":
            if "환불" not in text:
                issues.append("Refund inquiry but response doesn't mention refunds")

        elif inquiry.classified_category == "shipping":
            if "배송" not in text:
                issues.append("Shipping inquiry but response doesn't mention delivery")

        elif inquiry.classified_category == "exchange":
            if "교환" not in text:
                issues.append("Exchange inquiry but response doesn't mention exchange")

        # Check for specific data accuracy
        # Ensure any mentioned dates are reasonable
        date_pattern = r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'
        dates = re.findall(date_pattern, response.response_text)

        for year, month, day in dates:
            try:
                year, month, day = int(year), int(month), int(day)
                if year < 2024 or year > 2030:
                    issues.append(f"Suspicious date: {year}년")
                if month < 1 or month > 12:
                    issues.append(f"Invalid month: {month}")
                if day < 1 or day > 31:
                    issues.append(f"Invalid day: {day}")
            except:
                pass

        # Check for negative/inappropriate tone
        negative_words = ["짜증", "귀찮", "안 됨", "불가능", "안돼"]
        for word in negative_words:
            if word in text:
                issues.append(f"Contains inappropriate negative word: '{word}'")

        return {
            "passed": len(issues) == 0,
            "issues": issues
        }

    def _assess_risk(self, response: Response, inquiry: Inquiry) -> Dict:
        """
        Stage 3: Risk assessment

        Args:
            response: Response object
            inquiry: Inquiry object

        Returns:
            Risk assessment result
        """
        risk_score = 0
        issues = []
        text = response.response_text.lower()

        # Check for high-risk phrases
        for phrase in self.HIGH_RISK_PHRASES:
            if phrase in text:
                risk_score += 50
                issues.append(f"Contains high-risk phrase: '{phrase}'")

        # Check for financial commitments
        financial_mentions = sum(1 for keyword in self.FINANCIAL_KEYWORDS if keyword in text)
        if financial_mentions > 2:
            risk_score += 30
            issues.append("Multiple financial mentions detected")

        # Check for specific amounts (potential commitment)
        amount_pattern = r'\d{1,3}(,\d{3})*원'
        amounts = re.findall(amount_pattern, response.response_text)
        if amounts:
            risk_score += 20
            issues.append(f"Specific amounts mentioned: {amounts}")

        # Check inquiry risk level
        if inquiry.risk_level == "high":
            risk_score += 40
            issues.append("Inquiry itself is high-risk")
        elif inquiry.risk_level == "medium":
            risk_score += 20

        # Check for exceptions or special handling
        exception_words = ["예외", "특별", "한 번만", "이번만"]
        if any(word in text for word in exception_words):
            risk_score += 25
            issues.append("Mentions exceptions or special handling")

        # Check response complexity vs inquiry complexity
        if inquiry.complexity_score and inquiry.complexity_score > 70:
            if len(response.response_text) < 200:
                risk_score += 15
                issues.append("Complex inquiry but simple response")

        # Determine risk level
        if risk_score >= 70:
            level = "critical"
        elif risk_score >= 40:
            level = "high"
        elif risk_score >= 20:
            level = "medium"
        else:
            level = "low"

        return {
            "level": level,
            "score": risk_score,
            "issues": issues
        }

    def _calculate_final_confidence(
        self,
        response: Response,
        format_result: Dict,
        content_result: Dict,
        risk_result: Dict
    ) -> float:
        """
        Stage 4: Calculate final confidence score

        Args:
            response: Response object
            format_result: Format validation result
            content_result: Content validation result
            risk_result: Risk assessment result

        Returns:
            Final confidence score (0-100)
        """
        # Start with base confidence from generation
        confidence = response.confidence_score or 50.0

        # Deduct points for format issues
        format_issues = len(format_result["issues"])
        confidence -= format_issues * 5

        # Deduct points for content issues
        content_issues = len(content_result["issues"])
        confidence -= content_issues * 10

        # Deduct points based on risk level
        risk_penalties = {
            "critical": 40,
            "high": 25,
            "medium": 10,
            "low": 0
        }
        confidence -= risk_penalties.get(risk_result["level"], 0)

        # Ensure confidence is within bounds
        confidence = max(0, min(100, confidence))

        return round(confidence, 2)

    def _requires_human_approval(
        self,
        validation_passed: bool,
        confidence: float,
        risk_level: str
    ) -> bool:
        """
        Determine if human approval is required

        Args:
            validation_passed: Whether validation passed
            confidence: Final confidence score
            risk_level: Risk level

        Returns:
            True if human approval required
        """
        # Failed validation always requires human
        if not validation_passed:
            return True

        # Critical or high risk requires human
        if risk_level in ["critical", "high"]:
            return True

        # Low confidence requires human
        if confidence < settings.CONFIDENCE_THRESHOLD:
            return True

        # Medium risk + moderate confidence requires human
        if risk_level == "medium" and confidence < settings.AUTO_APPROVE_THRESHOLD:
            return True

        return False

    def can_auto_approve(self, response: Response) -> bool:
        """
        Check if response can be auto-approved

        Args:
            response: Response object

        Returns:
            True if can be auto-approved
        """
        return (
            response.validation_passed and
            response.confidence_score >= settings.AUTO_APPROVE_THRESHOLD and
            response.risk_level == "low"
        )

    def get_validation_summary(self, response_id: int) -> Dict:
        """
        Get validation summary for a response

        Args:
            response_id: Response ID

        Returns:
            Validation summary
        """
        response = self.db.query(Response).filter(Response.id == response_id).first()
        if not response:
            return None

        issues = json.loads(response.validation_issues) if response.validation_issues else []

        return {
            "response_id": response.id,
            "validation_passed": response.validation_passed,
            "confidence_score": response.confidence_score,
            "risk_level": response.risk_level,
            "format_check": response.format_check_passed,
            "content_check": response.content_check_passed,
            "issues_count": len(issues),
            "issues": issues,
            "can_auto_approve": self.can_auto_approve(response)
        }
