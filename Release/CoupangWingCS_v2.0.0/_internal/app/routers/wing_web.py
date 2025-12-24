"""
Wing Web Automation Router
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger
from typing import Optional
from ..services.wing_web_automation import WingWebAutomation
from ..config import settings


router = APIRouter(prefix="/wing-web", tags=["Wing Web Automation"])


class WebAutomationRequest(BaseModel):
    """Request model for web automation"""
    username: Optional[str] = None
    password: Optional[str] = None
    headless: bool = True


class WebAutomationResponse(BaseModel):
    """Response model for web automation"""
    success: bool
    message: str
    statistics: dict


@router.post("/auto-answer", response_model=WebAutomationResponse)
async def auto_answer_inquiries(request: WebAutomationRequest):
    """
    Automatically answer all inquiries on Coupang Wing website

    This endpoint will:
    1. Login to Coupang Wing
    2. Navigate to product inquiries page
    3. Read all inquiries
    4. Generate answers using ChatGPT
    5. Submit answers automatically

    Args:
        request: WebAutomationRequest with optional credentials and headless mode

    Returns:
        WebAutomationResponse with results
    """
    try:
        # Get credentials from request or environment
        username = request.username or settings.COUPANG_WING_USERNAME
        password = request.password or settings.COUPANG_WING_PASSWORD

        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="Username and password are required. Please provide them in the request or set COUPANG_WING_USERNAME and COUPANG_WING_PASSWORD in .env file"
            )

        logger.info(f"Starting web automation (headless={request.headless})...")

        # Create automation instance
        automation = WingWebAutomation(
            username=username,
            password=password,
            headless=request.headless
        )

        # Run full automation
        results = automation.run_full_automation()

        return WebAutomationResponse(
            success=results['success'],
            message=results['message'],
            statistics=results.get('statistics', {})
        )

    except Exception as e:
        logger.error(f"Error in auto_answer_inquiries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-login")
async def test_login(request: WebAutomationRequest):
    """
    Test login to Coupang Wing

    Args:
        request: WebAutomationRequest with credentials

    Returns:
        Login test result
    """
    try:
        username = request.username or settings.COUPANG_WING_USERNAME
        password = request.password or settings.COUPANG_WING_PASSWORD

        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="Username and password are required"
            )

        logger.info("Testing login...")

        automation = WingWebAutomation(
            username=username,
            password=password,
            headless=request.headless
        )

        try:
            if not automation.setup_driver():
                return {"success": False, "message": "Failed to setup WebDriver"}

            if automation.login():
                return {"success": True, "message": "Login successful"}
            else:
                return {"success": False, "message": "Login failed"}
        finally:
            automation.cleanup()

    except Exception as e:
        logger.error(f"Error in test_login: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_automation_status():
    """
    Get automation service status

    Returns:
        Service status information
    """
    return {
        "service": "Wing Web Automation",
        "status": "available",
        "features": [
            "Automatic login to Coupang Wing",
            "Read product inquiries",
            "Generate answers using ChatGPT",
            "Submit answers automatically"
        ],
        "requirements": [
            "COUPANG_WING_USERNAME",
            "COUPANG_WING_PASSWORD",
            "OPENAI_API_KEY"
        ]
    }
