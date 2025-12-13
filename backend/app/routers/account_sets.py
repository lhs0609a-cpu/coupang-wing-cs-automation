"""
Account Sets Router
쿠팡 + 네이버 계정을 하나의 세트로 관리하는 API
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from loguru import logger

from ..database import get_db
from ..models.account_set import AccountSet
from ..models.coupang_account import CoupangAccount
from ..models.naver_account import NaverAccount


router = APIRouter(
    prefix="/account-sets",
    tags=["account-sets"]
)


# Pydantic 모델
class AccountSetCreate(BaseModel):
    """계정 세트 생성 요청"""
    name: str = Field(..., description="세트 이름 (예: 기본 계정, 회사 계정)")
    description: Optional[str] = Field(None, description="세트 설명")

    # 쿠팡 계정 정보
    coupang_account_name: Optional[str] = Field(None, description="쿠팡 계정 이름")
    coupang_vendor_id: Optional[str] = Field(None, description="쿠팡 Vendor ID")
    coupang_access_key: Optional[str] = Field(None, description="쿠팡 Access Key")
    coupang_secret_key: Optional[str] = Field(None, description="쿠팡 Secret Key")
    coupang_wing_username: Optional[str] = Field(None, description="쿠팡 Wing 아이디")
    coupang_wing_password: Optional[str] = Field(None, description="쿠팡 Wing 비밀번호")

    # 네이버 계정 정보
    naver_account_name: Optional[str] = Field(None, description="네이버 계정 이름")
    naver_username: Optional[str] = Field(None, description="네이버 아이디")
    naver_password: Optional[str] = Field(None, description="네이버 비밀번호")

    is_default: bool = Field(False, description="기본 세트로 설정")


class AccountSetUpdate(BaseModel):
    """계정 세트 수정 요청"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


# API 엔드포인트

@router.post("")
async def create_account_set(
    account_set: AccountSetCreate,
    db: Session = Depends(get_db)
):
    """
    새로운 계정 세트 생성 (쿠팡 + 네이버 통합)
    """
    try:
        # 기본 세트로 설정하는 경우, 기존 기본 세트 해제
        if account_set.is_default:
            db.query(AccountSet).update({"is_default": False})

        coupang_account_id = None
        naver_account_id = None

        # 쿠팡 계정 생성 또는 업데이트
        if account_set.coupang_access_key and account_set.coupang_secret_key and account_set.coupang_vendor_id:
            # 기존 계정 확인
            existing_coupang = db.query(CoupangAccount).filter(
                CoupangAccount.vendor_id == account_set.coupang_vendor_id
            ).first()

            if existing_coupang:
                # 업데이트
                existing_coupang.access_key = account_set.coupang_access_key
                existing_coupang.secret_key = account_set.coupang_secret_key
                if account_set.coupang_wing_username:
                    existing_coupang.wing_username = account_set.coupang_wing_username
                if account_set.coupang_wing_password:
                    existing_coupang.wing_password = account_set.coupang_wing_password
                existing_coupang.is_active = True
                coupang_account_id = existing_coupang.id
                logger.info(f"쿠팡 계정 업데이트: {existing_coupang.name}")
            else:
                # 새로 생성
                new_coupang = CoupangAccount(
                    name=account_set.coupang_account_name or f"{account_set.name} - 쿠팡",
                    vendor_id=account_set.coupang_vendor_id,
                    wing_username=account_set.coupang_wing_username or account_set.coupang_vendor_id
                )
                new_coupang.access_key = account_set.coupang_access_key
                new_coupang.secret_key = account_set.coupang_secret_key
                if account_set.coupang_wing_password:
                    new_coupang.wing_password = account_set.coupang_wing_password

                db.add(new_coupang)
                db.flush()
                coupang_account_id = new_coupang.id
                logger.info(f"쿠팡 계정 생성: {new_coupang.name}")

        # 네이버 계정 생성 또는 업데이트
        if account_set.naver_username and account_set.naver_password:
            # 기존 계정 확인
            existing_naver = db.query(NaverAccount).filter(
                NaverAccount.naver_username == account_set.naver_username
            ).first()

            if existing_naver:
                # 업데이트
                existing_naver.naver_password = account_set.naver_password
                existing_naver.is_active = True
                naver_account_id = existing_naver.id
                logger.info(f"네이버 계정 업데이트: {existing_naver.name}")
            else:
                # 새로 생성
                new_naver = NaverAccount(
                    name=account_set.naver_account_name or f"{account_set.name} - 네이버",
                    client_id=account_set.naver_username,
                    naver_username=account_set.naver_username,
                    callback_url="http://localhost:3000/naver/callback"
                )
                new_naver.client_secret = "naver_automation_secret"
                new_naver.naver_password = account_set.naver_password

                db.add(new_naver)
                db.flush()
                naver_account_id = new_naver.id
                logger.info(f"네이버 계정 생성: {new_naver.name}")

        # 계정 세트 생성
        new_set = AccountSet(
            name=account_set.name,
            description=account_set.description,
            coupang_account_id=coupang_account_id,
            naver_account_id=naver_account_id,
            is_default=account_set.is_default
        )

        db.add(new_set)
        db.commit()
        db.refresh(new_set)

        logger.success(f"계정 세트 생성 완료: {new_set.name} (ID: {new_set.id})")

        return {
            "success": True,
            "message": f"계정 세트 '{new_set.name}'이(가) 생성되었습니다.",
            "data": new_set.to_dict(include_account_details=True)
        }

    except Exception as e:
        logger.error(f"계정 세트 생성 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_account_sets(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    모든 계정 세트 조회
    """
    try:
        query = db.query(AccountSet)

        if not include_inactive:
            query = query.filter(AccountSet.is_active == True)

        sets = query.order_by(AccountSet.is_default.desc(), AccountSet.created_at.desc()).all()

        return {
            "success": True,
            "count": len(sets),
            "data": [s.to_dict(include_account_details=True) for s in sets]
        }

    except Exception as e:
        logger.error(f"계정 세트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default")
async def get_default_account_set(
    db: Session = Depends(get_db)
):
    """
    기본 계정 세트 조회
    """
    try:
        account_set = db.query(AccountSet).filter(
            AccountSet.is_default == True,
            AccountSet.is_active == True
        ).first()

        if not account_set:
            # 기본 세트가 없으면 첫 번째 활성 세트 반환
            account_set = db.query(AccountSet).filter(
                AccountSet.is_active == True
            ).first()

        if not account_set:
            return {
                "success": False,
                "message": "사용 가능한 계정 세트가 없습니다.",
                "data": None
            }

        return {
            "success": True,
            "data": account_set.to_dict(include_account_details=True)
        }

    except Exception as e:
        logger.error(f"기본 계정 세트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{set_id}")
async def get_account_set(
    set_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 계정 세트 조회
    """
    try:
        account_set = db.query(AccountSet).filter(AccountSet.id == set_id).first()

        if not account_set:
            raise HTTPException(status_code=404, detail="계정 세트를 찾을 수 없습니다.")

        return {
            "success": True,
            "data": account_set.to_dict(include_account_details=True)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"계정 세트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{set_id}")
async def update_account_set(
    set_id: int,
    account_set: AccountSetUpdate,
    db: Session = Depends(get_db)
):
    """
    계정 세트 정보 수정
    """
    try:
        existing_set = db.query(AccountSet).filter(AccountSet.id == set_id).first()

        if not existing_set:
            raise HTTPException(status_code=404, detail="계정 세트를 찾을 수 없습니다.")

        # 기본 세트로 설정하는 경우, 기존 기본 세트 해제
        if account_set.is_default and not existing_set.is_default:
            db.query(AccountSet).filter(AccountSet.id != set_id).update({"is_default": False})

        # 필드 업데이트
        if account_set.name is not None:
            existing_set.name = account_set.name

        if account_set.description is not None:
            existing_set.description = account_set.description

        if account_set.is_default is not None:
            existing_set.is_default = account_set.is_default

        if account_set.is_active is not None:
            existing_set.is_active = account_set.is_active

        existing_set.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing_set)

        logger.success(f"계정 세트 수정 완료: {existing_set.name} (ID: {existing_set.id})")

        return {
            "success": True,
            "message": "계정 세트가 수정되었습니다.",
            "data": existing_set.to_dict(include_account_details=True)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"계정 세트 수정 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{set_id}")
