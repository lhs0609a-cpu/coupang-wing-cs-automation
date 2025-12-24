"""
Coupang API Client
Handles all communication with Coupang Wing API
"""
import hmac
import hashlib
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from loguru import logger
from ..config import settings


class CoupangAPIClient:
    """
    Client for Coupang Wing API
    """

    def __init__(
        self,
        access_key: str = None,
        secret_key: str = None,
        vendor_id: str = None
    ):
        self.access_key = access_key or settings.COUPANG_ACCESS_KEY
        self.secret_key = secret_key or settings.COUPANG_SECRET_KEY
        self.vendor_id = vendor_id or settings.COUPANG_VENDOR_ID
        self.base_url = settings.COUPANG_API_BASE_URL
        self.client = httpx.Client(timeout=30.0)

    def _generate_hmac(self, method: str, path: str, query: str = "") -> str:
        """
        Generate HMAC signature for Coupang API authentication

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            query: Query string

        Returns:
            HMAC signature
        """
        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}{method}{path}{query}"

        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _get_headers(self, method: str, path: str, query: str = "") -> Dict[str, str]:
        """
        Generate headers for API request

        Args:
            method: HTTP method
            path: API path
            query: Query string

        Returns:
            Headers dictionary
        """
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_hmac(method, path, query)

        return {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={timestamp}, signature={signature}",
            "X-EXTENDED-TIMEOUT": "30000"
        }

    def _make_request(
        self,
        method: str,
        path: str,
        query: str = "",
        data: Optional[Dict] = None,
        retry: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Coupang API with retry logic

        Args:
            method: HTTP method
            path: API path
            query: Query string
            data: Request body data
            retry: Current retry count

        Returns:
            Response data

        Raises:
            Exception: If request fails after all retries
        """
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{query}"

        headers = self._get_headers(method, path, query)

        try:
            if method == "GET":
                response = self.client.get(url, headers=headers)
            elif method == "POST":
                response = self.client.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = self.client.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            if response.text:
                return response.json()
            return {"code": "200", "message": "OK"}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")

            # Retry logic
            if retry < settings.MAX_RETRIES:
                logger.info(f"Retrying... (attempt {retry + 1}/{settings.MAX_RETRIES})")
                time.sleep(settings.RETRY_DELAY)
                return self._make_request(method, path, query, data, retry + 1)

            raise Exception(f"API request failed: {e.response.text}")

        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            raise

    # ========== Inquiry APIs ==========

    def get_online_inquiries(
        self,
        product_id: Optional[str] = None,
        status: Optional[str] = None,
        max_per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Get online inquiries (상품별 고객문의 조회)

        Args:
            product_id: Filter by product ID
            status: Filter by status (WAITING, ANSWERED, etc.)
            max_per_page: Maximum results per page

        Returns:
            Inquiry data
        """
        path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/onlineInquiries"

        query_params = []
        if product_id:
            query_params.append(f"productId={product_id}")
        if status:
            query_params.append(f"status={status}")
        query_params.append(f"maxPerPage={max_per_page}")

        query = "&".join(query_params) if query_params else ""

        logger.info(f"Fetching online inquiries: {query}")
        return self._make_request("GET", path, query)

    def get_call_center_inquiries(
        self,
        inquiry_status: Optional[str] = None,
        partner_transfer_status: Optional[str] = None,
        max_per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Get call center inquiries (쿠팡 고객센터 문의조회)

        Args:
            inquiry_status: Inquiry status (PROGRESS, COMPLETE, etc.)
            partner_transfer_status: Transfer status (TRANSFER, etc.)
            max_per_page: Maximum results per page

        Returns:
            Inquiry data
        """
        path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/callCenterInquiries"

        query_params = []
        if inquiry_status:
            query_params.append(f"inquiryStatus={inquiry_status}")
        if partner_transfer_status:
            query_params.append(f"partnerTransferStatus={partner_transfer_status}")
        query_params.append(f"maxPerPage={max_per_page}")

        query = "&".join(query_params)

        logger.info(f"Fetching call center inquiries: {query}")
        return self._make_request("GET", path, query)

    def get_inquiry_detail(self, inquiry_id: str, inquiry_type: str = "online") -> Dict[str, Any]:
        """
        Get detailed information about a specific inquiry

        Args:
            inquiry_id: Inquiry ID
            inquiry_type: Type of inquiry ('online' or 'callcenter')

        Returns:
            Inquiry details
        """
        if inquiry_type == "online":
            path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/onlineInquiries/{inquiry_id}"
        else:
            path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/callCenterInquiries/{inquiry_id}"

        logger.info(f"Fetching inquiry detail: {inquiry_id}")
        return self._make_request("GET", path)

    # ========== Response APIs ==========

    def submit_online_inquiry_reply(
        self,
        inquiry_id: str,
        content: str,
        reply_by: str = None
    ) -> Dict[str, Any]:
        """
        Submit reply to online inquiry (상품문의 답변등록)

        Args:
            inquiry_id: Inquiry ID to reply to
            content: Reply content (use \\n for line breaks)
            reply_by: Responder's Wing ID

        Returns:
            Response data

        Raises:
            Exception: If submission fails
        """
        reply_by = reply_by or settings.COUPANG_WING_ID

        path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/onlineInquiries/{inquiry_id}/replies"

        data = {
            "content": content,
            "vendorId": self.vendor_id,
            "replyBy": reply_by
        }

        logger.info(f"Submitting reply for inquiry {inquiry_id}")
        logger.debug(f"Reply content: {content[:100]}...")

        try:
            result = self._make_request("POST", path, data=data)
            logger.success(f"Reply submitted successfully for inquiry {inquiry_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to submit reply: {str(e)}")
            raise

    def confirm_call_center_inquiry(
        self,
        inquiry_id: str,
        confirm_by: str = None
    ) -> Dict[str, Any]:
        """
        Confirm call center inquiry (쿠팡 고객센터 문의확인)

        Args:
            inquiry_id: Inquiry ID to confirm
            confirm_by: Confirmer's Wing ID

        Returns:
            Response data
        """
        confirm_by = confirm_by or settings.COUPANG_WING_ID

        path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/callCenterInquiries/{inquiry_id}/confirms"

        data = {
            "confirmBy": confirm_by
        }

        logger.info(f"Confirming call center inquiry {inquiry_id}")

        try:
            result = self._make_request("POST", path, data=data)
            logger.success(f"Inquiry confirmed successfully: {inquiry_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to confirm inquiry: {str(e)}")
            raise

    # ========== Validation Methods ==========

    def validate_response_content(self, content: str) -> Dict[str, Any]:
        """
        Validate response content before submission

        Args:
            content: Response content to validate

        Returns:
            Validation result with issues if any
        """
        issues = []

        # Check if content is empty
        if not content or not content.strip():
            issues.append("Content is empty")

        # Check length
        if len(content) > settings.MAX_RESPONSE_LENGTH:
            issues.append(f"Content exceeds maximum length ({settings.MAX_RESPONSE_LENGTH})")

        # Check for proper JSON escaping
        try:
            json.dumps({"content": content})
        except Exception as e:
            issues.append(f"Content contains invalid characters for JSON: {str(e)}")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def check_duplicate_reply(self, inquiry_id: str) -> bool:
        """
        Check if inquiry already has a reply

        Args:
            inquiry_id: Inquiry ID to check

        Returns:
            True if reply already exists
        """
        try:
            detail = self.get_inquiry_detail(inquiry_id)
            # Check if response/reply exists in the detail
            return "reply" in detail or "response" in detail
        except:
            return False

    def __del__(self):
        """Cleanup HTTP client"""
        self.client.close()
