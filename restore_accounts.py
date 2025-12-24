"""
데이터베이스에서 계정 정보 복구 및 확인
"""
import sys
import os
sys.path.insert(0, 'backend')

from backend.app.database import SessionLocal, engine, Base
from backend.app.models.coupang_account import CoupangAccount
from backend.app.models.naver_account import NaverAccount

# 데이터베이스 테이블 생성 (없으면)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("\n" + "="*70)
    print("데이터베이스 계정 정보 복구 및 확인")
    print("="*70 + "\n")

    # 쿠팡 계정 조회
    coupang_accounts = db.query(CoupangAccount).all()
    print(f"📦 쿠팡 계정: {len(coupang_accounts)}개 발견")

    if coupang_accounts:
        for i, acc in enumerate(coupang_accounts, 1):
            print(f"\n  [{i}] {acc.name}")
            print(f"      ID: {acc.id}")
            print(f"      Vendor ID: {acc.vendor_id}")
            print(f"      Access Key: {acc.access_key[:20]}..." if len(acc.access_key) > 20 else f"      Access Key: {acc.access_key}")
            print(f"      Secret Key: {acc.secret_key[:20]}..." if len(acc.secret_key) > 20 else f"      Secret Key: {acc.secret_key}")
            print(f"      활성화: {acc.is_active}")
            print(f"      생성일: {acc.created_at}")
    else:
        print("  ⚠️ 저장된 쿠팡 계정이 없습니다.\n")

    print("\n" + "-"*70 + "\n")

    # 네이버 계정 조회
    naver_accounts = db.query(NaverAccount).all()
    print(f"🟢 네이버 계정: {len(naver_accounts)}개 발견")

    if naver_accounts:
        for i, acc in enumerate(naver_accounts, 1):
            print(f"\n  [{i}] {acc.name}")
            print(f"      ID: {acc.id}")
            print(f"      Username: {acc.naver_username}")
            print(f"      Password: {'*' * len(acc.naver_password) if acc.naver_password else '(없음)'}")
            print(f"      기본 계정: {acc.is_default}")
            print(f"      활성화: {acc.is_active}")
            print(f"      생성일: {acc.created_at}")
    else:
        print("  ⚠️ 저장된 네이버 계정이 없습니다.\n")

    print("\n" + "="*70)

    # 계정이 없으면 안내 메시지
    if len(coupang_accounts) == 0 and len(naver_accounts) == 0:
        print("\n⚠️ 저장된 계정이 전혀 없습니다!")
        print("\n가능한 원인:")
        print("  1. 계정을 아직 저장하지 않았습니다")
        print("  2. 데이터베이스 파일 경로가 잘못되었습니다")
        print("  3. 암호화 키가 변경되어 복호화에 실패했습니다")

        print("\n해결 방법:")
        print("  1. 백엔드 서버가 실행 중인지 확인: http://localhost:8000/docs")
        print("  2. 프론트엔드에서 계정을 다시 등록하세요")
        print("  3. .env 파일의 ENCRYPTION_KEY가 변경되지 않았는지 확인하세요")
    else:
        print("\n✅ 계정 정보가 정상적으로 저장되어 있습니다!")
        print("\n프론트엔드에서 자동으로 불러오려면:")
        print("  1. 백엔드 서버 실행: http://localhost:8000")
        print("  2. 프론트엔드 접속: http://localhost:3000")
        print("  3. 페이지 로드 시 자동으로 계정 정보가 불러와집니다")

    print("="*70 + "\n")

    # API 엔드포인트 테스트 안내
    print("💡 API로 직접 확인하려면:")
    print("  - 쿠팡 계정: http://localhost:8000/coupang-accounts")
    print("  - 네이버 계정: http://localhost:8000/naver-accounts/default/credentials")
    print()

except Exception as e:
    print(f"\n❌ 오류 발생: {str(e)}\n")
    import traceback
    traceback.print_exc()

finally:
    db.close()
