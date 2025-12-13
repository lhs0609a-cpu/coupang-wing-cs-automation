"""
자동 반품 처리 기능을 위한 DB 마이그레이션 스크립트
AutoReturnConfig 테이블을 생성하고 기본 설정을 추가합니다.
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models.auto_return_config import AutoReturnConfig
from app.models.return_log import ReturnLog
from loguru import logger


def migrate():
    """DB 마이그레이션 실행"""
    logger.info("자동 반품 처리 기능 마이그레이션 시작...")

    try:
        # 1. 테이블 생성
        logger.info("테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        logger.success("테이블 생성 완료")

        # 2. 기본 설정 추가
        db = SessionLocal()
        try:
            # 기존 설정 확인
            existing_config = db.query(AutoReturnConfig).first()

            if existing_config:
                logger.info("기존 자동화 설정이 존재합니다. 스킵합니다.")
            else:
                logger.info("기본 자동화 설정 생성 중...")
                default_config = AutoReturnConfig.get_default_config()
                config = AutoReturnConfig(**default_config)
                db.add(config)
                db.commit()
                logger.success("기본 자동화 설정 생성 완료")

            # 3. 통계 출력
            total_returns = db.query(ReturnLog).count()
            pending_returns = db.query(ReturnLog).filter(
                ReturnLog.status == "pending",
                ReturnLog.naver_processed == False
            ).count()

            logger.info(f"현재 반품 로그 통계:")
            logger.info(f"  - 전체: {total_returns}건")
            logger.info(f"  - 대기: {pending_returns}건")

        finally:
            db.close()

        logger.success("마이그레이션 완료!")
        logger.info("\n다음 단계:")
        logger.info("1. 서버를 재시작하여 스케줄러를 활성화하세요")
        logger.info("2. API 엔드포인트 /returns/automation/config 에서 자동화 설정을 확인하세요")
        logger.info("3. enabled=true로 설정하여 자동화를 활성화하세요")

    except Exception as e:
        logger.error(f"마이그레이션 중 오류 발생: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    migrate()
