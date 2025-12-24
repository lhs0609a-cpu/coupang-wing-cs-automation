# 개발자 가이드

## 빠른 시작

### 1. 로컬 개발 환경 설정

```bash
# 1. 저장소 클론
cd coupang-wing-cs-automation

# 2. 가상환경 생성 및 활성화
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값 설정

# 5. 데이터베이스 초기화
python -c "from app.database import init_db; init_db()"

# 6. 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 2. Docker로 시작 (권장)

```bash
# 1. 환경 변수 설정
cp .env.example .env

# 2. Docker Compose로 모든 서비스 실행
docker-compose -f docker-compose.dev.yml up

# 백그라운드 실행
docker-compose -f docker-compose.dev.yml up -d

# 로그 확인
docker-compose -f docker-compose.dev.yml logs -f backend
```

## 테스트 실행

### 전체 테스트
```bash
cd backend
pytest
```

### 특정 카테고리 테스트
```bash
# 단위 테스트만
pytest -m unit

# 통합 테스트만
pytest -m integration

# 느린 테스트 제외
pytest -m "not slow"
```

### 코드 커버리지
```bash
# HTML 리포트 생성
pytest --cov=app --cov-report=html

# 브라우저에서 확인
# htmlcov/index.html 열기
```

### 특정 파일/함수 테스트
```bash
# 특정 파일
pytest tests/test_cache.py

# 특정 함수
pytest tests/test_cache.py::test_cache_set_get

# Verbose 모드
pytest -v
```

## 새 기능 개발

### 1. 새 API 엔드포인트 추가

```python
# backend/app/routers/my_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..core.errors import raise_not_found
from ..core.cache import cached

router = APIRouter(prefix="/my-feature", tags=["My Feature"])

@router.get("/items/{item_id}")
@cached(ttl=300, key_prefix="item")
def get_item(item_id: int, db: Session = Depends(get_db)):
    """아이템 조회"""
    item = db.query(Item).get(item_id)

    if not item:
        raise_not_found("Item", item_id)

    return item

@router.post("/items")
def create_item(data: ItemCreate, db: Session = Depends(get_db)):
    """아이템 생성"""
    from ..services.monitoring import get_monitor
    monitor = get_monitor()

    # 모니터링
    monitor.log_user_action(
        user_id="system",
        action="item_create",
        item_data=data.dict()
    )

    item = Item(**data.dict())
    db.add(item)
    db.commit()

    return item
```

```python
# backend/app/main.py에 라우터 등록
from .routers import my_router

app.include_router(my_router.router, prefix="/api")
```

### 2. 새 서비스 추가

```python
# backend/app/services/my_service.py
from sqlalchemy.orm import Session
from loguru import logger

