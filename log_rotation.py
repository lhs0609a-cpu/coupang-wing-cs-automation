"""
로그 로테이션 시스템
로그 파일을 자동으로 관리하고 압축하여 디스크 공간 절약
"""
import os
import sys
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
import re


class LogRotation:
    """로그 로테이션 관리"""

    def __init__(self):
        """초기화"""
        self.project_root = Path(__file__).parent

        # 로그 디렉토리 목록
        self.log_dirs = [
            self.project_root / "logs",
            self.project_root / "backend" / "logs",
            self.project_root / "error_reports",
        ]

        # 설정 (환경변수 또는 기본값)
        self.max_size_mb = int(os.getenv("LOG_MAX_SIZE_MB", "50"))  # 파일당 최대 크기
        self.max_age_days = int(os.getenv("LOG_MAX_AGE_DAYS", "30"))  # 최대 보관 일수
        self.max_backups = int(os.getenv("LOG_MAX_BACKUPS", "10"))  # 백업 파일 최대 개수
        self.compress_age_days = int(os.getenv("LOG_COMPRESS_AGE_DAYS", "7"))  # 압축할 로그 나이

    def get_log_files(self, log_dir: Path) -> List[Path]:
        """
        로그 디렉토리의 모든 로그 파일 가져오기

        Args:
            log_dir: 로그 디렉토리

        Returns:
            로그 파일 목록
        """
        if not log_dir.exists():
            return []

        # .log, .txt, .log.N 형식의 파일들
        log_files = []

        for file in log_dir.iterdir():
            if file.is_file():
                # .log, .txt 확장자 또는 .log.1, .log.2 같은 백업 파일
                if (file.suffix in ['.log', '.txt'] or
                    re.match(r'.*\.log\.\d+$', file.name) or
                    re.match(r'.*\.txt\.\d+$', file.name)):
                    log_files.append(file)

        return sorted(log_files)

    def get_file_age_days(self, file_path: Path) -> int:
        """파일의 나이 (일수) 계산"""
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age.days

    def should_rotate_by_size(self, file_path: Path) -> bool:
        """크기 기준으로 로테이션이 필요한지 확인"""
        if not file_path.exists():
            return False

        size_mb = file_path.stat().st_size / (1024 * 1024)
        return size_mb >= self.max_size_mb

    def should_compress(self, file_path: Path) -> bool:
        """압축이 필요한지 확인"""
        if file_path.suffix == '.gz':
            return False  # 이미 압축됨

        age_days = self.get_file_age_days(file_path)
        return age_days >= self.compress_age_days

    def should_delete(self, file_path: Path) -> bool:
        """삭제가 필요한지 확인"""
        age_days = self.get_file_age_days(file_path)
        return age_days >= self.max_age_days

    def rotate_file(self, file_path: Path):
        """
        파일 로테이션 수행

        예: app.log → app.log.1, app.log.1 → app.log.2, ...
        """
        if not file_path.exists():
            return

        print(f"🔄 로테이션: {file_path.name}")

        # 기존 백업 파일 이름 변경 (역순)
        base_name = file_path.name

        # 최대 백업 수를 넘는 파일 삭제
        for i in range(self.max_backups, 0, -1):
            old_backup = file_path.parent / f"{base_name}.{i}"
            if old_backup.exists():
                if i >= self.max_backups:
                    old_backup.unlink()
                    print(f"  🗑️  삭제: {old_backup.name}")
                else:
                    new_backup = file_path.parent / f"{base_name}.{i+1}"
                    old_backup.rename(new_backup)

        # 현재 파일을 .1로 이동
        backup_path = file_path.parent / f"{base_name}.1"
        shutil.move(str(file_path), str(backup_path))
        print(f"  ✅ {file_path.name} → {backup_path.name}")

        # 새 파일 생성 (빈 파일)
        file_path.touch()

    def compress_file(self, file_path: Path) -> Optional[Path]:
        """
        파일 압축 (gzip)

        Args:
            file_path: 압축할 파일

        Returns:
            압축된 파일 경로 또는 None
        """
        if file_path.suffix == '.gz':
            return None  # 이미 압축됨

        gz_path = file_path.with_suffix(file_path.suffix + '.gz')

        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(gz_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # 원본 파일 삭제
            file_path.unlink()

            original_size = file_path.stat().st_size if file_path.exists() else 0
            compressed_size = gz_path.stat().st_size
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

            print(f"📦 압축: {file_path.name} → {gz_path.name}")
            print(f"   크기: {original_size / 1024:.1f} KB → {compressed_size / 1024:.1f} KB ({ratio:.1f}% 절약)")

            return gz_path

        except Exception as e:
            print(f"⚠️  압축 실패: {file_path.name} - {e}")
            return None

    def delete_old_files(self, log_dir: Path) -> int:
        """
        오래된 로그 파일 삭제

        Args:
            log_dir: 로그 디렉토리

        Returns:
            삭제된 파일 수
        """
        deleted_count = 0

        for file_path in self.get_log_files(log_dir):
            if self.should_delete(file_path):
                try:
                    file_path.unlink()
                    print(f"🗑️  삭제: {file_path.name} (나이: {self.get_file_age_days(file_path)}일)")
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠️  삭제 실패: {file_path.name} - {e}")

        return deleted_count

    def rotate_all_logs(self):
        """모든 로그 디렉토리의 로그 로테이션 수행"""
        print("\n" + "=" * 70)
        print("🔄 로그 로테이션 시작")
        print("=" * 70)
        print()

        total_rotated = 0
        total_compressed = 0
        total_deleted = 0

        for log_dir in self.log_dirs:
            if not log_dir.exists():
                print(f"⏭️  건너뜀: {log_dir} (존재하지 않음)")
                continue

            print(f"📁 처리 중: {log_dir}")
            print("-" * 70)

            log_files = self.get_log_files(log_dir)

            if not log_files:
                print("  로그 파일이 없습니다.")
                print()
                continue

            # 1. 크기 기준 로테이션
            for file_path in log_files:
                # .1, .2 같은 백업 파일은 건너뜀
                if re.match(r'.*\.\d+$', file_path.name) or file_path.suffix == '.gz':
                    continue

                if self.should_rotate_by_size(file_path):
                    self.rotate_file(file_path)
                    total_rotated += 1

            # 2. 오래된 파일 압축
            for file_path in self.get_log_files(log_dir):
                if self.should_compress(file_path):
                    if self.compress_file(file_path):
                        total_compressed += 1

            # 3. 매우 오래된 파일 삭제
            deleted = self.delete_old_files(log_dir)
            total_deleted += deleted

            print()

        print("=" * 70)
        print("✅ 로그 로테이션 완료")
        print(f"   로테이션: {total_rotated}개")
        print(f"   압축: {total_compressed}개")
        print(f"   삭제: {total_deleted}개")
        print("=" * 70)
        print()

    def get_statistics(self) -> dict:
        """로그 파일 통계 정보"""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'compressed_files': 0,
            'by_directory': {}
        }

        for log_dir in self.log_dirs:
            if not log_dir.exists():
                continue

            dir_stats = {
                'files': 0,
                'size_mb': 0,
                'compressed': 0,
                'oldest_days': 0,
            }

            log_files = self.get_log_files(log_dir)

            for file_path in log_files:
                dir_stats['files'] += 1
                dir_stats['size_mb'] += file_path.stat().st_size / (1024 * 1024)

                if file_path.suffix == '.gz':
                    dir_stats['compressed'] += 1

                age = self.get_file_age_days(file_path)
                if age > dir_stats['oldest_days']:
                    dir_stats['oldest_days'] = age

            stats['total_files'] += dir_stats['files']
            stats['total_size_mb'] += dir_stats['size_mb']
            stats['compressed_files'] += dir_stats['compressed']
            stats['by_directory'][str(log_dir)] = dir_stats

        return stats

    def display_statistics(self):
        """통계 정보 출력"""
        stats = self.get_statistics()

        print("\n" + "=" * 70)
        print("📊 로그 파일 통계")
        print("=" * 70)
        print()

        print(f"전체 파일 수: {stats['total_files']}")
        print(f"전체 크기: {stats['total_size_mb']:.2f} MB")
        print(f"압축된 파일: {stats['compressed_files']}")
        print()

        for dir_path, dir_stats in stats['by_directory'].items():
            if dir_stats['files'] == 0:
                continue

            print(f"📁 {dir_path}")
            print(f"   파일: {dir_stats['files']}개")
            print(f"   크기: {dir_stats['size_mb']:.2f} MB")
            print(f"   압축: {dir_stats['compressed']}개")
            print(f"   가장 오래된 로그: {dir_stats['oldest_days']}일")
            print()

        print("=" * 70)
        print()


def main():
    """메인 함수 - CLI로 실행"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Coupang Wing CS 자동화 시스템 - 로그 로테이션'
    )

    parser.add_argument(
        '--rotate',
        action='store_true',
        help='로그 로테이션 수행'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='로그 통계 정보 표시'
    )
    parser.add_argument(
        '--max-size',
        type=int,
        help='로테이션 크기 임계값 (MB)'
    )
    parser.add_argument(
        '--max-age',
        type=int,
        help='최대 보관 일수'
    )

    args = parser.parse_args()

    # 옵션이 없으면 도움말 출력
    if not args.rotate and not args.stats:
        parser.print_help()
        sys.exit(0)

    log_rotation = LogRotation()

    # 커스텀 설정 적용
    if args.max_size:
        log_rotation.max_size_mb = args.max_size
    if args.max_age:
        log_rotation.max_age_days = args.max_age

    try:
        if args.stats:
            log_rotation.display_statistics()

        if args.rotate:
            log_rotation.rotate_all_logs()

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
