"""
Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys

from .config import settings
from .database import init_db, engine
from .routers import inquiries, responses, automation, wing_web, advanced, ux_features, websocket, monitoring, batch, port_management, coupang_api, coupang_accounts, return_management, naver_api, naver_accounts, account_sets, promotion, naver_review, naverpay_delivery, naver_shopping, upload_monitoring, gpt_settings, issue_response, naver_delivery_sync, auto_mode
from .scheduler import get_scheduler
from .services.monitoring import get_monitor

# Import error handlers
from .core.errors import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler
)
from fastapi.exceptions import RequestValidationError

# Import middlewares
from .middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware
)


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI application
    """
    monitor = get_monitor()

    # Startup
    monitor.log_app_startup(version="1.0.0")
    logger.info("Starting Coupang Wing CS Automation System...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database
    try:
        import time
        start_time = time.time()
        monitor.log_db_connection_attempt()

        init_db()

        duration_ms = (time.time() - start_time) * 1000
        monitor.log_db_connection_success(duration_ms)
        logger.success("Database initialized successfully")
    except Exception as e:
        monitor.log_db_connection_failure(str(e))
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    # Start scheduler if enabled
    if getattr(settings, 'AUTO_START_SCHEDULER', True):
        try:
            scheduler = get_scheduler()
            scheduler.start()
            logger.success("Automation scheduler started")
        except Exception as e:
            monitor.log_exception("SchedulerError", str(e))
            logger.error(f"Failed to start scheduler: {str(e)}")

    monitor.log_app_ready()
    logger.success("Application ready to serve requests")

    yield

    # Shutdown
    monitor.log_app_shutdown(graceful=True)
    logger.info("Shutting down...")

    # Stop scheduler
    try:
        scheduler = get_scheduler()
        if scheduler.is_running:
            scheduler.stop()
            logger.info("Scheduler stopped")
    except:
        pass

    engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="Coupang Wing CS Automation API",
    description="Automated customer service response system for Coupang Wing",
    version="1.0.0",
    lifespan=lifespan
)


# Add custom middlewares (order matters - last added = first executed)
# Rate limiting first (innermost)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS - MUST BE LAST (so it executes FIRST)
# Allow all origins for production deployment (Vercel frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)

