"""
Promotion Router - 프로모션(쿠폰) 자동연동 API
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from loguru import logger

from ..database import SessionLocal, get_db
from ..services.coupon_auto_sync_service import CouponAutoSyncService
from sqlalchemy.orm import Session


router = APIRouter(prefix="/promotion", tags=["Promotion - 쿠폰 자동연동"])


# ==================== Request/Response Models ====================

class CouponConfigRequest(BaseModel):
    """쿠폰 자동연동 설정 요청"""
    is_enabled: Optional[bool] = None
    instant_coupon_enabled: Optional[bool] = None
    instant_coupon_id: Optional[int] = None
    instant_coupon_name: Optional[str] = None
    download_coupon_enabled: Optional[bool] = None
    download_coupon_id: Optional[int] = None
    download_coupon_name: Optional[str] = None
    apply_delay_days: Optional[int] = 1
    contract_id: Optional[int] = None
    excluded_categories: Optional[List[int]] = None
    excluded_product_ids: Optional[List[int]] = None


class ToggleRequest(BaseModel):
    """활성화/비활성화 요청"""
    enabled: bool


class ManualSyncRequest(BaseModel):
    """수동 동기화 요청"""
    target_date: Optional[str] = None  # yyyy-MM-dd


class BulkApplyRequest(BaseModel):
    """전체 상품 일괄 적용 요청"""
    days_back: Optional[int] = 30  # 며칠 전까지 조회할지 (기본 30일)
    skip_applied: Optional[bool] = True  # 이미 적용된 상품 건너뛰기 (기본: True)


# ==================== 설정 관리 API ====================

@router.get("/config/{account_id}")
async def get_coupon_config(account_id: int, db: Session = Depends(get_db)):
    """
    쿠폰 자동연동 설정 조회

    Args:
        account_id: 쿠팡 계정 ID
    """
    try:
        service = CouponAutoSyncService(db)
        config = service.get_config(account_id)

        if config:
            return {
                "success": True,
                "config": config.to_dict()
            }
        else:
            return {
                "success": True,
                "config": None,
                "message": "설정이 없습니다. 새로 생성해주세요."
            }
    except Exception as e:
        logger.error(f"Error getting coupon config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/{account_id}")
async def create_or_update_config(
    account_id: int,
    request: CouponConfigRequest,
    db: Session = Depends(get_db)
):
    """
    쿠폰 자동연동 설정 생성/수정

    Args:
        account_id: 쿠팡 계정 ID
        request: 설정 데이터
    """
    try:
        service = CouponAutoSyncService(db)

        config_data = request.dict(exclude_unset=True)
        config = service.create_or_update_config(account_id, config_data)

        return {
            "success": True,
            "message": "설정이 저장되었습니다.",
            "config": config.to_dict()
        }
    except Exception as e:
        logger.error(f"Error saving coupon config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/{account_id}/toggle")
async def toggle_coupon_config(
    account_id: int,
    request: ToggleRequest,
    db: Session = Depends(get_db)
):
    """
    쿠폰 자동연동 활성화/비활성화

    Args:
        account_id: 쿠팡 계정 ID
        request: 활성화 여부
    """
    try:
        service = CouponAutoSyncService(db)
        config = service.toggle_config(account_id, request.enabled)

        if config:
            status = "활성화" if request.enabled else "비활성화"
            return {
                "success": True,
                "message": f"쿠폰 자동연동이 {status}되었습니다.",
                "config": config.to_dict()
            }
        else:
            raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling coupon config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 계약서/쿠폰 조회 API ====================

@router.get("/contracts/{account_id}")
async def get_contracts(account_id: int, db: Session = Depends(get_db)):
    """
    계약서 목록 조회

    Args:
        account_id: 쿠팡 계정 ID
    """
    try:
        service = CouponAutoSyncService(db)
        result = service.get_contracts(account_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contracts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coupons/instant/{account_id}")
async def get_instant_coupons(
    account_id: int,
    status: str = "APPLIED",
    db: Session = Depends(get_db)
):
    """
    즉시할인쿠폰 목록 조회

    Args:
        account_id: 쿠팡 계정 ID
        status: 쿠폰 상태 (STANDBY, APPLIED, PAUSED, EXPIRED, DETACHED)
    """
    try:
        service = CouponAutoSyncService(db)
        result = service.get_instant_coupons(account_id, status)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting instant coupons: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 수동 동기화 API ====================

@router.post("/sync/{account_id}/detect")
async def detect_new_products(
    account_id: int,
    request: ManualSyncRequest = None,
    db: Session = Depends(get_db)
):
    """
    신규 상품 감지

    Args:
        account_id: 쿠팡 계정 ID
        request: 대상 날짜 (선택)
    """
    try:
        service = CouponAutoSyncService(db)
        target_date = request.target_date if request else None
        result = service.detect_new_products(account_id, target_date)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting new products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/{account_id}/register")
async def register_products(
    account_id: int,
    request: ManualSyncRequest = None,
    db: Session = Depends(get_db)
):
    """
    신규 상품 감지 및 추적 등록

    Args:
        account_id: 쿠팡 계정 ID
        request: 대상 날짜 (선택)
    """
    try:
        service = CouponAutoSyncService(db)
        target_date = request.target_date if request else None

        # 1. 신규 상품 감지
        detect_result = service.detect_new_products(account_id, target_date)
        if not detect_result["success"]:
            raise HTTPException(status_code=400, detail=detect_result["message"])

        new_products = detect_result.get("new_products", [])
        if not new_products:
            return {
                "success": True,
                "message": "등록할 신규 상품이 없습니다.",
                "detected": 0,
                "registered": 0
            }

        # 2. 추적 등록
        register_result = service.register_products_for_tracking(account_id, new_products)

        return {
            "success": True,
            "message": f"{register_result['registered']}개 상품이 등록되었습니다.",
            "detected": len(new_products),
            "registered": register_result["registered"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/{account_id}/apply")
async def apply_coupons(account_id: int, db: Session = Depends(get_db)):
    """
    대기 중인 상품에 쿠폰 적용

    Args:
        account_id: 쿠팡 계정 ID
    """
    try:
        service = CouponAutoSyncService(db)
        result = service.apply_coupons_to_pending_products(account_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying coupons: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/{account_id}/full")
async def run_full_sync(
    account_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    전체 동기화 실행 (감지 + 등록 + 적용)

    Args:
        account_id: 쿠팡 계정 ID
    """
    try:
        service = CouponAutoSyncService(db)

        # 백그라운드에서 실행
        def run_sync():
            db_session = SessionLocal()
            try:
                sync_service = CouponAutoSyncService(db_session)
                sync_service.run_auto_sync(account_id)
            finally:
                db_session.close()

        background_tasks.add_task(run_sync)

        return {
            "success": True,
            "message": "동기화가 백그라운드에서 시작되었습니다."
        }
    except Exception as e:
        logger.error(f"Error running full sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/{account_id}/bulk-apply")
