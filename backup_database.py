"""
데이터베이스 백업 스크립트
계정 정보와 반품 로그를 안전하게 백업합니다.
"""
import os
import sys
import shutil
import sqlite3
from datetime import datetime

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


def backup_database():
    """데이터베이스를 백업합니다"""

    # 데이터베이스 파일 경로
    db_path = "E:\\u\\coupang-wing-cs-automation\\database\\coupang_cs.db"

    if not os.path.exists(db_path):
        db_path = "./database/coupang_cs.db"

    if not os.path.exists(db_path):
        print("❌ 데이터베이스 파일을 찾을 수 없습니다")
        return False

    # 백업 폴더 생성
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    # 백업 파일명 (날짜_시간)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"coupang_cs_backup_{timestamp}.db")

    try:
        # SQLite WAL 모드 체크포인트 (안전한 백업)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA wal_checkpoint(FULL)")
        conn.close()

        # 파일 복사
        shutil.copy2(db_path, backup_path)

        # 백업 파일 크기
        size_mb = os.path.getsize(backup_path) / (1024 * 1024)

        print(f"✅ 백업 완료!")
        print(f"   파일: {backup_path}")
        print(f"   크기: {size_mb:.2f} MB")

        # .env 파일도 백업 (암호화 키 포함)
        env_path = ".env"
        if os.path.exists(env_path):
            env_backup_path = os.path.join(backup_dir, f"env_backup_{timestamp}.txt")
            shutil.copy2(env_path, env_backup_path)
            print(f"✅ .env 파일도 백업됨: {env_backup_path}")
            print(f"   ⚠️  이 파일에는 암호화 키가 포함되어 있으므로 안전하게 보관하세요!")

        # 오래된 백업 파일 정리 (30개만 유지)
        cleanup_old_backups(backup_dir, keep=30)

        return True

    except Exception as e:
        print(f"❌ 백업 실패: {str(e)}")
        return False


def cleanup_old_backups(backup_dir, keep=30):
    """오래된 백업 파일 정리"""
    try:
        # 백업 파일 목록 (생성 시간순 정렬)
        backup_files = []
        for filename in os.listdir(backup_dir):
            if filename.startswith("coupang_cs_backup_") and filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                mtime = os.path.getmtime(filepath)
                backup_files.append((mtime, filepath))

        # 오래된 순으로 정렬
        backup_files.sort(reverse=True)

        # keep 개수를 초과하는 파일 삭제
        if len(backup_files) > keep:
            deleted_count = 0
            for _, filepath in backup_files[keep:]:
                os.remove(filepath)
                deleted_count += 1

            if deleted_count > 0:
                print(f"📁 오래된 백업 {deleted_count}개 삭제됨 (최근 {keep}개 유지)")

    except Exception as e:
        print(f"⚠️  백업 정리 중 오류: {str(e)}")


def restore_database(backup_path):
    """백업에서 데이터베이스 복원"""
    db_path = "E:\\u\\coupang-wing-cs-automation\\database\\coupang_cs.db"

    if not os.path.exists(db_path):
        db_path = "./database/coupang_cs.db"

    try:
        # 기존 DB 백업 (복원 전)
        if os.path.exists(db_path):
            safety_backup = f"{db_path}.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, safety_backup)
            print(f"⚠️  복원 전 현재 DB 백업: {safety_backup}")

        # 백업 파일 복원
        shutil.copy2(backup_path, db_path)
        print(f"✅ 데이터베이스 복원 완료!")
        print(f"   복원 파일: {backup_path}")

        return True

    except Exception as e:
        print(f"❌ 복원 실패: {str(e)}")
        return False


def list_backups():
    """백업 목록 출력"""
    backup_dir = "backups"

    if not os.path.exists(backup_dir):
        print("📁 백업 폴더가 없습니다")
        return

    backup_files = []
    for filename in os.listdir(backup_dir):
        if filename.startswith("coupang_cs_backup_") and filename.endswith(".db"):
            filepath = os.path.join(backup_dir, filename)
            mtime = os.path.getmtime(filepath)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            backup_files.append((mtime, filepath, size_mb))

    if not backup_files:
        print("📁 백업 파일이 없습니다")
        return

    # 최신 순 정렬
    backup_files.sort(reverse=True)

    print(f"\n📦 총 {len(backup_files)}개의 백업 파일:")
    print("-" * 80)
    for idx, (mtime, filepath, size_mb) in enumerate(backup_files, 1):
        timestamp = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{idx:2d}. {os.path.basename(filepath)}")
        print(f"    생성: {timestamp}  크기: {size_mb:.2f} MB")
    print("-" * 80)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "backup":
            backup_database()
        elif command == "list":
            list_backups()
        elif command == "restore" and len(sys.argv) > 2:
            restore_database(sys.argv[2])
        else:
            print("사용법:")
            print("  python backup_database.py backup        # 백업 생성")
            print("  python backup_database.py list          # 백업 목록")
            print("  python backup_database.py restore <파일> # 복원")
    else:
        # 기본: 백업 생성
        backup_database()