class MyService:
    """내 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def do_something(self, data):
        """무언가 수행"""
        logger.info(f"Doing something with {data}")

        # 비즈니스 로직
        result = self._process(data)

        # 모니터링
        from ..services.monitoring import get_monitor
        monitor = get_monitor()
        monitor.log_user_action(
            user_id="system",
            action="my_action",
            result=result
        )

        return result
```

### 3. 테스트 작성

```python
# backend/tests/test_my_feature.py
import pytest

@pytest.mark.unit
def test_get_item(client, sample_item):
    """아이템 조회 테스트"""
    response = client.get(f"/api/my-feature/items/{sample_item.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_item.id

@pytest.mark.unit
def test_get_nonexistent_item(client):
    """존재하지 않는 아이템 조회"""
    response = client.get("/api/my-feature/items/99999")

    assert response.status_code == 404
    data = response.json()
    assert data["error"] is True
    assert data["error_code"] == "ERR_1002"

# 픽스처 추가 (conftest.py)
@pytest.fixture
def sample_item(test_db):
    """샘플 아이템 생성"""
    item = Item(name="Test Item", value=100)
    test_db.add(item)
    test_db.commit()
    test_db.refresh(item)
    return item
```

## 에러 처리

### 표준 에러 발생

```python
from app.core.errors import (
    raise_not_found,
    raise_validation_error,
    raise_permission_denied,
    ValidationException,
    DatabaseException
)

# 리소스 미발견
raise_not_found("User", user_id)

# 검증 에러
raise_validation_error("Invalid email", email=email)

# 권한 부족
raise_permission_denied("Admin access required")

# 커스텀 예외
raise ValidationException(
    "Invalid input",
    details={"field": "email", "value": email}
)
```

### 에러 응답 형식

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "error": true,
  "error_code": "ERR_1002",
  "message": "User not found",
  "details": {
    "resource": "User",
    "id": "123"
  },
  "trace_id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## 캐싱 사용

### 함수 결과 캐싱

```python
from app.core.cache import cached, cache_template

@cached(ttl=300, key_prefix="stats")
def get_statistics():
    """통계 조회 (5분 캐싱)"""
    return expensive_calculation()

@cache_template(ttl=3600)
def get_template(template_id: int):
    """템플릿 조회 (1시간 캐싱)"""
    return db.query(Template).get(template_id)
```

### 캐시 무효화

```python
from app.core.cache import cache_invalidate

# 특정 prefix를 가진 모든 캐시 삭제
cache_invalidate("template:")
cache_invalidate("user:123:")
```

### 캐시 통계

```python
from app.core.cache import get_cache

cache = get_cache()
stats = cache.get_stats()
# {
#   "hits": 150,
#   "misses": 50,
#   "hit_rate": 0.75,
#   "size": 100
# }
```

## 배치 작업 추적

### 배치 작업 생성

```python
from app.services.batch_tracker import get_batch_tracker

tracker = get_batch_tracker()

# 작업 생성
job_id = tracker.create_job(
    job_type="bulk_approve",
    total_items=100,
    metadata={"user_id": 123}
)

# 작업 시작
tracker.start_job(job_id)

# 항목 처리
for item in items:
    try:
        result = process_item(item)
        tracker.add_result(
            job_id,
            item_id=item.id,
            success=True,
            message="Processed successfully"
        )
    except Exception as e:
        tracker.add_result(
            job_id,
            item_id=item.id,
            success=False,
            message=str(e),
            details={"error": str(e)}
        )

# 작업 완료
tracker.complete_job(job_id)
```

### 진행률 조회

```bash
# API로 조회
GET /api/batch/jobs/{job_id}

# Response:
{
  "job_id": "...",
  "status": "running",
  "progress_percent": 65.5,
  "processed_items": 65,
  "failed_items": 1,
  "total_items": 100,
  "timing": {
    "elapsed_seconds": 120,
    "eta_seconds": 60
  }
}
```

## 모니터링

### 이벤트 로깅

```python
from app.services.monitoring import get_monitor

monitor = get_monitor()

# 네트워크 연결
monitor.log_network_connection_attempt("https://api.example.com")
monitor.log_network_connection_success("https://api.example.com", duration_ms=150)

# 데이터베이스
monitor.log_db_query("SELECT", "inquiries", duration_ms=25)

# 사용자 액션
monitor.log_user_action(
    user_id="user123",
    action="inquiry_created",
    resource="inquiry",
    resource_id=456
)

# 에러
monitor.log_exception(
    exception_type="ValueError",
    message="Invalid input",
    stack_trace=traceback.format_exc()
)
```

### 모니터링 대시보드

```bash
# 성능 메트릭
GET /api/monitoring/metrics

# 최근 이벤트
GET /api/monitoring/events?category=database&limit=50

# 알림 목록
GET /api/monitoring/alerts?hours=24

# 시스템 리소스
GET /api/monitoring/stats/system
```

## 유용한 팁

### 1. 디버깅

```python
# Loguru로 디버그 로깅
from loguru import logger

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")

# 변수 출력
logger.debug(f"Processing item: {item}")

# 예외 로깅
try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed")  # 스택 트레이스 포함
```

### 2. API 문서

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- OpenAPI JSON: http://localhost:8080/openapi.json

### 3. Rate Limit 테스트

```python
# Rate limit 초과 테스트
for i in range(100):
    response = client.get("/api/inquiries")
    print(f"Request {i}: {response.status_code}")
    print(f"Remaining: {response.headers.get('X-RateLimit-Remaining-Minute')}")
```

### 4. 트러블슈팅

```bash
# 로그 확인
tail -f backend/logs/app.log

# trace_id로 에러 추적
grep "a1b2c3d4" backend/logs/app.log

# 데이터베이스 초기화
python -c "from app.database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"

# 캐시 초기화
python -c "from app.core.cache import get_cache; get_cache().clear()"
```

## 코드 스타일

### 1. Import 순서

```python
# 표준 라이브러리
import os
from datetime import datetime

# 서드파티
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 로컬
from ..database import get_db
from ..models import Inquiry
from ..core.errors import raise_not_found
```

### 2. 타입 힌트

```python
from typing import List, Dict, Optional

def process_items(
    items: List[int],
    options: Optional[Dict[str, str]] = None
) -> Dict[str, int]:
    """항목 처리"""
    return {"processed": len(items)}
```

### 3. Docstring

```python
def complex_function(param1: str, param2: int) -> Dict:
    """
    복잡한 함수

    Args:
        param1: 첫 번째 파라미터 설명
        param2: 두 번째 파라미터 설명

    Returns:
        결과 딕셔너리

    Raises:
        ValueError: param2가 0일 때
    """
    pass
```

## 기여하기

1. 브랜치 생성: `git checkout -b feature/my-feature`
2. 코드 작성 및 테스트
3. 커밋: `git commit -m "Add my feature"`
4. 푸시: `git push origin feature/my-feature`
5. Pull Request 생성

## 문의

문제가 발생하면:
1. `IMPROVEMENTS.md` 확인
2. 로그 파일 확인
3. 모니터링 대시보드 확인
4. 이슈 생성