async def bulk_apply_coupons(
    account_id: int,
    request: BulkApplyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    전체 상품에 쿠폰 일괄 적용

    Args:
        account_id: 쿠팡 계정 ID
        request: 일괄 적용 설정 (days_back, skip_applied)
    """
    try:
        days_back = request.days_back or 365
        skip_applied = request.skip_applied if request.skip_applied is not None else True

        # 백그라운드에서 실행
        def run_bulk_apply():
            db_session = SessionLocal()
            try:
                sync_service = CouponAutoSyncService(db_session)
                result = sync_service.apply_coupons_to_all_products(account_id, days_back, skip_applied)
                logger.info(f"Bulk apply result: {result}")
            finally:
                db_session.close()

        background_tasks.add_task(run_bulk_apply)

        skip_msg = "이미 적용된 상품 제외" if skip_applied else "전체 상품 대상"
        return {
            "success": True,
            "message": f"전체 상품에 쿠폰 일괄 적용이 시작되었습니다. ({skip_msg})"
        }
    except Exception as e:
        logger.error(f"Error running bulk apply: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/{account_id}/restart")
async def restart_bulk_apply(
    account_id: int,
    request: BulkApplyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    쿠폰 일괄 적용 재시작 (기존 작업 취소 후 새로 시작)

    Args:
        account_id: 쿠팡 계정 ID
        request: 일괄 적용 설정
    """
    try:
        service = CouponAutoSyncService(db)

        # 1. 기존 작업 취소
        cancel_result = service.cancel_bulk_apply_progress(account_id)
        logger.info(f"Cancel result: {cancel_result}")

        days_back = request.days_back or 365
        skip_applied = request.skip_applied if request.skip_applied is not None else True

        # 2. 새 작업 시작 (백그라운드)
        def run_bulk_apply():
            db_session = SessionLocal()
            try:
                sync_service = CouponAutoSyncService(db_session)
                result = sync_service.apply_coupons_to_all_products(account_id, days_back, skip_applied)
                logger.info(f"Bulk apply result: {result}")
            finally:
                db_session.close()

        background_tasks.add_task(run_bulk_apply)

        skip_msg = "이미 적용된 상품 제외" if skip_applied else "전체 상품 대상"
        return {
            "success": True,
            "message": f"기존 작업을 취소하고 새로 시작합니다. ({skip_msg})"
        }
    except Exception as e:
        logger.error(f"Error restarting bulk apply: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 진행 상황 조회 API ====================

@router.get("/progress/{account_id}")
async def get_bulk_apply_progress(account_id: int, db: Session = Depends(get_db)):
    """
    일괄 적용 진행 상황 조회

    Args:
        account_id: 쿠팡 계정 ID
    """
    try:
        service = CouponAutoSyncService(db)
        progress = service.get_latest_bulk_apply_progress(account_id)

        if progress:
            return {
                "success": True,
                "progress": progress.to_dict()
            }
        else:
            return {
                "success": True,
                "progress": None,
                "message": "진행 중인 작업이 없습니다."
            }
    except Exception as e:
        logger.error(f"Error getting bulk apply progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/progress/{account_id}")
async def cancel_bulk_apply_progress(account_id: int, db: Session = Depends(get_db)):
    """
    진행 중인 일괄 적용 작업 취소/리셋

    Args:
        account_id: 쿠팡 계정 ID
    """
    try:
        service = CouponAutoSyncService(db)
        result = service.cancel_bulk_apply_progress(account_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling bulk apply progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 추적/이력 조회 API ====================

@router.get("/tracking/{account_id}")
async def get_tracking_list(
    account_id: int,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    상품 쿠폰 적용 추적 목록 조회

    Args:
        account_id: 쿠팡 계정 ID
        status: 상태 필터 (pending, processing, completed, failed, skipped)
        limit: 조회 개수
        offset: 시작 위치
    """
    try:
        service = CouponAutoSyncService(db)
        result = service.get_tracking_list(account_id, status, limit, offset)
        return result
    except Exception as e:
        logger.error(f"Error getting tracking list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{account_id}")
async def get_apply_logs(
    account_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    쿠폰 적용 이력 조회

    Args:
        account_id: 쿠팡 계정 ID
        limit: 조회 개수
        offset: 시작 위치
    """
    try:
        service = CouponAutoSyncService(db)
        result = service.get_apply_logs(account_id, limit, offset)
        return result
    except Exception as e:
        logger.error(f"Error getting apply logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{account_id}")
async def get_statistics(account_id: int, db: Session = Depends(get_db)):
    """
    쿠폰 자동연동 통계 조회

    Args:
        account_id: 쿠팡 계정 ID
    """
    try:
        service = CouponAutoSyncService(db)
        result = service.get_statistics(account_id)
        return result
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 관리자 API ====================

@router.post("/admin/sync-all")
async def run_sync_all_accounts(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    모든 활성화된 계정에 대해 자동 동기화 실행 (관리자용)
    """
    try:
        def run_all_sync():
            db_session = SessionLocal()
            try:
                sync_service = CouponAutoSyncService(db_session)
                sync_service.run_auto_sync_all_accounts()
            finally:
                db_session.close()

        background_tasks.add_task(run_all_sync)

        return {
            "success": True,
            "message": "모든 계정의 동기화가 백그라운드에서 시작되었습니다."
        }
    except Exception as e:
        logger.error(f"Error running sync for all accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
