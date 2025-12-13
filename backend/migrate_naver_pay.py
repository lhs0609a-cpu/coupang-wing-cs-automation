"""
네이버페이 기반 반품 처리를 위한 DB 마이그레이션
ReturnLog 테이블에 receiver_name, receiver_phone 컬럼 추가
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from sqlalchemy import text
from loguru import logger


def migrate():
    """DB 마이그레이션 실행"""
    logger.info("네이버페이 반품 처리 마이그레이션 시작...")

    db = SessionLocal()
    try:
        # receiver_name 컬럼 추가
        try:
            db.execute(text(
                "ALTER TABLE return_logs ADD COLUMN receiver_name VARCHAR(100)"
            ))
            logger.success("receiver_name 컬럼 추가 완료")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                logger.info("receiver_name 컬럼이 이미 존재합니다. 스킵.")
            else:
                logger.error(f"receiver_name 컬럼 추가 실패: {str(e)}")
                raise

        # receiver_phone 컬럼 추가
        try:
            db.execute(text(
                "ALTER TABLE return_logs ADD COLUMN receiver_phone VARCHAR(50)"
            ))
            logger.success("receiver_phone 컬럼 추가 완료")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                logger.info("receiver_phone 컬럼이 이미 존재합니다. 스킵.")
            else:
                logger.error(f"receiver_phone 컬럼 추가 실패: {str(e)}")
                raise

        db.commit()

        logger.success("마이그레이션 완료!")
        logger.info("\n다음 단계:")
        logger.info("1. 쿠팡에서 반품 조회 시 수령인 정보가 자동으로 저장됩니다")
        logger.info("2. 네이버페이(https://pay.naver.com/pc/history)에서 상품명+수령인으로 매칭")
        logger.info("3. 자동 반품 처리 실행")

    except Exception as e:
        logger.error(f"마이그레이션 중 오류 발생: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
