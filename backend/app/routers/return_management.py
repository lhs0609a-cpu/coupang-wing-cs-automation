"""
Return Management Router
반품 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from ..database import get_db
from ..services.coupang_api_client import CoupangAPIClient
from ..services.naver_smartstore_automation import NaverSmartStoreAutomation
from ..services.naver_pay_automation import NaverPayAutomation
from ..services.auto_return_collector import AutoReturnCollector
from ..services.auto_return_processor import AutoReturnProcessor
from ..models.return_log import ReturnLog
from ..models.coupang_account import CoupangAccount
from ..models.auto_return_config import AutoReturnConfig
from ..config import settings


router = APIRouter(
    prefix="/returns",
    tags=["returns"]
)


# Pydantic 모델
class ReturnRequestParams(BaseModel):
    """반품 요청 조회 파라미터"""
    start_date: str = Field(..., description="시작일 (yyyy-MM-ddTHH:mm)")
    end_date: str = Field(..., description="종료일 (yyyy-MM-ddTHH:mm)")
    status: Optional[str] = Field(None, description="RU, UC, CC, PR")
    cancel_type: Optional[str] = Field(None, description="RETURN, CANCEL, 또는 None (전체 조회)")


class NaverCredentials(BaseModel):
    """네이버 계정 정보"""
    username: str = Field(..., description="네이버 아이디")
    password: str = Field(..., description="네이버 비밀번호")


class ProcessReturnRequest(BaseModel):
    """반품 처리 요청"""
    return_log_ids: List[int] = Field(..., description="처리할 반품 로그 ID 목록")
    naver_credentials: NaverCredentials
    headless: bool = Field(True, description="백그라운드 실행 여부")


class AutoReturnConfigUpdate(BaseModel):
    """자동화 설정 업데이트"""
    enabled: Optional[bool] = None
    fetch_enabled: Optional[bool] = None
    fetch_interval_minutes: Optional[int] = None
    fetch_lookback_hours: Optional[int] = None
    process_enabled: Optional[bool] = None
    process_interval_minutes: Optional[int] = None
    process_batch_size: Optional[int] = None
    auto_process_statuses: Optional[List[str]] = None
    exclude_statuses: Optional[List[str]] = None
    max_retry_count: Optional[int] = None
    retry_delay_seconds: Optional[List[int]] = None
    notify_on_failure: Optional[bool] = None
    notify_on_success: Optional[bool] = None
    notification_email: Optional[str] = None
    use_headless: Optional[bool] = None
    selenium_timeout: Optional[int] = None


# API 엔드포인트

@router.get("/fetch-from-coupang")
async def fetch_returns_from_coupang(
    params: ReturnRequestParams = Depends(),
    db: Session = Depends(get_db)
):
    """
    쿠팡에서 반품/출고중지 요청 목록 조회 및 DB 저장
    """
    try:
        logger.info(f"쿠팡 반품 조회 시작: {params.start_date} ~ {params.end_date}")

        # 데이터베이스에서 쿠팡 계정 가져오기
        coupang_account = db.query(CoupangAccount).first()

        if not coupang_account:
            raise HTTPException(
                status_code=400,
                detail="쿠팡 계정이 등록되지 않았습니다. '계정 설정'에서 쿠팡 API 키를 등록해주세요."
            )

        # 쿠팡 API 클라이언트 (데이터베이스 계정 사용)
        coupang_client = CoupangAPIClient(
            access_key=coupang_account.access_key,
            secret_key=coupang_account.secret_key,
            vendor_id=coupang_account.vendor_id
        )

        # 반품 목록 조회
        result = coupang_client.get_return_requests(
            start_date=params.start_date,
            end_date=params.end_date,
            status=params.status,
            cancel_type=params.cancel_type
        )

        if not result or "data" not in result:
            return {
                "success": False,
                "message": "조회 결과 없음",
                "count": 0
            }

        return_data = result["data"]
        logger.info(f"조회된 반품 건수: {len(return_data)}")

        # DB에 저장
        saved_count = 0
        updated_count = 0

        for item in return_data:
            try:
                receipt_id = item.get("receiptId")
                order_id = str(item.get("orderId"))

                # returnItems 배열 처리 - 각 항목을 별도로 저장
                return_items = item.get("returnItems", [])

                if not return_items:
                    logger.warning(f"Receipt {receipt_id}: returnItems 없음, 스킵")
                    continue

                # 수령인 정보 추출
                receiver_name = item.get("requesterName")
                receiver_phone = item.get("requesterPhoneNumber")
                receiver_real_phone = item.get("requesterRealPhoneNumber")
                receiver_address = item.get("requesterAddress")
                receiver_address_detail = item.get("requesterAddressDetail")
                receiver_zipcode = item.get("requesterZipCode")

                # 시간 파싱
                coupang_created_at = None
                coupang_modified_at = None
                try:
                    if item.get("createdAt"):
                        coupang_created_at = datetime.fromisoformat(item.get("createdAt").replace("Z", "+00:00"))
                    if item.get("modifiedAt"):
                        coupang_modified_at = datetime.fromisoformat(item.get("modifiedAt").replace("Z", "+00:00"))
                except:
                    pass

                # 완료 확인 시간 파싱
                complete_confirm_date = None
                try:
                    if item.get("completeConfirmDate"):
                        complete_confirm_date = datetime.fromisoformat(item.get("completeConfirmDate").replace("Z", "+00:00"))
                except:
                    pass

                # 반품 배송비 파싱
                return_shipping_charge = None
                return_shipping_charge_currency = None
                shipping_charge_obj = item.get("returnShippingCharge")
                if shipping_charge_obj:
                    try:
                        units = shipping_charge_obj.get("units", 0)
                        nanos = shipping_charge_obj.get("nanos", 0)
                        return_shipping_charge = float(units) + (float(nanos) / 1_000_000_000)
                        return_shipping_charge_currency = shipping_charge_obj.get("currencyCode")
                    except:
                        pass

                # 동봉 배송비 파싱
                enclose_price = None
                enclose_price_currency = None
                enclose_obj = item.get("enclosePrice")
                if enclose_obj:
                    try:
                        units = enclose_obj.get("units", 0)
                        nanos = enclose_obj.get("nanos", 0)
                        enclose_price = float(units) + (float(nanos) / 1_000_000_000)
                        enclose_price_currency = enclose_obj.get("currencyCode")
                    except:
                        pass

                # 각 returnItem마다 별도의 ReturnLog 생성
                for return_item in return_items:
                    product_name = return_item.get("vendorItemName") or return_item.get("vendorItemPackageName", "")
                    vendor_item_id = str(return_item.get("vendorItemId"))
                    cancel_count = return_item.get("cancelCount", 1)

                    # 기존 레코드 확인 (receipt_id + vendor_item_id 조합으로)
                    existing = db.query(ReturnLog).filter(
                        ReturnLog.coupang_receipt_id == receipt_id,
                        ReturnLog.vendor_item_id == vendor_item_id
                    ).first()

                    if existing:
                        # 업데이트
                        existing.receipt_status = item.get("receiptStatus")
                        existing.coupang_modified_at = coupang_modified_at
                        existing.receiver_name = receiver_name
                        existing.receiver_phone = receiver_phone
                        existing.receiver_real_phone = receiver_real_phone
                        existing.receiver_address = receiver_address
                        existing.receiver_address_detail = receiver_address_detail
                        existing.receiver_zipcode = receiver_zipcode
                        existing.complete_confirm_type = item.get("completeConfirmType")
                        existing.complete_confirm_date = complete_confirm_date
                        existing.return_delivery_dtos = item.get("returnDeliveryDtos")
                        existing.raw_data = item
                        existing.updated_at = datetime.now()
                        updated_count += 1
                        logger.debug(f"Updated: {product_name} (receipt {receipt_id})")
                    else:
                        # 신규 생성
                        new_log = ReturnLog(
                            # 쿠팡 정보
                            coupang_receipt_id=receipt_id,
                            coupang_order_id=order_id,
                            coupang_payment_id=str(item.get("paymentId")),
                            coupang_created_at=coupang_created_at,
                            coupang_modified_at=coupang_modified_at,

                            # 상품 정보
                            product_name=product_name,
                            vendor_item_id=vendor_item_id,
                            vendor_item_package_id=return_item.get("vendorItemPackageId"),
                            vendor_item_package_name=return_item.get("vendorItemPackageName"),
                            seller_product_id=return_item.get("sellerProductId"),
                            seller_product_name=return_item.get("sellerProductName"),
                            cancel_count=cancel_count,
                            cancel_count_sum=item.get("cancelCountSum"),
                            purchase_count=return_item.get("purchaseCount"),
                            shipment_box_id=return_item.get("shipmentBoxId"),
                            release_status=return_item.get("releaseStatus"),

                            # 수령인/회수지 정보
                            receiver_name=receiver_name,
                            receiver_phone=receiver_phone,
                            receiver_real_phone=receiver_real_phone,
                            receiver_address=receiver_address,
                            receiver_address_detail=receiver_address_detail,
                            receiver_zipcode=receiver_zipcode,

                            # 반품 상태
                            receipt_type=item.get("receiptType"),
                            receipt_status=item.get("receiptStatus"),
                            release_stop_status=item.get("releaseStopStatus"),

                            # 반품 사유
                            cancel_reason_category1=item.get("cancelReasonCategory1"),
                            cancel_reason_category2=item.get("cancelReasonCategory2"),
                            cancel_reason=item.get("cancelReason"),
                            reason_code=item.get("reasonCode"),
                            reason_code_text=item.get("reasonCodeText"),

                            # 귀책 및 환불 정보
                            fault_by_type=item.get("faultByType"),
                            pre_refund=item.get("preRefund"),
                            return_shipping_charge=return_shipping_charge,
                            return_shipping_charge_currency=return_shipping_charge_currency,
                            enclose_price=enclose_price,
                            enclose_price_currency=enclose_price_currency,

                            # 배송 정보
                            return_delivery_id=item.get("returnDeliveryId"),
                            return_delivery_type=item.get("returnDeliveryType"),
                            return_delivery_dtos=item.get("returnDeliveryDtos"),

                            # 완료 확인 정보
                            complete_confirm_type=item.get("completeConfirmType"),
                            complete_confirm_date=complete_confirm_date,
                            cancel_complete_user=return_item.get("cancelCompleteUser"),

                            # 네이버 처리 정보
                            naver_processed=False,
                            status="pending",
                            raw_data=item
                        )

                        db.add(new_log)
                        saved_count += 1
                        logger.debug(f"Created: {product_name} (receipt {receipt_id})")

            except Exception as e:
                logger.error(f"반품 로그 저장 오류 (receipt {receipt_id}): {str(e)}")
                import traceback
                traceback.print_exc()
                db.rollback()
                continue

        # 모든 처리 완료 후 한번에 커밋
        db.commit()
        logger.success(f"저장 완료 - 신규: {saved_count}, 업데이트: {updated_count}")

        return {
            "success": True,
            "message": f"조회 및 저장 완료",
            "total_fetched": saved_count + updated_count,  # 실제 저장/업데이트된 항목 수
            "saved": saved_count,
            "updated": updated_count,
            "api_response_count": len(return_data)  # API에서 받은 레코드 수
        }

    except Exception as e:
        logger.error(f"쿠팡 반품 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fetch-by-receipt/{receipt_id}")
async def fetch_return_by_receipt_id(
    receipt_id: int,
    db: Session = Depends(get_db)
):
    """
    쿠팡에서 반품요청 단건 조회 (receiptId로 조회)

    Args:
        receipt_id: 반품 접수번호

    Returns:
        반품 상세 정보

    Raises:
        400: receiptId가 vendorId에 속하지 않거나 찾을 수 없는 경우 (철회된 경우 포함)
    """
    try:
        logger.info(f"쿠팡 반품 단건 조회: receiptId={receipt_id}")

        # 데이터베이스에서 쿠팡 계정 가져오기
        coupang_account = db.query(CoupangAccount).first()

        if not coupang_account:
            raise HTTPException(
                status_code=400,
                detail="쿠팡 계정이 등록되지 않았습니다. '계정 설정'에서 쿠팡 API 키를 등록해주세요."
            )

        # 쿠팡 API 클라이언트
        coupang_client = CoupangAPIClient(
            access_key=coupang_account.access_key,
            secret_key=coupang_account.secret_key,
            vendor_id=coupang_account.vendor_id
        )

        # 단건 조회
        result = coupang_client.get_return_request_by_receipt_id(receipt_id)

        if not result or "data" not in result:
            raise HTTPException(
                status_code=404,
                detail=f"receiptId {receipt_id}를 찾을 수 없습니다."
            )

        return_data = result["data"]

        # 응답이 배열인 경우 첫 번째 항목 반환
        if isinstance(return_data, list) and len(return_data) > 0:
            return_info = return_data[0]
        else:
            return_info = return_data

        logger.info(f"반품 단건 조회 성공: receiptId={receipt_id}, status={return_info.get('receiptStatus')}")

        return {
            "success": True,
            "data": return_info
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"쿠팡 반품 단건 조회 오류: {error_msg}")

        # 400 에러인 경우 (철회된 경우 등)
        if "400" in error_msg or "ReceiptId doesn't belong" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=f"receiptId {receipt_id}가 유효하지 않거나 철회되었습니다. 반품철회 이력을 확인해주세요."
            )

        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/list")
async def get_return_logs(
    status: Optional[str] = None,
    naver_processed: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    반품 로그 목록 조회
    """
    try:
        query = db.query(ReturnLog)

        if status:
            query = query.filter(ReturnLog.status == status)

        if naver_processed is not None:
            query = query.filter(ReturnLog.naver_processed == naver_processed)

        # 최신순 정렬
        query = query.order_by(ReturnLog.created_at.desc())

        # 페이지네이션
        total = query.count()
        logs = query.offset(offset).limit(limit).all()

        return {
            "success": True,
            "total": total,
            "offset": offset,
            "limit": limit,
            "data": [
                {
                    "id": log.id,
                    "coupang_receipt_id": log.coupang_receipt_id,
                    "coupang_order_id": log.coupang_order_id,
                    "product_name": log.product_name,
                    "receiver_name": log.receiver_name,
                    "receiver_phone": log.receiver_phone,
                    "receipt_type": log.receipt_type,
                    "receipt_status": log.receipt_status,
                    "cancel_count": log.cancel_count,
                    "cancel_reason_category1": log.cancel_reason_category1,
                    "cancel_reason_category2": log.cancel_reason_category2,
                    "naver_processed": log.naver_processed,
                    "naver_processed_at": log.naver_processed_at.isoformat() if log.naver_processed_at else None,
                    "naver_process_type": log.naver_process_type,
                    "status": log.status,
                    "created_at": log.created_at.isoformat(),
                    "updated_at": log.updated_at.isoformat()
                }
                for log in logs
            ]
        }

    except Exception as e:
        logger.error(f"반품 로그 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/confirm-receive/{receipt_id}")
