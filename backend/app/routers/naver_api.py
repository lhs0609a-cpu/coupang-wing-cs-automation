"""
Naver API Router
네이버 OAuth 2.0 및 페이 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger
import secrets

from ..services.naver_oauth_service import NaverOAuthService
from ..services.naver_pay_service import NaverPayService


router = APIRouter(
    prefix="/naver",
    tags=["naver"]
)


# Pydantic 모델
class OAuthCallbackRequest(BaseModel):
    """OAuth 콜백 요청"""
    code: str = Field(..., description="인증 코드")
    state: str = Field(..., description="상태 토큰")


class TokenRefreshRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str = Field(..., description="Refresh Token")


class TokenDeleteRequest(BaseModel):
    """토큰 삭제 요청"""
    access_token: str = Field(..., description="Access Token")


# API 엔드포인트

@router.get("/oauth/login-url")
async def get_naver_login_url(
    state: Optional[str] = None
):
    """
    네이버 로그인 URL 생성

    사용자를 이 URL로 리다이렉트하면 네이버 로그인 페이지로 이동합니다.
    로그인 후 설정된 콜백 URL로 인증 코드가 전달됩니다.
    """
    try:
        # 상태 토큰 생성 (CSRF 방지)
        if not state:
            state = secrets.token_urlsafe(32)

        oauth_service = NaverOAuthService()
        login_url = oauth_service.get_authorization_url(state=state)

        return {
            "success": True,
            "login_url": login_url,
            "state": state,
            "message": "이 URL로 리다이렉트하여 네이버 로그인을 진행하세요."
        }

    except Exception as e:
        logger.error(f"네이버 로그인 URL 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oauth/callback")
async def handle_oauth_callback(request: OAuthCallbackRequest):
    """
    OAuth 콜백 처리 (Access Token 발급)

    네이버 로그인 후 콜백으로 전달된 인증 코드로 Access Token을 발급받습니다.
    프론트엔드에서 이 API를 호출하여 토큰을 받아야 합니다.
    """
    try:
        oauth_service = NaverOAuthService()
        result = oauth_service.get_access_token(
            code=request.code,
            state=request.state
        )

        if result.get("success"):
            return {
                "success": True,
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token"),
                "token_type": result["token_type"],
                "expires_in": result["expires_in"],
                "message": "Access Token이 발급되었습니다."
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": result.get("error"),
                    "error_description": result.get("error_description")
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth 콜백 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oauth/refresh")
async def refresh_token(request: TokenRefreshRequest):
    """
    Access Token 갱신

    Refresh Token을 사용하여 새로운 Access Token을 발급받습니다.
    """
    try:
        oauth_service = NaverOAuthService()
        result = oauth_service.refresh_access_token(request.refresh_token)

        if result.get("success"):
            return {
                "success": True,
                "access_token": result["access_token"],
                "token_type": result["token_type"],
                "expires_in": result["expires_in"],
                "message": "Access Token이 갱신되었습니다."
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": result.get("error"),
                    "error_description": result.get("error_description")
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"토큰 갱신 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oauth/logout")
async def logout(request: TokenDeleteRequest):
    """
    로그아웃 (Access Token 삭제)

    Access Token을 삭제하여 로그아웃합니다.
    """
    try:
        oauth_service = NaverOAuthService()
        result = oauth_service.delete_access_token(request.access_token)

        if result.get("success"):
            return {
                "success": True,
                "message": "로그아웃되었습니다."
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": result.get("error"),
                    "error_description": result.get("error_description")
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그아웃 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pay/address")
async def get_pay_address(
    access_token: str = Query(..., description="네이버 로그인 Access Token")
):
    """
    네이버 페이 배송지 정보 조회

    Access Token을 사용하여 사용자의 네이버 페이 배송지 정보를 조회합니다.
    네이버 페이 회원만 조회 가능합니다.
    """
    try:
        pay_service = NaverPayService(access_token=access_token)
        result = pay_service.get_pay_address()

        if result.get("success"):
            return {
                "success": True,
                "data": result["data"],
                "message": "배송지 정보 조회 성공"
            }
        else:
            error_code = result.get("error")
            error_desc = result.get("error_description")

            # HTTP 상태 코드 매핑
            if error_code == "no_token":
                status_code = 401
            elif error_code == "http_401":
                status_code = 401
            elif error_code == "http_403":
                status_code = 403
            elif error_code == "http_404":
                status_code = 404
            elif error_code == "http_500":
                status_code = 500
            else:
                status_code = 400

            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": error_code,
                    "error_description": error_desc
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배송지 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pay/address/formatted")
async def get_formatted_address(
    access_token: str = Query(..., description="네이버 로그인 Access Token")
):
    """
    네이버 페이 배송지 정보 조회 (포맷된 주소)

    배송지 정보를 반품 신청에 사용하기 쉽게 포맷하여 반환합니다.
    """
    try:
        pay_service = NaverPayService(access_token=access_token)
        result = pay_service.get_pay_address()

        if result.get("success"):
            address_data = result["data"]
            receiver_info = pay_service.get_receiver_info(address_data)
            formatted_address = pay_service.format_address_for_return(address_data)

            return {
                "success": True,
                "receiver_info": receiver_info,
                "formatted_address": formatted_address,
                "message": "배송지 정보 조회 및 포맷 완료"
            }
        else:
            error_code = result.get("error")
            error_desc = result.get("error_description")

            raise HTTPException(
                status_code=400,
                detail={
                    "error": error_code,
                    "error_description": error_desc
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배송지 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
