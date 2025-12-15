"""
GPT Settings API Router
GPT 응답 설정 관리 API
"""
import json
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/gpt-settings", tags=["gpt-settings"])

# 설정 파일 경로
SETTINGS_FILE = Path(__file__).resolve().parent.parent / "database" / "gpt_settings.json"


class GPTSettings(BaseModel):
    """GPT 설정 모델"""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 800
    top_p: float = 0.9
    frequency_penalty: float = 0.3
    presence_penalty: float = 0.3
    system_prompt: Optional[str] = None
    auto_approve_enabled: bool = False
    auto_approve_threshold: float = 90.0
    response_style: str = "formal"  # formal, casual, friendly


class GPTSettingsUpdate(BaseModel):
    """GPT 설정 업데이트 모델"""
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    system_prompt: Optional[str] = None
    auto_approve_enabled: Optional[bool] = None
    auto_approve_threshold: Optional[float] = None
    response_style: Optional[str] = None


# 기본 시스템 프롬프트
DEFAULT_SYSTEM_PROMPT = """당신은 쿠팡 판매자의 고객 응대 전문가입니다.

역할 및 책임:
- 고객 문의에 대해 정확하고 친절한 답변을 작성합니다
- 쿠팡의 정책과 가이드라인을 준수합니다
- 전문적이고 예의 바른 어투를 사용합니다

답변 작성 가이드라인:
1. 반드시 "안녕하세요, 고객님." 또는 "안녕하세요, [고객명]님."으로 시작
2. 고객의 문의 내용을 정확히 이해하고 답변
3. 구체적이고 명확한 정보 제공
4. 필요시 단계별 안내 제공
5. 반드시 "감사합니다." 또는 "감사드립니다."로 마무리

금지 사항:
- 100% 보장, 절대, 무조건 등의 단정적 표현 사용 금지
- 법적 자문 제공 금지
- 쿠팡 정책에 어긋나는 약속 금지
- 부정확한 정보 제공 금지"""


def load_settings() -> GPTSettings:
    """설정 파일에서 GPT 설정 로드"""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return GPTSettings(**data)
    except Exception as e:
        logger.error(f"설정 로드 오류: {e}")

    # 기본 설정 반환
    return GPTSettings(system_prompt=DEFAULT_SYSTEM_PROMPT)


def save_settings(settings: GPTSettings) -> bool:
    """GPT 설정을 파일에 저장"""
    try:
        # 디렉토리 생성
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings.model_dump(), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"설정 저장 오류: {e}")
        return False


@router.get("", response_model=GPTSettings)
def get_gpt_settings():
    """현재 GPT 설정 조회"""
    settings = load_settings()
    return settings


@router.put("", response_model=GPTSettings)
def update_gpt_settings(update: GPTSettingsUpdate):
    """GPT 설정 업데이트"""
    current = load_settings()

    # 제공된 필드만 업데이트
    update_data = update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            setattr(current, field, value)

    # 저장
    if save_settings(current):
        logger.info("GPT 설정 업데이트 완료")
        return current
    else:
        raise HTTPException(status_code=500, detail="설정 저장 실패")


@router.post("/reset")
def reset_gpt_settings():
    """GPT 설정을 기본값으로 리셋"""
    default = GPTSettings(system_prompt=DEFAULT_SYSTEM_PROMPT)

    if save_settings(default):
        return {"success": True, "message": "설정이 초기화되었습니다", "settings": default}
    else:
        raise HTTPException(status_code=500, detail="설정 초기화 실패")


@router.get("/models")
def get_available_models():
    """사용 가능한 GPT 모델 목록"""
    return {
        "models": [
            {"id": "gpt-4", "name": "GPT-4", "description": "가장 강력한 모델 (느림, 비용 높음)"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "빠른 GPT-4 (비용 중간)"},
            {"id": "gpt-4o", "name": "GPT-4o", "description": "최신 GPT-4 옴니 모델"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "경제적인 GPT-4o (빠름, 저렴)"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "빠르고 저렴한 모델"}
        ]
    }


@router.get("/response-styles")
def get_response_styles():
    """응답 스타일 목록"""
    return {
        "styles": [
            {"id": "formal", "name": "격식체", "description": "정중하고 공식적인 어투"},
            {"id": "friendly", "name": "친근체", "description": "따뜻하고 친근한 어투"},
            {"id": "casual", "name": "일반체", "description": "자연스럽고 편안한 어투"}
        ]
    }
