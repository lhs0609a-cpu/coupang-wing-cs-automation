"""
쿠팡윙 CS 자동화 - 트렌디한 GUI 런처
"""
import customtkinter as ctk
import threading
import requests
import time
import os
from pathlib import Path
from typing import Optional
import json

# CustomTkinter 설정
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CoupangWingGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 윈도우 설정
        self.title("🚀 쿠팡윙 CS 자동화 V2")
        self.geometry("1000x800")
        self.resizable(True, True)

        # 변수 초기화
        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        self.api_key_var = ctk.StringVar()
        self.headless_var = ctk.BooleanVar(value=True)
        self.auto_mode_var = ctk.BooleanVar(value=False)

        # .env 파일에서 기본값 로드
        self.load_env_defaults()

        # 서버 상태
        self.server_running = False
        self.automation_running = False

        # UI 구성
        self.setup_ui()

        # 서버 상태 체크 시작
        self.check_server_status()

    def load_env_defaults(self):
        """env 파일에서 기본값 로드"""
        env_path = Path("backend/.env")
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")

                                if key == 'COUPANG_WING_USERNAME':
                                    self.username_var.set(value)
                                elif key == 'COUPANG_WING_PASSWORD':
                                    self.password_var.set(value)
                                elif key == 'OPENAI_API_KEY':
                                    self.api_key_var.set(value)
            except Exception as e:
                print(f"env 파일 로드 중 오류: {e}")

    def setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너 (2열 레이아웃)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # 왼쪽 패널 - 설정 및 컨트롤
        self.left_panel = ctk.CTkFrame(self, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # 오른쪽 패널 - 로그 및 통계
        self.right_panel = ctk.CTkFrame(self, corner_radius=0, fg_color=("#E8E8E8", "#1a1a1a"))
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        # 왼쪽 패널 구성
        self.setup_left_panel()

        # 오른쪽 패널 구성
        self.setup_right_panel()

    def setup_left_panel(self):
        """왼쪽 패널 UI 구성"""
        self.left_panel.grid_rowconfigure(10, weight=1)

        # 헤더
        header = ctk.CTkLabel(
            self.left_panel,
            text="🚀 쿠팡윙 CS 자동화",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=("#1f538d", "#3a7ebf")
        )
        header.grid(row=0, column=0, columnspan=2, pady=(30, 10), padx=30, sticky="w")

        subtitle = ctk.CTkLabel(
            self.left_panel,
            text="V2 - 완전 자동화 시스템",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle.grid(row=1, column=0, columnspan=2, pady=(0, 30), padx=30, sticky="w")

        # 로그인 정보 섹션
        login_frame = ctk.CTkFrame(self.left_panel, corner_radius=15)
        login_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=30, sticky="ew")

        ctk.CTkLabel(
            login_frame,
            text="🔐 로그인 정보",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(20, 15), padx=20, sticky="w")

        # 아이디
        ctk.CTkLabel(
            login_frame,
            text="아이디",
            font=ctk.CTkFont(size=14)
        ).grid(row=1, column=0, pady=(10, 5), padx=20, sticky="w")

        self.username_entry = ctk.CTkEntry(
            login_frame,
            textvariable=self.username_var,
            placeholder_text="your_email@example.com",
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=10
        )
        self.username_entry.grid(row=2, column=0, columnspan=2, pady=(0, 10), padx=20, sticky="ew")

        # 비밀번호
        ctk.CTkLabel(
            login_frame,
            text="비밀번호",
            font=ctk.CTkFont(size=14)
        ).grid(row=3, column=0, pady=(10, 5), padx=20, sticky="w")

        self.password_entry = ctk.CTkEntry(
            login_frame,
            textvariable=self.password_var,
            placeholder_text="••••••••",
            show="•",
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=10
        )
        self.password_entry.grid(row=4, column=0, columnspan=2, pady=(0, 10), padx=20, sticky="ew")

        # API 키
        ctk.CTkLabel(
            login_frame,
            text="OpenAI API Key",
            font=ctk.CTkFont(size=14)
        ).grid(row=5, column=0, pady=(10, 5), padx=20, sticky="w")

        self.api_key_entry = ctk.CTkEntry(
            login_frame,
            textvariable=self.api_key_var,
            placeholder_text="sk-...",
            show="•",
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=10
        )
        self.api_key_entry.grid(row=6, column=0, columnspan=2, pady=(0, 20), padx=20, sticky="ew")

        login_frame.grid_columnconfigure(0, weight=1)

        # 설정 섹션
        settings_frame = ctk.CTkFrame(self.left_panel, corner_radius=15)
        settings_frame.grid(row=3, column=0, columnspan=2, pady=10, padx=30, sticky="ew")

        ctk.CTkLabel(
            settings_frame,
            text="⚙️ 실행 설정",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(20, 15), padx=20, sticky="w")

        # Headless 모드
        self.headless_checkbox = ctk.CTkCheckBox(
            settings_frame,
            text="Headless 모드 (백그라운드 실행)",
            variable=self.headless_var,
            font=ctk.CTkFont(size=13),
            corner_radius=8
        )
        self.headless_checkbox.grid(row=1, column=0, pady=10, padx=20, sticky="w")

        # 자동 모드
        self.auto_mode_checkbox = ctk.CTkCheckBox(
            settings_frame,
            text="자동 모드 (5분마다 체크)",
            variable=self.auto_mode_var,
            font=ctk.CTkFont(size=13),
            corner_radius=8
        )
        self.auto_mode_checkbox.grid(row=2, column=0, pady=(0, 20), padx=20, sticky="w")

        # 버튼 섹션
        button_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=2, pady=20, padx=30, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        # 로그인 테스트 버튼
        self.test_login_btn = ctk.CTkButton(
            button_frame,
            text="🔍 로그인 테스트",
            command=self.test_login,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=("#3a7ebf", "#1f538d"),
            hover_color=("#5591c5", "#2d6ca8")
        )
        self.test_login_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        # 서버 시작 버튼
        self.server_btn = ctk.CTkButton(
            button_frame,
            text="🌐 서버 시작",
            command=self.toggle_server,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=("#2a9d8f", "#264653"),
            hover_color=("#3bb3a4", "#2e5763")
        )
        self.server_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # 메인 실행 버튼 (크고 눈에 띄게)
        self.run_btn = ctk.CTkButton(
            self.left_panel,
            text="▶️ 자동화 시작",
            command=self.run_automation,
            height=60,
            font=ctk.CTkFont(size=20, weight="bold"),
            corner_radius=15,
            fg_color=("#e76f51", "#c44536"),
            hover_color=("#f4845f", "#d65545")
        )
        self.run_btn.grid(row=5, column=0, columnspan=2, pady=20, padx=30, sticky="ew")

        # 중지 버튼
        self.stop_btn = ctk.CTkButton(
            self.left_panel,
            text="⏸️ 중지",
            command=self.stop_automation,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=12,
            fg_color=("#666666", "#444444"),
            hover_color=("#777777", "#555555"),
            state="disabled"
        )
        self.stop_btn.grid(row=6, column=0, columnspan=2, pady=(0, 20), padx=30, sticky="ew")

        # 서버 상태 표시
        self.status_label = ctk.CTkLabel(
            self.left_panel,
            text="⚪ 서버: 연결 안됨",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.grid(row=7, column=0, columnspan=2, pady=(0, 20), padx=30, sticky="w")

    def setup_right_panel(self):
        """오른쪽 패널 UI 구성"""
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # 통계 카드
        stats_frame = ctk.CTkFrame(self.right_panel, corner_radius=15)
        stats_frame.grid(row=0, column=0, pady=30, padx=30, sticky="ew")
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            stats_frame,
            text="📊 통계",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=4, pady=(20, 15), padx=20, sticky="w")

        # 통계 카드들
        self.stat_total = self.create_stat_card(stats_frame, "총 문의", "0", 1)
        self.stat_answered = self.create_stat_card(stats_frame, "답변 완료", "0", 2)
        self.stat_failed = self.create_stat_card(stats_frame, "실패", "0", 3)
        self.stat_skipped = self.create_stat_card(stats_frame, "건너뜀", "0", 4)

        # 로그 섹션
        log_frame = ctk.CTkFrame(self.right_panel, corner_radius=15)
        log_frame.grid(row=1, column=0, pady=(0, 30), padx=30, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_frame,
            text="📝 실행 로그",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")

        # 로그 텍스트 박스
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=10,
            wrap="word"
        )
        self.log_text.grid(row=1, column=0, pady=(0, 20), padx=20, sticky="nsew")

        # 초기 로그 메시지
        self.add_log("✅ GUI 시스템 준비 완료")
        self.add_log("ℹ️  로그인 정보를 입력하고 '자동화 시작' 버튼을 클릭하세요")

    def create_stat_card(self, parent, label, value, column):
        """통계 카드 생성"""
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=("#3a7ebf", "#1f538d"))
        card.grid(row=1, column=column-1, pady=(0, 20), padx=10, sticky="ew")

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        value_label.pack(pady=(15, 5))

        label_label = ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=("#cccccc", "#aaaaaa")
        )
        label_label.pack(pady=(0, 15))

        return value_label

    def add_log(self, message):
        """로그 추가"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

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

    def check_server_status(self):
        """서버 상태 주기적 체크"""
        def check():
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    self.server_running = True
                    self.status_label.configure(
                        text="🟢 서버: 실행 중",
                        text_color=("#2a9d8f", "#3bb3a4")
                    )
                    self.server_btn.configure(text="🛑 서버 중지")
                else:
                    raise Exception()
            except:
                self.server_running = False
                self.status_label.configure(
                    text="⚪ 서버: 연결 안됨",
                    text_color="gray"
                )
                self.server_btn.configure(text="🌐 서버 시작")

            # 5초마다 체크
            self.after(5000, self.check_server_status)

        threading.Thread(target=check, daemon=True).start()

    def toggle_server(self):
        """서버 시작/중지"""
        if self.server_running:
            self.add_log("⚠️  서버 중지 기능은 수동으로 터미널에서 수행해주세요")
        else:
            self.add_log("🌐 서버 시작 중...")
            threading.Thread(target=self.start_server, daemon=True).start()

    def start_server(self):
        """서버 시작"""
        import subprocess
        try:
            # START.bat 실행
            subprocess.Popen(["cmd", "/c", "START.bat"], shell=True)
            self.add_log("✅ 서버 시작 명령 실행 완료")
            self.add_log("ℹ️  서버가 시작되는 데 약 10초 소요됩니다...")
        except Exception as e:
            self.add_log(f"❌ 서버 시작 실패: {e}")

    def test_login(self):
        """로그인 테스트"""
        if not self.validate_inputs():
            return

        self.add_log("🔍 로그인 테스트 시작...")
        self.test_login_btn.configure(state="disabled", text="테스트 중...")

        def test():
            try:
                # env 파일 업데이트
                self.save_to_env()

                response = requests.post(
                    "http://localhost:8000/api/wing-web/test-login",
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
                self.test_login_btn.configure(state="normal", text="🔍 로그인 테스트")

        threading.Thread(target=test, daemon=True).start()

    def run_automation(self):
        """자동화 실행"""
        if not self.validate_inputs():
            return

        if not self.server_running:
            self.add_log("❌ 서버가 실행되지 않았습니다. 먼저 서버를 시작하세요.")
            return

        self.add_log("=" * 50)
        self.add_log("🚀 V2 자동화 시작!")
        self.add_log("=" * 50)

        self.automation_running = True
        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # 통계 초기화
        self.update_stats(0, 0, 0, 0)

        def run():
            try:
                # env 파일 업데이트
                self.save_to_env()

                self.add_log(f"ℹ️  Headless 모드: {self.headless_var.get()}")
                self.add_log("⏳ 자동화 실행 중... (최대 5분 소요)")

                response = requests.post(
                    "http://localhost:8000/api/wing-web/auto-answer-v2",
                    json={
                        "username": self.username_var.get(),
                        "password": self.password_var.get(),
                        "headless": self.headless_var.get()
                    },
                    timeout=300
                )

                if response.status_code == 200:
                    result = response.json()

                    # 통계 업데이트
                    stats = result.get('statistics', {})
                    self.update_stats(
                        total=stats.get('total_inquiries', 0),
                        answered=stats.get('answered', 0),
                        failed=stats.get('failed', 0),
                        skipped=stats.get('skipped', 0)
                    )

                    self.add_log("=" * 50)
                    self.add_log(f"✅ {result.get('message', '처리 완료')}")
                    self.add_log(f"📊 총 문의: {stats.get('total_inquiries', 0)}")
                    self.add_log(f"✅ 답변 완료: {stats.get('answered', 0)}")
                    self.add_log(f"❌ 실패: {stats.get('failed', 0)}")
                    self.add_log(f"⏭️  건너뜀: {stats.get('skipped', 0)}")
                    self.add_log("=" * 50)
                else:
                    self.add_log(f"❌ 서버 오류: {response.status_code}")
                    self.add_log(f"   {response.text}")

            except requests.exceptions.Timeout:
                self.add_log("❌ 요청 시간 초과 (5분)")
                self.add_log("   문의가 많거나 서버가 느린 경우 발생할 수 있습니다")
            except Exception as e:
                self.add_log(f"❌ 자동화 실행 실패: {e}")
            finally:
                self.automation_running = False
                self.run_btn.configure(state="normal")
                self.stop_btn.configure(state="disabled")

        threading.Thread(target=run, daemon=True).start()

    def stop_automation(self):
        """자동화 중지"""
        self.add_log("⏸️  자동화 중지 요청 (현재 작업은 완료됩니다)")
        self.automation_running = False
        self.stop_btn.configure(state="disabled")

    def validate_inputs(self):
        """입력값 검증"""
        if not self.username_var.get():
            self.add_log("❌ 아이디를 입력하세요")
            return False

        if not self.password_var.get():
            self.add_log("❌ 비밀번호를 입력하세요")
            return False

        if not self.api_key_var.get():
            self.add_log("❌ OpenAI API 키를 입력하세요")
            return False

        return True

    def save_to_env(self):
        """설정을 .env 파일에 저장"""
        env_path = Path("backend/.env")
        env_content = []

        # 기존 .env 파일 읽기
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.readlines()

        # 업데이트할 키
        updates = {
            'COUPANG_WING_USERNAME': self.username_var.get(),
            'COUPANG_WING_PASSWORD': self.password_var.get(),
            'OPENAI_API_KEY': self.api_key_var.get()
        }

        # 기존 줄 업데이트
        updated_keys = set()
        for i, line in enumerate(env_content):
            for key, value in updates.items():
                if line.startswith(f"{key}="):
                    env_content[i] = f"{key}={value}\n"
                    updated_keys.add(key)

        # 새로운 키 추가
        for key, value in updates.items():
            if key not in updated_keys:
                env_content.append(f"{key}={value}\n")

        # 파일 저장
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(env_content)


def main():
    """메인 함수"""
    app = CoupangWingGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
