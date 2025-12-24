"""
Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys

from .config import settings
from .database import init_db, engine
from .routers import inquiries, responses, automation, wing_web


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
    # Startup
    logger.info("Starting Coupang Wing CS Automation System...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database
    try:
        init_db()
        logger.success("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")
    engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="Coupang Wing CS Automation API",
    description="Automated customer service response system for Coupang Wing",
    version="1.0.0",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(inquiries.router, prefix="/api")
app.include_router(responses.router, prefix="/api")
app.include_router(automation.router, prefix="/api")
app.include_router(wing_web.router, prefix="/api")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "Coupang Wing CS Automation API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected"
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
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG
    )
