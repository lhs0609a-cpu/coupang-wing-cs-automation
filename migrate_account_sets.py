"""
계정 세트 테이블 생성 마이그레이션
"""
import sys
sys.path.insert(0, 'backend')

from backend.app.database import engine, Base
from backend.app.models.account_set import AccountSet

print("\n" + "="*70)
print("계정 세트 테이블 생성")
print("="*70 + "\n")

try:
    # 테이블 생성
    Base.metadata.create_all(engine)

    print("✅ 계정 세트 테이블이 성공적으로 생성되었습니다!")
    print("\n테이블:")
    print("  - account_sets")
    print("\n컬럼:")
    print("  - id (PRIMARY KEY)")
    print("  - name (계정 세트 이름)")
    print("  - description (설명)")
    print("  - coupang_account_id (FOREIGN KEY → coupang_accounts.id)")
    print("  - naver_account_id (FOREIGN KEY → naver_accounts.id)")
    print("  - is_default (기본 세트 여부)")
    print("  - is_active (활성화 여부)")
    print("  - last_used_at (마지막 사용 시간)")
    print("  - created_at (생성 시간)")
    print("  - updated_at (수정 시간)")

    print("\n" + "="*70)
    print("\n✅ 완료! 이제 계정 세트 기능을 사용할 수 있습니다.")
    print("\n다음 단계:")
    print("  1. 백엔드 서버 재시작: start_servers.bat")
    print("  2. 프론트엔드 접속: http://localhost:3000")
    print("  3. 반품 관리 → 계정 설정에서 계정 세트 저장")
    print("="*70 + "\n")

except Exception as e:
    print(f"\n❌ 오류 발생: {str(e)}\n")
    import traceback
    traceback.print_exc()
