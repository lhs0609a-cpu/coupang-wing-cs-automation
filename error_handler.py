"""
고급 에러 핸들링 시스템
상세한 에러 리포트 자동 생성 및 해결 방법 제시
"""
import os
import sys
import traceback
import platform
import inspect
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class ErrorHandler:
    """고급 에러 핸들러"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.error_reports_dir = self.project_root / "error_reports"
        self.error_reports_dir.mkdir(exist_ok=True)

    def handle_exception(
        self,
        exc_type,
        exc_value,
        exc_traceback,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        예외 처리 및 상세 리포트 생성

        Args:
            exc_type: 예외 타입
            exc_value: 예외 값
            exc_traceback: 트레이스백
            context: 추가 컨텍스트 정보
        """
        # 리포트 생성
        report = self.generate_error_report(
            exc_type,
            exc_value,
            exc_traceback,
            context
        )

        # 파일로 저장
        report_file = self.save_error_report(report)

        # 콘솔에 출력
        print("\n" + "=" * 70)
        print("🚨 에러가 발생했습니다!")
        print("=" * 70)
        print(report)
        print("=" * 70)
        print(f"\n📄 상세 리포트 저장: {report_file}")
        print("\n💡 해결 방법을 참고하거나, 리포트를 개발자에게 전달하세요.")

    def generate_error_report(
        self,
        exc_type,
        exc_value,
        exc_traceback,
        context: Optional[Dict] = None
    ) -> str:
        """
        상세한 에러 리포트 생성

        Returns:
            리포트 텍스트
        """
        lines = []

        # 헤더
        lines.append("=" * 70)
        lines.append("🚨 에러 리포트")
        lines.append("=" * 70)
        lines.append("")

        # 시스템 정보
        lines.append(f"📅 발생 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"🖥️  시스템: {platform.system()} {platform.release()}")
        lines.append(f"🐍 Python: {sys.version.split()[0]}")
        lines.append(f"📁 작업 디렉토리: {Path.cwd()}")
        lines.append("")

        # 에러 정보
        lines.append("❌ 에러 정보")
        lines.append("-" * 70)
        lines.append(f"타입: {exc_type.__name__}")
        lines.append(f"메시지: {str(exc_value)}")
        lines.append("")

        # 발생 위치
        if exc_traceback:
            tb = traceback.extract_tb(exc_traceback)
            last_frame = tb[-1]

            lines.append("발생 위치:")
            lines.append(f"  파일: {Path(last_frame.filename).name}")
            lines.append(f"  라인: {last_frame.lineno}")
            lines.append(f"  함수: {last_frame.name}")
            lines.append("")

            # 코드 컨텍스트
            lines.append("코드:")
            lines.extend(self._get_code_context(last_frame))
            lines.append("")

        # 상세 분석
        analysis = self._analyze_error(exc_type, exc_value, exc_traceback)
        if analysis:
            lines.append("🔍 상세 분석")
            lines.append("-" * 70)
            lines.extend(analysis)
            lines.append("")

        # 변수 상태 (가능한 경우)
        if exc_traceback:
            var_state = self._get_variable_state(exc_traceback)
            if var_state:
                lines.append("당시 변수 상태:")
                lines.extend(var_state)
                lines.append("")

        # 해결 방법
        solutions = self._get_solutions(exc_type, exc_value)
        if solutions:
            lines.append("💡 해결 방법")
            lines.append("-" * 70)
            lines.extend(solutions)
            lines.append("")

        # Claude에게 붙여넣기용
        claude_prompt = self._generate_claude_prompt(
            exc_type,
            exc_value,
            exc_traceback
        )
        lines.append("📋 Claude에게 붙여넣기용")
        lines.append("-" * 70)
        lines.append("다음을 복사해서 Claude에게 보내세요:")
        lines.append("")
        lines.append("'''")
        lines.extend(claude_prompt)
        lines.append("'''")
        lines.append("")

        # 스택 트레이스 (전체)
        lines.append("📊 전체 스택 트레이스")
        lines.append("-" * 70)
        lines.extend(traceback.format_exception(exc_type, exc_value, exc_traceback))

        return '\n'.join(lines)

    def _get_code_context(self, frame, context_lines: int = 3) -> list:
        """에러 발생 코드 컨텍스트 가져오기"""
        lines = []

        try:
            # 파일 읽기
            with open(frame.filename, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()

            # 컨텍스트 라인 계산
            error_line = frame.lineno
            start = max(0, error_line - context_lines - 1)
            end = min(len(file_lines), error_line + context_lines)

            # 라인 출력
            for i in range(start, end):
                line_num = i + 1
                line_text = file_lines[i].rstrip()

                if line_num == error_line:
                    lines.append(f"  {line_num} | {line_text}  ← 여기서 에러")
                else:
                    lines.append(f"  {line_num} | {line_text}")

        except Exception:
            lines.append("  (코드 컨텍스트를 가져올 수 없습니다)")

        return lines

    def _get_variable_state(self, exc_traceback) -> list:
        """에러 발생 시점의 변수 상태 가져오기"""
        lines = []

        try:
            # 마지막 프레임의 로컬 변수
            frame = exc_traceback.tb_frame

            local_vars = frame.f_locals

            # 중요 변수만 출력 (너무 많으면 생략)
            important_vars = {}
            for key, value in local_vars.items():
                # self, __builtins__ 등 제외
                if key.startswith('__') or key == 'self':
                    continue

                # 값 길이 제한
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."

                important_vars[key] = str_value

                # 최대 10개만
                if len(important_vars) >= 10:
                    break

            if important_vars:
                for key, value in important_vars.items():
                    lines.append(f"  {key}: {value}")
            else:
                lines.append("  (로컬 변수 없음)")

        except Exception:
            lines.append("  (변수 상태를 가져올 수 없습니다)")

        return lines

    def _analyze_error(self, exc_type, exc_value, exc_traceback) -> list:
        """에러 원인 분석"""
        lines = []

        error_name = exc_type.__name__
        error_message = str(exc_value)

        # 일반적인 에러 패턴 분석
        if error_name == "FileNotFoundError":
            lines.append("문제 원인:")
            lines.append("  - 파일 또는 디렉토리가 존재하지 않습니다")
            lines.append("  - 경로가 잘못되었을 수 있습니다")
            lines.append("  - 필요한 폴더가 생성되지 않았을 수 있습니다")

        elif error_name == "ModuleNotFoundError":
            module_name = error_message.split("'")[1] if "'" in error_message else "알 수 없음"
            lines.append("문제 원인:")
            lines.append(f"  - '{module_name}' 패키지가 설치되지 않았습니다")
            lines.append("  - requirements.txt에 누락되었을 수 있습니다")
            lines.append("  - 가상환경이 활성화되지 않았을 수 있습니다")

        elif error_name == "KeyError":
            key = error_message.strip("'\"")
            lines.append("문제 원인:")
            lines.append(f"  - 딕셔너리에 '{key}' 키가 존재하지 않습니다")
            lines.append("  - 설정 파일이 잘못되었을 수 있습니다")
            lines.append("  - 환경 변수가 설정되지 않았을 수 있습니다")

        elif error_name == "AttributeError":
            lines.append("문제 원인:")
            lines.append("  - 객체에 해당 속성 또는 메서드가 없습니다")
            lines.append("  - None 값을 참조했을 수 있습니다")
            lines.append("  - 타입이 예상과 다를 수 있습니다")

        elif error_name == "ConnectionError" or error_name == "ConnectionRefusedError":
            lines.append("문제 원인:")
            lines.append("  - 데이터베이스 또는 서비스에 연결할 수 없습니다")
            lines.append("  - 서비스가 실행 중이 아닐 수 있습니다")
            lines.append("  - 네트워크 문제일 수 있습니다")
            lines.append("  - 포트가 차단되었을 수 있습니다")

        elif error_name == "ImportError":
            lines.append("문제 원인:")
            lines.append("  - 모듈을 가져올 수 없습니다")
            lines.append("  - 순환 참조(circular import)일 수 있습니다")
            lines.append("  - 파일 구조가 잘못되었을 수 있습니다")

        elif "Database" in error_message or "sqlite" in error_message.lower():
            lines.append("문제 원인:")
            lines.append("  - 데이터베이스 연결 또는 쿼리 문제")
            lines.append("  - 데이터베이스 파일이 손상되었을 수 있습니다")
            lines.append("  - 테이블이 생성되지 않았을 수 있습니다")

        return lines

    def _get_solutions(self, exc_type, exc_value) -> list:
        """해결 방법 제시"""
        lines = []
        error_name = exc_type.__name__
        error_message = str(exc_value)

        if error_name == "FileNotFoundError":
            lines.append("[방법 1] 파일/폴더 확인 (추천)")
            lines.append("  1. 해당 파일이 존재하는지 확인하세요")
            lines.append("  2. 경로가 올바른지 확인하세요")
            lines.append("  3. 필요한 경우 폴더를 생성하세요")
            lines.append("")
            lines.append("[방법 2] 경로 수정")
            lines.append("  - 절대 경로 대신 상대 경로 사용")
            lines.append("  - Path 객체 사용 (pathlib)")

        elif error_name == "ModuleNotFoundError":
            module_name = error_message.split("'")[1] if "'" in error_message else "알 수 없음"
            lines.append("[방법 1] 패키지 설치 (추천)")
            lines.append("  다음 명령을 실행하세요:")
            lines.append(f"    pip install {module_name}")
            lines.append("")
            lines.append("[방법 2] requirements.txt 재설치")
            lines.append("    pip install -r requirements.txt")
            lines.append("")
            lines.append("[방법 3] 가상환경 확인")
            lines.append("  가상환경이 활성화되어 있는지 확인하세요")

        elif error_name == "KeyError":
            key = error_message.strip("'\"")
            lines.append("[방법 1] 환경 변수 설정 (추천)")
            lines.append("  1. .env 파일을 여세요")
            lines.append(f"  2. 다음 줄을 추가하세요:")
            lines.append(f"     {key}=적절한_값")
            lines.append("")
            lines.append("[방법 2] 기본값 사용")
            lines.append("  코드를 수정하여 기본값을 제공하세요:")
            lines.append(f"    value = dict.get('{key}', '기본값')")

        elif error_name in ["ConnectionError", "ConnectionRefusedError"]:
            lines.append("[방법 1] 서비스 시작")
            lines.append("  연결하려는 서비스가 실행 중인지 확인하세요")
            lines.append("")
            lines.append("[방법 2] 설정 확인")
            lines.append("  - 호스트 주소가 올바른지 확인")
            lines.append("  - 포트 번호가 올바른지 확인")
            lines.append("  - 방화벽 설정 확인")
            lines.append("")
            lines.append("[방법 3] 데이터베이스 초기화 (DB 에러인 경우)")
            lines.append("    python health_check.py")

        elif error_name == "AttributeError":
            lines.append("[방법 1] None 체크")
            lines.append("  객체가 None이 아닌지 확인하세요:")
            lines.append("    if obj is not None:")
            lines.append("        obj.method()")
            lines.append("")
            lines.append("[방법 2] 타입 확인")
            lines.append("  객체의 타입이 예상과 같은지 확인하세요")

        else:
            # 일반적인 해결 방법
            lines.append("[방법 1] health_check.py 실행")
            lines.append("    python health_check.py")
            lines.append("")
            lines.append("[방법 2] 로그 확인")
            lines.append("    logs/app.log 파일을 확인하세요")
            lines.append("")
            lines.append("[방법 3] 환경 재설정")
            lines.append("  1. 가상환경 재생성")
            lines.append("  2. 패키지 재설치")
            lines.append("  3. 데이터베이스 초기화")

        return lines

    def _generate_claude_prompt(self, exc_type, exc_value, exc_traceback) -> list:
        """Claude에게 붙여넣기용 프롬프트 생성"""
        lines = []

        error_name = exc_type.__name__
        error_message = str(exc_value)

        # 트레이스백에서 코드 위치 추출
        if exc_traceback:
            tb = traceback.extract_tb(exc_traceback)
            last_frame = tb[-1]

            lines.append(f"{error_name} 에러가 발생했습니다.")
            lines.append("")
            lines.append("에러 정보:")
            lines.append(f"- 파일: {Path(last_frame.filename).name}, {last_frame.lineno}번 줄")
            lines.append(f"- 에러: {error_name} - {error_message}")

            # 코드 컨텍스트
            code_lines = self._get_code_context(last_frame)
            if code_lines:
                lines.append("")
                lines.append("현재 코드:")
                lines.append("```python")
                lines.extend(code_lines)
                lines.append("```")

            lines.append("")
            lines.append("이 문제를 해결하는 코드를 작성해주세요.")

        return lines

    def save_error_report(self, report: str) -> Path:
        """에러 리포트 파일로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"error_report_{timestamp}.txt"
        filepath = self.error_reports_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        return filepath


# 전역 예외 핸들러 설정
def setup_global_exception_handler():
    """전역 예외 핸들러 설정"""
    handler = ErrorHandler()

    def exception_hook(exc_type, exc_value, exc_traceback):
        """sys.excepthook 함수"""
        # KeyboardInterrupt는 정상적인 종료이므로 리포트 생성하지 않음
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 에러 처리
        handler.handle_exception(exc_type, exc_value, exc_traceback)

    # sys.excepthook 설정
    sys.excepthook = exception_hook


# 프로그램 시작 시 자동으로 설정
setup_global_exception_handler()


if __name__ == "__main__":
    # 테스트용
    print("에러 핸들러 테스트")
    print("강제로 에러를 발생시킵니다...")

    # 테스트 에러
    try:
        # FileNotFoundError
        open("존재하지_않는_파일.txt", 'r')
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        handler = ErrorHandler()
        handler.handle_exception(exc_type, exc_value, exc_traceback)