async def delete_account_set(
    set_id: int,
    db: Session = Depends(get_db)
):
    """
    계정 세트 삭제
    """
    try:
        account_set = db.query(AccountSet).filter(AccountSet.id == set_id).first()

        if not account_set:
            raise HTTPException(status_code=404, detail="계정 세트를 찾을 수 없습니다.")

        # 기본 세트인 경우 경고
        if account_set.is_default:
            # 다른 세트가 있으면 첫 번째 세트를 기본으로 설정
            other_set = db.query(AccountSet).filter(
                AccountSet.id != set_id,
                AccountSet.is_active == True
            ).first()

            if other_set:
                other_set.is_default = True
                logger.info(f"새로운 기본 세트 설정: {other_set.name} (ID: {other_set.id})")

        set_name = account_set.name
        db.delete(account_set)
        db.commit()

        logger.success(f"계정 세트 삭제 완료: {set_name} (ID: {set_id})")

        return {
            "success": True,
            "message": f"계정 세트 '{set_name}'이(가) 삭제되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"계정 세트 삭제 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{set_id}/set-default")
async def set_default_account_set(
    set_id: int,
    db: Session = Depends(get_db)
):
    """
    계정 세트를 기본으로 설정
    """
    try:
        account_set = db.query(AccountSet).filter(AccountSet.id == set_id).first()

        if not account_set:
            raise HTTPException(status_code=404, detail="계정 세트를 찾을 수 없습니다.")

        # 모든 세트의 기본 설정 해제
        db.query(AccountSet).update({"is_default": False})

        # 선택한 세트를 기본으로 설정
        account_set.is_default = True
        account_set.last_used_at = datetime.utcnow()
        db.commit()

        logger.success(f"기본 계정 세트 설정 완료: {account_set.name} (ID: {account_set.id})")

        return {
            "success": True,
            "message": f"'{account_set.name}'을(를) 기본 계정 세트로 설정했습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기본 계정 세트 설정 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
