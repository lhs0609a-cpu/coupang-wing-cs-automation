"""
저장된 계정 세트 확인 스크립트
"""
import sys
import os

# UTF-8 출력 설정
if os.name == 'nt':  # Windows
    os.system('chcp 65001 >nul')

sys.path.insert(0, 'backend')

from backend.app.database import SessionLocal
from backend.app.models.account_set import AccountSet
from backend.app.models.coupang_account import CoupangAccount
from backend.app.models.naver_account import NaverAccount

print("\n" + "="*70)
print("[백엔드 데이터베이스] 저장된 계정 정보 확인")
print("="*70 + "\n")

db = SessionLocal()

try:
    # 계정 세트 조회
    account_sets = db.query(AccountSet).all()

    print(f"[OK] 계정 세트: {len(account_sets)}개")
    for idx, account_set in enumerate(account_sets, 1):
        print(f"\n{idx}. {account_set.name}")
        print(f"   - ID: {account_set.id}")
        print(f"   - 설명: {account_set.description or 'N/A'}")
        print(f"   - 기본 세트: {'[YES]' if account_set.is_default else '[NO]'}")
        print(f"   - 활성화: {'[YES]' if account_set.is_active else '[NO]'}")

        if account_set.coupang_account_id:
            coupang = db.query(CoupangAccount).get(account_set.coupang_account_id)
            if coupang:
                print(f"   - 쿠팡: {coupang.name} (Vendor ID: {coupang.vendor_id})")

        if account_set.naver_account_id:
            naver = db.query(NaverAccount).get(account_set.naver_account_id)
            if naver:
                print(f"   - 네이버: {naver.name} (아이디: {naver.naver_username})")

        print(f"   - 생성일: {account_set.created_at}")

    print("\n" + "-"*70)

    # 쿠팡 계정 조회
    coupang_accounts = db.query(CoupangAccount).all()
    print(f"\n[OK] 쿠팡 계정: {len(coupang_accounts)}개")
    for idx, account in enumerate(coupang_accounts, 1):
        print(f"{idx}. {account.name} (Vendor ID: {account.vendor_id})")

    # 네이버 계정 조회
    naver_accounts = db.query(NaverAccount).all()
    print(f"\n[OK] 네이버 계정: {len(naver_accounts)}개")
    for idx, account in enumerate(naver_accounts, 1):
        print(f"{idx}. {account.name} (아이디: {account.naver_username})")

    print("\n" + "="*70)
    print("[OK] 모든 데이터가 백엔드 데이터베이스에 영구 저장되어 있습니다!")
    print(f"[FILE] 데이터베이스 파일: backend/database/coupang_cs.db")
    print(f"[SECURE] 암호화: Fernet 암호화 사용 (.env의 ENCRYPTION_KEY)")
    print("="*70 + "\n")

except Exception as e:
    print(f"[ERROR] 오류 발생: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
