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

    def _generate_hmac(self, method: str, path: str, query: str = "", datetime_str: str = None) -> tuple:
        """
        Generate HMAC signature for Coupang API authentication

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            query: Query string
            datetime_str: Datetime in yyMMddTHHmmssZ format (optional)

        Returns:
            Tuple of (signature, datetime_str)
        """
        if datetime_str is None:
            # Generate datetime in yyMMddTHHmmssZ format (GMT/UTC)
            # Use datetime module for proper UTC time (works on both Windows and Linux)
            from datetime import timezone
            utc_now = datetime.now(timezone.utc)
            datetime_str = utc_now.strftime('%y%m%dT%H%M%SZ')

        message = f"{datetime_str}{method}{path}{query}"

        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature, datetime_str

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
        signature, timestamp = self._generate_hmac(method, path, query)

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
        answered_type: str = "NOANSWER",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Get online inquiries (상품별 고객문의 조회)

        Args:
            product_id: Filter by product ID
            status: Filter by status (WAITING, ANSWERED, etc.)
            answered_type: Answer status - 'ANSWERED', 'NOANSWER', or 'ALL' (required)
            start_date: Start date in yyyy-MM-dd format (defaults to 7 days ago)
            end_date: End date in yyyy-MM-dd format (defaults to today)
            max_per_page: Maximum results per page

        Returns:
            Inquiry data
        """
        # Set default date range (last 6 days) if not provided
        # API requires interval to be less than or equal to 7 days (so we use 6)
        # Use UTC time to match API server timezone
        if not start_date or not end_date:
            from datetime import timedelta, timezone
            today_utc = datetime.now(timezone.utc)
            end_date = end_date or today_utc.strftime('%Y-%m-%d')
            start_date = start_date or (today_utc - timedelta(days=6)).strftime('%Y-%m-%d')

        path = f"/v2/providers/openapi/apis/api/v5/vendors/{self.vendor_id}/onlineInquiries"

        query_params = []
        # vendorId is required
        query_params.append(f"vendorId={self.vendor_id}")
        # answeredType is required by Coupang API
        query_params.append(f"answeredType={answered_type}")
        # Date range is required (max 7 days) - correct parameter names
        query_params.append(f"inquiryStartAt={start_date}")
        query_params.append(f"inquiryEndAt={end_date}")
        # Pagination
        query_params.append(f"pageSize={max_per_page}")
        query_params.append(f"pageNum=1")

        query = "&".join(query_params) if query_params else ""

        logger.info(f"Fetching online inquiries: {query}")
        return self._make_request("GET", path, query)

    def get_call_center_inquiries(
        self,
        partner_counseling_status: str = "NO_ANSWER",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Get call center inquiries (쿠팡 고객센터 문의조회)

        Args:
            partner_counseling_status: Counseling status (required)
                - 'NONE': 전체
                - 'ANSWER': 답변완료
                - 'NO_ANSWER': 미답변 (판매자 답변 필요)
                - 'TRANSFER': 미확인 (쿠팡 상담완료, 판매자 확인 필요)
            start_date: Start date in yyyy-MM-dd format (defaults to 6 days ago)
            end_date: End date in yyyy-MM-dd format (defaults to today)
            max_per_page: Maximum results per page

        Returns:
            Inquiry data
        """
        # Set default date range (last 6 days) if not provided
        # API requires interval to be less than or equal to 7 days (so we use 6)
        # Use UTC time to match API server timezone
        if not start_date or not end_date:
            from datetime import timedelta, timezone
            today_utc = datetime.now(timezone.utc)
            end_date = end_date or today_utc.strftime('%Y-%m-%d')
            start_date = start_date or (today_utc - timedelta(days=6)).strftime('%Y-%m-%d')

        path = f"/v2/providers/openapi/apis/api/v5/vendors/{self.vendor_id}/callCenterInquiries"

        query_params = []
        # vendorId is required
        query_params.append(f"vendorId={self.vendor_id}")
        # partnerCounselingStatus is required by Coupang API
        # NONE=전체, ANSWER=답변완료, NO_ANSWER=미답변, TRANSFER=미확인
        query_params.append(f"partnerCounselingStatus={partner_counseling_status}")
        # Date range (max 7 days) - correct parameter names
        query_params.append(f"inquiryStartAt={start_date}")
        query_params.append(f"inquiryEndAt={end_date}")
        # Pagination
        query_params.append(f"pageSize={max_per_page}")
        query_params.append(f"pageNum=1")

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