async def confirm_return_receive(
    receipt_id: int,
    db: Session = Depends(get_db)
):
    """
    반품상품 입고 확인처리

    receiptStatus가 RETURNS_UNCHECKED (반품접수) 상태인 반품 건에 대해 처리합니다.

    처리 후:
    - 빠른환불 대상: 바로 환불 및 반품 승인/완료 처리
    - 빠른환불 미대상: 추가로 '반품 요청 승인 처리' 필요

    Args:
        receipt_id: 반품 접수번호

    Note:
        빠른환불 대상 상품: 일반 배송이면서 상품 가격이 10만원 미만
        (신선식품, 주문제작 상품 등은 제외)
    """
    try:
        logger.info(f"반품 입고 확인 처리: receiptId={receipt_id}")

        # 쿠팡 계정 조회
        coupang_account = db.query(CoupangAccount).first()
        if not coupang_account:
            raise HTTPException(
                status_code=400,
                detail="쿠팡 계정이 등록되지 않았습니다."
            )

        # API 클라이언트
        coupang_client = CoupangAPIClient(
            access_key=coupang_account.access_key,
            secret_key=coupang_account.secret_key,
            vendor_id=coupang_account.vendor_id
        )

        # 입고 확인 처리
        result = coupang_client.confirm_return_receive(receipt_id)

        # DB 업데이트
        return_log = db.query(ReturnLog).filter(
            ReturnLog.coupang_receipt_id == receipt_id
        ).first()

        if return_log:
            return_log.receipt_status = "VENDOR_WAREHOUSE_CONFIRM"
            return_log.updated_at = datetime.now()
            db.commit()
            logger.info(f"DB 업데이트 완료: receiptId={receipt_id}")

        logger.success(f"입고 확인 처리 성공: receiptId={receipt_id}")

        return {
            "success": True,
            "message": "반품 입고 확인 처리가 완료되었습니다.",
            "receipt_id": receipt_id,
            "api_response": result
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"입고 확인 처리 오류: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@router.put("/approve/{receipt_id}")
async def approve_return_request(
    receipt_id: int,
    cancel_count: int,
    db: Session = Depends(get_db)
):
    """
    반품요청 승인 처리

    receiptStatus가 VENDOR_WAREHOUSE_CONFIRM (입고완료) 상태인 반품 건에 대해 처리합니다.
    [입고 확인 처리] 후, [반품 승인 처리]를 진행하면 환불 처리됩니다.

    Args:
        receipt_id: 반품 접수번호
        cancel_count: 반품접수 수량 (반품 목록 조회에서 확인한 수량과 일치해야 함)

    Note:
        - 선환불(빠른환불) 정책에 의해 환불처리된 경우: API 호출 불필요
        - 입고확인 완료 후 일정 시간 경과 시: 쿠팡 시스템이 자동 승인 (API 호출 불필요)
    """
    try:
        logger.info(f"반품 승인 처리: receiptId={receipt_id}, cancelCount={cancel_count}")

        # 쿠팡 계정 조회
        coupang_account = db.query(CoupangAccount).first()
        if not coupang_account:
            raise HTTPException(
                status_code=400,
                detail="쿠팡 계정이 등록되지 않았습니다."
            )

        # API 클라이언트
        coupang_client = CoupangAPIClient(
            access_key=coupang_account.access_key,
            secret_key=coupang_account.secret_key,
            vendor_id=coupang_account.vendor_id
        )

        # 반품 승인 처리
        result = coupang_client.approve_return_request(receipt_id, cancel_count)

        # DB 업데이트
        return_log = db.query(ReturnLog).filter(
            ReturnLog.coupang_receipt_id == receipt_id
        ).first()

        if return_log:
            return_log.receipt_status = "RETURNS_COMPLETED"
            return_log.status = "completed"
            return_log.updated_at = datetime.now()
            db.commit()
            logger.info(f"DB 업데이트 완료: receiptId={receipt_id}")

        logger.success(f"반품 승인 처리 성공: receiptId={receipt_id}")

        return {
            "success": True,
            "message": "반품 승인 처리가 완료되었습니다. 환불이 진행됩니다.",
            "receipt_id": receipt_id,
            "cancel_count": cancel_count,
            "api_response": result
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"반품 승인 처리 오류: {error_msg}")

        # 상세한 에러 메시지 처리
        if "이미 반품이 완료" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=f"이미 반품이 완료되었습니다. receiptId={receipt_id}"
            )
        elif "취소반품접수내역이 존재하지 않습니다" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=f"반품 접수내역이 존재하지 않거나 철회되었습니다. receiptId={receipt_id}"
            )
        elif "cancelCount가 일치하지 않습니다" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=f"반품 수량이 일치하지 않습니다. 입력한 수량: {cancel_count}"
            )

        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/process-naver")
