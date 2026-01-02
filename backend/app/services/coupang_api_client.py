"""
Coupang Open API Client with HMAC Authentication
"""
import hmac
import hashlib
import datetime
import requests
from typing import Optional, Dict, Any
from loguru import logger
from ..config import settings


class CoupangAPIClient:
    """Coupang Open API 클라이언트"""

    BASE_URL = "https://api-gateway.coupang.com"

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        vendor_id: Optional[str] = None
    ):
        """
        Initialize Coupang API Client

        Args:
            access_key: Coupang Access Key (A00492891)
            secret_key: Coupang Secret Key
            vendor_id: Vendor ID (A00492891)
        """
        self.access_key = access_key or settings.COUPANG_ACCESS_KEY
        self.secret_key = secret_key or settings.COUPANG_SECRET_KEY
        self.vendor_id = vendor_id or settings.COUPANG_VENDOR_ID

        if not all([self.access_key, self.secret_key, self.vendor_id]):
            raise ValueError(
                "Missing Coupang API credentials. Please set "
                "COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY, and COUPANG_VENDOR_ID"
            )

    def _generate_hmac(self, method: str, path: str, query: str = "", datetime_str: str = None) -> tuple:
        """
        Generate HMAC signature for Coupang API

        Coupang uses HMAC SHA256 authentication:
        HMAC(secretKey, datetime + method + path + query)

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            query: Query string (optional)
            datetime_str: Pre-formatted datetime string (optional)

        Returns:
            Tuple of (signature, datetime_str)
        """
        # Get current datetime in Coupang format (2-digit year) - capture once!
        if datetime_str is None:
            now = datetime.datetime.utcnow()
            datetime_str = now.strftime('%y%m%d') + 'T' + now.strftime('%H%M%S') + 'Z'

        # Create message to sign
        message = datetime_str + method + path + query

        # Generate HMAC
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Debug logging
        logger.debug(f"HMAC Debug - DateTime: {datetime_str}")
        logger.debug(f"HMAC Debug - Method: {method}")
        logger.debug(f"HMAC Debug - Path: {path}")
        logger.debug(f"HMAC Debug - Query: {query}")
        logger.debug(f"HMAC Debug - Message: {message}")
        logger.debug(f"HMAC Debug - Access Key: {self.access_key}")
        logger.debug(f"HMAC Debug - Signature: {signature}")

        return signature, datetime_str

    def _get_headers(self, method: str, path: str, query: str = "") -> Dict[str, str]:
        """
        Get headers with HMAC authentication

        Args:
            method: HTTP method
            path: API path
            query: Query string

        Returns:
            Headers dict
        """
        signature, datetime_str = self._generate_hmac(method, path, query)

        return {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={datetime_str}, signature={signature}"
        }

    def get_online_inquiries(
        self,
        start_date: str,
        end_date: str,
        answered_type: str = "NOANSWER",
        page_num: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        상품별 고객문의 조회

        Args:
            start_date: 조회시작일 (yyyy-MM-dd)
            end_date: 조회종료일 (yyyy-MM-dd)
            answered_type: 답변상태 (ALL, ANSWERED, NOANSWER)
            page_num: 페이지 번호 (기본 1)
            page_size: 페이지 크기 (기본 50, 최대 50)

        Returns:
            API response
        """
        path = f"/v2/providers/openapi/apis/api/v5/vendors/{self.vendor_id}/onlineInquiries"
        query = f"inquiryStartAt={start_date}&inquiryEndAt={end_date}&vendorId={self.vendor_id}&answeredType={answered_type}&pageSize={page_size}&pageNum={page_num}"

        url = f"{self.BASE_URL}{path}?{query}"
        # HMAC 생성 시 query string은 ? 없이 전달
        headers = self._get_headers("GET", path, query)

        logger.info(f"Fetching online inquiries: {start_date} ~ {end_date}, type={answered_type}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching online inquiries: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def reply_to_online_inquiry(
        self,
        inquiry_id: int,
        content: str,
        reply_by: str
    ) -> Dict[str, Any]:
        """
        상품별 고객문의 답변

        Args:
            inquiry_id: 문의 ID
            content: 답변 내용 (줄바꿈은 \\n 사용)
            reply_by: 응답자 Wing ID (lhs0609)

        Returns:
            API response
        """
        path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/onlineInquiries/{inquiry_id}/replies"

        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("POST", path)

        payload = {
            "content": content,
            "vendorId": self.vendor_id,
            "replyBy": reply_by
        }

        logger.info(f"Replying to inquiry {inquiry_id}")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error replying to inquiry {inquiry_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_call_center_inquiries(
        self,
        start_date: str,
        end_date: str,
        status: str = "NO_ANSWER",
        page_num: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        쿠팡 고객센터 문의 조회

        Args:
            start_date: 조회시작일 (yyyy-MM-dd)
            end_date: 조회종료일 (yyyy-MM-dd)
            status: 문의 상태 (partnerCounselingStatus: 'NONE', 'NO_ANSWER', 'ANSWER', 'TRANSFER')
                   NO_ANSWER = 미답변 (판매자의 답변이 필요한 상태)
                   TRANSFER = 미확인 (판매자의 확인이 필요한 상태)
                   ANSWER = 답변완료
                   NONE = 전체
            page_num: 페이지 번호
            page_size: 페이지 크기

        Returns:
            API response
        """
        path = f"/v2/providers/openapi/apis/api/v5/vendors/{self.vendor_id}/callCenterInquiries"

        # Build query parameters
        params = [
            f"inquiryStartAt={start_date}",
            f"inquiryEndAt={end_date}",
            f"vendorId={self.vendor_id}",
            f"partnerCounselingStatus={status}",
            f"pageSize={page_size}",
            f"pageNum={page_num}"
        ]

        query = "&".join(params)
        url = f"{self.BASE_URL}{path}?{query}"
        headers = self._get_headers("GET", path, query)

        logger.info(f"Fetching call center inquiries: {start_date} ~ {end_date}, partnerCounselingStatus={status}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching call center inquiries: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def reply_to_call_center_inquiry(
        self,
        inquiry_id: str,
        content: str,
        reply_by: str,
        parent_answer_id: int
    ) -> Dict[str, Any]:
        """
        쿠팡 고객센터 문의 답변

        Args:
            inquiry_id: 문의 ID
            content: 답변 내용 (2~1000자, 줄바꿈은 \\n)
            reply_by: 응답자 Wing ID
            parent_answer_id: 부모 이관글 ID

        Returns:
            API response
        """
        path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/callCenterInquiries/{inquiry_id}/replies"

        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("POST", path)

        payload = {
            "vendorId": self.vendor_id,
            "inquiryId": inquiry_id,
            "content": content,
            "replyBy": reply_by,
            "parentAnswerId": parent_answer_id
        }

        logger.info(f"Replying to call center inquiry {inquiry_id}, reply_by={reply_by}")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error replying to call center inquiry {inquiry_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def confirm_call_center_inquiry(
        self,
        inquiry_id: str,
        confirm_by: str
    ) -> Dict[str, Any]:
        """
        쿠팡 고객센터 문의 확인

        Args:
            inquiry_id: 문의 ID
            confirm_by: 확인자 Wing ID

        Returns:
            API response
        """
        path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/callCenterInquiries/{inquiry_id}/confirms"

        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("POST", path)

        payload = {
            "confirmBy": confirm_by
        }

        logger.info(f"Confirming call center inquiry {inquiry_id}")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error confirming call center inquiry {inquiry_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_return_requests(
        self,
        start_date: str,
        end_date: str,
        status: Optional[str] = None,
        cancel_type: Optional[str] = None,
        search_type: str = "timeFrame",
        order_id: Optional[int] = None,
        max_per_page: int = 50
    ) -> Dict[str, Any]:
        """
        반품/취소 요청 목록 조회

        Args:
            start_date: 검색 시작일 (yyyy-MM-dd or yyyy-MM-ddTHH:mm for timeFrame)
            end_date: 검색 종료일 (yyyy-MM-dd or yyyy-MM-ddTHH:mm for timeFrame)
            status: 반품상태 (RU: 출고중지요청, UC: 반품접수, CC: 반품완료, PR: 쿠팡확인요청)
                   cancelType=CANCEL일 경우 사용 불가
            cancel_type: RETURN(반품), CANCEL(취소), 또는 None(전체 조회)
            search_type: 조회 방식 (timeFrame: 분단위, default)
            order_id: 주문번호 (status 없이 조회 시 필수)
            max_per_page: 페이지당 최대 조회 수 (기본 50)

        Returns:
            API response with return/cancel requests
        """
        path = f"/v2/providers/openapi/apis/api/v6/vendors/{self.vendor_id}/returnRequests"

        # Build query parameters
        params = [
            f"searchType={search_type}",
            f"createdAtFrom={start_date}",
            f"createdAtTo={end_date}"
        ]

        # cancelType은 선택적으로 추가 (None이면 전체 조회)
        if cancel_type:
            params.append(f"cancelType={cancel_type}")

        # status는 cancelType=CANCEL일 때 제외
        if status and cancel_type != "CANCEL":
            params.append(f"status={status}")

        # orderId는 status가 없을 때 필수
        if order_id:
            params.append(f"orderId={order_id}")

        # maxPerPage (timeFrame일 때는 지원 안 함)
        if search_type != "timeFrame":
            params.append(f"maxPerPage={max_per_page}")

        query = "&".join(params)
        url = f"{self.BASE_URL}{path}?{query}"
        headers = self._get_headers("GET", path, query)

        logger.info(f"Fetching return requests: {start_date} ~ {end_date}, status={status}, cancelType={cancel_type}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching return requests: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_return_request_by_receipt_id(self, receipt_id: int) -> Dict[str, Any]:
        """
        반품요청 단건 조회

        Args:
            receipt_id: 취소(반품) 접수번호

        Returns:
            API response with single return request detail

        Raises:
            HTTPException: 400 - receiptId가 vendorId에 속하지 않거나 찾을 수 없는 경우
                          (고객에 의해 철회된 경우 포함)
        """
        path = f"/v2/providers/openapi/apis/api/v6/vendors/{self.vendor_id}/returnRequests/{receipt_id}"

        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("GET", path)

        logger.info(f"Fetching return request by receipt ID: {receipt_id}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching return request {receipt_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def confirm_return_receive(self, receipt_id: int) -> Dict[str, Any]:
        """
        반품상품 입고 확인처리

        receiptStatus가 RETURNS_UNCHECKED (반품접수) 상태인 반품 건에 대해 처리합니다.
        - 빠른환불 미대상 상품: 입고 확인 필요
        - 빠른환불 대상 상품: 송장 트래킹 불가능한 경우에만 필요

        처리 후:
        - 빠른환불 대상: 바로 환불 및 반품 승인/완료 처리
        - 빠른환불 미대상: 추가로 '반품 요청 승인 처리' 필요

        Args:
            receipt_id: 취소(반품) 접수번호

        Returns:
            API response

        Note:
            빠른환불 대상 상품: 일반 배송이면서 상품 가격이 10만원 미만
            (신선식품, 주문제작 상품 등은 제외)
        """
        path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/returnRequests/{receipt_id}/receiveConfirmation"

        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("PUT", path)

        payload = {
            "vendorId": self.vendor_id,
            "receiptId": receipt_id
        }

        logger.info(f"Confirming return receive for receipt ID: {receipt_id}")

        try:
            response = requests.put(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error confirming return receive {receipt_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def approve_return_request(self, receipt_id: int, cancel_count: int) -> Dict[str, Any]:
        """
        반품요청 승인 처리

        receiptStatus가 VENDOR_WAREHOUSE_CONFIRM (입고완료) 상태인 반품 건에 대해 처리합니다.
        [반품 상품 입고 확인 처리] 후, [반품 요청 승인 처리]를 진행하면 환불 처리됩니다.

        Note:
            - 선환불(빠른환불) 정책에 의해 환불처리된 경우: API 호출 불필요
            - 입고확인 완료 후 일정 시간 경과 시: 쿠팡 시스템이 자동 승인 (API 호출 불필요)

        Args:
            receipt_id: 취소(반품) 접수번호
            cancel_count: 반품접수 수량 (반품 목록 조회에서 확인한 수량과 일치해야 함)

        Returns:
            API response

        Raises:
            400: 취소반품접수내역이 존재하지 않음 (철회된 경우)
            400: 이미 반품이 완료됨
            400: 취소반품접수수량과 cancelCount가 일치하지 않음
            500: 환불 승인 불가능한 상태
        """
        path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/returnRequests/{receipt_id}/approval"

        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("PUT", path)

        payload = {
            "vendorId": self.vendor_id,
            "receiptId": receipt_id,
            "cancelCount": cancel_count
        }

        logger.info(f"Approving return request for receipt ID: {receipt_id}, cancel count: {cancel_count}")

        try:
            response = requests.put(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error approving return request {receipt_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
