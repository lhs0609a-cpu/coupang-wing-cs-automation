"""
네이버 배송 → 쿠팡 송장 동기화 API 라우터
"""
import logging
import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.naver_delivery_sync import NaverDeliveryInfo, CoupangPendingOrder, get_coupang_courier_code
from ..models.coupang_account import CoupangAccount
from ..services.naver_delivery_sync_service import NaverDeliverySyncService
from ..services.naverpay_scraper import get_scraper, scrape_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/delivery-sync", tags=["Delivery Sync"])


# ========== Pydantic Models ==========

class SyncRequest(BaseModel):
    """동기화 요청"""
    auto_upload: bool = False
    naver_account_id: Optional[int] = None
    coupang_account_id: Optional[int] = None


class ManualMatchRequest(BaseModel):
    """수동 매칭 요청"""
    delivery_id: int
    shipment_box_id: str
    order_id: str
    vendor_item_id: str


class ManualUploadRequest(BaseModel):
    """수동 업로드 요청"""
    delivery_id: int


class CoupangOrderFetchRequest(BaseModel):
    """쿠팡 발주서 조회 요청"""
    coupang_account_id: int
    hours_back: int = 24


class SyncStats(BaseModel):
    """동기화 통계"""
    total: int
    pending: int
    matched: int
    uploaded: int
    failed: int


# ========== Helper Functions ==========

def get_coupang_credentials(db: Session, account_id: int) -> dict:
    """쿠팡 계정 인증 정보 가져오기"""
    account = db.query(CoupangAccount).filter(
        CoupangAccount.id == account_id
    ).first()

    if not account:
        return None

    return {
        "access_key": account.access_key,
        "secret_key": account.secret_key,
        "vendor_id": account.vendor_id
    }


def get_sync_service(db: Session, coupang_account_id: int = None) -> NaverDeliverySyncService:
    """동기화 서비스 인스턴스 생성"""
    creds = None
    if coupang_account_id:
        creds = get_coupang_credentials(db, coupang_account_id)

    return NaverDeliverySyncService(
        db=db,
        coupang_access_key=creds["access_key"] if creds else None,
        coupang_secret_key=creds["secret_key"] if creds else None,
        coupang_vendor_id=creds["vendor_id"] if creds else None
    )


# ========== Sync API ==========

