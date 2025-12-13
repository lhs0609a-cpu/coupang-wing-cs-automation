"""
네이버페이 배송 추적 API 라우터
"""
import logging
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.models.delivery import NaverPayDelivery, NaverPaySchedule
from app.services.naverpay_scraper import get_scraper, reset_scraper
from app.services.delivery_tracker import (
    get_tracking_url,
    get_all_couriers,
    get_courier_name,
    normalize_courier_name
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/naverpay", tags=["NaverPay Delivery"])


# ========== Pydantic Models ==========

class LoginRequest(BaseModel):
    username: str
    password: str


class DeliveryResponse(BaseModel):
    id: int
    recipient: str
    courier: str
    tracking_number: str
    product_name: Optional[str]
    order_date: Optional[str]
    collected_at: Optional[str]
    collected_date: str
    tracking_url: Optional[str] = None


class ScheduleRequest(BaseModel):
    schedule_type: str  # "interval" or "cron"
    interval_minutes: Optional[int] = None
    cron_expression: Optional[str] = None


class DeliveryStats(BaseModel):
    total_count: int
    today_count: int
    courier_stats: dict
    recent_dates: List[str]


# ========== Login API ==========

@router.post("/login")
async def login(request: LoginRequest):
    """네이버 로그인"""
    try:
        scraper = await get_scraper()
        result = await scraper.login(request.username, request.password)
        return result
    except Exception as e:
        logger.error(f"로그인 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout():
    """로그아웃 및 브라우저 종료"""
    try:
        await reset_scraper()
        return {"success": True, "message": "로그아웃 완료"}
    except Exception as e:
        logger.error(f"로그아웃 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/login-status")
async def get_login_status():
    """로그인 상태 확인"""
    try:
        scraper = await get_scraper()
        return await scraper.get_login_status()
    except Exception as e:
        return {"is_logged_in": False, "username": None}


# ========== Scraping API ==========

@router.post("/scrape")
async def scrape_deliveries(db: Session = Depends(get_db)):
    """배송 정보 스크래핑 (동기식)"""
    try:
        scraper = await get_scraper()
        deliveries = await scraper.scrape_deliveries_sync()

        # DB에 저장
        today = date.today().isoformat()
        saved_count = 0

        for delivery in deliveries:
            # 중복 체크
            existing = db.query(NaverPayDelivery).filter(
                NaverPayDelivery.tracking_number == delivery["tracking_number"],
                NaverPayDelivery.collected_date == today
            ).first()

            if not existing:
                new_delivery = NaverPayDelivery(
                    recipient=delivery["recipient"],
                    courier=normalize_courier_name(delivery["courier"]),
                    tracking_number=delivery["tracking_number"],
                    product_name=delivery.get("product_name"),
                    order_date=delivery.get("order_date"),
                    collected_date=today
                )
                db.add(new_delivery)
                saved_count += 1

        db.commit()

        return {
            "success": True,
            "total_found": len(deliveries),
            "new_saved": saved_count,
            "deliveries": deliveries
        }

    except Exception as e:
        logger.error(f"스크래핑 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scrape/stream")
async def scrape_deliveries_stream(db: Session = Depends(get_db)):
    """배송 정보 스크래핑 (SSE 스트리밍)"""

    async def event_generator():
        try:
            scraper = await get_scraper()
            today = date.today().isoformat()
            saved_count = 0

            async for result in scraper.scrape_deliveries():
                if result["type"] == "delivery":
                    # DB에 저장
                    delivery = result["data"]
                    existing = db.query(NaverPayDelivery).filter(
                        NaverPayDelivery.tracking_number == delivery["tracking_number"],
                        NaverPayDelivery.collected_date == today
                    ).first()

                    if not existing:
                        new_delivery = NaverPayDelivery(
                            recipient=delivery["recipient"],
                            courier=normalize_courier_name(delivery["courier"]),
                            tracking_number=delivery["tracking_number"],
                            product_name=delivery.get("product_name"),
                            collected_date=today
                        )
                        db.add(new_delivery)
                        db.commit()
                        saved_count += 1
                        result["data"]["is_new"] = True
                    else:
                        result["data"]["is_new"] = False

                yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'summary', 'new_saved': saved_count})}\n\n"

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


# ========== Deliveries API ==========

