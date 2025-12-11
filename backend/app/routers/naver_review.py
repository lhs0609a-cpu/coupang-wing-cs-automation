"""
Naver Review Automation Router
네이버 리뷰 자동화 API 라우터
"""
import os
import uuid
import random
import threading
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from loguru import logger

from ..database import get_db, SessionLocal
from ..models import NaverAccount
from ..models.naver_review import (
    NaverReviewTemplate,
    NaverReviewLog,
    NaverReviewImage,
    NaverReviewStats
)
from ..services.naver_review_automation import (
    NaverReviewBot,
    get_bot_instance,
    create_bot_instance,
    stop_bot,
    SELENIUM_AVAILABLE
)

router = APIRouter(prefix="/naver-review", tags=["naver-review"])

# 업로드 설정
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "naver_review_uploads")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# 업로드 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 실시간 로그 저장 (메모리)
_realtime_logs = []
_max_logs = 500


# === Pydantic Models ===

class ReviewTemplateCreate(BaseModel):
    """리뷰 템플릿 생성"""
    star_rating: int = 5
    review_text: str
    image_paths: Optional[List[str]] = None


class ReviewTemplateUpdate(BaseModel):
    """리뷰 템플릿 수정"""
    star_rating: Optional[int] = None
    review_text: Optional[str] = None
    image_paths: Optional[List[str]] = None
    is_active: Optional[bool] = None


class StartAutomationRequest(BaseModel):
    """자동화 시작 요청"""
    naver_account_id: int
    login_method: str = "manual"  # "auto" or "manual"
    headless: bool = False


class ApplyImagesRequest(BaseModel):
    """이미지 랜덤 배분 요청"""
    min_images: int = 1
    max_images: int = 3


# === Helper Functions ===