# Register error handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Include routers
app.include_router(inquiries.router, prefix="/api")
app.include_router(responses.router, prefix="/api")
app.include_router(automation.router, prefix="/api")
app.include_router(wing_web.router, prefix="/api")
app.include_router(coupang_api.router, prefix="/api")
app.include_router(coupang_accounts.router, prefix="/api")
app.include_router(advanced.router, prefix="/api")
app.include_router(ux_features.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
app.include_router(port_management.router, prefix="/api")
app.include_router(return_management.router, prefix="/api")
app.include_router(naver_api.router, prefix="/api")
app.include_router(naver_accounts.router, prefix="/api")
app.include_router(account_sets.router, prefix="/api")
app.include_router(promotion.router, prefix="/api")
app.include_router(naver_review.router, prefix="/api")
app.include_router(naverpay_delivery.router, prefix="/api")
app.include_router(naver_shopping.router, prefix="/api")
app.include_router(upload_monitoring.router, prefix="/api")
app.include_router(gpt_settings.router, prefix="/api")
app.include_router(issue_response.router, prefix="/api")
app.include_router(naver_delivery_sync.router, prefix="/api")
app.include_router(auto_mode.router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
def root():
    """Root endpoint - Dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>쿠팡 윙 CS 자동화 시스템</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
                max-width: 800px;
                width: 100%;
            }
            h1 {
                color: #333;
                font-size: 2.5em;
                margin-bottom: 10px;
                text-align: center;
            }
            .subtitle {
                color: #666;
                text-align: center;
                margin-bottom: 40px;
                font-size: 1.1em;
            }
            .status {
                background: #10b981;
                color: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                margin-bottom: 30px;
                font-size: 1.2em;
            }
            .links {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            .link-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 15px;
                text-decoration: none;
                text-align: center;
                transition: transform 0.3s, box-shadow 0.3s;
                cursor: pointer;
            }
            .link-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            .link-card h3 {
                font-size: 1.3em;
                margin-bottom: 10px;
            }
            .link-card p {
                font-size: 0.9em;
                opacity: 0.9;
            }
            .info {
                background: #f3f4f6;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
            }
            .info-item {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #e5e7eb;
            }
            .info-item:last-child { border-bottom: none; }
            .label { color: #666; font-weight: 500; }
            .value { color: #333; font-weight: bold; }
            .footer {
                text-align: center;
                color: #999;
                font-size: 0.9em;
                margin-top: 30px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 쿠팡 윙 CS 자동화</h1>
            <div class="subtitle">고객 문의 자동 응답 시스템</div>

            <div class="status">
                ✅ 시스템 정상 작동 중
            </div>

            <div class="links">
                <a href="/docs" class="link-card">
                    <h3>📚 API 문서</h3>
                    <p>Swagger UI</p>
                </a>
                <a href="/redoc" class="link-card">
                    <h3>📖 API 가이드</h3>
                    <p>ReDoc</p>
                </a>
                <a href="/health" class="link-card">
                    <h3>💚 헬스체크</h3>
                    <p>시스템 상태</p>
                </a>
                <a href="/api/system/stats" class="link-card">
                    <h3>📊 통계</h3>
                    <p>시스템 통계</p>
                </a>
            </div>

            <div class="info">
                <div class="info-item">
                    <span class="label">서비스명</span>
                    <span class="value">Coupang Wing CS Automation</span>
                </div>
                <div class="info-item">
                    <span class="label">버전</span>
                    <span class="value">v1.0.0</span>
                </div>
                <div class="info-item">
                    <span class="label">환경</span>
                    <span class="value">""" + settings.ENVIRONMENT + """</span>
                </div>
                <div class="info-item">
                    <span class="label">포트</span>
                    <span class="value">8000</span>
                </div>
            </div>

            <div class="footer">
                © 2024 Coupang Wing CS Automation System
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    monitor = get_monitor()
    metrics = monitor.get_performance_metrics()

    healthy = (
        metrics['error_rate'] < 0.1 and
        metrics['memory_percent'] < 90 and
        metrics['cpu_percent'] < 90
    )

    monitor.log_health_check(healthy, metrics)

    return {
        "status": "healthy" if healthy else "degraded",
        "database": "connected",
        "uptime_seconds": metrics['uptime_seconds'],
        "error_rate": metrics['error_rate']
    }


@app.get("/api/system/stats")
def get_system_stats():
    """Get overall system statistics"""
    from .database import SessionLocal
    from .services import InquiryCollector, ResponseSubmitter

    db = SessionLocal()
    try:
        collector = InquiryCollector(db)
        submitter = ResponseSubmitter(db)

        inquiry_stats = collector.get_inquiry_stats()
        submission_stats = submitter.get_submission_stats()

        return {
            "inquiries": inquiry_stats,
            "submissions": submission_stats
        }
    finally:
        db.close()


@app.post("/api/system/process-pipeline")
def run_full_pipeline(limit: int = 10):
    """
    Run the full processing pipeline:
    1. Collect inquiries
    2. Analyze inquiries
    3. Generate responses
    4. Validate responses
    """
    from .database import SessionLocal
    from .services import (
        InquiryCollector,
        InquiryAnalyzer,
        ResponseGenerator,
        ResponseValidator
    )

    db = SessionLocal()
    try:
        results = {
            "collected": 0,
            "analyzed": 0,
            "generated": 0,
            "validated": 0,
            "errors": []
        }

        # Step 1: Collect inquiries
        try:
            collector = InquiryCollector(db)
            inquiries = collector.collect_new_inquiries()
            results["collected"] = len(inquiries)
            logger.info(f"Collected {len(inquiries)} inquiries")
        except Exception as e:
            logger.error(f"Error collecting inquiries: {str(e)}")
            results["errors"].append(f"Collection error: {str(e)}")

        # Step 2 & 3: Analyze and generate responses for pending inquiries
        pending = collector.get_pending_inquiries(limit=limit)

        analyzer = InquiryAnalyzer(db)
        generator = ResponseGenerator(db)
        validator = ResponseValidator(db)

        for inquiry in pending:
            try:
                # Analyze
                analysis = analyzer.analyze_inquiry(inquiry)
                results["analyzed"] += 1

                # Check if requires human
                if inquiry.requires_human:
                    logger.warning(f"Inquiry {inquiry.id} requires human review")
                    continue

                # Generate response
                response = generator.generate_response(inquiry)
                if response:
                    results["generated"] += 1

                    # Validate
                    validation = validator.validate_response(response, inquiry)
                    if validation["passed"]:
                        results["validated"] += 1

            except Exception as e:
                logger.error(f"Error processing inquiry {inquiry.id}: {str(e)}")
                results["errors"].append(f"Inquiry {inquiry.id}: {str(e)}")

        return {"success": True, "results": results}

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    response = JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )
    # Add CORS headers to error response
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG
    )