@router.get("/deliveries", response_model=List[DeliveryResponse])
async def get_deliveries(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    courier: Optional[str] = Query(None, description="택배사 필터"),
    db: Session = Depends(get_db)
):
    """저장된 배송 정보 조회"""
    try:
        query = db.query(NaverPayDelivery)

        if start_date:
            query = query.filter(NaverPayDelivery.collected_date >= start_date)
        if end_date:
            query = query.filter(NaverPayDelivery.collected_date <= end_date)
        if courier:
            query = query.filter(NaverPayDelivery.courier == courier)

        deliveries = query.order_by(NaverPayDelivery.collected_at.desc()).all()

        result = []
        for d in deliveries:
            item = d.to_dict()
            item["tracking_url"] = get_tracking_url(d.courier, d.tracking_number)
            result.append(item)

        return result

    except Exception as e:
        logger.error(f"배송 정보 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deliveries/dates")
async def get_collection_dates(db: Session = Depends(get_db)):
    """수집 날짜 목록 조회"""
    try:
        from sqlalchemy import func, distinct

        dates = db.query(
            distinct(NaverPayDelivery.collected_date)
        ).order_by(NaverPayDelivery.collected_date.desc()).all()

        return [d[0] for d in dates]

    except Exception as e:
        logger.error(f"날짜 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deliveries/stats")
async def get_delivery_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> DeliveryStats:
    """배송 통계 조회"""
    try:
        from sqlalchemy import func

        query = db.query(NaverPayDelivery)
        today = date.today().isoformat()

        if start_date:
            query = query.filter(NaverPayDelivery.collected_date >= start_date)
        if end_date:
            query = query.filter(NaverPayDelivery.collected_date <= end_date)

        total_count = query.count()

        today_count = db.query(NaverPayDelivery).filter(
            NaverPayDelivery.collected_date == today
        ).count()

        # 택배사별 통계
        courier_stats = {}
        courier_counts = db.query(
            NaverPayDelivery.courier,
            func.count(NaverPayDelivery.id)
        ).group_by(NaverPayDelivery.courier).all()

        for courier, count in courier_counts:
            courier_stats[courier] = count

        # 최근 수집 날짜
        recent_dates = db.query(
            NaverPayDelivery.collected_date
        ).distinct().order_by(
            NaverPayDelivery.collected_date.desc()
        ).limit(7).all()

        return DeliveryStats(
            total_count=total_count,
            today_count=today_count,
            courier_stats=courier_stats,
            recent_dates=[d[0] for d in recent_dates]
        )

    except Exception as e:
        logger.error(f"통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/deliveries/{delivery_id}")
