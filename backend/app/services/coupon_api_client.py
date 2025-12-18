"""
Coupang Coupon API Client
쿠폰 관련 API 클라이언트
"""
import hmac
import hashlib
import datetime
import requests
from typing import Optional, Dict, Any, List
from loguru import logger


class CouponAPIClient:
    """쿠팡 쿠폰 API 클라이언트"""

    BASE_URL = "https://api-gateway.coupang.com"

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        vendor_id: str,
        wing_username: Optional[str] = None
    ):
        """
        Initialize Coupon API Client

        Args:
            access_key: Coupang Access Key
            secret_key: Coupang Secret Key
            vendor_id: Vendor ID (예: A00012345)
            wing_username: Wing 로그인 ID (다운로드쿠폰 생성에 필요)
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.vendor_id = vendor_id
        self.wing_username = wing_username

    def _generate_hmac(self, method: str, path: str, query: str = "") -> tuple:
        """Generate HMAC signature for Coupang API"""
        now = datetime.datetime.utcnow()
        datetime_str = now.strftime('%y%m%d') + 'T' + now.strftime('%H%M%S') + 'Z'

        message = datetime_str + method + path + query

        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature, datetime_str

    def _get_headers(self, method: str, path: str, query: str = "") -> Dict[str, str]:
        """Get headers with HMAC authentication"""
        signature, datetime_str = self._generate_hmac(method, path, query)

        return {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={datetime_str}, signature={signature}"
        }

    # ==================== 계약서 API ====================

    def get_contract_list(self) -> Dict[str, Any]:
        """
        계약서 목록 조회

        Returns:
            계약서 목록
        """
        path = f"/v2/providers/fms/apis/api/v2/vendors/{self.vendor_id}/contract/list"
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("GET", path)

        logger.info(f"Fetching contract list for vendor {self.vendor_id}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching contract list: {str(e)}")
            raise

    # ==================== 즉시할인쿠폰 API ====================

    def get_instant_coupons(
        self,
        status: str = "APPLIED",
        page: int = 1,
        size: int = 100,
        sort: str = "desc"
    ) -> Dict[str, Any]:
        """
        즉시할인쿠폰 목록 조회

        Args:
            status: 쿠폰 상태 (STANDBY, APPLIED, PAUSED, EXPIRED, DETACHED)
            page: 페이지 번호
            size: 페이지당 건수
            sort: 정렬 (asc, desc)

        Returns:
            쿠폰 목록
        """
        path = f"/v2/providers/fms/apis/api/v2/vendors/{self.vendor_id}/coupons"
        query = f"status={status}&page={page}&size={size}&sort={sort}"
        url = f"{self.BASE_URL}{path}?{query}"
        headers = self._get_headers("GET", path, query)

        logger.info(f"Fetching instant coupons: status={status}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching instant coupons: {str(e)}")
            raise

    def get_instant_coupon(self, coupon_id: int) -> Dict[str, Any]:
        """
        즉시할인쿠폰 단건 조회

        Args:
            coupon_id: 쿠폰 ID

        Returns:
            쿠폰 상세 정보
        """
        path = f"/v2/providers/fms/apis/api/v2/vendors/{self.vendor_id}/coupon"
        query = f"couponId={coupon_id}"
        url = f"{self.BASE_URL}{path}?{query}"
        headers = self._get_headers("GET", path, query)

        logger.info(f"Fetching instant coupon: {coupon_id}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching instant coupon {coupon_id}: {str(e)}")
            raise

    def apply_instant_coupon_to_items(
        self,
        coupon_id: int,
        vendor_item_ids: List[int]
    ) -> Dict[str, Any]:
        """
        즉시할인쿠폰 아이템 생성 (상품에 쿠폰 적용)

        Args:
            coupon_id: 쿠폰 ID
            vendor_item_ids: 옵션 ID 목록 (최대 10,000개)

        Returns:
            요청 결과 (requestedId 포함)
        """
        path = f"/v2/providers/fms/apis/api/v1/vendors/{self.vendor_id}/coupons/{coupon_id}/items"
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("POST", path)

        payload = {
            "vendorItems": vendor_item_ids
        }

        logger.info(f"Applying instant coupon {coupon_id} to {len(vendor_item_ids)} items")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error applying instant coupon: {str(e)}")
            raise

    def get_instant_coupon_request_status(self, requested_id: str) -> Dict[str, Any]:
        """
        즉시할인쿠폰 요청상태 확인

        Args:
            requested_id: 요청 ID

        Returns:
            처리 상태 (REQUESTED, DONE, FAIL)
        """
        path = f"/v2/providers/fms/apis/api/v1/vendors/{self.vendor_id}/requested/{requested_id}"
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("GET", path)

        logger.info(f"Checking instant coupon request status: {requested_id}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking request status: {str(e)}")
            raise

    # ==================== 다운로드쿠폰 API ====================

    def get_download_coupons(
        self,
        status: str = "IN_PROGRESS",
        page: int = 0,
        size: int = 100
    ) -> Dict[str, Any]:
        """
        다운로드쿠폰 목록 조회

        Args:
            status: 쿠폰 상태 (READY, IN_PROGRESS, PAUSED, FINISHED)
            page: 페이지 번호 (0부터 시작)
            size: 페이지당 건수

        Returns:
            쿠폰 목록
        """
        path = f"/v2/providers/marketplace_openapi/apis/api/v1/coupons"
        query = f"status={status}&page={page}&size={size}"
        url = f"{self.BASE_URL}{path}?{query}"
        headers = self._get_headers("GET", path, query)

        logger.info(f"Fetching download coupons: status={status}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            # 400 에러 등 API 미지원 시 빈 배열 반환
            if response.status_code == 400:
                logger.warning(f"Download coupons API returned 400 - API may not be supported")
                return {"code": "NOT_SUPPORTED", "message": "API 미지원", "content": []}
            if response.status_code == 403:
                logger.warning(f"Download coupons API returned 403 - Access denied")
                return {"code": "FORBIDDEN", "message": "접근 권한 없음", "content": []}
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching download coupons: {str(e)}")
            # 예외 발생 시에도 빈 배열 반환 (프론트엔드 에러 방지)
            return {"code": "ERROR", "message": str(e), "content": []}

    def get_download_coupon(self, coupon_id: int) -> Dict[str, Any]:
        """
        다운로드쿠폰 단건 조회

        Args:
            coupon_id: 쿠폰 ID

        Returns:
            쿠폰 상세 정보
        """
        path = f"/v2/providers/marketplace_openapi/apis/api/v1/coupons/{coupon_id}"
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("GET", path)

        logger.info(f"Fetching download coupon: {coupon_id}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            # 400/404 에러 시 None 반환
            if response.status_code in [400, 404]:
                logger.warning(f"Download coupon {coupon_id} not found or API error")
                return {"code": "NOT_FOUND", "message": f"쿠폰 {coupon_id}을(를) 찾을 수 없습니다"}
            if response.status_code == 403:
                logger.warning(f"Download coupon API returned 403 - Access denied")
                return {"code": "FORBIDDEN", "message": "접근 권한 없음"}
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching download coupon {coupon_id}: {str(e)}")
            return {"code": "ERROR", "message": str(e)}

    def apply_download_coupon_to_items(
        self,
        coupon_id: int,
        vendor_item_ids: List[int],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        다운로드쿠폰 아이템 생성 (상품에 쿠폰 적용)

        Args:
            coupon_id: 쿠폰 ID
            vendor_item_ids: 옵션 ID 목록 (최대 100개)
            user_id: WING 로그인 ID

        Returns:
            요청 결과

        Note:
            상품 추가에 실패하면 해당 쿠폰은 파기됩니다!
        """
        # userId 필수 확인
        effective_user_id = user_id or self.wing_username
        if not effective_user_id:
            logger.error("userId is required for download coupon application")
            return {
                "requestResultStatus": "FAILED",
                "errorMessage": "WING 로그인 ID(userId)가 필요합니다. 쿠팡 계정 설정에서 wing_username을 입력해주세요."
            }

        path = "/v2/providers/marketplace_openapi/apis/api/v1/coupon-items"
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("PUT", path)

        # vendorItemIds는 정수 배열이어야 함
        int_vendor_item_ids = [int(vid) for vid in vendor_item_ids]

        payload = {
            "couponItems": [
                {
                    "couponId": int(coupon_id),  # 정수로 전송
                    "userId": effective_user_id,
                    "vendorItemIds": int_vendor_item_ids
                }
            ]
        }

        logger.info(f"Applying download coupon {coupon_id} to {len(vendor_item_ids)} items, userId={effective_user_id}")
        logger.info(f"Download coupon payload: {payload}")

        try:
            response = requests.put(url, headers=headers, json=payload, timeout=60)

            # 응답 로깅
            logger.info(f"Download coupon response status: {response.status_code}")
            logger.info(f"Download coupon response body: {response.text[:1000] if response.text else 'empty'}")

            # 응답 파싱 (에러든 성공이든 일단 파싱)
            try:
                result = response.json() if response.text else {}
            except:
                result = {"raw": response.text}

            # 배열 응답 처리 (쿠팡 API는 배열로 응답)
            if isinstance(result, list) and len(result) > 0:
                result = result[0]  # 첫 번째 요소 사용

            # 에러 응답 처리
            if response.status_code >= 400:
                error_msg = (
                    result.get("errorMessage") or
                    result.get("message") or
                    result.get("raw") or
                    f"HTTP {response.status_code} 에러"
                )
                error_code = result.get("errorCode", "UNKNOWN")

                logger.error(f"Download coupon error: status={response.status_code}, code={error_code}, message={error_msg}")

                # 구체적인 에러 메시지 매핑
                if "deleted" in error_msg.lower():
                    error_msg = f"쿠폰이 삭제되었습니다. 새 쿠폰을 생성해주세요. (원본: {error_msg})"
                elif "not started" in error_msg.lower() or "시작" in error_msg:
                    error_msg = f"쿠폰이 아직 시작되지 않았습니다. 시작일을 확인해주세요. (원본: {error_msg})"
                elif response.status_code == 403:
                    error_msg = "접근 권한이 없습니다. API 키를 확인해주세요."
                elif response.status_code == 404:
                    error_msg = f"쿠폰 ID {coupon_id}를 찾을 수 없습니다."

                return {
                    "requestResultStatus": "FAILED",
                    "errorCode": error_code,
                    "errorMessage": error_msg
                }

            # 성공 응답 처리
            request_status = result.get("requestResultStatus", "UNKNOWN")
            if request_status == "SUCCESS":
                logger.info(f"Download coupon applied successfully")
                return {
                    "requestResultStatus": "SUCCESS",
                    "body": result.get("body")
                }
            elif request_status == "FAIL":
                error_msg = result.get("errorMessage", "알 수 없는 오류")
                logger.error(f"Download coupon application failed: {error_msg}")
                return {
                    "requestResultStatus": "FAILED",
                    "errorCode": result.get("errorCode", "UNKNOWN"),
                    "errorMessage": error_msg
                }
            else:
                # UNKNOWN 상태 - 응답 그대로 반환
                logger.warning(f"Download coupon unknown response: {result}")
                return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error applying download coupon: {str(e)}", exc_info=True)
            return {
                "requestResultStatus": "FAILED",
                "errorMessage": f"네트워크 오류: {str(e)}"
            }

    def get_download_coupon_request_status(self, request_transaction_id: str) -> Dict[str, Any]:
        """
        다운로드쿠폰 요청상태 확인

        Args:
            request_transaction_id: 요청 트랜잭션 ID

        Returns:
            처리 상태
        """
        path = "/v2/providers/marketplace_openapi/apis/api/v1/coupons/transactionStatus"
        query = f"requestTransactionId={request_transaction_id}"
        url = f"{self.BASE_URL}{path}?{query}"
        headers = self._get_headers("GET", path, query)

        logger.info(f"Checking download coupon request status: {request_transaction_id}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking request status: {str(e)}")
            raise

    # ==================== 상품 API ====================

    def get_products_by_date(
        self,
        created_at: str,
        status: str = "APPROVED",
        max_per_page: int = 100,
        next_token: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        상품 목록 페이징 조회 (특정 날짜 등록 상품)

        Args:
            created_at: 상품등록일 (yyyy-MM-dd)
            status: 상품 상태 (APPROVED 권장)
            max_per_page: 페이지당 건수 (최대 100)
            next_token: 다음 페이지 토큰

        Returns:
            상품 목록
        """
        path = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"

        params = [
            f"vendorId={self.vendor_id}",
            f"status={status}",
            f"createdAt={created_at}",
            f"maxPerPage={max_per_page}"
        ]
        if next_token:
            params.append(f"nextToken={next_token}")

        query = "&".join(params)
        url = f"{self.BASE_URL}{path}?{query}"
        headers = self._get_headers("GET", path, query)

        logger.info(f"Fetching products: createdAt={created_at}, status={status}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching products: {str(e)}")
            raise

    def get_product_detail(self, seller_product_id: int) -> Dict[str, Any]:
        """
        상품 상세 조회 (vendorItemId 확인용)

        Args:
            seller_product_id: 등록상품 ID

        Returns:
            상품 상세 정보 (vendorItemId 포함)
        """
        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{seller_product_id}"
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("GET", path)

        logger.info(f"Fetching product detail: {seller_product_id}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching product detail: {str(e)}")
            raise

    def get_all_products_by_date(
        self,
        created_at: str,
        status: str = "APPROVED"
    ) -> List[Dict[str, Any]]:
        """
        특정 날짜에 등록된 모든 상품 조회 (페이징 자동 처리)

        Args:
            created_at: 상품등록일 (yyyy-MM-dd)
            status: 상품 상태

        Returns:
            전체 상품 목록
        """
        all_products = []
        next_token = None

        while True:
            result = self.get_products_by_date(
                created_at=created_at,
                status=status,
                max_per_page=100,
                next_token=next_token
            )

            if result.get("code") == "SUCCESS":
                products = result.get("data", [])
                all_products.extend(products)

                next_token_str = result.get("nextToken", "")
                if next_token_str and next_token_str.strip():
                    next_token = int(next_token_str)
                else:
                    break
            else:
                logger.error(f"Failed to fetch products: {result.get('message')}")
                break

        logger.info(f"Total products fetched for {created_at}: {len(all_products)}")
        return all_products

    def get_vendor_item_ids(self, seller_product_id: int) -> List[int]:
        """
        상품의 vendorItemId 목록 조회

        Args:
            seller_product_id: 등록상품 ID

        Returns:
            vendorItemId 목록
        """
        result = self.get_product_detail(seller_product_id)

        vendor_item_ids = []
        if result.get("code") == "SUCCESS":
            items = result.get("data", {}).get("items", [])
            for item in items:
                vendor_item_id = item.get("vendorItemId")
                if vendor_item_id:
                    vendor_item_ids.append(vendor_item_id)

        return vendor_item_ids

    def get_all_products(
        self,
        status: str = "APPROVED",
        max_per_page: int = 100,
        next_token: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        전체 상품 목록 조회 (날짜 필터 없음)

        Args:
            status: 상품 상태 (APPROVED 권장)
            max_per_page: 페이지당 건수 (최대 100)
            next_token: 다음 페이지 토큰

        Returns:
            상품 목록
        """
        path = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"

        params = [
            f"vendorId={self.vendor_id}",
            f"status={status}",
            f"maxPerPage={max_per_page}"
        ]
        if next_token:
            params.append(f"nextToken={next_token}")

        query = "&".join(params)
        url = f"{self.BASE_URL}{path}?{query}"
        headers = self._get_headers("GET", path, query)

        logger.info(f"Fetching all products: status={status}, nextToken={next_token}")

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching products: {str(e)}")
            raise

    def get_all_approved_products(self) -> List[Dict[str, Any]]:
        """
        승인된 모든 상품 조회 (페이징 자동 처리)

        Returns:
            전체 승인 상품 목록
        """
        all_products = []
        next_token = None
        page_count = 0
        max_pages = 100  # 안전장치: 최대 100페이지 (10,000개)

        logger.info(f"[DEBUG] Starting to fetch all approved products for vendor {self.vendor_id}")

        while page_count < max_pages:
            page_count += 1
            logger.info(f"[DEBUG] Fetching page {page_count}, next_token={next_token}")

            try:
                result = self.get_all_products(
                    status="APPROVED",
                    max_per_page=100,
                    next_token=next_token
                )

                logger.info(f"[DEBUG] Page {page_count} response code: {result.get('code')}")

                if result.get("code") == "SUCCESS":
                    products = result.get("data", [])
                    logger.info(f"[DEBUG] Page {page_count}: received {len(products)} products")
                    all_products.extend(products)

                    next_token_str = result.get("nextToken", "")
                    logger.info(f"[DEBUG] Page {page_count}: nextToken = '{next_token_str}'")

                    if next_token_str and next_token_str.strip():
                        next_token = int(next_token_str)
                    else:
                        logger.info(f"[DEBUG] No more pages, stopping pagination")
                        break
                else:
                    logger.error(f"[DEBUG] Failed to fetch products on page {page_count}: code={result.get('code')}, message={result.get('message')}")
                    logger.error(f"[DEBUG] Full response: {result}")
                    break

            except Exception as e:
                logger.error(f"[DEBUG] Exception on page {page_count}: {str(e)}")
                break

        logger.info(f"[DEBUG] Total approved products fetched: {len(all_products)} from {page_count} pages")
        return all_products
