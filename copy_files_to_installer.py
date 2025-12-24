"""
프로젝트 파일을 FullAutoInstaller로 복사하는 스크립트
"""

import os
import shutil
from pathlib import Path

def main():
    # 기본 경로 설정
    source_dir = Path(__file__).parent
    target_dir = source_dir / "CoupangWingCS_FullAutoInstaller"
    app_dir = target_dir / "app"

    print("="*70)
    print("  프로젝트 파일 복사 스크립트")
    print("="*70)
    print(f"\n소스 디렉토리: {source_dir}")
    print(f"타겟 디렉토리: {target_dir}")
    print(f"앱 디렉토리: {app_dir}\n")

    # app 폴더 생성
    print("[1/4] app 폴더 생성 중...")
    if app_dir.exists():
        print("  기존 app 폴더 삭제 중...")
        shutil.rmtree(app_dir)

    app_dir.mkdir(parents=True, exist_ok=True)
    print("  완료!\n")

    # Backend 복사
    print("[2/4] Backend 폴더 복사 중...")
    backend_source = source_dir / "backend"
    backend_target = app_dir / "backend"

    if backend_source.exists():
        shutil.copytree(backend_source, backend_target, dirs_exist_ok=True)
        print(f"  {backend_source} -> {backend_target}")
        print("  완료!\n")
    else:
        print(f"  오류: {backend_source} 폴더를 찾을 수 없습니다!\n")
        return 1

    # Frontend 복사
    print("[3/4] Frontend 폴더 복사 중...")
    frontend_source = source_dir / "frontend"
    frontend_target = app_dir / "frontend"

    if frontend_source.exists():
        shutil.copytree(frontend_source, frontend_target, dirs_exist_ok=True)
        print(f"  {frontend_source} -> {frontend_target}")
        print("  완료!\n")
    else:
        print(f"  오류: {frontend_source} 폴더를 찾을 수 없습니다!\n")
        return 1

    # Launcher 파일 복사
    print("[4/4] Launcher 파일 복사 중...")
    launcher_source = target_dir / "launcher_final.py"
    launcher_target = app_dir / "launcher.py"

    if launcher_source.exists():
        shutil.copy2(launcher_source, launcher_target)
        print(f"  {launcher_source} -> {launcher_target}")
        print("  완료!\n")
    else:
        print(f"  경고: {launcher_source}를 찾을 수 없습니다!\n")

    # README 파일 생성
    print("[추가] README 파일 생성 중...")
    readme_content = """============================================================
  쿠팡 윙 CS 자동화 시스템 v3.0.0
  완전 자동 설치 및 실행 버전
============================================================

사용 방법:
  1. START.bat 파일을 더블클릭하세요
  2. 자동으로 필요한 프로그램이 설치됩니다
  3. 설치 완료 후 자동으로 프로그램이 실행됩니다

시스템 요구사항:
  - Windows 10 이상
  - 인터넷 연결 (최초 설치 시)
  - 디스크 여유 공간 약 500MB

설치되는 프로그램:
  - Python 3.11.9 (임베디드 버전)
  - Node.js 20.18.1 (포터블 버전)
  - 모든 필수 Python 패키지
  - 모든 필수 npm 패키지

문제 해결:
  - 방화벽 경고가 나타나면 '액세스 허용'을 클릭하세요
  - 설치 중 오류가 발생하면 관리자 권한으로 실행해보세요
  - 포트 8000-8009가 사용 중이면 다른 프로그램을 종료하세요

제작: CoupangWingCS Team
버전: 3.0.0
날짜: 2025-10-31
============================================================
"""

    readme_path = target_dir / "README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  {readme_path}")
    print("  완료!\n")

    # 검증
    print("="*70)
    print("  파일 검증 중...")
    print("="*70)

    files_to_check = [
        target_dir / "START.bat",
        target_dir / "install_python.bat",
        target_dir / "install_nodejs.bat",
        target_dir / "install_dependencies.bat",
        target_dir / "README.txt",
        app_dir / "backend",
        app_dir / "frontend",
    ]

    all_good = True
    for file_path in files_to_check:
        if file_path.exists():
            print(f"  ✓ {file_path.name}")
        else:
            print(f"  ✗ {file_path.name} - 없음!")
            all_good = False

    print()

    if all_good:
        print("="*70)
        print("  모든 파일이 성공적으로 복사되었습니다!")
        print("="*70)
        print(f"\n배포 폴더: {target_dir}")
        print("\n이제 'CoupangWingCS_FullAutoInstaller' 폴더를")
        print("다른 컴퓨터에 복사하여 START.bat을 실행하면 됩니다!\n")
        return 0
    else:
        print("="*70)
        print("  일부 파일이 누락되었습니다!")
        print("="*70)
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