async def process_naver_returns(
    request: ProcessReturnRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    네이버 스마트스토어 반품/취소 처리
    """
    try:
        # 처리할 로그 조회
        logs = db.query(ReturnLog).filter(
            ReturnLog.id.in_(request.return_log_ids),
            ReturnLog.naver_processed == False
        ).all()

        if not logs:
            return {
                "success": False,
                "message": "처리할 반품 로그가 없습니다."
            }

        logger.info(f"네이버 처리 시작: {len(logs)}건")

        # 네이버 자동화 서비스
        naver_automation = NaverSmartStoreAutomation(
            username=request.naver_credentials.username,
            password=request.naver_credentials.password,
            headless=request.headless
        )

        # 처리할 아이템 리스트 생성
        return_items = []
        for log in logs:
            return_items.append({
                "product_name": log.product_name,
                "coupang_order_id": log.coupang_order_id,
                "receipt_status": log.receipt_status,
                "return_reason": f"{log.cancel_reason_category1} - {log.cancel_reason_category2}"
            })

            # 상태 업데이트 (처리 중)
            log.status = "processing"
            db.commit()

        # 배치 처리 실행
        result = naver_automation.process_coupang_returns_batch(return_items)

        # 처리 결과 업데이트
        for log in logs:
            if result.get("success"):
                log.naver_processed = True
                log.naver_processed_at = datetime.now()
                log.status = "completed"

                # 처리 타입 설정
                if log.receipt_status == "RELEASE_STOP_UNCHECKED":
                    log.naver_process_type = "ORDER_CANCEL"
                else:
                    log.naver_process_type = "RETURN_REQUEST"

                log.naver_result = result.get("message")
            else:
                log.status = "failed"
                log.naver_error = result.get("message")

            db.commit()

        return {
            "success": result.get("success"),
            "message": result.get("message"),
            "statistics": result.get("statistics")
        }

    except Exception as e:
        logger.error(f"네이버 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_return_statistics(db: Session = Depends(get_db)):
    """
    반품 처리 통계
    """
    try:
        total = db.query(ReturnLog).count()
        pending = db.query(ReturnLog).filter(ReturnLog.status == "pending").count()
        processing = db.query(ReturnLog).filter(ReturnLog.status == "processing").count()
        completed = db.query(ReturnLog).filter(ReturnLog.status == "completed").count()
        failed = db.query(ReturnLog).filter(ReturnLog.status == "failed").count()

        naver_processed = db.query(ReturnLog).filter(ReturnLog.naver_processed == True).count()
        naver_pending = db.query(ReturnLog).filter(ReturnLog.naver_processed == False).count()

        # 최근 24시간 통계
        yesterday = datetime.now() - timedelta(hours=24)
        recent_24h = db.query(ReturnLog).filter(ReturnLog.created_at >= yesterday).count()

        return {
            "success": True,
            "statistics": {
                "total": total,
                "status": {
                    "pending": pending,
                    "processing": processing,
                    "completed": completed,
                    "failed": failed
                },
                "naver": {
                    "processed": naver_processed,
                    "pending": naver_pending
                },
                "recent_24h": recent_24h
            }
        }

    except Exception as e:
        logger.error(f"통계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{return_log_id}")
async def delete_return_log(return_log_id: int, db: Session = Depends(get_db)):
    """
    반품 로그 삭제
    """
    try:
        log = db.query(ReturnLog).filter(ReturnLog.id == return_log_id).first()

        if not log:
            raise HTTPException(status_code=404, detail="반품 로그를 찾을 수 없습니다.")

        db.delete(log)
        db.commit()

        return {
            "success": True,
            "message": "반품 로그가 삭제되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"반품 로그 삭제 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 자동화 설정 API

@router.get("/automation/config")
async def get_automation_config(db: Session = Depends(get_db)):
    """
    자동화 설정 조회
    """
    try:
        config = db.query(AutoReturnConfig).first()

        if not config:
            # 기본 설정 생성
            default_values = AutoReturnConfig.get_default_config()
            config = AutoReturnConfig(**default_values)
            db.add(config)
            db.commit()
            db.refresh(config)

        return {
            "success": True,
            "config": config.to_dict()
        }

    except Exception as e:
        logger.error(f"자동화 설정 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/automation/config")
async def update_automation_config(
    config_update: AutoReturnConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    자동화 설정 업데이트
    """
    try:
        config = db.query(AutoReturnConfig).first()

        if not config:
            # 설정이 없으면 기본값으로 생성
            default_values = AutoReturnConfig.get_default_config()
            config = AutoReturnConfig(**default_values)
            db.add(config)

        # 업데이트할 필드만 변경
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        config.updated_at = datetime.now()
        db.commit()
        db.refresh(config)

        return {
            "success": True,
            "message": "자동화 설정이 업데이트되었습니다.",
            "config": config.to_dict()
        }

    except Exception as e:
        logger.error(f"자동화 설정 업데이트 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/run-collector")
async def run_auto_collector(db: Session = Depends(get_db)):
    """
    자동 수집 즉시 실행 (테스트용)
    """
    try:
        collector = AutoReturnCollector(db)
        result = collector.collect_returns()

        return {
            "success": result["success"],
            "message": result["message"],
            "data": result
        }

    except Exception as e:
        logger.error(f"자동 수집 실행 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/run-processor")
async def run_auto_processor(db: Session = Depends(get_db)):
    """
    자동 처리 즉시 실행 (테스트용)
    """
    try:
        processor = AutoReturnProcessor(db)
        result = processor.process_pending_returns()

        return {
            "success": result["success"],
            "message": result["message"],
            "data": result
        }

    except Exception as e:
        logger.error(f"자동 처리 실행 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/retry-failed")
async def retry_failed_returns(
    max_count: int = 10,
    db: Session = Depends(get_db)
):
    """
    실패한 반품 재처리
    """
    try:
        processor = AutoReturnProcessor(db)
        result = processor.retry_failed_returns(max_count=max_count)

        return {
            "success": result["success"],
            "message": result["message"],
            "data": result
        }

    except Exception as e:
        logger.error(f"실패 건 재처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automation/statistics")
async def get_automation_statistics(db: Session = Depends(get_db)):
    """
    자동화 통계 조회
    """
    try:
        processor = AutoReturnProcessor(db)
        stats = processor.get_processing_statistics()

        return {
            "success": True,
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"자동화 통계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
