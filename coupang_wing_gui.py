"""
🚀 쿠팡윙 CS 자동화 - 프리미엄 GUI
최신 트렌드 디자인 + 완전 자동화
"""
import customtkinter as ctk
import threading
import requests
import time
import os
import socket
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional, Tuple
import json

# CustomTkinter 설정
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ServerManager:
    """서버 관리 클래스"""

    def __init__(self):
        self.backend_process = None
        self.backend_port = None
        self.is_running = False

    def find_free_port(self, start_port=8000, end_port=8100):
        """사용 가능한 포트 찾기"""
        for port in range(start_port, end_port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return None

    def start_backend_server(self, log_callback):
        """백엔드 서버 시작"""
        try:
            # 포트 찾기
            port = self.find_free_port()
            if not port:
                log_callback("❌ 사용 가능한 포트를 찾을 수 없습니다")
                return False

            self.backend_port = port
            log_callback(f"✅ 포트 {port} 발견")

            # 서버 시작
            backend_dir = Path("backend")
            venv_python = Path("venv/Scripts/python.exe")

            if not venv_python.exists():
                log_callback("❌ 가상환경을 찾을 수 없습니다")
                return False

            log_callback("🚀 백엔드 서버 시작 중...")

            # 백그라운드에서 서버 실행
            self.backend_process = subprocess.Popen(
                [str(venv_python), "-m", "uvicorn", "app.main:app",
                 "--host", "0.0.0.0", "--port", str(port)],
                cwd=str(backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            # 서버 시작 대기
            max_retries = 30
            for i in range(max_retries):
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=2)
                    if response.status_code == 200:
                        self.is_running = True
                        log_callback(f"✅ 서버 시작 완료 (http://localhost:{port})")
                        return True
                except:
                    time.sleep(0.5)
                    if i % 5 == 0:
                        log_callback(f"⏳ 서버 시작 대기 중... ({i+1}/{max_retries})")

            log_callback("❌ 서버 시작 시간 초과")
            return False

        except Exception as e:
            log_callback(f"❌ 서버 시작 실패: {e}")
            return False

    def stop_server(self):
        """서버 중지"""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process = None
            self.is_running = False


class ModernProgressBar(ctk.CTkFrame):
    """모던한 프로그레스 바"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")

        self.progress_bar = ctk.CTkProgressBar(
            self,
            mode="indeterminate",
            height=8,
            corner_radius=4,
            border_width=0,
            progress_color=("#3b82f6", "#2563eb")
        )
        self.progress_bar.pack(fill="x", expand=True)
        self.progress_bar.set(0)

    def start(self):
        """프로그레스 바 시작"""
        self.progress_bar.start()

    def stop(self):
        """프로그레스 바 중지"""
        self.progress_bar.stop()
        self.progress_bar.set(0)


class GlassFrame(ctk.CTkFrame):
    """유리 효과 프레임"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            corner_radius=20,
            border_width=1,
            border_color=("#e5e7eb", "#374151"),
            fg_color=("#ffffff", "#1f2937")
        )


class CoupangWingModernGUI(ctk.CTk):
    """쿠팡윙 CS 자동화 - 프리미엄 GUI"""

    def __init__(self):
        super().__init__()

        # 윈도우 설정
        self.title("🚀 쿠팡윙 CS 자동화 Pro")
        self.geometry("1200x850")

        # 서버 매니저
        self.server_manager = ServerManager()

        # 변수
        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        self.api_key_var = ctk.StringVar()
        self.headless_var = ctk.BooleanVar(value=True)

        # 상태
        self.is_running = False

        # .env 로드
        self.load_env()

        # UI 구성
        self.setup_ui()

    def load_env(self):
        """환경 변수 로드"""
        env_path = Path("backend/.env")
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            value = value.strip().strip('"').strip("'")

                            if key == 'COUPANG_WING_USERNAME':
                                self.username_var.set(value)
                            elif key == 'COUPANG_WING_PASSWORD':
                                self.password_var.set(value)
                            elif key == 'OPENAI_API_KEY':
                                self.api_key_var.set(value)
            except Exception as e:
                print(f"환경 변수 로드 실패: {e}")

    def save_env(self):
        """환경 변수 저장"""
        env_path = Path("backend/.env")
        env_path.parent.mkdir(exist_ok=True)

        # 기존 파일 읽기
        lines = []
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        # 업데이트
        updates = {
            'COUPANG_WING_USERNAME': self.username_var.get(),
            'COUPANG_WING_PASSWORD': self.password_var.get(),
            'OPENAI_API_KEY': self.api_key_var.get(),
            'OPENAI_MODEL': 'gpt-4'
        }

        updated = set()
        for i, line in enumerate(lines):
            for key, value in updates.items():
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    updated.add(key)

        # 새로운 키 추가
        for key, value in updates.items():
            if key not in updated:
                lines.append(f"{key}={value}\n")

        # 저장
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def setup_ui(self):
        """UI 구성"""
        # 그라데이션 배경 효과
        self.configure(fg_color=("#f8fafc", "#0f172a"))

        # 메인 컨테이너
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)

        # 헤더
        self.create_header(main_container)

        # 컨텐츠 영역 (2열)
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", pady=20)
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # 왼쪽: 설정 패널
        self.create_settings_panel(content_frame)

        # 오른쪽: 모니터링 패널
        self.create_monitoring_panel(content_frame)

        main_container.grid_rowconfigure(1, weight=1)

    def create_header(self, parent):
        """헤더 생성"""
        header_frame = GlassFrame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        # 좌측: 로고와 타이틀
        left_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_frame.pack(side="left", padx=30, pady=20)

        title = ctk.CTkLabel(
            left_frame,
            text="🚀 쿠팡윙 CS 자동화",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=("#3b82f6", "#60a5fa")
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            left_frame,
            text="AI 기반 완전 자동화 시스템",
            font=ctk.CTkFont(size=14),
            text_color=("#6b7280", "#9ca3af")
        )
        subtitle.pack(anchor="w", pady=(5, 0))

        # 우측: 상태 표시
        self.status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        self.status_frame.pack(side="right", padx=30, pady=20)

        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color="gray"
        )
        self.status_indicator.pack(side="left", padx=(0, 10))

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="시스템 대기 중",
            font=ctk.CTkFont(size=14),
            text_color=("#6b7280", "#9ca3af")
        )
        self.status_label.pack(side="left")

    def create_settings_panel(self, parent):
        """설정 패널 생성"""
        panel = GlassFrame(parent)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # 스크롤 가능한 프레임
        scroll_frame = ctk.CTkScrollableFrame(
            panel,
            fg_color="transparent",
            corner_radius=0
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 섹션 제목
        ctk.CTkLabel(
            scroll_frame,
            text="⚙️ 설정",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 20))

        # 로그인 정보 섹션
        login_section = self.create_section(scroll_frame, "🔐 로그인 정보")

        self.create_input_field(login_section, "이메일", self.username_var, "your_email@example.com")
        self.create_input_field(login_section, "비밀번호", self.password_var, "••••••••", show="•")
        self.create_input_field(login_section, "OpenAI API Key", self.api_key_var, "sk-...", show="•")

        # 실행 옵션 섹션
        options_section = self.create_section(scroll_frame, "🎯 실행 옵션")

        headless_check = ctk.CTkCheckBox(
            options_section,
            text="Headless 모드 (백그라운드 실행)",
            variable=self.headless_var,
            font=ctk.CTkFont(size=13),
            checkbox_width=24,
            checkbox_height=24,
            corner_radius=6
        )
        headless_check.pack(anchor="w", pady=10)

        # 메인 실행 버튼
        self.main_button = ctk.CTkButton(
            scroll_frame,
            text="▶️  자동화 시작",
            command=self.run_full_automation,
            height=70,
            font=ctk.CTkFont(size=22, weight="bold"),
            corner_radius=15,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1e40af"),
            border_width=0
        )
        self.main_button.pack(fill="x", pady=30)

        # 프로그레스 바
        self.progress_bar = ModernProgressBar(scroll_frame)
        self.progress_bar.pack(fill="x", pady=(0, 20))

        # 추가 버튼들
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        test_btn = ctk.CTkButton(
            button_frame,
            text="🔍 로그인 테스트",
            command=self.test_login_only,
            height=45,
            font=ctk.CTkFont(size=14),
            corner_radius=10,
            fg_color=("#8b5cf6", "#7c3aed"),
            hover_color=("#7c3aed", "#6d28d9")
        )
        test_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        stop_btn = ctk.CTkButton(
            button_frame,
            text="⏹️ 중지",
            command=self.stop_automation,
            height=45,
            font=ctk.CTkFont(size=14),
            corner_radius=10,
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c")
        )
        stop_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def create_monitoring_panel(self, parent):
        """모니터링 패널 생성"""
        panel = GlassFrame(parent)
        panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        container = ctk.CTkFrame(panel, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # 섹션 제목
        ctk.CTkLabel(
            container,
            text="📊 실시간 모니터링",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 20))

        # 통계 카드
        stats_frame = ctk.CTkFrame(container, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_total = self.create_stat_card(stats_frame, "총 문의", "0", 0, "#3b82f6")
        self.stat_answered = self.create_stat_card(stats_frame, "답변 완료", "0", 1, "#10b981")
        self.stat_failed = self.create_stat_card(stats_frame, "실패", "0", 2, "#ef4444")
        self.stat_skipped = self.create_stat_card(stats_frame, "건너뜀", "0", 3, "#f59e0b")

        # 로그 영역
        log_label = ctk.CTkLabel(
            container,
            text="📝 실행 로그",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w"
        )
        log_label.pack(fill="x", pady=(20, 10))

        # 로그 텍스트박스
        self.log_text = ctk.CTkTextbox(
            container,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=10,
            wrap="word",
            border_width=0
        )
        self.log_text.pack(fill="both", expand=True)

        # 초기 메시지
        self.add_log("✨ 시스템 준비 완료")
        self.add_log("💡 설정을 입력하고 '자동화 시작' 버튼을 클릭하세요")

    def create_section(self, parent, title):
        """섹션 생성"""
        frame = ctk.CTkFrame(parent, fg_color=("#f1f5f9", "#1e293b"), corner_radius=15)
        frame.pack(fill="x", pady=(0, 20))

        # 제목
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(20, 15))

        # 컨텐츠 컨테이너
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=(0, 20))

        return content

    def create_input_field(self, parent, label, variable, placeholder, show=None):
        """입력 필드 생성"""
        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            text_color=("#374151", "#d1d5db")
        ).pack(fill="x", pady=(10, 5))

        entry = ctk.CTkEntry(
            parent,
            textvariable=variable,
            placeholder_text=placeholder,
            height=45,
            font=ctk.CTkFont(size=13),
            corner_radius=10,
            border_width=1,
            border_color=("#e5e7eb", "#374151")
        )
        if show:
            entry.configure(show=show)
        entry.pack(fill="x", pady=(0, 5))

    def create_stat_card(self, parent, label, value, column, color):
        """통계 카드 생성"""
        card = ctk.CTkFrame(
            parent,
            corner_radius=15,
            fg_color=(color, color),
            border_width=0
        )
        card.grid(row=0, column=column, padx=5, sticky="ew")

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="white"
        )
        value_label.pack(pady=(20, 5))

        label_label = ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        label_label.pack(pady=(0, 20))

        return value_label

    def add_log(self, message):
        """로그 추가"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.update()

    def update_status(self, text, color="gray"):
        """상태 업데이트"""
        self.status_label.configure(text=text)
        self.status_indicator.configure(text_color=color)

    def update_stats(self, total=None, answered=None, failed=None, skipped=None):
        """통계 업데이트"""
        if total is not None:
            self.stat_total.configure(text=str(total))
        if answered is not None:
            self.stat_answered.configure(text=str(answered))
        if failed is not None:
            self.stat_failed.configure(text=str(failed))
        if skipped is not None:
            self.stat_skipped.configure(text=str(skipped))

    def validate_inputs(self):
        """입력 검증"""
        if not self.username_var.get():
            self.add_log("❌ 이메일을 입력하세요")
            return False
        if not self.password_var.get():
            self.add_log("❌ 비밀번호를 입력하세요")
            return False
        if not self.api_key_var.get():
            self.add_log("❌ OpenAI API 키를 입력하세요")
            return False
        return True

    def run_full_automation(self):
        """완전 자동화 실행"""
        if not self.validate_inputs():
            return

        if self.is_running:
            self.add_log("⚠️  이미 실행 중입니다")
            return

        self.is_running = True
        self.main_button.configure(state="disabled")
        self.progress_bar.start()

        def automation_thread():
            try:
                # 1. 환경 변수 저장
                self.add_log("=" * 60)
                self.add_log("🚀 쿠팡윙 CS 자동화 시작")
                self.add_log("=" * 60)

                self.update_status("환경 설정 중...", "#f59e0b")
                self.add_log("💾 환경 변수 저장 중...")
                self.save_env()
                self.add_log("✅ 환경 변수 저장 완료")

                # 2. 서버 시작
                self.update_status("서버 시작 중...", "#f59e0b")
                if not self.server_manager.is_running:
                    self.add_log("🌐 백엔드 서버 시작 중...")
                    if not self.server_manager.start_backend_server(self.add_log):
                        self.add_log("❌ 서버 시작 실패")
                        return
                else:
                    self.add_log("✅ 서버가 이미 실행 중입니다")

                # 3. 자동화 실행
                self.update_status("자동화 실행 중...", "#3b82f6")
                self.add_log("🤖 V2 자동화 시작...")
                self.add_log(f"ℹ️  Headless 모드: {self.headless_var.get()}")

                port = self.server_manager.backend_port
                response = requests.post(
                    f"http://localhost:{port}/api/wing-web/auto-answer-v2",
                    json={
                        "username": self.username_var.get(),
                        "password": self.password_var.get(),
                        "headless": self.headless_var.get()
                    },
                    timeout=300
                )

                if response.status_code == 200:
                    result = response.json()
                    stats = result.get('statistics', {})

                    # 통계 업데이트
                    self.update_stats(
                        total=stats.get('total_inquiries', 0),
                        answered=stats.get('answered', 0),
                        failed=stats.get('failed', 0),
                        skipped=stats.get('skipped', 0)
                    )

                    self.add_log("=" * 60)
                    self.add_log(f"✅ {result.get('message', '처리 완료')}")
                    self.add_log(f"📊 총 문의: {stats.get('total_inquiries', 0)}")
                    self.add_log(f"✅ 답변 완료: {stats.get('answered', 0)}")
                    self.add_log(f"❌ 실패: {stats.get('failed', 0)}")
                    self.add_log(f"⏭️  건너뜀: {stats.get('skipped', 0)}")
                    self.add_log("=" * 60)

                    self.update_status("완료", "#10b981")
                else:
                    self.add_log(f"❌ 서버 오류: {response.status_code}")
                    self.add_log(f"   {response.text}")
                    self.update_status("오류 발생", "#ef4444")

            except requests.exceptions.Timeout:
                self.add_log("❌ 요청 시간 초과 (5분)")
                self.update_status("시간 초과", "#ef4444")
            except Exception as e:
                self.add_log(f"❌ 오류 발생: {e}")
                self.update_status("오류 발생", "#ef4444")
            finally:
                self.is_running = False
                self.main_button.configure(state="normal")
                self.progress_bar.stop()

        threading.Thread(target=automation_thread, daemon=True).start()

    def test_login_only(self):
        """로그인만 테스트"""
        if not self.validate_inputs():
            return

        self.add_log("🔍 로그인 테스트 시작...")
        self.progress_bar.start()

        def test_thread():
            try:
                # 환경 변수 저장
                self.save_env()

                # 서버 확인
                if not self.server_manager.is_running:
                    if not self.server_manager.start_backend_server(self.add_log):
                        return

                # 로그인 테스트
                port = self.server_manager.backend_port
                response = requests.post(
                    f"http://localhost:{port}/api/wing-web/test-login",
                    json={
                        "username": self.username_var.get(),
                        "password": self.password_var.get(),
                        "headless": self.headless_var.get()
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.add_log(f"✅ {result.get('message', '로그인 성공!')}")
                    else:
                        self.add_log(f"❌ {result.get('message', '로그인 실패')}")
                else:
                    self.add_log(f"❌ 서버 오류: {response.status_code}")

            except Exception as e:
                self.add_log(f"❌ 로그인 테스트 실패: {e}")
            finally:
                self.progress_bar.stop()

        threading.Thread(target=test_thread, daemon=True).start()

    def stop_automation(self):
        """자동화 중지"""
        if self.is_running:
            self.add_log("⏹️  중지 요청 (현재 작업은 완료됩니다)")
            self.is_running = False
        else:
            self.add_log("ℹ️  실행 중인 작업이 없습니다")


def main():
    """메인 함수"""
    app = CoupangWingModernGUI()

    # 종료 시 서버 정리
    def on_closing():
        if app.server_manager.is_running:
            app.server_manager.stop_server()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