@router.post("/sync/stream")
async def sync_deliveries_stream(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """
    네이버 배송 정보 수집 및 쿠팡 매칭 (SSE 스트리밍)

    1. 네이버 배송 정보 수집
    2. 쿠팡 발주서와 수취인 이름 매칭
    3. (선택) 자동 송장 업로드
    """
    async def event_generator():
        try:
            service = get_sync_service(db, request.coupang_account_id)

            async for result in service.sync_deliveries(
                auto_upload=request.auto_upload,
                naver_account_id=request.naver_account_id,
                coupang_account_id=request.coupang_account_id
            ):
                yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/sync")
async def sync_deliveries(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """
    네이버 배송 정보 수집 및 쿠팡 매칭 (동기식)
    """
    try:
        service = get_sync_service(db, request.coupang_account_id)

        results = {
            "collected": 0,
            "matched": 0,
            "uploaded": 0,
            "deliveries": [],
            "matches": []
        }

        async for result in service.sync_deliveries(
            auto_upload=request.auto_upload,
            naver_account_id=request.naver_account_id,
            coupang_account_id=request.coupang_account_id
        ):
            if result["type"] == "delivery":
                results["collected"] += 1
                results["deliveries"].append(result["data"])
            elif result["type"] == "matched":
                results["matched"] += 1
                results["matches"].append(result["data"])
            elif result["type"] == "uploaded":
                if result["data"]["success"]:
                    results["uploaded"] += 1
            elif result["type"] == "complete":
                pass  # 완료 이벤트는 무시
            elif result["type"] == "error":
                raise HTTPException(status_code=500, detail=result["message"])

        return {
            "success": True,
            **results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"동기화 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Naver Delivery Info API ==========

@router.get("/deliveries")
async def get_deliveries(
    status: Optional[str] = Query(None, description="상태 필터 (pending, matched, uploaded, failed)"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """저장된 배송 정보 조회"""
    try:
        query = db.query(NaverDeliveryInfo)

        if status:
            query = query.filter(NaverDeliveryInfo.status == status)

        deliveries = query.order_by(NaverDeliveryInfo.created_at.desc()).limit(limit).all()

        return [d.to_dict() for d in deliveries]

    except Exception as e:
        logger.error(f"배송 정보 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deliveries/{delivery_id}")
async def get_delivery(delivery_id: int, db: Session = Depends(get_db)):
    """배송 정보 상세 조회"""
    try:
        delivery = db.query(NaverDeliveryInfo).filter(
            NaverDeliveryInfo.id == delivery_id
        ).first()

        if not delivery:
            raise HTTPException(status_code=404, detail="배송 정보를 찾을 수 없습니다")

        return delivery.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배송 정보 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/deliveries/{delivery_id}")
async def delete_delivery(delivery_id: int, db: Session = Depends(get_db)):
    """배송 정보 삭제"""
    try:
        delivery = db.query(NaverDeliveryInfo).filter(
            NaverDeliveryInfo.id == delivery_id
        ).first()

        if not delivery:
            raise HTTPException(status_code=404, detail="배송 정보를 찾을 수 없습니다")

        db.delete(delivery)
        db.commit()

        return {"success": True, "message": "삭제 완료"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Coupang Orders API ==========

@router.post("/coupang/fetch-orders")
async def fetch_coupang_orders(
    request: CoupangOrderFetchRequest,
    db: Session = Depends(get_db)
):
    """쿠팡 발주서 조회 (상품준비중)"""
    try:
        creds = get_coupang_credentials(db, request.coupang_account_id)
        if not creds:
            raise HTTPException(status_code=404, detail="쿠팡 계정을 찾을 수 없습니다")

        from ..services.coupang_shipment_service import CoupangShipmentService

        service = CoupangShipmentService(
            db=db,
            access_key=creds["access_key"],
            secret_key=creds["secret_key"],
            vendor_id=creds["vendor_id"]
        )

        orders = service.get_pending_orders(hours_back=request.hours_back)

        return {
            "success": True,
            "count": len(orders),
            "orders": orders
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"쿠팡 발주서 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coupang/pending-orders")
async def get_coupang_pending_orders(
    only_unuploaded: bool = Query(True, description="미등록 건만 조회"),
    db: Session = Depends(get_db)
):
    """DB에 캐시된 쿠팡 발주서 조회"""
    try:
        query = db.query(CoupangPendingOrder).filter(
            CoupangPendingOrder.status == "INSTRUCT"
        )

        if only_unuploaded:
            query = query.filter(CoupangPendingOrder.is_invoice_uploaded == False)

        orders = query.order_by(CoupangPendingOrder.created_at.desc()).all()

        return [o.to_dict() for o in orders]

    except Exception as e:
        logger.error(f"발주서 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Manual Operations API ==========

@router.post("/manual/match")
async def manual_match(
    request: ManualMatchRequest,
    db: Session = Depends(get_db)
):
    """수동 매칭"""
    try:
        service = get_sync_service(db)
        result = service.manual_match(
            delivery_id=request.delivery_id,
            shipment_box_id=request.shipment_box_id,
            order_id=request.order_id,
            vendor_item_id=request.vendor_item_id
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"수동 매칭 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual/upload")
async def manual_upload(
    request: ManualUploadRequest,
    coupang_account_id: int = Query(..., description="쿠팡 계정 ID"),
    db: Session = Depends(get_db)
):
    """수동 송장 업로드"""
    try:
        service = get_sync_service(db, coupang_account_id)
        result = service.manual_upload_invoice(delivery_id=request.delivery_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"수동 업로드 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual/bulk-upload")
async def bulk_upload(
    delivery_ids: List[int],
    coupang_account_id: int = Query(..., description="쿠팡 계정 ID"),
    db: Session = Depends(get_db)
):
    """일괄 송장 업로드"""
    try:
        service = get_sync_service(db, coupang_account_id)

        results = {
            "total": len(delivery_ids),
            "success": 0,
            "failed": 0,
            "details": []
        }

        for delivery_id in delivery_ids:
            result = service.manual_upload_invoice(delivery_id=delivery_id)

            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "delivery_id": delivery_id,
                **result
            })

        return results

    except Exception as e:
        logger.error(f"일괄 업로드 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Stats API ==========

@router.get("/stats", response_model=SyncStats)
async def get_sync_stats(db: Session = Depends(get_db)):
    """동기화 통계"""
    try:
        service = get_sync_service(db)
        return service.get_delivery_stats()

    except Exception as e:
        logger.error(f"통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Courier Mapping API ==========

@router.get("/couriers")
async def get_courier_mapping():
    """택배사 코드 매핑 조회"""
    from ..models.naver_delivery_sync import NAVER_TO_COUPANG_COURIER

    return {
        "mapping": NAVER_TO_COUPANG_COURIER,
        "count": len(NAVER_TO_COUPANG_COURIER)
    }


@router.get("/couriers/convert")
async def convert_courier_code(
    naver_name: str = Query(..., description="네이버 택배사명")
):
    """네이버 택배사명 → 쿠팡 코드 변환"""
    code = get_coupang_courier_code(naver_name)

    return {
        "naver_name": naver_name,
        "coupang_code": code,
        "found": code is not None
    }


# ========== Debug API ==========

@router.get("/debug/naver-login-status")
async def get_naver_login_status():
    """네이버 로그인 상태 확인"""
    try:
        scraper = await get_scraper()
        return await scraper.get_login_status()
    except Exception as e:
        return {"is_logged_in": False, "error": str(e)}


@router.get("/debug/logs")
async def get_sync_logs(
    limit: int = Query(50, ge=1, le=200)
):
    """동기화 로그 조회"""
    return {
        "success": True,
        "logs": scrape_logger.get_logs(limit),
        "total_count": len(scrape_logger.logs)
    }
