"""
Naver Accounts Router
네이버 계정 설정 관리 API
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from loguru import logger

from ..database import get_db
from ..models.naver_account import NaverAccount


router = APIRouter(
    prefix="/naver-accounts",
    tags=["naver-accounts"]
)


# Pydantic 모델
class NaverAccountCreate(BaseModel):
    """네이버 계정 생성 요청"""
    name: str = Field(..., description="계정 이름 (예: 기본 네이버 계정)")
    description: Optional[str] = Field(None, description="계정 설명")
    client_id: str = Field(..., description="네이버 Client ID")
    client_secret: str = Field(..., description="네이버 Client Secret")
    callback_url: Optional[str] = Field("http://localhost:3000/naver/callback", description="OAuth 콜백 URL")
    naver_username: Optional[str] = Field(None, description="네이버 아이디 (선택, Selenium용)")
    naver_password: Optional[str] = Field(None, description="네이버 비밀번호 (선택, Selenium용)")
    is_default: bool = Field(False, description="기본 계정으로 설정")


class NaverAccountUpdate(BaseModel):
    """네이버 계정 수정 요청"""
    name: Optional[str] = Field(None, description="계정 이름")
    description: Optional[str] = Field(None, description="계정 설명")
    client_id: Optional[str] = Field(None, description="네이버 Client ID")
    client_secret: Optional[str] = Field(None, description="네이버 Client Secret")
    callback_url: Optional[str] = Field(None, description="OAuth 콜백 URL")
    naver_username: Optional[str] = Field(None, description="네이버 아이디")
    naver_password: Optional[str] = Field(None, description="네이버 비밀번호")
    is_active: Optional[bool] = Field(None, description="활성화 여부")
    is_default: Optional[bool] = Field(None, description="기본 계정 여부")


# API 엔드포인트

@router.post("")
async def create_naver_account(
    account: NaverAccountCreate,
    db: Session = Depends(get_db)
):
    """
    네이버 계정 설정 생성
    """
    try:
        # 기본 계정으로 설정하는 경우, 기존 기본 계정 해제
        if account.is_default:
            db.query(NaverAccount).update({"is_default": False})

        # 새 계정 생성
        new_account = NaverAccount(
            name=account.name,
            description=account.description,
            client_id=account.client_id,
            callback_url=account.callback_url,
            naver_username=account.naver_username,
            is_default=account.is_default
        )

        # 암호화된 필드 설정
        new_account.client_secret = account.client_secret
        if account.naver_password:
            new_account.naver_password = account.naver_password

        db.add(new_account)
        db.commit()
        db.refresh(new_account)

        logger.success(f"네이버 계정 생성 완료: {new_account.name} (ID: {new_account.id})")

        return {
            "success": True,
            "message": "네이버 계정이 생성되었습니다.",
            "data": new_account.to_dict(include_secrets=False)
        }

    except Exception as e:
        logger.error(f"네이버 계정 생성 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_naver_accounts(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    네이버 계정 목록 조회
    """
    try:
        query = db.query(NaverAccount)

        if not include_inactive:
            query = query.filter(NaverAccount.is_active == True)

        accounts = query.order_by(NaverAccount.is_default.desc(), NaverAccount.created_at.desc()).all()

        return {
            "success": True,
            "count": len(accounts),
            "data": [account.to_dict(include_secrets=False) for account in accounts]
        }

    except Exception as e:
        logger.error(f"네이버 계정 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}")
async def get_naver_account(
    account_id: int,
    include_secrets: bool = False,
    db: Session = Depends(get_db)
):
    """
    네이버 계정 상세 조회
    """
    try:
        account = db.query(NaverAccount).filter(NaverAccount.id == account_id).first()

        if not account:
            raise HTTPException(status_code=404, detail="네이버 계정을 찾을 수 없습니다.")

        return {
            "success": True,
            "data": account.to_dict(include_secrets=include_secrets)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"네이버 계정 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default/info")
