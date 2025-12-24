"""
자가 진단 시스템 (Health Check System)
프로그램 시작 전 모든 요구사항 자동 검사 및 수정
"""
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Tuple


class HealthCheck:
    """자가 진단 시스템"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_root = self.project_root / "backend"
        self.issues = []  # 발견된 문제들
        self.fixes = []  # 수정 시도한 문제들
        self.failed_fixes = []  # 수정 실패한 문제들

    def check_all(self) -> bool:
        """
        모든 항목 검사

        Returns:
            모든 검사 통과 여부
        """
        print("\n" + "=" * 60)
        print("🏥 시스템 자가 진단 시작")
        print("=" * 60 + "\n")

        checks = [
            ("Python 버전", self.check_python_version),
            ("필수 파일", self.check_required_files),
            ("환경 변수 파일", self.check_env_file),
            ("필수 패키지", self.check_packages),
            ("데이터베이스", self.check_database),
            ("포트 사용 가능", self.check_port),
            ("디스크 공간", self.check_disk_space),
            ("메모리", self.check_memory),
            ("필수 폴더", self.check_directories),
        ]

        results = []

        for check_name, check_func in checks:
            print(f"🔍 검사 중: {check_name}...", end=' ')
            try:
                passed, message = check_func()
                if passed:
                    print(f"✅ 통과")
                else:
                    print(f"❌ 실패: {message}")
                    self.issues.append((check_name, message))

                results.append(passed)

            except Exception as e:
                print(f"⚠️  오류: {str(e)}")
                self.issues.append((check_name, str(e)))
                results.append(False)

        # 결과 요약
        print("\n" + "=" * 60)
        passed = sum(results)
        total = len(results)

        if all(results):
            print(f"✅ 모든 검사 통과! ({passed}/{total})")
            return True
        else:
            print(f"⚠️  일부 검사 실패 ({passed}/{total})")

            # 자동 수정 시도
            if self.issues:
                print("\n🔧 문제 자동 수정 시도 중...")
                self.auto_fix()

            return False

    def check_python_version(self) -> Tuple[bool, str]:
        """Python 버전 확인 (3.8 이상)"""
        version = sys.version_info

        if version.major < 3 or (version.major == 3 and version.minor < 8):
            return False, f"Python 3.8 이상 필요 (현재: {version.major}.{version.minor}.{version.micro})"

        return True, f"Python {version.major}.{version.minor}.{version.micro}"

    def check_required_files(self) -> Tuple[bool, str]:
        """필수 파일 존재 확인"""
        required_files = [
            "backend/app/main.py",
            "backend/app/database.py",
            "backend/app/config.py",
            "backend/requirements.txt",
        ]

        missing = []
        for file in required_files:
            if not (self.project_root / file).exists():
                missing.append(file)

        if missing:
            return False, f"누락된 파일: {', '.join(missing)}"

        return True, "모든 필수 파일 존재"

    def check_env_file(self) -> Tuple[bool, str]:
        """환경 변수 파일 확인"""
        env_file = self.backend_root / ".env"

        if not env_file.exists():
            return False, ".env 파일이 없습니다"

        # 필수 환경 변수 확인
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()

        required_vars = ["OPENAI_API_KEY", "DATABASE_URL"]
        missing = [var for var in required_vars if var not in content]

        if missing:
            return False, f"누락된 환경 변수: {', '.join(missing)}"

        return True, "환경 변수 파일 정상"

    def check_packages(self) -> Tuple[bool, str]:
        """필수 패키지 설치 확인"""
        requirements_file = self.backend_root / "requirements.txt"

        if not requirements_file.exists():
            return False, "requirements.txt 파일이 없습니다"

        # pip list 실행
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list"],
                capture_output=True,
                text=True,
                check=True
            )

            installed = result.stdout.lower()

            # 필수 패키지 확인
            required_packages = ["fastapi", "uvicorn", "sqlalchemy", "openai", "selenium"]
            missing = [pkg for pkg in required_packages if pkg not in installed]

            if missing:
                return False, f"누락된 패키지: {', '.join(missing)}"

            return True, "모든 필수 패키지 설치됨"

        except subprocess.CalledProcessError as e:
            return False, f"pip list 실행 실패: {str(e)}"

    def check_database(self) -> Tuple[bool, str]:
        """데이터베이스 연결 확인"""
        db_file = self.backend_root / "coupang_wing.db"

        # SQLite 파일 존재 확인
        if not db_file.exists():
            return False, "데이터베이스 파일이 없습니다"

        # 파일 크기 확인 (최소 8KB)
        size = db_file.stat().st_size
        if size < 8192:
            return False, "데이터베이스 파일이 손상되었거나 비어있습니다"

        return True, f"데이터베이스 정상 (크기: {size // 1024}KB)"

    def check_port(self, port: int = 8080) -> Tuple[bool, str]:
        """포트 사용 가능 확인"""
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return True, f"포트 {port} 사용 가능"

        except OSError:
            return False, f"포트 {port}가 이미 사용 중입니다"

    def check_disk_space(self, min_gb: float = 1.0) -> Tuple[bool, str]:
        """디스크 공간 확인"""
        import shutil

        try:
            total, used, free = shutil.disk_usage(self.project_root)

            free_gb = free / (1024 ** 3)

            if free_gb < min_gb:
                return False, f"디스크 공간 부족 (여유: {free_gb:.2f}GB, 필요: {min_gb}GB)"

            return True, f"디스크 공간 충분 (여유: {free_gb:.2f}GB)"

        except Exception as e:
            return False, f"디스크 공간 확인 실패: {str(e)}"

    def check_memory(self, min_mb: int = 512) -> Tuple[bool, str]:
        """메모리 상태 확인"""
        try:
            import psutil

            mem = psutil.virtual_memory()
            available_mb = mem.available / (1024 ** 2)

            if available_mb < min_mb:
                return False, f"메모리 부족 (여유: {available_mb:.0f}MB, 필요: {min_mb}MB)"

            return True, f"메모리 충분 (여유: {available_mb:.0f}MB)"

        except ImportError:
            return True, "psutil 미설치 (선택적 검사)"

    def check_directories(self) -> Tuple[bool, str]:
        """필수 폴더 존재 확인"""
        required_dirs = [
            "backend/app",
            "backend/app/models",
            "backend/app/routers",
            "backend/app/services",
        ]

        missing = []
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).is_dir():
                missing.append(dir_path)

        if missing:
            return False, f"누락된 폴더: {', '.join(missing)}"

        return True, "모든 필수 폴더 존재"

    def auto_fix(self):
        """발견된 문제 자동 수정 시도"""
        print("\n" + "=" * 60)

        for check_name, message in self.issues:
            print(f"\n🔧 수정 시도: {check_name}")
            print(f"   문제: {message}")

            fixed = False

            # 환경 변수 파일 생성
            if ".env 파일이 없습니다" in message:
                fixed = self.fix_env_file()

            # 필수 패키지 설치
            elif "누락된 패키지" in message:
                fixed = self.fix_packages()

            # 데이터베이스 초기화
            elif "데이터베이스 파일이 없습니다" in message or "손상되었거나" in message:
                fixed = self.fix_database()

            # 필수 폴더 생성
            elif "누락된 폴더" in message:
                fixed = self.fix_directories()

            # 포트 변경 제안
            elif "포트" in message and "사용 중" in message:
                fixed = self.fix_port()

            if fixed:
                print(f"   ✅ 수정 성공")
                self.fixes.append((check_name, message))
            else:
                print(f"   ❌ 자동 수정 실패")
                self.failed_fixes.append((check_name, message))

        # 수정 결과
        print("\n" + "=" * 60)
        if self.fixes:
            print(f"✅ {len(self.fixes)}개 문제 자동 수정 완료")

        if self.failed_fixes:
            print(f"⚠️  {len(self.failed_fixes)}개 문제 수동 수정 필요")

    def fix_env_file(self) -> bool:
        """.env 파일 생성"""
        try:
            env_example = self.backend_root / ".env.example"
            env_file = self.backend_root / ".env"

            if env_example.exists():
                # .env.example 복사
                shutil.copy(env_example, env_file)
                print(f"   📝 .env.example을 .env로 복사했습니다")
            else:
                # 기본 .env 생성
                default_env = """# Coupang Wing CS Automation Settings

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./coupang_wing.db

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Server
HOST=0.0.0.0
PORT=8080

