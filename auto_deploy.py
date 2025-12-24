"""
자동 배포 스크립트
버전 증가, 변경 이력 자동 기록, 배포 패키지 생성
"""
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path


class AutoDeploy:
    """자동 배포 관리자"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.version_file = self.project_root / "version.txt"
        self.changelog_file = self.project_root / "CHANGELOG.md"

    def read_version(self):
        """현재 버전 읽기"""
        if not self.version_file.exists():
            return "1.0.0"

        with open(self.version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()

    def write_version(self, version):
        """버전 파일에 쓰기"""
        with open(self.version_file, 'w', encoding='utf-8') as f:
            f.write(version)

    def increment_version(self, part='patch'):
        """
        버전 증가

        Args:
            part: 'major', 'minor', 'patch' 중 하나
        """
        current = self.read_version()
        major, minor, patch = map(int, current.split('.'))

        if part == 'major':
            major += 1
            minor = 0
            patch = 0
        elif part == 'minor':
            minor += 1
            patch = 0
        elif part == 'patch':
            patch += 1
        else:
            raise ValueError(f"Invalid version part: {part}")

        new_version = f"{major}.{minor}.{patch}"
        self.write_version(new_version)

        print(f"✅ 버전 업데이트: {current} → {new_version}")
        return new_version

    def update_changelog(self, version, changes):
        """
        CHANGELOG.md 업데이트

        Args:
            version: 새 버전
            changes: 변경사항 리스트
        """
        if not self.changelog_file.exists():
            print("⚠️  CHANGELOG.md가 없습니다. 건너뜁니다.")
            return

        # 현재 changelog 읽기
        with open(self.changelog_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 새 버전 섹션 생성
        today = datetime.now().strftime('%Y-%m-%d')
        new_section = f"\n## [{version}] - {today}\n\n"

        if changes:
            new_section += "### 변경됨 (Changed)\n"
            for change in changes:
                new_section += f"- {change}\n"
        else:
            new_section += "### 변경됨 (Changed)\n"
            new_section += "- 패치 업데이트\n"

        new_section += "\n---\n"

        # [Unreleased] 섹션 뒤에 삽입
        if "[Unreleased]" in content:
            parts = content.split("[Unreleased]")
            # [Unreleased] 섹션 찾기
            unreleased_end = parts[1].find("---")
            if unreleased_end != -1:
                updated = (
                    parts[0] + "[Unreleased]" +
                    parts[1][:unreleased_end + 3] +
                    new_section +
                    parts[1][unreleased_end + 3:]
                )
            else:
                updated = content + new_section
        else:
            # [Unreleased] 섹션이 없으면 맨 앞에 추가
            lines = content.split('\n')
            # 첫 번째 ## 찾기
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('## ['):
                    insert_pos = i
                    break

            lines.insert(insert_pos, new_section)
            updated = '\n'.join(lines)

        # 파일에 쓰기
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(updated)

        print(f"✅ CHANGELOG.md 업데이트 완료")

    def create_deployment_package(self, version):
        """
        배포 패키지 생성

        Args:
            version: 버전 번호
        """
        # 프로젝트명 가져오기
        project_name = self.project_root.name

        # 배포 폴더 생성
        deploy_folder = self.project_root.parent / f"{project_name}_v{version}"

        # 이미 존재하면 삭제
        if deploy_folder.exists():
            response = input(f"⚠️  {deploy_folder.name} 폴더가 이미 존재합니다. 덮어쓰시겠습니까? (y/n): ")
            if response.lower() != 'y':
                print("❌ 배포 취소")
                return None

            shutil.rmtree(deploy_folder)

        # 폴더 생성
        deploy_folder.mkdir(parents=True, exist_ok=True)

        # 복사할 파일/폴더 목록
        items_to_copy = [
            'backend',
            'version.txt',
            'CHANGELOG.md',
            'README.md',
            'IMPROVEMENTS.md',
            'DEVELOPER_GUIDE.md',
            'install.bat',
            'install.sh',
            'run.bat',
            'run.sh',
            'requirements.txt',
            '.env.example',
            'health_check.py',
            'error_handler.py',
            'docker-compose.dev.yml',
        ]

        # 제외할 폴더
        exclude_dirs = {
            '__pycache__',
            '.pytest_cache',
            'venv',
            'env',
            '.git',
            'logs',
            'data',
            'error_reports',
            'htmlcov',
            '.coverage'
        }

        print(f"\n📦 배포 패키지 생성 중: {deploy_folder.name}")
        print("=" * 60)

        copied_count = 0

        for item in items_to_copy:
            src = self.project_root / item

            if not src.exists():
                print(f"⏭️  건너뜀: {item} (존재하지 않음)")
                continue

            dst = deploy_folder / item

            try:
                if src.is_dir():
                    # 폴더 복사 (제외 폴더 제외)
                    shutil.copytree(
                        src,
                        dst,
                        ignore=lambda dir, files: [
                            f for f in files
                            if any(excl in Path(dir, f).parts for excl in exclude_dirs)
                        ]
                    )
                else:
                    # 파일 복사
                    shutil.copy2(src, dst)

                print(f"✅ 복사: {item}")
                copied_count += 1

            except Exception as e:
                print(f"❌ 실패: {item} - {str(e)}")

        # 필요한 폴더 생성
        (deploy_folder / 'logs').mkdir(exist_ok=True)
        (deploy_folder / 'data').mkdir(exist_ok=True)
        (deploy_folder / 'error_reports').mkdir(exist_ok=True)

        print("=" * 60)
        print(f"✅ 배포 패키지 생성 완료: {copied_count}개 항목 복사")
        print(f"📁 위치: {deploy_folder}")

        return deploy_folder

    def run_interactive(self):
        """대화형 배포 프로세스"""
        print("\n" + "=" * 60)
        print("🚀 Coupang Wing CS 자동화 시스템 - 자동 배포")
        print("=" * 60 + "\n")

        current_version = self.read_version()
        print(f"현재 버전: {current_version}")

        # 버전 증가 타입 선택
        print("\n버전 증가 타입을 선택하세요:")
        print("  1. PATCH (버그 수정) - 예: 1.0.0 → 1.0.1")
        print("  2. MINOR (기능 추가) - 예: 1.0.0 → 1.1.0")
        print("  3. MAJOR (중대한 변경) - 예: 1.0.0 → 2.0.0")
        print("  4. 배포만 (버전 변경 없음)")
        print("  0. 취소")

        choice = input("\n선택 (0-4): ").strip()

        version_map = {
            '1': 'patch',
            '2': 'minor',
            '3': 'major'
        }

        if choice == '0':
            print("❌ 배포 취소")
            return

        new_version = current_version

        if choice in version_map:
            new_version = self.increment_version(version_map[choice])

            # 변경사항 입력
            print("\n변경사항을 입력하세요 (빈 줄 입력 시 종료):")
            changes = []
            while True:
                change = input("- ").strip()
                if not change:
                    break
                changes.append(change)

            if changes:
                self.update_changelog(new_version, changes)

        elif choice != '4':
            print("❌ 잘못된 선택")
            return

        # 배포 패키지 생성
        print("\n배포 패키지를 생성하시겠습니까? (y/n): ", end='')
        if input().strip().lower() == 'y':
            deploy_folder = self.create_deployment_package(new_version)

            if deploy_folder:
                print("\n" + "=" * 60)
                print("🎉 배포 완료!")
                print("=" * 60)
                print(f"\n📦 배포 폴더: {deploy_folder}")
                print(f"📌 버전: {new_version}")
                print("\n다음 단계:")
                print(f"  1. {deploy_folder}로 이동")
                print("  2. install.bat (Windows) 또는 install.sh (Mac/Linux) 실행")
                print("  3. 서버 실행 확인")


def main():
    """메인 함수"""
    try:
        deploy = AutoDeploy()
        deploy.run_interactive()

    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 취소했습니다.")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
