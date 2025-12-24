"""
데이터베이스 계정 확인 스크립트
"""
import sys
sys.path.insert(0, 'backend')

from backend.app.database import SessionLocal
from backend.app.models.coupang_account import CoupangAccount
from backend.app.models.naver_account import NaverAccount

db = SessionLocal()

try:
    coupang_accounts = db.query(CoupangAccount).all()
    naver_accounts = db.query(NaverAccount).all()

    print(f"\n{'='*60}")
    print(f"데이터베이스 계정 정보")
    print(f"{'='*60}\n")

    print(f"쿠팡 계정: {len(coupang_accounts)}개")
    for acc in coupang_accounts:
        print(f"  - ID: {acc.id}")
        print(f"    이름: {acc.name}")
        print(f"    Vendor ID: {acc.vendor_id}")
        print(f"    Access Key: {acc.access_key[:20]}..." if acc.access_key else "    Access Key: (없음)")
        print(f"    활성화: {acc.is_active}")
        print()

    print(f"네이버 계정: {len(naver_accounts)}개")
    for acc in naver_accounts:
        print(f"  - ID: {acc.id}")
        print(f"    이름: {acc.name}")
        print(f"    Username: {acc.naver_username}")
        print(f"    기본 계정: {acc.is_default}")
        print(f"    활성화: {acc.is_active}")
        print()

    if len(coupang_accounts) == 0 and len(naver_accounts) == 0:
        print("⚠️ 저장된 계정이 없습니다.")
        print("   반품 관리 페이지에서 '계정 설정' 버튼을 눌러 계정을 등록하세요.")

    print(f"{'='*60}\n")

finally:
    db.close()