def allowed_file(filename: str) -> bool:
    """허용된 파일 확장자 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_realtime_log(log_data: dict):
    """실시간 로그 추가"""
    global _realtime_logs
    _realtime_logs.append({
        **log_data,
        'timestamp': datetime.now().isoformat()
    })
    # 최대 로그 수 유지
    if len(_realtime_logs) > _max_logs:
        _realtime_logs = _realtime_logs[-_max_logs:]


def update_bot_status(status_data: dict):
    """봇 상태 업데이트 콜백"""
    # WebSocket으로 전송하는 로직 추가 가능
    logger.info(f"Bot status: {status_data}")


# === API Endpoints ===

@router.get("/status")
def get_status():
    """현재 봇 상태 조회"""
    bot = get_bot_instance()
    if bot:
        return bot.get_status()
    return {
        'is_running': False,
        'current': 0,
        'total': 0,
        'status': '대기 중',
        'session_id': None
    }


@router.get("/selenium-available")
def check_selenium():
    """Selenium 사용 가능 여부 확인"""
    return {
        "available": SELENIUM_AVAILABLE,
        "message": "Selenium is available" if SELENIUM_AVAILABLE else "Selenium is not installed"
    }


@router.post("/start")
def start_automation(
    request: StartAutomationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """자동화 시작"""
    if not SELENIUM_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Selenium이 설치되지 않았습니다. 서버에서 Selenium을 설치해주세요."
        )

    # 이미 실행 중인지 확인
    existing_bot = get_bot_instance()
    if existing_bot and existing_bot.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 자동화가 실행 중입니다."
        )

    # 네이버 계정 조회
    account = db.query(NaverAccount).filter(NaverAccount.id == request.naver_account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="네이버 계정을 찾을 수 없습니다."
        )

    # 리뷰 템플릿 조회
    templates = db.query(NaverReviewTemplate).filter(
        NaverReviewTemplate.is_active == True
    ).all()

    if not templates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="활성화된 리뷰 템플릿이 없습니다. 먼저 리뷰 템플릿을 추가해주세요."
        )

    # 리뷰 데이터 준비
    reviews = []
    for template in templates:
        image_paths = []
        if template.image_paths:
            for img_path in template.image_paths.split(";"):
                img_path = img_path.strip()
                if img_path:
                    # 상대 경로를 절대 경로로 변환
                    if not os.path.isabs(img_path):
                        img_path = os.path.join(UPLOAD_FOLDER, os.path.basename(img_path))
                    image_paths.append(img_path)

        reviews.append({
            'star_rating': template.star_rating,
            'review_text': template.review_text,
            'image_paths': image_paths
        })

    # 봇 생성 및 실행
    bot = create_bot_instance(
        log_callback=add_realtime_log,
        status_callback=update_bot_status
    )

    # 백그라운드에서 자동화 실행
    def run_bot():
        try:
            naver_id = account.naver_id or ""
            naver_pw = ""  # 보안상 비밀번호는 수동 입력 권장

            result = bot.run_automation(
                login_method=request.login_method,
                naver_id=naver_id,
                naver_pw=naver_pw,
                reviews=reviews,
                headless=request.headless
            )

            # 결과 저장
            try:
                session = SessionLocal()
                try:
                    # 일일 통계 업데이트
                    today = date.today()
                    stats = session.query(NaverReviewStats).filter(
                        func.date(NaverReviewStats.date) == today,
                        NaverReviewStats.naver_account_id == request.naver_account_id
                    ).first()

                    if not stats:
                        stats = NaverReviewStats(
                            date=datetime.combine(today, datetime.min.time()),
                            naver_account_id=request.naver_account_id
                        )
                        session.add(stats)

                    stats.total_reviews += result.get('completed', 0) + result.get('failed', 0)
                    stats.success_count += result.get('completed', 0)
                    stats.failed_count += result.get('failed', 0)
                    stats.total_points += result.get('total_points', 0)
                    session.commit()
                finally:
                    session.close()
            except Exception as e:
                logger.error(f"Failed to save stats: {e}")

            logger.info(f"Automation completed: {result}")
        except Exception as e:
            logger.error(f"Automation error: {e}")

    # 별도 스레드에서 실행
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()

    return {
        "success": True,
        "message": "자동화가 시작되었습니다.",
        "session_id": bot.session_id
    }


@router.post("/stop")
def stop_automation():
    """자동화 중지"""
    bot = get_bot_instance()
    if bot and bot.is_running:
        stop_bot()
        return {"success": True, "message": "자동화가 중지되었습니다."}
    return {"success": False, "message": "실행 중인 자동화가 없습니다."}


# === 리뷰 템플릿 API ===

@router.get("/templates")
def get_templates(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """리뷰 템플릿 목록 조회"""
    query = db.query(NaverReviewTemplate)
    if not include_inactive:
        query = query.filter(NaverReviewTemplate.is_active == True)

    templates = query.order_by(NaverReviewTemplate.created_at.desc()).all()
    return [t.to_dict() for t in templates]


@router.post("/templates", status_code=status.HTTP_201_CREATED)
def create_template(
    template: ReviewTemplateCreate,
    db: Session = Depends(get_db)
):
    """리뷰 템플릿 생성"""
    image_paths_str = ";".join(template.image_paths) if template.image_paths else None

    new_template = NaverReviewTemplate(
        star_rating=template.star_rating,
        review_text=template.review_text,
        image_paths=image_paths_str
    )

    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    logger.info(f"Created review template: {new_template.id}")
    return new_template.to_dict()


@router.put("/templates/{template_id}")
def update_template(
    template_id: int,
    template: ReviewTemplateUpdate,
    db: Session = Depends(get_db)
):
    """리뷰 템플릿 수정"""
    db_template = db.query(NaverReviewTemplate).filter(
        NaverReviewTemplate.id == template_id
    ).first()

    if not db_template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다.")

    if template.star_rating is not None:
        db_template.star_rating = template.star_rating
    if template.review_text is not None:
        db_template.review_text = template.review_text
    if template.image_paths is not None:
        db_template.image_paths = ";".join(template.image_paths) if template.image_paths else None
    if template.is_active is not None:
        db_template.is_active = template.is_active

    db.commit()
    db.refresh(db_template)

    return db_template.to_dict()


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """리뷰 템플릿 삭제"""
    template = db.query(NaverReviewTemplate).filter(
        NaverReviewTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다.")

    db.delete(template)
    db.commit()


# === 이미지 관리 API ===

@router.get("/images")
def get_images(db: Session = Depends(get_db)):
    """업로드된 이미지 목록 조회"""
    images = db.query(NaverReviewImage).filter(
        NaverReviewImage.is_active == True
    ).order_by(NaverReviewImage.created_at.desc()).all()

    return [img.to_dict() for img in images]


@router.post("/images")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """이미지 업로드"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")

    # 파일 크기 확인
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기가 16MB를 초과합니다.")

    # 고유 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    ext = file.filename.rsplit('.', 1)[1].lower()
    new_filename = f"{timestamp}_{unique_id}.{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, new_filename)

    # 파일 저장
    with open(file_path, "wb") as f:
        f.write(content)

    # DB에 저장
    image = NaverReviewImage(
        filename=new_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    logger.info(f"Uploaded image: {new_filename}")
    return image.to_dict()


@router.get("/images/file/{filename}")
def get_image_file(filename: str):
    """이미지 파일 서빙"""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    return FileResponse(file_path)


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """이미지 삭제"""
    image = db.query(NaverReviewImage).filter(NaverReviewImage.id == image_id).first()

    if not image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")

    # 파일 삭제
    if os.path.exists(image.file_path):
        os.remove(image.file_path)

    db.delete(image)
    db.commit()


@router.post("/images/apply-random")
def apply_random_images(
    request: ApplyImagesRequest,
    db: Session = Depends(get_db)
):
    """모든 템플릿에 이미지 랜덤 배분"""
    # 활성 이미지 조회
    images = db.query(NaverReviewImage).filter(
        NaverReviewImage.is_active == True
    ).all()

    if not images:
        raise HTTPException(status_code=400, detail="업로드된 이미지가 없습니다.")

    # 활성 템플릿 조회
    templates = db.query(NaverReviewTemplate).filter(
        NaverReviewTemplate.is_active == True
    ).all()

    if not templates:
        raise HTTPException(status_code=400, detail="활성화된 템플릿이 없습니다.")

    image_paths = [img.filename for img in images]
    updated_count = 0

    for template in templates:
        # 랜덤하게 이미지 선택
        num_images = random.randint(
            min(request.min_images, len(image_paths)),
            min(request.max_images, len(image_paths))
        )
        selected_images = random.sample(image_paths, num_images)
        template.image_paths = ";".join(selected_images)
        updated_count += 1

    db.commit()

    return {
        "success": True,
        "message": f"{updated_count}개 템플릿에 이미지 랜덤 배분 완료",
        "templates_updated": updated_count,
        "images_available": len(images)
    }


# === 로그 API ===

@router.get("/logs")
def get_logs(
    session_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """실행 로그 조회"""
    query = db.query(NaverReviewLog).order_by(NaverReviewLog.created_at.desc())

    if session_id:
        query = query.filter(NaverReviewLog.session_id == session_id)

    logs = query.limit(limit).all()
    return [log.to_dict() for log in logs]


@router.get("/logs/realtime")
def get_realtime_logs(limit: int = 100):
    """실시간 로그 조회 (메모리)"""
    return _realtime_logs[-limit:]


@router.delete("/logs/realtime")
def clear_realtime_logs():
    """실시간 로그 초기화"""
    global _realtime_logs
    _realtime_logs = []
    return {"success": True, "message": "로그가 초기화되었습니다."}


# === 통계 API ===

@router.get("/stats")
def get_stats(
    naver_account_id: Optional[int] = None,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """통계 조회"""
    from datetime import timedelta

    start_date = datetime.now() - timedelta(days=days)

    query = db.query(NaverReviewStats).filter(
        NaverReviewStats.date >= start_date
    )

    if naver_account_id:
        query = query.filter(NaverReviewStats.naver_account_id == naver_account_id)

    stats = query.order_by(NaverReviewStats.date.desc()).all()

    # 집계
    total_reviews = sum(s.total_reviews for s in stats)
    total_success = sum(s.success_count for s in stats)
    total_failed = sum(s.failed_count for s in stats)
    total_points = sum(s.total_points for s in stats)

    return {
        "summary": {
            "total_reviews": total_reviews,
            "success_count": total_success,
            "failed_count": total_failed,
            "total_points": total_points,
            "success_rate": round(total_success / total_reviews * 100, 1) if total_reviews > 0 else 0
        },
        "daily": [s.to_dict() for s in stats]
    }


@router.get("/stats/today")
def get_today_stats(
    naver_account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """오늘 통계 조회"""
    today = date.today()

    query = db.query(NaverReviewStats).filter(
        func.date(NaverReviewStats.date) == today
    )

    if naver_account_id:
        query = query.filter(NaverReviewStats.naver_account_id == naver_account_id)

    stats = query.all()

    total_reviews = sum(s.total_reviews for s in stats)
    total_success = sum(s.success_count for s in stats)
    total_points = sum(s.total_points for s in stats)

    return {
        "date": today.isoformat(),
        "total_reviews": total_reviews,
        "success_count": total_success,
        "total_points": total_points,
        "success_rate": round(total_success / total_reviews * 100, 1) if total_reviews > 0 else 0
    }
