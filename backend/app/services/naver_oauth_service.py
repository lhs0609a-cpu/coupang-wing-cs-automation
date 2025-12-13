"""
Naver OAuth 2.0 Authentication Service
네이버 로그인 OAuth 2.0 인증 서비스
"""
import requests
import urllib.parse
from typing import Dict, Optional
from loguru import logger
from ..config import settings


class NaverOAuthService:
    """
    네이버 OAuth 2.0 인증 서비스
    - 로그인 URL 생성
    - Access Token 발급
    - Access Token 갱신
    """

    # OAuth 엔드포인트
    AUTHORIZE_URL = "https://nid.naver.com/oauth2.0/authorize"
    TOKEN_URL = "https://nid.naver.com/oauth2.0/token"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        callback_url: Optional[str] = None,
        account_id: Optional[int] = None,
        db: Optional[any] = None
    ):
        """
        초기화

        Args:
            client_id: 네이버 애플리케이션 Client ID
            client_secret: 네이버 애플리케이션 Client Secret
            callback_url: OAuth 콜백 URL
            account_id: DB의 네이버 계정 ID (우선순위 최상)
            db: Database Session (account_id 사용 시 필요)
        """
        # DB에서 계정 정보 가져오기 (최우선)
        if account_id and db:
            from ..models.naver_account import NaverAccount
            account = db.query(NaverAccount).filter(NaverAccount.id == account_id).first()
            if account:
                self.client_id = account.client_id
                self.client_secret = account.client_secret
                self.callback_url = account.callback_url or settings.NAVER_CALLBACK_URL
                logger.info(f"DB에서 네이버 계정 로드: {account.name} (ID: {account.id})")
            else:
                logger.warning(f"네이버 계정 ID {account_id}를 찾을 수 없습니다.")
                self.client_id = client_id or settings.NAVER_CLIENT_ID
                self.client_secret = client_secret or settings.NAVER_CLIENT_SECRET
                self.callback_url = callback_url or settings.NAVER_CALLBACK_URL
        else:
            self.client_id = client_id or settings.NAVER_CLIENT_ID
            self.client_secret = client_secret or settings.NAVER_CLIENT_SECRET
            self.callback_url = callback_url or settings.NAVER_CALLBACK_URL

        if not all([self.client_id, self.client_secret]):
            logger.warning(
                "네이버 API 자격 증명이 설정되지 않았습니다. "
                "네이버 계정을 등록하거나 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET를 설정해주세요."
            )

    def get_authorization_url(self, state: str = "RANDOM_STATE") -> str:
        """
        네이버 로그인 인증 URL 생성

        Args:
            state: CSRF 방지를 위한 상태 토큰

        Returns:
            str: 네이버 로그인 URL
        """
        if not self.client_id:
            raise ValueError("NAVER_CLIENT_ID가 설정되지 않았습니다.")

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.callback_url,
            "state": state
        }

        query_string = urllib.parse.urlencode(params)
        auth_url = f"{self.AUTHORIZE_URL}?{query_string}"

        logger.info(f"네이버 로그인 URL 생성: {auth_url}")
        return auth_url

    def get_access_token(
        self,
        code: str,
        state: str
    ) -> Dict[str, any]:
        """
        인증 코드로 Access Token 발급

        Args:
            code: 네이버 로그인 인증 코드
            state: 상태 토큰

        Returns:
            Dict: 토큰 정보
            {
                "access_token": "...",
                "refresh_token": "...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        """
        if not all([self.client_id, self.client_secret]):
            raise ValueError("네이버 API 자격 증명이 설정되지 않았습니다.")

        params = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "state": state
        }

        logger.info("네이버 Access Token 발급 요청...")

        try:
            response = requests.post(
                self.TOKEN_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()

            if "access_token" in token_data:
                logger.success("✅ Access Token 발급 성공")
                return {
                    "success": True,
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "token_type": token_data.get("token_type", "bearer"),
                    "expires_in": token_data.get("expires_in", 3600)
                }
            else:
                logger.error(f"❌ Access Token 발급 실패: {token_data}")
                return {
                    "success": False,
                    "error": token_data.get("error", "unknown_error"),
                    "error_description": token_data.get("error_description", "알 수 없는 오류")
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Access Token 발급 요청 오류: {str(e)}")
            return {
                "success": False,
                "error": "request_failed",
                "error_description": str(e)
            }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, any]:
        """
        Refresh Token으로 Access Token 갱신

        Args:
            refresh_token: Refresh Token

        Returns:
            Dict: 새로운 토큰 정보
        """
        if not all([self.client_id, self.client_secret]):
            raise ValueError("네이버 API 자격 증명이 설정되지 않았습니다.")

        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token
        }

        logger.info("네이버 Access Token 갱신 요청...")

        try:
            response = requests.post(
                self.TOKEN_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()

            if "access_token" in token_data:
                logger.success("✅ Access Token 갱신 성공")
                return {
                    "success": True,
                    "access_token": token_data["access_token"],
                    "token_type": token_data.get("token_type", "bearer"),
                    "expires_in": token_data.get("expires_in", 3600)
                }
            else:
                logger.error(f"❌ Access Token 갱신 실패: {token_data}")
                return {
                    "success": False,
                    "error": token_data.get("error", "unknown_error"),
                    "error_description": token_data.get("error_description", "알 수 없는 오류")
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Access Token 갱신 요청 오류: {str(e)}")
            return {
                "success": False,
                "error": "request_failed",
                "error_description": str(e)
            }

    def delete_access_token(self, access_token: str) -> Dict[str, any]:
        """
        Access Token 삭제 (로그아웃)

        Args:
            access_token: 삭제할 Access Token

        Returns:
            Dict: 삭제 결과
        """
        if not all([self.client_id, self.client_secret]):
            raise ValueError("네이버 API 자격 증명이 설정되지 않았습니다.")

        params = {
            "grant_type": "delete",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "access_token": access_token,
            "service_provider": "NAVER"
        }

        logger.info("네이버 Access Token 삭제 요청...")

        try:
            response = requests.post(
                self.TOKEN_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if result.get("result") == "success":
                logger.success("✅ Access Token 삭제 성공")
                return {
                    "success": True,
                    "message": "토큰이 삭제되었습니다."
                }
            else:
                logger.error(f"❌ Access Token 삭제 실패: {result}")
                return {
                    "success": False,
                    "error": result.get("error", "unknown_error"),
                    "error_description": result.get("error_description", "알 수 없는 오류")
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Access Token 삭제 요청 오류: {str(e)}")
            return {
                "success": False,
                "error": "request_failed",
                "error_description": str(e)
            }
