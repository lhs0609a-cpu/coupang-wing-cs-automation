"""
Database Migration Script
데이터베이스 마이그레이션 스크립트
"""
from app.database import init_db
# Import all models to register them with SQLAlchemy
from app.models import (
    inquiry_log,
    response_log,
    automation_log,
    coupang_account,
    return_log,
    naver_account
)

if __name__ == "__main__":
    print("🔄 데이터베이스 마이그레이션 시작...")
    try:
        init_db()
        print("✅ 데이터베이스 마이그레이션 완료!")
        print("   - 모든 테이블이 생성되었습니다.")
        print("   - naver_accounts 테이블")
        print("   - return_logs 테이블")
        print("   - inquiry_logs 테이블")
        print("   - response_logs 테이블")
        print("   - automation_logs 테이블")
        print("   - coupang_accounts 테이블")
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
