"""
자동 업데이트 체크 시스템
원격 서버에서 새 버전을 확인하고 사용자에게 알림
"""
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple


class UpdateChecker:
    """업데이트 확인 및 관리"""

    def __init__(self, update_url: Optional[str] = None):
        """
        초기화

        Args:
            update_url: 업데이트 정보 URL (기본값: 환경변수 또는 로컬)
        """
        self.project_root = Path(__file__).parent
        self.version_file = self.project_root / "version.txt"
        self.update_cache_file = self.project_root / ".update_cache.json"

        # 업데이트 URL (환경변수 또는 인자로 받음)
        self.update_url = (
            update_url or
            os.getenv("UPDATE_CHECK_URL", "") or
            None  # None이면 업데이트 체크 안 함
        )

        # 체크 간격 (기본 24시간)
        self.check_interval_hours = int(os.getenv("UPDATE_CHECK_INTERVAL", "24"))

    def get_current_version(self) -> str:
        """현재 설치된 버전 가져오기"""
        if not self.version_file.exists():
            return "0.0.0"

        with open(self.version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()

    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """버전 문자열을 튜플로 파싱"""
        try:
            parts = version.split('.')
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            return (0, 0, 0)

    def compare_versions(self, current: str, latest: str) -> int:
        """
        버전 비교

        Returns:
            1: latest > current (업데이트 있음)
            0: latest == current (동일)
            -1: latest < current (현재가 더 최신)
        """
        current_tuple = self.parse_version(current)
        latest_tuple = self.parse_version(latest)

        if latest_tuple > current_tuple:
            return 1
        elif latest_tuple == current_tuple:
            return 0
        else:
            return -1

    def fetch_latest_version_info(self) -> Optional[Dict]:
        """
        원격 서버에서 최신 버전 정보 가져오기

        Returns:
            {
                "version": "1.1.0",
                "release_date": "2025-01-20",
                "download_url": "https://...",
                "changelog": "...",
                "critical": false
            }
        """
        if not self.update_url:
            return None

        try:
            # HTTP(S) 요청
            with urllib.request.urlopen(self.update_url, timeout=10) as response:
                data = response.read()
                version_info = json.loads(data.decode('utf-8'))
                return version_info

        except urllib.error.URLError as e:
            print(f"⚠️  업데이트 서버 접속 실패: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"⚠️  버전 정보 파싱 실패: {e}")
            return None
        except Exception as e:
            print(f"⚠️  업데이트 확인 중 오류: {e}")
            return None

    def should_check_update(self) -> bool:
        """업데이트를 체크해야 하는지 확인 (캐시 기반)"""
        if not self.update_cache_file.exists():
            return True

        try:
            with open(self.update_cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            last_check = datetime.fromisoformat(cache.get('last_check', '2000-01-01'))
            now = datetime.now()

            # 설정된 간격이 지났는지 확인
            if now - last_check > timedelta(hours=self.check_interval_hours):
                return True

            return False

        except (json.JSONDecodeError, ValueError, KeyError):
            return True

    def update_cache(self, version_info: Optional[Dict] = None):
        """캐시 업데이트"""
        cache = {
            'last_check': datetime.now().isoformat(),
            'latest_version_info': version_info
        }

        with open(self.update_cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    def check_for_updates(self, force: bool = False) -> Optional[Dict]:
        """
        업데이트 확인

        Args:
            force: 캐시 무시하고 강제 확인

        Returns:
            업데이트 정보 또는 None
        """
        # 강제가 아니고 체크할 시간이 아니면 건너뜀
        if not force and not self.should_check_update():
            return None

        # 업데이트 URL이 없으면 건너뜀
        if not self.update_url:
            return None

        print("🔍 업데이트 확인 중...")

        # 최신 버전 정보 가져오기
        latest_info = self.fetch_latest_version_info()

        # 캐시 업데이트
        self.update_cache(latest_info)

        if not latest_info:
            return None

        # 버전 비교
        current_version = self.get_current_version()
        latest_version = latest_info.get('version', '0.0.0')

        comparison = self.compare_versions(current_version, latest_version)

        if comparison == 1:
            # 새 버전 있음
            return {
                'current': current_version,
                'latest': latest_version,
                'info': latest_info
            }

        return None

    def display_update_notification(self, update_info: Dict):
        """업데이트 알림 표시"""
        current = update_info['current']
        latest = update_info['latest']
        info = update_info['info']

        print("\n" + "=" * 60)
        print("🎉 새로운 버전이 있습니다!")
        print("=" * 60)
        print(f"현재 버전: {current}")
        print(f"최신 버전: {latest}")

        if 'release_date' in info:
            print(f"릴리스 날짜: {info['release_date']}")

        if info.get('critical', False):
            print("\n⚠️  중요 업데이트: 보안 또는 중대한 버그 수정이 포함되어 있습니다.")

        if 'changelog' in info:
            print(f"\n변경사항:\n{info['changelog']}")

        if 'download_url' in info:
            print(f"\n다운로드: {info['download_url']}")

        print("\n업데이트 설치 방법:")
        print("  1. 최신 버전 다운로드")
        print("  2. 백업 생성 (데이터베이스 및 .env 파일)")
        print("  3. 새 버전으로 덮어쓰기")
        print("  4. pip install -r requirements.txt --upgrade")
        print("  5. 서버 재시작")
        print("=" * 60 + "\n")

    def check_and_notify(self, force: bool = False):
        """업데이트 확인 및 알림 (편의 메서드)"""
        update_info = self.check_for_updates(force=force)

        if update_info:
            self.display_update_notification(update_info)
            return True
        elif force:
            current = self.get_current_version()
            print(f"✅ 최신 버전을 사용 중입니다. (v{current})")

        return False


def main():
    """메인 함수 - CLI로 실행"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Coupang Wing CS 자동화 시스템 - 업데이트 체크'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='강제로 업데이트 확인 (캐시 무시)'
    )
    parser.add_argument(
        '--url',
        type=str,
        help='업데이트 정보 URL'
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help='현재 버전 표시'
    )

    args = parser.parse_args()

    checker = UpdateChecker(update_url=args.url)

    if args.version:
        print(f"현재 버전: {checker.get_current_version()}")
        return

    try:
        checker.check_and_notify(force=args.force)
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 취소했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
