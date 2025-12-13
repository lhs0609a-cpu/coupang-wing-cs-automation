"""
Response Generator Service
Generates responses to customer inquiries using templates and knowledge base
"""
import json
import re
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger

from ..models import Inquiry, Response, KnowledgeBase
from ..config import settings


class ResponseGenerator:
    """
    Generates responses to customer inquiries
    """

    def __init__(self, db: Session):
        self.db = db
        self.templates_dir = settings.TEMPLATES_DIR
        self.policies_dir = settings.POLICIES_DIR
        self.faq_dir = settings.FAQ_DIR

    def generate_response(
        self,
        inquiry: Inquiry,
        method: str = "template"
    ) -> Optional[Response]:
        """
        Generate response for an inquiry

        Args:
            inquiry: Inquiry object
            method: Generation method ('template', 'ai', or 'hybrid')

        Returns:
            Response object or None if generation failed
        """
        logger.info(f"Generating response for inquiry {inquiry.id} using {method} method")

        try:
            if method == "template":
                response = self._generate_from_template(inquiry)
            elif method == "ai":
                response = self._generate_with_ai(inquiry)
            elif method == "hybrid":
                response = self._generate_hybrid(inquiry)
            else:
                logger.error(f"Unknown generation method: {method}")
                return None

            if response:
                logger.success(f"Response generated for inquiry {inquiry.id}")
                return response
            else:
                logger.warning(f"Failed to generate response for inquiry {inquiry.id}")
                return None

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return None

    def _generate_from_template(self, inquiry: Inquiry) -> Optional[Response]:
        """
        Generate response using template system

        Args:
            inquiry: Inquiry object

        Returns:
            Response object or None
        """
        category = inquiry.classified_category or "general"

        # Load template
        template_content = self._load_template(category)
        if not template_content:
            logger.warning(f"No template found for category: {category}")
            template_content = self._load_template("general_response")

        if not template_content:
            return None

        # Load policy information
        policy_info = self._load_policy(category)

        # Prepare template variables
        variables = self._prepare_template_variables(inquiry, policy_info)

        # Fill template
        response_text = self._fill_template(template_content, variables)

        # Calculate confidence score
        confidence = self._calculate_template_confidence(inquiry, category)

        # Create Response object
        response = Response(
            inquiry_id=inquiry.id,
            response_text=response_text,
            original_response=response_text,
            confidence_score=confidence,
            template_used=f"{category}.txt",
            generation_method="template",
            status="draft"
        )

        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)

        return response

    def _load_template(self, category: str) -> Optional[str]:
        """
        Load template file

        Args:
            category: Template category

        Returns:
            Template content or None
        """
        template_file = self.templates_dir / f"{category}.txt"

        if not template_file.exists():
            logger.warning(f"Template not found: {template_file}")
            return None

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading template: {str(e)}")
            return None

    def _load_policy(self, category: str) -> Dict:
        """
        Load policy information

        Args:
            category: Policy category

        Returns:
            Policy data dictionary
        """
        # Map inquiry categories to policy files
        policy_map = {
            "shipping": "shipping_policy",
            "refund": "refund_policy",
            "exchange": "exchange_policy"
        }

        policy_name = policy_map.get(category)
        if not policy_name:
            return {}

        policy_file = self.policies_dir / f"{policy_name}.json"

        if not policy_file.exists():
            return {}

        try:
            with open(policy_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading policy: {str(e)}")
            return {}

    def _prepare_template_variables(
        self,
        inquiry: Inquiry,
        policy_info: Dict
    ) -> Dict[str, str]:
        """
        Prepare variables for template filling

        Args:
            inquiry: Inquiry object
            policy_info: Policy information

        Returns:
            Dictionary of template variables
        """
        variables = {
            "customer_name": inquiry.customer_name or "고객",
            "product_name": inquiry.product_name or "상품",
            "order_number": inquiry.order_number or "N/A",
            "inquiry_content": inquiry.inquiry_text[:200],
            "delivery_status": "배송 준비 중",
            "estimated_delivery_date": self._calculate_delivery_date(),
            "delay_reason": "현재 주문량이 많아 배송이 다소 지연되고 있습니다.",
            "refund_amount": "상품 금액",
            "return_pickup_date": self._calculate_pickup_date(),
            "exchange_reason": "상품 교환",
            "new_product_delivery_date": self._calculate_delivery_date(days=7),
            "stock_status": "재고 확인 중",
            "restock_date": self._calculate_delivery_date(days=7),
            "answer_content": "",
            "response_content": "",
            "additional_information": "",
            "additional_notes": "",
            "exchange_details": "",
            "refund_details": "",
            "stock_details": "",
            "order_guidance": ""
        }

        # Customize based on category
        category = inquiry.classified_category

        if category == "shipping":
            variables["answer_content"] = self._get_shipping_info(inquiry, policy_info)
        elif category == "refund":
            variables["refund_details"] = self._get_refund_info(inquiry, policy_info)
        elif category == "exchange":
            variables["exchange_details"] = self._get_exchange_info(inquiry, policy_info)
        elif category == "stock":
            variables["stock_details"] = "재고 상황을 확인하여 별도로 안내드리겠습니다."
        else:
            variables["response_content"] = self._get_general_response(inquiry)

        return variables

    def _fill_template(self, template: str, variables: Dict[str, str]) -> str:
        """
        Fill template with variables

        Args:
            template: Template string
            variables: Variable dictionary

        Returns:
            Filled template
        """
        result = template

        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))

        # Remove unfilled placeholders
        result = re.sub(r'\{\{[^}]+\}\}', '', result)

        # Clean up extra newlines
        result = re.sub(r'\n\n\n+', '\n\n', result)

        return result.strip()

    def _calculate_delivery_date(self, days: int = 2) -> str:
        """
        Calculate estimated delivery date

        Args:
            days: Days from now

        Returns:
            Formatted date string
        """
        date = datetime.now() + timedelta(days=days)
        return date.strftime("%Y년 %m월 %d일")

    def _calculate_pickup_date(self) -> str:
        """
        Calculate pickup date

        Returns:
            Formatted date string
        """
        date = datetime.now() + timedelta(days=1)
        return date.strftime("%Y년 %m월 %d일")

    def _get_shipping_info(self, inquiry: Inquiry, policy_info: Dict) -> str:
        """
        Get shipping information response

        Args:
            inquiry: Inquiry object
            policy_info: Policy information

        Returns:
            Response text
        """
        text = inquiry.inquiry_text.lower()

        if "언제" in text or "얼마" in text or "기간" in text:
            return "로켓배송 상품은 주문 후 1-2일 내 배송됩니다. 서울/수도권은 익일 배송, 지방은 1-2일 소요됩니다."
        elif "조회" in text or "추적" in text:
            return "쿠팡 앱 또는 웹사이트의 '주문 내역'에서 실시간 배송 추적이 가능합니다."
        elif "지연" in text or "늦" in text:
            return "배송 지연으로 불편을 드려 죄송합니다. 현재 배송 상황을 확인하여 빠르게 안내드리겠습니다."
        else:
            return "배송 관련 문의 주셔서 감사합니다. 배송 상황을 확인하여 안내드리겠습니다."

    def _get_refund_info(self, inquiry: Inquiry, policy_info: Dict) -> str:
        """
        Get refund information response

        Args:
            inquiry: Inquiry object
            policy_info: Policy information

        Returns:
            Response text
        """
        return "상품 수령 후 7일 이내 환불 요청이 가능하며, 상품 확인 후 3-5영업일 내 환불됩니다."

    def _get_exchange_info(self, inquiry: Inquiry, policy_info: Dict) -> str:
        """
        Get exchange information response

        Args:
            inquiry: Inquiry object
            policy_info: Policy information

        Returns:
            Response text
        """
        return "상품 수령 후 7일 이내 교환 신청이 가능합니다. 재고 확인 후 새 상품을 발송해 드리겠습니다."

    def _get_general_response(self, inquiry: Inquiry) -> str:
        """
        Get general response

        Args:
            inquiry: Inquiry object

        Returns:
            Response text
        """
        # Try to match with FAQ
        faq_answer = self._search_faq(inquiry.inquiry_text)
        if faq_answer:
            return faq_answer

        return "문의 주신 내용을 확인하여 빠르게 답변드리겠습니다."

    def _search_faq(self, inquiry_text: str) -> Optional[str]:
        """
        Search FAQ for matching answer

        Args:
            inquiry_text: Inquiry text

        Returns:
            FAQ answer or None
        """
        faq_file = self.faq_dir / "common_qa.json"

        if not faq_file.exists():
            return None

        try:
            with open(faq_file, 'r', encoding='utf-8') as f:
                faq_data = json.load(f)

            text_lower = inquiry_text.lower()

            for faq in faq_data.get("faqs", []):
                keywords = faq.get("keywords", [])
                if any(keyword in text_lower for keyword in keywords):
                    return faq.get("answer")

            return None

        except Exception as e:
            logger.error(f"Error searching FAQ: {str(e)}")
            return None

    def _calculate_template_confidence(self, inquiry: Inquiry, category: str) -> float:
        """
        Calculate confidence score for template-based response

        Args:
            inquiry: Inquiry object
            category: Category used

        Returns:
            Confidence score (0-100)
        """
        base_score = 70.0

        # Increase confidence if category matches well
        if inquiry.confidence_score:
            base_score += (inquiry.confidence_score - 70) * 0.3

        # Decrease confidence for complex inquiries
        if inquiry.complexity_score and inquiry.complexity_score > 70:
            base_score -= 15

        # Decrease confidence for risky inquiries
        if inquiry.risk_level == "high":
            base_score -= 20
        elif inquiry.risk_level == "medium":
            base_score -= 10

        return max(0, min(100, base_score))

    def _generate_with_ai(self, inquiry: Inquiry) -> Optional[Response]:
        """
        Generate response using AI (OpenAI)

        Args:
            inquiry: Inquiry object

        Returns:
            Response object or None
        """
        from .ai_response_generator import AIResponseGenerator

        try:
            # Load policy context
            category = inquiry.classified_category or "general"
            policy_info = self._load_policy(category)
            policy_text = json.dumps(policy_info, ensure_ascii=False, indent=2) if policy_info else ""

            # Generate with AI
            ai_generator = AIResponseGenerator()
            result = ai_generator.generate_response(
                inquiry=inquiry,
                policy_context=policy_text
            )

            if not result:
                logger.error("AI generation failed")
                return None

            # Calculate confidence
            confidence = result.get("confidence", 75.0)

            # Create Response object
            response = Response(
                inquiry_id=inquiry.id,
                response_text=result["response_text"],
                original_response=result["response_text"],
                confidence_score=confidence,
                template_used="ai_generated",
                generation_method="ai",
                status="draft"
            )

            self.db.add(response)
            self.db.commit()
            self.db.refresh(response)

            logger.success(f"AI response generated for inquiry {inquiry.id}")
            return response

        except Exception as e:
            logger.error(f"Error in AI generation: {str(e)}")
            return None

    def _generate_hybrid(self, inquiry: Inquiry) -> Optional[Response]:
        """
        Generate response using hybrid approach (template + AI)

        Args:
            inquiry: Inquiry object

        Returns:
            Response object or None
        """
        from .ai_response_generator import AIResponseGenerator

        # Try template first
        response = self._generate_from_template(inquiry)

        if not response:
            # If template fails, use AI
            return self._generate_with_ai(inquiry)

        # If template confidence is low, enhance with AI
        if response.confidence_score < 70:
            logger.info("Template confidence low, enhancing with AI")

            try:
                category = inquiry.classified_category or "general"
                policy_info = self._load_policy(category)
                policy_text = json.dumps(policy_info, ensure_ascii=False) if policy_info else ""

                ai_generator = AIResponseGenerator()
                enhanced = ai_generator.enhance_template_response(
                    template_response=response.response_text,
                    inquiry=inquiry,
                    policy_context=policy_text
                )

                if enhanced:
                    response.response_text = enhanced
                    response.original_response = response.response_text
                    response.generation_method = "hybrid"
                    response.confidence_score = min(85, response.confidence_score + 15)
                    self.db.commit()

            except Exception as e:
                logger.error(f"Error enhancing with AI: {str(e)}")

        return response
