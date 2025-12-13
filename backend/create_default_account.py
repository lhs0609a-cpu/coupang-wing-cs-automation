"""
기본 쿠팡 계정 자동 생성
"""
from app.database import SessionLocal
from app.models.coupang_account import CoupangAccount
from loguru import logger

def create_default_account():
    db = SessionLocal()
    try:
        # 기존 계정 확인
        existing = db.query(CoupangAccount).filter(
            CoupangAccount.vendor_id == "A00492891"
        ).first()

        if existing:
            logger.info(f"기존 쿠팡 계정이 이미 존재합니다: {existing.name} (ID: {existing.id})")

            # 기존 계정 업데이트
            existing.name = "반품 관리용 쿠팡 계정"
            existing.access_key = "A00492891"
            existing.secret_key = "534fcf1c8dfe9d5e222b507f52e772d4637738b7"
            existing.wing_username = "lhs0609"
            existing.is_active = True

            db.commit()
            logger.success(f"쿠팡 계정 업데이트 완료: {existing.name}")
            return existing
        else:
            # 새 계정 생성
            new_account = CoupangAccount(
                name="반품 관리용 쿠팡 계정",
                vendor_id="A00492891",
                wing_username="lhs0609"
            )

            # 암호화된 키 설정
            new_account.access_key = "A00492891"
            new_account.secret_key = "534fcf1c8dfe9d5e222b507f52e772d4637738b7"

            db.add(new_account)
            db.commit()
            db.refresh(new_account)

            logger.success(f"쿠팡 계정 생성 완료: {new_account.name} (ID: {new_account.id})")
            return new_account

    except Exception as e:
        db.rollback()
        logger.error(f"쿠팡 계정 생성/업데이트 실패: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_default_account()