async def get_default_naver_account(
    include_secrets: bool = False,
    db: Session = Depends(get_db)
):
    """
    기본 네이버 계정 조회
    """
    try:
        account = db.query(NaverAccount).filter(
            NaverAccount.is_default == True,
            NaverAccount.is_active == True
        ).first()

        if not account:
            # 기본 계정이 없으면 첫 번째 활성 계정 반환
            account = db.query(NaverAccount).filter(
                NaverAccount.is_active == True
            ).first()

        if not account:
            raise HTTPException(status_code=404, detail="사용 가능한 네이버 계정이 없습니다.")

        return {
            "success": True,
            "data": account.to_dict(include_secrets=include_secrets)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기본 네이버 계정 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default/credentials")
async def get_default_naver_credentials(
    db: Session = Depends(get_db)
):
    """
    기본 네이버 계정의 인증 정보 조회 (비밀번호 포함)
    주의: 이 엔드포인트는 프론트엔드에서 자동 로그인용으로만 사용해야 합니다.
    """
    try:
        account = db.query(NaverAccount).filter(
            NaverAccount.is_default == True,
            NaverAccount.is_active == True
        ).first()

        if not account:
            # 기본 계정이 없으면 첫 번째 활성 계정 반환
            account = db.query(NaverAccount).filter(
                NaverAccount.is_active == True
            ).first()

        if not account:
            return {
                "success": False,
                "message": "사용 가능한 네이버 계정이 없습니다.",
                "data": None
            }

        # 비밀번호 포함하여 반환
        return {
            "success": True,
            "data": {
                "id": account.id,
                "name": account.name,
                "username": account.naver_username,
                "password": account.naver_password  # 복호화된 비밀번호
            }
        }

    except Exception as e:
        logger.error(f"기본 네이버 계정 인증 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{account_id}")
async def update_naver_account(
    account_id: int,
    account: NaverAccountUpdate,
    db: Session = Depends(get_db)
):
    """
    네이버 계정 수정
    """
    try:
        existing_account = db.query(NaverAccount).filter(NaverAccount.id == account_id).first()

        if not existing_account:
            raise HTTPException(status_code=404, detail="네이버 계정을 찾을 수 없습니다.")

        # 기본 계정으로 설정하는 경우, 기존 기본 계정 해제
        if account.is_default and not existing_account.is_default:
            db.query(NaverAccount).filter(NaverAccount.id != account_id).update({"is_default": False})

        # 필드 업데이트
        update_data = account.dict(exclude_unset=True)

        # 암호화가 필요한 필드 처리
        if "client_secret" in update_data:
            existing_account.client_secret = update_data.pop("client_secret")

        if "naver_password" in update_data:
            existing_account.naver_password = update_data.pop("naver_password")

        # 나머지 필드 업데이트
        for key, value in update_data.items():
            setattr(existing_account, key, value)

        existing_account.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing_account)

        logger.success(f"네이버 계정 수정 완료: {existing_account.name} (ID: {existing_account.id})")

        return {
            "success": True,
            "message": "네이버 계정이 수정되었습니다.",
            "data": existing_account.to_dict(include_secrets=False)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"네이버 계정 수정 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{account_id}")
async def delete_naver_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    네이버 계정 삭제
    """
    try:
        account = db.query(NaverAccount).filter(NaverAccount.id == account_id).first()

        if not account:
            raise HTTPException(status_code=404, detail="네이버 계정을 찾을 수 없습니다.")

        # 기본 계정인 경우 경고
        if account.is_default:
            # 다른 계정이 있으면 첫 번째 계정을 기본으로 설정
            other_account = db.query(NaverAccount).filter(
                NaverAccount.id != account_id,
                NaverAccount.is_active == True
            ).first()

            if other_account:
                other_account.is_default = True
                logger.info(f"새로운 기본 계정 설정: {other_account.name} (ID: {other_account.id})")

        account_name = account.name
        db.delete(account)
        db.commit()

        logger.success(f"네이버 계정 삭제 완료: {account_name} (ID: {account_id})")

        return {
            "success": True,
            "message": f"네이버 계정 '{account_name}'이(가) 삭제되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"네이버 계정 삭제 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_id}/set-default")
async def set_default_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    기본 계정으로 설정
    """
    try:
        account = db.query(NaverAccount).filter(NaverAccount.id == account_id).first()

        if not account:
            raise HTTPException(status_code=404, detail="네이버 계정을 찾을 수 없습니다.")

        # 모든 계정의 기본 설정 해제
        db.query(NaverAccount).update({"is_default": False})

        # 선택한 계정을 기본으로 설정
        account.is_default = True
        db.commit()

        logger.success(f"기본 계정 설정 완료: {account.name} (ID: {account.id})")

        return {
            "success": True,
            "message": f"'{account.name}'을(를) 기본 계정으로 설정했습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기본 계정 설정 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_id}/test")
async def test_naver_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    네이버 계정 연결 테스트
    """
    try:
        from ..services.naver_oauth_service import NaverOAuthService

        account = db.query(NaverAccount).filter(NaverAccount.id == account_id).first()

        if not account:
            raise HTTPException(status_code=404, detail="네이버 계정을 찾을 수 없습니다.")

        # OAuth 서비스 생성
        oauth_service = NaverOAuthService(
            client_id=account.client_id,
            client_secret=account.client_secret,
            callback_url=account.callback_url
        )

        # 로그인 URL 생성으로 설정 테스트
        try:
            login_url = oauth_service.get_authorization_url()

            # 마지막 사용 시간 업데이트
            account.last_used_at = datetime.utcnow()
            db.commit()

            return {
                "success": True,
                "message": "네이버 계정 설정이 정상입니다.",
                "test_login_url": login_url
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"네이버 계정 설정 오류: {str(e)}"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"네이버 계정 테스트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
