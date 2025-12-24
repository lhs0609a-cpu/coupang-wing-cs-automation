"""
AI Response Generator using OpenAI
"""
import json
from typing import Dict, Optional
from openai import OpenAI
from loguru import logger

from ..models import Inquiry
from ..config import settings


class AIResponseGenerator:
    """
    Generates responses using OpenAI GPT models
    """

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_response(
        self,
        inquiry: Inquiry,
        policy_context: str = "",
        template_hint: str = ""
    ) -> Optional[Dict[str, any]]:
        """
        Generate response using OpenAI

        Args:
            inquiry: Inquiry object
            policy_context: Related policy information
            template_hint: Template or guideline hint

        Returns:
            Dictionary with response_text and metadata
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return None

        try:
            # Prepare system prompt
            system_prompt = self._create_system_prompt(policy_context)

            # Prepare user message
            user_message = self._create_user_message(inquiry, template_hint)

            logger.info(f"Generating AI response for inquiry {inquiry.id}")

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=800,
                top_p=0.9,
                frequency_penalty=0.3,
                presence_penalty=0.3
            )

            # Extract response
            ai_response = response.choices[0].message.content.strip()

            # Parse metadata if included
            result = {
                "response_text": ai_response,
                "model": settings.OPENAI_MODEL,
                "tokens_used": response.usage.total_tokens,
                "confidence": self._estimate_confidence(response)
            }

            logger.success(f"AI response generated for inquiry {inquiry.id}")
            return result

        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return None

    def _create_system_prompt(self, policy_context: str) -> str:
        """
        Create system prompt for OpenAI

        Args:
            policy_context: Policy information

        Returns:
            System prompt string
        """
        prompt = """당신은 쿠팡 판매자의 고객 응대 전문가입니다.

역할 및 책임:
- 고객 문의에 대해 정확하고 친절한 답변을 작성합니다
- 쿠팡의 정책과 가이드라인을 준수합니다
- 전문적이고 예의 바른 어투를 사용합니다

답변 작성 가이드라인:
1. 반드시 "안녕하세요, 고객님." 또는 "안녕하세요, [고객명]님."으로 시작
2. 고객의 문의 내용을 정확히 이해하고 답변
3. 구체적이고 명확한 정보 제공
4. 필요시 단계별 안내 제공
5. 반드시 "감사합니다." 또는 "감사드립니다."로 마무리

금지 사항:
- 100% 보장, 절대, 무조건 등의 단정적 표현 사용 금지
- 법적 자문 제공 금지
- 쿠팡 정책에 어긋나는 약속 금지
- 부정확한 정보 제공 금지

답변 형식:
- 인사말
- 본문 (문의 내용 확인 + 상세 답변)
- 추가 안내사항 (필요시)
- 마무리 인사
"""

        if policy_context:
            prompt += f"\n\n관련 정책 정보:\n{policy_context}"

        return prompt

    def _create_user_message(self, inquiry: Inquiry, template_hint: str) -> str:
        """
        Create user message for OpenAI

        Args:
            inquiry: Inquiry object
            template_hint: Template hint

        Returns:
            User message string
        """
        message = f"""다음 고객 문의에 대한 답변을 작성해주세요.

[고객 정보]
고객명: {inquiry.customer_name or '고객'}
주문번호: {inquiry.order_number or 'N/A'}
상품명: {inquiry.product_name or 'N/A'}

[문의 내용]
{inquiry.inquiry_text}

[문의 분류]
카테고리: {inquiry.classified_category or '일반 문의'}
"""

        if inquiry.risk_level == "high":
            message += "\n⚠️ 주의: 이 문의는 높은 위험도로 분류되었습니다. 신중하게 답변해주세요."

        if template_hint:
            message += f"\n\n[답변 참고사항]\n{template_hint}"

        message += "\n\n위 정보를 바탕으로 전문적이고 친절한 답변을 한국어로 작성해주세요."

        return message

    def _estimate_confidence(self, response) -> float:
        """
        Estimate confidence based on response metadata

        Args:
            response: OpenAI response object

        Returns:
            Confidence score (0-100)
        """
        # Base confidence for AI responses
        base_confidence = 75.0

        # Adjust based on finish reason
        if hasattr(response.choices[0], 'finish_reason'):
            if response.choices[0].finish_reason == 'stop':
                base_confidence += 10
            elif response.choices[0].finish_reason == 'length':
                base_confidence -= 10

        return min(100, max(0, base_confidence))

    def enhance_template_response(
        self,
        template_response: str,
        inquiry: Inquiry,
        policy_context: str = ""
    ) -> Optional[str]:
        """
        Enhance template-based response using AI

        Args:
            template_response: Original template response
            inquiry: Inquiry object
            policy_context: Policy information

        Returns:
            Enhanced response or None
        """
        if not self.client:
            return None

        try:
            system_prompt = """당신은 고객 응대 텍스트를 개선하는 전문가입니다.
주어진 템플릿 답변을 더 자연스럽고 개인화되게 개선해주세요.
단, 핵심 정보와 정책은 반드시 유지해야 합니다."""

            user_message = f"""다음 템플릿 답변을 개선해주세요.

[원본 답변]
{template_response}

[고객 문의]
{inquiry.inquiry_text}

개선된 답변을 작성해주세요. 핵심 정보는 유지하되, 더 자연스럽고 따뜻한 어투로 작성해주세요."""

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.5,
                max_tokens=800
            )

            enhanced = response.choices[0].message.content.strip()
            logger.info(f"Template response enhanced for inquiry {inquiry.id}")

            return enhanced

        except Exception as e:
            logger.error(f"Error enhancing response: {str(e)}")
            return None

    def validate_response_with_ai(
        self,
        response_text: str,
        inquiry: Inquiry
    ) -> Dict[str, any]:
        """
        Use AI to validate response quality

        Args:
            response_text: Response to validate
            inquiry: Original inquiry

        Returns:
            Validation result
        """
        if not self.client:
            return {"valid": True, "issues": [], "confidence": 50}

        try:
            system_prompt = """당신은 고객 응대 품질 검수 전문가입니다.
답변의 품질을 평가하고 문제점을 찾아주세요."""

            user_message = f"""다음 답변의 품질을 평가해주세요.

[고객 문의]
{inquiry.inquiry_text}

[작성된 답변]
{response_text}

다음 항목을 JSON 형식으로 평가해주세요:
{{
  "appropriate": true/false,
  "professional": true/false,
  "complete": true/false,
  "issues": ["문제점 나열"],
  "score": 0-100
}}"""

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return {
                "valid": result.get("appropriate", True) and result.get("complete", True),
                "issues": result.get("issues", []),
                "confidence": result.get("score", 70)
            }

        except Exception as e:
            logger.error(f"Error validating with AI: {str(e)}")
            return {"valid": True, "issues": [], "confidence": 50}
