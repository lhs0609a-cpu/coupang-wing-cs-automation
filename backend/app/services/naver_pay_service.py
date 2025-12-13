"""
Naver Pay API Service
네이버 페이 API 서비스 (배송지 조회 등)
"""
import requests
from typing import Dict, Optional
from loguru import logger
from ..config import settings


class NaverPayService:
    """
    네이버 페이 API 서비스
    - 배송지 정보 조회
    """

    # API 엔드포인트
    PAY_ADDRESS_URL = "https://openapi.naver.com/v1/nid/payaddress"

    def __init__(self, access_token: Optional[str] = None):
        """
        초기화

        Args:
            access_token: 네이버 로그인 Access Token
        """
        self.access_token = access_token

    def get_pay_address(self, access_token: Optional[str] = None) -> Dict[str, any]:
        """
        네이버 페이 배송지 정보 조회

        Args:
            access_token: 네이버 로그인 Access Token (없으면 초기화 시 설정한 토큰 사용)

        Returns:
            Dict: 배송지 정보
            {
                "success": True,
                "data": {
                    "receiverName": "홍길동",
                    "zipCode": "16825",
                    "baseAddress": "경기도 성남시 불정로 7",
                    "detailAddress": "그린팩토리",
                    "roadNameYn": "Y",
                    "telNo": "010-0000-0000"
                }
            }
        """
        token = access_token or self.access_token

        if not token:
            logger.error("Access Token이 제공되지 않았습니다.")
            return {
                "success": False,
                "error": "no_token",
                "error_description": "Access Token이 필요합니다."
            }

        # 요청 헤더 설정
        headers = {
            "Authorization": f"Bearer {token}"
        }

        logger.info("네이버 페이 배송지 정보 조회 시작...")

        try:
            response = requests.get(
                self.PAY_ADDRESS_URL,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if result.get("result") == "success":
                data = result.get("data", {})
                logger.success("✅ 배송지 정보 조회 성공")
                logger.info(f"  수령인: {data.get('receiverName')}")
                logger.info(f"  주소: {data.get('baseAddress')} {data.get('detailAddress')}")
                logger.info(f"  우편번호: {data.get('zipCode')}")

                return {
                    "success": True,
                    "data": {
                        "receiverName": data.get("receiverName"),
                        "zipCode": data.get("zipCode"),
                        "baseAddress": data.get("baseAddress"),
                        "detailAddress": data.get("detailAddress"),
                        "roadNameYn": data.get("roadNameYn"),
                        "telNo": data.get("telNo")
                    }
                }
            else:
                logger.error(f"❌ 배송지 정보 조회 실패: {result}")
                return {
                    "success": False,
                    "error": "api_error",
                    "error_description": "배송지 정보를 가져올 수 없습니다."
                }

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_msg = ""

            if status_code == 401:
                error_msg = "인증 실패: Access Token이 유효하지 않습니다."
            elif status_code == 403:
                error_msg = "권한 없음: 사용자가 권한 제공에 동의하지 않았습니다."
            elif status_code == 404:
                error_msg = "배송지 정보를 찾을 수 없습니다."
            elif status_code == 500:
                error_msg = "서버 오류: 네이버 API 서버에 문제가 발생했습니다."
            else:
                error_msg = f"HTTP {status_code} 오류"

            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": f"http_{status_code}",
                "error_description": error_msg
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 배송지 정보 조회 요청 오류: {str(e)}")
            return {
                "success": False,
                "error": "request_failed",
                "error_description": str(e)
            }

    def format_address_for_return(
        self,
        address_data: Dict[str, str]
    ) -> str:
        """
        배송지 정보를 반품 신청용 주소 문자열로 포맷

        Args:
            address_data: 배송지 정보 딕셔너리

        Returns:
            str: 포맷된 주소 문자열
        """
        base_address = address_data.get("baseAddress", "")
        detail_address = address_data.get("detailAddress", "")
        zip_code = address_data.get("zipCode", "")

        if base_address:
            if detail_address:
                full_address = f"{base_address} {detail_address}"
            else:
                full_address = base_address

            if zip_code:
                full_address = f"[{zip_code}] {full_address}"

            return full_address
        else:
            return "주소 정보 없음"

    def get_receiver_info(
        self,
        address_data: Dict[str, str]
    ) -> Dict[str, str]:
        """
        수령인 정보 추출

        Args:
            address_data: 배송지 정보 딕셔너리

        Returns:
            Dict: 수령인 정보
        """
        return {
            "name": address_data.get("receiverName", ""),
            "phone": address_data.get("telNo", ""),
            "zipcode": address_data.get("zipCode", ""),
            "address": self.format_address_for_return(address_data)
        }
