"""
Coupang Accounts Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import CoupangAccount
from loguru import logger


router = APIRouter(prefix="/coupang-accounts", tags=["coupang-accounts"])


# Pydantic models for request/response
class CoupangAccountCreate(BaseModel):
    """쿠팡 계정 생성 요청"""
    name: str
    vendor_id: str
    access_key: str
    secret_key: str
    wing_username: Optional[str] = None
    wing_password: Optional[str] = None


class CoupangAccountUpdate(BaseModel):
    """쿠팡 계정 수정 요청"""
    name: Optional[str] = None
    vendor_id: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    wing_username: Optional[str] = None
    wing_password: Optional[str] = None
    is_active: Optional[bool] = None


class CoupangAccountResponse(BaseModel):
    """쿠팡 계정 응답"""
    id: int
    name: str
    vendor_id: str
    access_key: str
    secret_key: str
    wing_username: Optional[str]
    wing_password: Optional[str]
    is_active: bool
    last_used_at: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[CoupangAccountResponse])
def get_all_accounts(
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """
    모든 쿠팡 계정 조회

    Args:
        include_inactive: 비활성 계정 포함 여부
    """
    try:
        query = db.query(CoupangAccount)

        if not include_inactive:
            query = query.filter(CoupangAccount.is_active == True)

        accounts = query.order_by(CoupangAccount.created_at.desc()).all()

        # Convert to dict with decrypted keys
        result = []
        for account in accounts:
            result.append(account.to_dict(include_keys=True))

        return result

    except Exception as e:
        logger.error(f"Error fetching accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch accounts: {str(e)}"
        )


@router.get("/{account_id}", response_model=CoupangAccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 쿠팡 계정 조회
    """
    account = db.query(CoupangAccount).filter(CoupangAccount.id == account_id).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )

    return account.to_dict(include_keys=True)


@router.post("", response_model=CoupangAccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: CoupangAccountCreate,
    db: Session = Depends(get_db)
):
    """
    새 쿠팡 계정 생성
    """
    try:
        # Check if vendor_id already exists
        existing = db.query(CoupangAccount).filter(
            CoupangAccount.vendor_id == account_data.vendor_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Account with vendor_id {account_data.vendor_id} already exists"
            )

        # Create new account
        new_account = CoupangAccount(
            name=account_data.name,
            vendor_id=account_data.vendor_id,
            wing_username=account_data.wing_username or account_data.vendor_id
        )

        # Set encrypted keys using property setters
        new_account.access_key = account_data.access_key
        new_account.secret_key = account_data.secret_key
        if account_data.wing_password:
            new_account.wing_password = account_data.wing_password

        db.add(new_account)
        db.commit()
        db.refresh(new_account)

        logger.info(f"Created new Coupang account: {new_account.name} (ID: {new_account.id})")

        return new_account.to_dict(include_keys=True)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}"
        )


@router.put("/{account_id}", response_model=CoupangAccountResponse)
def update_account(
    account_id: int,
    account_data: CoupangAccountUpdate,
    db: Session = Depends(get_db)
):
    """
    쿠팡 계정 정보 수정
    """
    try:
        account = db.query(CoupangAccount).filter(CoupangAccount.id == account_id).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {account_id} not found"
            )

        # Update fields
        if account_data.name is not None:
            account.name = account_data.name

        if account_data.vendor_id is not None:
            account.vendor_id = account_data.vendor_id

        if account_data.access_key is not None:
            account.access_key = account_data.access_key

        if account_data.secret_key is not None:
            account.secret_key = account_data.secret_key

        if account_data.wing_username is not None:
            account.wing_username = account_data.wing_username

        if account_data.wing_password is not None:
            account.wing_password = account_data.wing_password

        if account_data.is_active is not None:
            account.is_active = account_data.is_active

        account.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(account)

        logger.info(f"Updated Coupang account: {account.name} (ID: {account.id})")

        return account.to_dict(include_keys=True)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update account: {str(e)}"
        )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    쿠팡 계정 삭제
    """
    from ..models import AccountSet

    try:
        account = db.query(CoupangAccount).filter(CoupangAccount.id == account_id).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {account_id} not found"
            )

        # 연결된 AccountSet의 참조를 먼저 해제
        db.query(AccountSet).filter(AccountSet.coupang_account_id == account_id).update(
            {"coupang_account_id": None}
        )

        db.delete(account)
        db.commit()

        logger.info(f"Deleted Coupang account: {account.name} (ID: {account.id})")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


@router.post("/{account_id}/mark-used")
def mark_account_used(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    계정 마지막 사용 시간 업데이트
    """
    try:
        account = db.query(CoupangAccount).filter(CoupangAccount.id == account_id).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {account_id} not found"
            )

        account.last_used_at = datetime.utcnow()
        db.commit()

        return {"message": "Account usage updated"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking account used: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update account: {str(e)}"
        )
