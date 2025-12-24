"""
.env 파일의 계정 정보를 데이터베이스에 자동 저장
"""
import sys
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

sys.path.insert(0, 'backend')

from backend.app.database import SessionLocal, engine, Base
from backend.app.models.coupang_account import CoupangAccount
from backend.app.models.naver_account import NaverAccount

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("\n" + "="*70)
    print(".env 파일의 계정 정보를 데이터베이스에 저장")
    print("="*70 + "\n")

    # 쿠팡 계정 정보 가져오기
    coupang_access_key = os.getenv("COUPANG_ACCESS_KEY")
    coupang_secret_key = os.getenv("COUPANG_SECRET_KEY")
    coupang_vendor_id = os.getenv("COUPANG_VENDOR_ID")
    coupang_username = os.getenv("COUPANG_WING_USERNAME")

    # 쿠팡 계정 저장
    if coupang_access_key and coupang_secret_key and coupang_vendor_id:
        # 기존 계정 확인
        existing_coupang = db.query(CoupangAccount).filter(
            CoupangAccount.vendor_id == coupang_vendor_id
        ).first()

        if existing_coupang:
            print(f"✅ 쿠팡 계정이 이미 존재합니다: {existing_coupang.name} (ID: {existing_coupang.id})")
            print(f"   Vendor ID: {existing_coupang.vendor_id}")
            print(f"   Access Key: {existing_coupang.access_key[:20]}...")

            # 업데이트
            existing_coupang.access_key = coupang_access_key
            existing_coupang.secret_key = coupang_secret_key
            if coupang_username:
                existing_coupang.wing_username = coupang_username
            existing_coupang.is_active = True
            db.commit()
            print("   → 최신 정보로 업데이트했습니다.\n")
        else:
            # 새로 생성
            new_coupang = CoupangAccount(
                name="쿠팡 기본 계정 (.env)",
                vendor_id=coupang_vendor_id,
                wing_username=coupang_username or coupang_vendor_id
            )
            new_coupang.access_key = coupang_access_key
            new_coupang.secret_key = coupang_secret_key

            db.add(new_coupang)
            db.commit()
            db.refresh(new_coupang)

            print(f"✅ 쿠팡 계정을 데이터베이스에 저장했습니다!")
            print(f"   ID: {new_coupang.id}")
            print(f"   이름: {new_coupang.name}")
            print(f"   Vendor ID: {new_coupang.vendor_id}\n")
    else:
        print("⚠️ .env 파일에 쿠팡 계정 정보가 없습니다.\n")

    print("-"*70 + "\n")

    # 현재 저장된 모든 계정 조회
    all_coupang = db.query(CoupangAccount).all()
    all_naver = db.query(NaverAccount).all()

    print(f"📦 데이터베이스에 저장된 쿠팡 계정: {len(all_coupang)}개")
    for acc in all_coupang:
        print(f"   - {acc.name} (Vendor: {acc.vendor_id}, 활성: {acc.is_active})")

    print(f"\n🟢 데이터베이스에 저장된 네이버 계정: {len(all_naver)}개")
    for acc in all_naver:
        print(f"   - {acc.name} (Username: {acc.naver_username}, 기본: {acc.is_default}, 활성: {acc.is_active})")

    print("\n" + "="*70)
    print("\n✅ 완료! 이제 프론트엔드에서 계정 정보를 불러올 수 있습니다.")
    print("\n📌 다음 단계:")
    print("   1. 백엔드 서버 시작: http://localhost:8000")
    print("   2. 프론트엔드 접속: http://localhost:3000")
    print("   3. 반품 관리 페이지에서 계정 정보가 자동으로 로드됩니다")
    print("="*70 + "\n")

except Exception as e:
    print(f"\n❌ 오류 발생: {str(e)}\n")
    import traceback
    traceback.print_exc()
    db.rollback()

finally:
    db.close()
