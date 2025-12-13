"""
Automation API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from loguru import logger

from ..database import get_db
from ..services.auto_workflow import AutoWorkflow
from ..config import settings
from ..services.ai_response_generator import AIResponseGenerator

router = APIRouter(prefix="/automation", tags=["automation"])


class AutoWorkflowRequest(BaseModel):
    limit: int = 10
    auto_submit: bool = True


@router.post("/run-full-workflow")
def run_full_workflow(
    request: AutoWorkflowRequest,
    db: Session = Depends(get_db)
):
    """
    Run complete automated workflow:
    1. Collect inquiries
    2. Analyze inquiries
    3. Generate AI responses
    4. Validate responses
    5. Auto-approve if safe
    6. Auto-submit to Coupang (if enabled)
    """
    try:
        workflow = AutoWorkflow(db)
        results = workflow.run_full_auto_workflow(
            limit=request.limit,
            auto_submit=request.auto_submit
        )
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-process-and-submit")
def auto_process_and_submit(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Automatically process and submit responses (convenience endpoint)
    """
    try:
        workflow = AutoWorkflow(db)
        results = workflow.auto_process_and_submit(limit=limit)
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-pending-approvals")
def process_pending_approvals(db: Session = Depends(get_db)):
    """
    Process all pending approvals and auto-approve/submit safe ones
    """
    try:
        workflow = AutoWorkflow(db)
        results = workflow.process_pending_approvals()
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_automation_stats(db: Session = Depends(get_db)):
    """
    Get automation statistics
    """
    try:
        workflow = AutoWorkflow(db)
        stats = workflow.get_workflow_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chatgpt/status")
def get_chatgpt_status():
    """
    Check ChatGPT (OpenAI) API connection status
    """
    try:
        # Check if API key is configured
        if not settings.OPENAI_API_KEY:
            return {
                "connected": False,
                "status": "disconnected",
                "message": "OpenAI API 키가 설정되지 않았습니다",
                "model": None
            }

        # Try to initialize the AI Response Generator
        try:
            generator = AIResponseGenerator()
            if generator.client is None:
                return {
                    "connected": False,
                    "status": "disconnected",
                    "message": "OpenAI 클라이언트 초기화 실패",
                    "model": None
                }

            # Try a simple API call to verify connection
            response = generator.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": "test"}
                ],
                max_tokens=5
            )

            return {
                "connected": True,
                "status": "connected",
                "message": "ChatGPT API에 성공적으로 연결되었습니다",
                "model": settings.OPENAI_MODEL
            }
        except Exception as e:
            error_message = str(e)
            logger.error(f"ChatGPT connection test failed: {error_message}")
            return {
                "connected": False,
                "status": "error",
                "message": f"API 연결 실패: {error_message}",
                "model": settings.OPENAI_MODEL
            }
    except Exception as e:
        logger.error(f"Error checking ChatGPT status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chatgpt/test-connection")
def test_chatgpt_connection():
    """
    Test ChatGPT connection and try to establish it
    """
    try:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요."
            )

        generator = AIResponseGenerator()

        if generator.client is None:
            raise HTTPException(
                status_code=500,
                detail="OpenAI 클라이언트를 초기화할 수 없습니다"
            )

        # Test with a simple request
        response = generator.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "user", "content": "안녕하세요"}
            ],
            max_tokens=10
        )

        logger.info("ChatGPT connection test successful")

        return {
            "success": True,
            "connected": True,
            "message": "ChatGPT API 연결에 성공했습니다",
            "model": settings.OPENAI_MODEL,
            "test_response": response.choices[0].message.content
        }
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        logger.error(f"ChatGPT connection test failed: {error_message}")
        raise HTTPException(
            status_code=500,
            detail=f"연결 테스트 실패: {error_message}"
        )