# Security
SECRET_KEY=your_secret_key_here

# Scheduler
AUTO_START_SCHEDULER=true
"""
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write(default_env)

                print(f"   📝 기본 .env 파일을 생성했습니다")

            print(f"   ⚠️  .env 파일을 열어 필요한 값을 설정해주세요!")
            return True

        except Exception as e:
            print(f"   ❌ .env 파일 생성 실패: {str(e)}")
            return False

    def fix_packages(self) -> bool:
        """필수 패키지 설치"""
        try:
            print(f"   📦 필수 패키지 설치 중...")

            requirements_file = self.backend_root / "requirements.txt"

            if not requirements_file.exists():
                print(f"   ❌ requirements.txt 파일이 없습니다")
                return False

            # pip install 실행
            result = subprocess.run(
                [
                    sys.executable, "-m", "pip", "install",
                    "-r", str(requirements_file),
                    "--quiet"
                ],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"   ✅ 패키지 설치 완료")
                return True
            else:
                print(f"   ❌ 패키지 설치 실패: {result.stderr}")
                return False

        except Exception as e:
            print(f"   ❌ 패키지 설치 중 오류: {str(e)}")
            return False

    def fix_database(self) -> bool:
        """데이터베이스 초기화"""
        try:
            print(f"   🗄️  데이터베이스 초기화 중...")

            # database.py의 init_db 함수 호출
            sys.path.insert(0, str(self.backend_root))

            from app.database import init_db

            init_db()

            print(f"   ✅ 데이터베이스 초기화 완료")
            return True

        except Exception as e:
            print(f"   ❌ 데이터베이스 초기화 실패: {str(e)}")
            return False

    def fix_directories(self) -> bool:
        """필수 폴더 생성"""
        try:
            required_dirs = [
                "logs",
                "data",
                "error_reports",
            ]

            for dir_name in required_dirs:
                dir_path = self.project_root / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"   📁 {dir_name} 폴더 생성")

            return True

        except Exception as e:
            print(f"   ❌ 폴더 생성 실패: {str(e)}")
            return False

    def fix_port(self) -> bool:
        """포트 변경 제안"""
        print(f"   💡 다음 중 하나를 선택하세요:")
        print(f"      1. 포트 8080을 사용 중인 프로그램 종료")
        print(f"      2. .env 파일에서 PORT를 다른 값으로 변경 (예: 8081)")
        print(f"      3. uvicorn 실행 시 --port 옵션 사용")

        return False  # 수동 조치 필요

    def generate_report(self):
        """자가 진단 리포트 생성"""
        report_file = self.project_root / "health_check_report.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("🏥 시스템 자가 진단 리포트\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"검사 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"시스템: {platform.system()} {platform.release()}\n")
            f.write(f"Python: {sys.version}\n\n")

            if self.issues:
                f.write("❌ 발견된 문제\n")
                f.write("-" * 60 + "\n")
                for i, (check, message) in enumerate(self.issues, 1):
                    f.write(f"{i}. {check}: {message}\n")
                f.write("\n")

            if self.fixes:
                f.write("✅ 자동 수정된 문제\n")
                f.write("-" * 60 + "\n")
                for i, (check, message) in enumerate(self.fixes, 1):
                    f.write(f"{i}. {check}: {message}\n")
                f.write("\n")

            if self.failed_fixes:
                f.write("⚠️  수동 조치 필요\n")
                f.write("-" * 60 + "\n")
                for i, (check, message) in enumerate(self.failed_fixes, 1):
                    f.write(f"{i}. {check}: {message}\n")

        print(f"\n📄 자가 진단 리포트 저장: {report_file}")


def main():
    """메인 함수"""
    from datetime import datetime

    checker = HealthCheck()

    # 모든 검사 실행
    all_passed = checker.check_all()

    # 리포트 생성
    if not all_passed:
        checker.generate_report()

    # 결과 출력
    print("\n" + "=" * 60)

    if all_passed:
        print("✅ 시스템이 정상 작동 준비 완료!")
        print("\n다음 명령으로 서버를 시작하세요:")
        print("  Windows: run.bat")
        print("  Mac/Linux: ./run.sh")
        return 0
    else:
        print("⚠️  일부 문제를 수정하지 못했습니다.")
        print("\n상세 내용은 health_check_report.txt를 확인하세요.")

        if checker.failed_fixes:
            print("\n수동 조치가 필요한 문제:")
            for check, message in checker.failed_fixes:
                print(f"  - {check}: {message}")

        return 1


if __name__ == "__main__":
    sys.exit(main())