async def delete_delivery(delivery_id: int, db: Session = Depends(get_db)):
    """배송 정보 삭제"""
    try:
        delivery = db.query(NaverPayDelivery).filter(
            NaverPayDelivery.id == delivery_id
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


@router.delete("/deliveries/cleanup")
async def cleanup_old_deliveries(
    days: int = Query(90, description="보관 기간(일)"),
    db: Session = Depends(get_db)
):
    """오래된 배송 정보 삭제"""
    try:
        from datetime import timedelta

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        deleted = db.query(NaverPayDelivery).filter(
            NaverPayDelivery.collected_date < cutoff_date
        ).delete()

        db.commit()

        return {
            "success": True,
            "deleted_count": deleted,
            "cutoff_date": cutoff_date
        }

    except Exception as e:
        logger.error(f"정리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Tracking API ==========

@router.get("/tracking-url/{courier}/{tracking_number}")
async def get_tracking_url_api(courier: str, tracking_number: str):
    """택배 추적 URL 생성"""
    url = get_tracking_url(courier, tracking_number)
    if not url:
        raise HTTPException(status_code=400, detail="지원하지 않는 택배사입니다")

    return {"tracking_url": url, "courier": courier, "tracking_number": tracking_number}


@router.get("/couriers")
async def get_couriers():
    """지원 택배사 목록"""
    return get_all_couriers()


# ========== Schedule API ==========

@router.post("/schedule")
async def create_schedule(request: ScheduleRequest, db: Session = Depends(get_db)):
    """수집 스케줄 생성 (APScheduler 연동)"""
    try:
        import uuid
        from app.scheduler import get_scheduler

        job_id = f"naverpay_scrape_{uuid.uuid4().hex[:8]}"

        # APScheduler에 실제 작업 등록
        scheduler = get_scheduler()
        success = scheduler.add_naverpay_schedule(
            job_id=job_id,
            schedule_type=request.schedule_type,
            interval_minutes=request.interval_minutes,
            cron_expression=request.cron_expression
        )

        if not success:
            raise HTTPException(status_code=400, detail="스케줄 등록 실패")

        # DB에 저장
        schedule = NaverPaySchedule(
            job_id=job_id,
            schedule_type=request.schedule_type,
            interval_minutes=request.interval_minutes,
            cron_expression=request.cron_expression,
            is_active=1
        )

        db.add(schedule)
        db.commit()

        return {
            "success": True,
            "job_id": job_id,
            "message": "스케줄 생성 완료",
            "schedule_type": request.schedule_type,
            "interval_minutes": request.interval_minutes,
            "cron_expression": request.cron_expression
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/list")
async def list_schedules(db: Session = Depends(get_db)):
    """스케줄 목록 조회 (APScheduler 상태 포함)"""
    try:
        from app.scheduler import get_scheduler

        # DB에서 스케줄 조회
        db_schedules = db.query(NaverPaySchedule).all()

        # APScheduler에서 실제 실행 상태 가져오기
        scheduler = get_scheduler()
        running_jobs = {job['id']: job for job in scheduler.get_naverpay_schedules()}

        result = []
        for s in db_schedules:
            schedule_dict = s.to_dict()
            # APScheduler 상태 병합
            if s.job_id in running_jobs:
                schedule_dict['next_run'] = running_jobs[s.job_id].get('next_run')
                schedule_dict['is_registered'] = True
                schedule_dict['is_paused'] = running_jobs[s.job_id].get('is_paused', False)
            else:
                schedule_dict['is_registered'] = False
                schedule_dict['is_paused'] = False
            result.append(schedule_dict)

        return result

    except Exception as e:
        logger.error(f"스케줄 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedule/{job_id}")
async def delete_schedule(job_id: str, db: Session = Depends(get_db)):
    """스케줄 삭제 (APScheduler에서도 제거)"""
    try:
        from app.scheduler import get_scheduler

        schedule = db.query(NaverPaySchedule).filter(
            NaverPaySchedule.job_id == job_id
        ).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")

        # APScheduler에서 제거
        scheduler = get_scheduler()
        scheduler.remove_naverpay_schedule(job_id)

        # DB에서 삭제
        db.delete(schedule)
        db.commit()

        return {"success": True, "message": "스케줄 삭제 완료"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/{job_id}/toggle")
async def toggle_schedule(job_id: str, db: Session = Depends(get_db)):
    """스케줄 활성화/비활성화 토글 (APScheduler pause/resume)"""
    try:
        from app.scheduler import get_scheduler

        schedule = db.query(NaverPaySchedule).filter(
            NaverPaySchedule.job_id == job_id
        ).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")

        scheduler = get_scheduler()

        if schedule.is_active:
            # 비활성화
            scheduler.pause_naverpay_schedule(job_id)
            schedule.is_active = 0
        else:
            # 활성화
            scheduler.resume_naverpay_schedule(job_id)
            schedule.is_active = 1

        db.commit()

        return {
            "success": True,
            "is_active": bool(schedule.is_active),
            "message": "활성화됨" if schedule.is_active else "일시정지됨"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 토글 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/history")
async def get_schedule_history(
    limit: int = Query(50, description="조회 개수"),
    db: Session = Depends(get_db)
):
    """스케줄 실행 이력 조회"""
    try:
        from app.models.delivery import NaverPayScheduleHistory

        history = db.query(NaverPayScheduleHistory).order_by(
            NaverPayScheduleHistory.executed_at.desc()
        ).limit(limit).all()

        return [h.to_dict() for h in history]

    except Exception as e:
        logger.error(f"실행 이력 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/{job_id}/run-now")
async def run_schedule_now(job_id: str, db: Session = Depends(get_db)):
    """스케줄 즉시 실행"""
    try:
        from app.scheduler import get_scheduler

        schedule = db.query(NaverPaySchedule).filter(
            NaverPaySchedule.job_id == job_id
        ).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")

        scheduler = get_scheduler()
        scheduler.auto_scrape_naverpay()

        # 마지막 실행 시간 업데이트
        schedule.last_run_at = datetime.now()
        db.commit()

        return {"success": True, "message": "즉시 실행 완료"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"즉시 실행 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Export API ==========

@router.get("/export/csv")
async def export_to_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """CSV 파일 내보내기"""
    import csv
    import io

    try:
        query = db.query(NaverPayDelivery)

        if start_date:
            query = query.filter(NaverPayDelivery.collected_date >= start_date)
        if end_date:
            query = query.filter(NaverPayDelivery.collected_date <= end_date)

        deliveries = query.order_by(NaverPayDelivery.collected_at.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)

        # 헤더
        writer.writerow(['수령인', '택배사', '송장번호', '상품명', '주문일', '수집일'])

        # 데이터
        for d in deliveries:
            writer.writerow([
                d.recipient,
                d.courier,
                d.tracking_number,
                d.product_name or '',
                d.order_date or '',
                d.collected_date
            ])

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=deliveries_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )

    except Exception as e:
        logger.error(f"CSV 내보내기 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
