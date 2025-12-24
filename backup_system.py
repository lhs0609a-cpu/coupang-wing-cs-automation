"""
자동 백업 시스템
데이터베이스, 설정 파일, 중요 데이터 자동 백업 및 복원
"""
import os
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json


class BackupSystem:
    """백업 및 복원 관리"""

    def __init__(self, backup_dir: Optional[Path] = None):
        """
        초기화

        Args:
            backup_dir: 백업 저장 디렉토리
        """
        self.project_root = Path(__file__).parent
        self.backup_dir = backup_dir or self.project_root / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 백업 대상 정의
        self.backup_targets = {
            'database': [
                'backend/coupang_wing.db',
                'backend/coupang_cs.db',
            ],
            'config': [
                'backend/.env',
                '.env',
            ],
            'knowledge_base': [
                'backend/knowledge_base',
            ],
            'data': [
                'data',
            ],
            'logs': [
                'logs',
                'backend/logs',
            ],
        }

        # 백업 보관 정책 (환경변수 또는 기본값)
        self.keep_daily = int(os.getenv("BACKUP_KEEP_DAILY", "7"))  # 일일 백업 7개
        self.keep_weekly = int(os.getenv("BACKUP_KEEP_WEEKLY", "4"))  # 주간 백업 4개
        self.keep_monthly = int(os.getenv("BACKUP_KEEP_MONTHLY", "12"))  # 월간 백업 12개

    def get_backup_filename(self, backup_type: str = 'full') -> str:
        """
        백업 파일명 생성

        Args:
            backup_type: 'full', 'database', 'config' 등

        Returns:
            파일명 (예: backup_full_20250115_143022.zip)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"backup_{backup_type}_{timestamp}.zip"

    def create_backup(
        self,
        backup_type: str = 'full',
        include_logs: bool = False,
        compress: bool = True
    ) -> Optional[Path]:
        """
        백업 생성

        Args:
            backup_type: 'full', 'database', 'config', 'data'
            include_logs: 로그 포함 여부
            compress: 압축 여부

        Returns:
            백업 파일 경로 또는 None (실패 시)
        """
        print(f"\n📦 백업 생성 중: {backup_type}")
        print("=" * 60)

        # 백업 파일명
        backup_filename = self.get_backup_filename(backup_type)
        backup_path = self.backup_dir / backup_filename

        # 백업할 대상 결정
        targets_to_backup = []

        if backup_type == 'full':
            # 전체 백업
            for category, paths in self.backup_targets.items():
                if category == 'logs' and not include_logs:
                    continue
                targets_to_backup.extend(paths)

        elif backup_type in self.backup_targets:
            # 특정 카테고리 백업
            targets_to_backup = self.backup_targets[backup_type]

        else:
            print(f"❌ 알 수 없는 백업 타입: {backup_type}")
            return None

        # 압축 아카이브 생성
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED) as zipf:
                backed_up_count = 0

                for target_path in targets_to_backup:
                    full_path = self.project_root / target_path

                    if not full_path.exists():
                        print(f"⏭️  건너뜀: {target_path} (존재하지 않음)")
                        continue

                    if full_path.is_file():
                        # 파일 백업
                        zipf.write(full_path, arcname=target_path)
                        print(f"✅ 백업: {target_path}")
                        backed_up_count += 1

                    elif full_path.is_dir():
                        # 디렉토리 백업 (재귀)
                        for file_path in full_path.rglob('*'):
                            if file_path.is_file():
                                arcname = file_path.relative_to(self.project_root)
                                zipf.write(file_path, arcname=arcname)
                                backed_up_count += 1

                        print(f"✅ 백업: {target_path}/ (폴더)")

            # 메타데이터 저장
            metadata = {
                'backup_type': backup_type,
                'timestamp': datetime.now().isoformat(),
                'include_logs': include_logs,
                'files_count': backed_up_count,
                'size_bytes': backup_path.stat().st_size,
            }

            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            print("=" * 60)
            print(f"✅ 백업 완료!")
            print(f"📁 위치: {backup_path}")
            print(f"📊 파일 수: {backed_up_count}")
            print(f"💾 크기: {backup_path.stat().st_size / (1024*1024):.2f} MB")
            print()

            return backup_path

        except Exception as e:
            print(f"❌ 백업 생성 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def list_backups(self, backup_type: Optional[str] = None) -> List[Dict]:
        """
        백업 목록 조회

        Args:
            backup_type: 특정 타입만 조회 (None이면 전체)

        Returns:
            백업 목록
        """
        backups = []

        for backup_file in sorted(self.backup_dir.glob('backup_*.zip'), reverse=True):
            # 메타데이터 읽기
            metadata_file = backup_file.with_suffix('.json')

            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                # 메타데이터 없으면 파일명에서 추출
                parts = backup_file.stem.split('_')
                metadata = {
                    'backup_type': parts[1] if len(parts) > 1 else 'unknown',
                    'timestamp': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                    'files_count': 0,
                    'size_bytes': backup_file.stat().st_size,
                }

            # 타입 필터링
            if backup_type and metadata['backup_type'] != backup_type:
                continue

            backups.append({
                'file': backup_file,
                'metadata': metadata
            })

        return backups

    def display_backups(self, backup_type: Optional[str] = None):
        """백업 목록 출력"""
        backups = self.list_backups(backup_type=backup_type)

        if not backups:
            print("📂 백업이 없습니다.")
            return

        print("\n" + "=" * 80)
        print("📦 백업 목록")
        print("=" * 80)

        for i, backup in enumerate(backups, 1):
            metadata = backup['metadata']
            file_path = backup['file']

            timestamp = datetime.fromisoformat(metadata['timestamp'])
            size_mb = metadata['size_bytes'] / (1024 * 1024)

            print(f"\n[{i}] {file_path.name}")
            print(f"    타입: {metadata['backup_type']}")
            print(f"    생성일: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    크기: {size_mb:.2f} MB")
            print(f"    파일 수: {metadata.get('files_count', 'N/A')}")

        print("\n" + "=" * 80 + "\n")

    def restore_backup(self, backup_file: Path, dry_run: bool = False) -> bool:
        """
        백업 복원

        Args:
            backup_file: 복원할 백업 파일
            dry_run: True면 실제 복원하지 않고 시뮬레이션만

        Returns:
            성공 여부
        """
        if not backup_file.exists():
            print(f"❌ 백업 파일이 없습니다: {backup_file}")
            return False

        print(f"\n🔄 백업 복원 {'시뮬레이션' if dry_run else '중'}: {backup_file.name}")
        print("=" * 60)

        if not dry_run:
            # 확인
            response = input("⚠️  기존 파일이 덮어씌워집니다. 계속하시겠습니까? (y/n): ")
            if response.lower() != 'y':
                print("❌ 복원 취소")
                return False

        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                files = zipf.namelist()
                print(f"📄 복원할 파일 수: {len(files)}")
                print()

                for file in files:
                    target_path = self.project_root / file

                    if dry_run:
                        print(f"  [시뮬레이션] 복원: {file}")
                    else:
                        # 디렉토리 생성
                        target_path.parent.mkdir(parents=True, exist_ok=True)

                        # 파일 추출
                        zipf.extract(file, self.project_root)
                        print(f"✅ 복원: {file}")

            print("=" * 60)
            if dry_run:
                print("✅ 시뮬레이션 완료! (실제 파일은 변경되지 않았습니다)")
            else:
                print("✅ 복원 완료!")
            print()

            return True

        except Exception as e:
            print(f"❌ 복원 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def cleanup_old_backups(self):
        """보관 정책에 따라 오래된 백업 삭제"""
        print("\n🧹 오래된 백업 정리 중...")
        print("=" * 60)

        backups = self.list_backups()

        if not backups:
            print("정리할 백업이 없습니다.")
            return

        now = datetime.now()
        deleted_count = 0

        # 백업을 날짜별로 분류
        daily_backups = []
        weekly_backups = []
        monthly_backups = []

        for backup in backups:
            timestamp = datetime.fromisoformat(backup['metadata']['timestamp'])
            age_days = (now - timestamp).days

            if age_days < 7:
                daily_backups.append(backup)
            elif age_days < 30:
                weekly_backups.append(backup)
            else:
                monthly_backups.append(backup)

        # 일일 백업: 최근 N개 유지
        if len(daily_backups) > self.keep_daily:
            for backup in daily_backups[self.keep_daily:]:
                self._delete_backup(backup)
                deleted_count += 1

        # 주간 백업: 최근 N개 유지
        if len(weekly_backups) > self.keep_weekly:
            for backup in weekly_backups[self.keep_weekly:]:
                self._delete_backup(backup)
                deleted_count += 1

        # 월간 백업: 최근 N개 유지
        if len(monthly_backups) > self.keep_monthly:
            for backup in monthly_backups[self.keep_monthly:]:
                self._delete_backup(backup)
                deleted_count += 1

        print("=" * 60)
        print(f"✅ 정리 완료: {deleted_count}개 백업 삭제")
        print()

    def _delete_backup(self, backup: Dict):
        """백업 파일 삭제 (내부 메서드)"""
        try:
            backup_file = backup['file']
            metadata_file = backup_file.with_suffix('.json')

            backup_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()

            print(f"🗑️  삭제: {backup_file.name}")

        except Exception as e:
            print(f"⚠️  삭제 실패: {backup_file.name} - {e}")


def main():
    """메인 함수 - CLI로 실행"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Coupang Wing CS 자동화 시스템 - 백업 관리'
    )

    subparsers = parser.add_subparsers(dest='command', help='명령')

    # 백업 생성
    create_parser = subparsers.add_parser('create', help='백업 생성')
    create_parser.add_argument(
        '--type',
        choices=['full', 'database', 'config', 'data'],
        default='full',
        help='백업 타입 (기본: full)'
    )
    create_parser.add_argument(
        '--include-logs',
        action='store_true',
        help='로그 포함'
    )
    create_parser.add_argument(
        '--no-compress',
        action='store_true',
        help='압축하지 않음'
    )

    # 백업 목록
    list_parser = subparsers.add_parser('list', help='백업 목록 조회')
    list_parser.add_argument(
        '--type',
        choices=['full', 'database', 'config', 'data'],
        help='특정 타입만 조회'
    )

    # 백업 복원
    restore_parser = subparsers.add_parser('restore', help='백업 복원')
    restore_parser.add_argument(
        'backup_file',
        type=str,
        help='복원할 백업 파일명'
    )
    restore_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='시뮬레이션만 (실제 복원 안 함)'
    )

    # 정리
    cleanup_parser = subparsers.add_parser('cleanup', help='오래된 백업 정리')

    args = parser.parse_args()

    # 명령이 없으면 도움말 출력
    if not args.command:
        parser.print_help()
        sys.exit(0)

    backup_system = BackupSystem()

    try:
        if args.command == 'create':
            backup_system.create_backup(
                backup_type=args.type,
                include_logs=args.include_logs,
                compress=not args.no_compress
            )

        elif args.command == 'list':
            backup_system.display_backups(backup_type=args.type)

        elif args.command == 'restore':
            backup_file = backup_system.backup_dir / args.backup_file
            backup_system.restore_backup(backup_file, dry_run=args.dry_run)

        elif args.command == 'cleanup':
            backup_system.cleanup_old_backups()

    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 취소했습니다.")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
