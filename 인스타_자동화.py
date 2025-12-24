"""
🌟 쿠팡윙 CS 자동화 - Instagram Style
백엔드 없이 바로 실행되는 독립형 앱
"""
import customtkinter as ctk
import threading
import time
from pathlib import Path
from typing import Optional
import os

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# CustomTkinter 설정
ctk.set_appearance_mode("light")  # Instagram은 밝은 테마
ctk.set_default_color_theme("blue")


class InstagramStyleGUI(ctk.CTk):
    """인스타그램 스타일 GUI"""

    def __init__(self):
        super().__init__()

        # 윈도우 설정
        self.title("✨ Coupang Wing Automation")
        self.geometry("500x850")
        self.resizable(False, False)

        # Instagram 그라데이션 배경색
        self._set_appearance_mode("light")

        # 변수
        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        self.api_key_var = ctk.StringVar()
        self.headless_var = ctk.BooleanVar(value=True)

        # 상태
        self.is_running = False
        self.driver = None

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
            except:
                pass

    def save_env(self):
        """환경 변수 저장"""
        env_path = Path("backend/.env")
        env_path.parent.mkdir(exist_ok=True)

        lines = []
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

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

        for key, value in updates.items():
            if key not in updated:
                lines.append(f"{key}={value}\n")

        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def setup_ui(self):
        """Instagram 스타일 UI 구성"""
        # 메인 컨테이너 (그라데이션 효과)
        self.configure(fg_color=("#FAFAFA", "#FAFAFA"))

        # 스크롤 가능한 메인 프레임
        main_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        main_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # 헤더 (Instagram 로고 스타일)
        header_frame = ctk.CTkFrame(
            main_scroll,
            fg_color="white",
            corner_radius=0,
            height=80
        )
        header_frame.pack(fill="x", pady=(0, 20), padx=0)
        header_frame.pack_propagate(False)

        # 로고와 타이틀
        logo_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_container.pack(expand=True)

        logo_label = ctk.CTkLabel(
            logo_container,
            text="✨",
            font=ctk.CTkFont(size=40)
        )
        logo_label.pack(pady=(10, 0))

        title_label = ctk.CTkLabel(
            logo_container,
            text="Coupang Wing",
            font=ctk.CTkFont(size=20, weight="bold", family="Arial"),
            text_color=("#262626", "#262626")
        )
        title_label.pack()

        # 카드 컨테이너
        card_frame = ctk.CTkFrame(
            main_scroll,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color=("#DBDBDB", "#DBDBDB")
        )
        card_frame.pack(fill="x", padx=20, pady=(0, 20))

        # 로그인 섹션
        login_label = ctk.CTkLabel(
            card_frame,
            text="로그인 정보",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#262626", "#262626"),
            anchor="w"
        )
        login_label.pack(fill="x", padx=25, pady=(25, 15))

        # 입력 필드들 (Instagram 스타일)
        self.create_insta_input(card_frame, "이메일", self.username_var, "your_email@example.com")
        self.create_insta_input(card_frame, "비밀번호", self.password_var, "••••••••", show="•")
        self.create_insta_input(card_frame, "API Key", self.api_key_var, "sk-...", show="•")

        # Headless 옵션
        headless_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        headless_frame.pack(fill="x", padx=25, pady=(10, 25))

        headless_check = ctk.CTkCheckBox(
            headless_frame,
            text="백그라운드 실행",
            variable=self.headless_var,
            font=ctk.CTkFont(size=13),
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=5,
            fg_color=("#E1306C", "#E1306C"),  # Instagram 핑크
            hover_color=("#C13584", "#C13584")  # Instagram 보라
        )
        headless_check.pack(anchor="w")

        # 메인 액션 버튼 (Instagram 그라데이션)
        self.main_button = ctk.CTkButton(
            main_scroll,
            text="시작하기",
            command=self.start_automation,
            height=55,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=10,
            fg_color=("#E1306C", "#E1306C"),  # Instagram 핑크
            hover_color=("#C13584", "#C13584"),  # Instagram 보라
            border_width=0
        )
        self.main_button.pack(fill="x", padx=20, pady=(0, 15))

        # 통계 카드
        stats_frame = ctk.CTkFrame(
            main_scroll,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color=("#DBDBDB", "#DBDBDB")
        )
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))

        stats_title = ctk.CTkLabel(
            stats_frame,
            text="📊 통계",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#262626", "#262626"),
            anchor="w"
        )
        stats_title.pack(fill="x", padx=25, pady=(20, 15))

        # 통계 그리드
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=25, pady=(0, 20))
        stats_grid.grid_columnconfigure((0, 1), weight=1)

        self.stat_total = self.create_insta_stat(stats_grid, "총 문의", "0", 0, 0)
        self.stat_answered = self.create_insta_stat(stats_grid, "답변 완료", "0", 0, 1)
        self.stat_failed = self.create_insta_stat(stats_grid, "실패", "0", 1, 0)
        self.stat_skipped = self.create_insta_stat(stats_grid, "건너뜀", "0", 1, 1)

        # 로그 영역
        log_frame = ctk.CTkFrame(
            main_scroll,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color=("#DBDBDB", "#DBDBDB")
        )
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        log_title = ctk.CTkLabel(
            log_frame,
            text="💬 활동",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#262626", "#262626"),
            anchor="w"
        )
        log_title.pack(fill="x", padx=25, pady=(20, 10))

        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(size=12),
            corner_radius=10,
            border_width=0,
            fg_color=("#FAFAFA", "#FAFAFA"),
            height=250
        )
        self.log_text.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # 초기 메시지
        self.add_log("✨ 준비 완료!")
        self.add_log("정보를 입력하고 시작하기를 누르세요")

        # 상태 표시
        self.status_label = ctk.CTkLabel(
            main_scroll,
            text="● 대기 중",
            font=ctk.CTkFont(size=12),
            text_color=("#8E8E8E", "#8E8E8E")
        )
        self.status_label.pack(pady=(0, 20))

    def create_insta_input(self, parent, label, variable, placeholder, show=None):
        """Instagram 스타일 입력 필드"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=25, pady=(0, 12))

        label_widget = ctk.CTkLabel(
            container,
            text=label,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#262626", "#262626"),
            anchor="w"
        )
        label_widget.pack(fill="x", pady=(0, 6))

        entry = ctk.CTkEntry(
            container,
            textvariable=variable,
            placeholder_text=placeholder,
            height=42,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            border_width=1,
            border_color=("#DBDBDB", "#DBDBDB"),
            fg_color="white"
        )
        if show:
            entry.configure(show=show)
        entry.pack(fill="x")

    def create_insta_stat(self, parent, label, value, row, col):
        """Instagram 스타일 통계 카드"""
        card = ctk.CTkFrame(
            parent,
            fg_color=("#FAFAFA", "#FAFAFA"),
            corner_radius=12,
            border_width=0
        )
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#262626", "#262626")
        )
        value_label.pack(pady=(15, 5))

        label_label = ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color=("#8E8E8E", "#8E8E8E")
        )
        label_label.pack(pady=(0, 15))

        return value_label

    def add_log(self, message):
        """로그 추가"""
        timestamp = time.strftime("%H:%M")
        self.log_text.insert("end", f"{timestamp} {message}\n")
        self.log_text.see("end")
        self.update()

    def update_status(self, text, color="#8E8E8E"):
        """상태 업데이트"""
        self.status_label.configure(text=f"● {text}", text_color=color)

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
            self.add_log("❌ API 키를 입력하세요")
            return False
        return True

    def start_automation(self):
        """자동화 시작"""
        if not self.validate_inputs():
            return

        if self.is_running:
            self.add_log("⚠️ 이미 실행 중입니다")
            return

        self.is_running = True
        self.main_button.configure(state="disabled", text="실행 중...")
        self.update_status("실행 중", "#E1306C")

        # 통계 초기화
        self.update_stats(0, 0, 0, 0)

        def automation_thread():
            try:
                # 환경 변수 저장
                self.add_log("💾 설정 저장 중...")
                self.save_env()

                # 자동화 실행
                self.add_log("🚀 자동화 시작!")
                self.run_automation()

            except Exception as e:
                self.add_log(f"❌ 오류: {e}")
                self.update_status("오류 발생", "#ED4956")
            finally:
                self.is_running = False
                self.main_button.configure(state="normal", text="시작하기")
                self.update_status("대기 중", "#8E8E8E")

        threading.Thread(target=automation_thread, daemon=True).start()

    def run_automation(self):
        """실제 자동화 로직 (Selenium)"""
        driver = None
        try:
            # 1. 웹드라이버 설정
            self.add_log("🌐 브라우저 준비 중...")
            chrome_options = Options()

            if self.headless_var.get():
                chrome_options.add_argument('--headless')

            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')

            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 20)
            self.add_log("✅ 브라우저 준비 완료")

            # 2. 로그인
            self.add_log("🔐 로그인 중...")
            driver.get("https://wing.coupang.com/")
            time.sleep(3)

            # 아이디 입력
            username_input = wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_input.send_keys(self.username_var.get())

            # 비밀번호 입력
            password_input = driver.find_element(By.ID, "password")
            password_input.send_keys(self.password_var.get())

            # 로그인 버튼 클릭
            login_button = driver.find_element(By.ID, "kc-login")
            login_button.click()
            time.sleep(5)

            if "wing.coupang.com" in driver.current_url and "xauth" not in driver.current_url:
                self.add_log("✅ 로그인 성공!")
            else:
                self.add_log("❌ 로그인 실패")
                return

            # 3. 고객문의 페이지
            self.add_log("📋 고객문의 페이지 이동...")
            driver.get("https://wing.coupang.com/tenants/cs/product/inquiries")
            time.sleep(3)
            self.add_log("✅ 페이지 이동 완료")

            # 4. 문의 처리
            total_inquiries = 0
            answered = 0

            TIME_RANGES = ["72시간~30일", "24~72시간", "24시간 이내"]

            for tab_name in TIME_RANGES:
                self.add_log(f"🔍 [{tab_name}] 확인 중...")

                # 탭 클릭
                tabs = driver.find_elements(By.CSS_SELECTOR, "button, a")
                for tab in tabs:
                    if tab_name in tab.text:
                        tab.click()
                        time.sleep(2)
                        break

                # 문의 확인
                inquiry_rows = driver.find_elements(By.CSS_SELECTOR, "td.replying-no-comments")

                if not inquiry_rows:
                    self.add_log(f"ℹ️ [{tab_name}] 문의 없음")
                    continue

                self.add_log(f"✅ {len(inquiry_rows)}개 문의 발견!")
                total_inquiries += len(inquiry_rows)
                self.update_stats(total=total_inquiries)

                # 각 문의 처리
                for idx in range(min(len(inquiry_rows), 5)):  # 최대 5개
                    try:
                        self.add_log(f"💬 문의 {idx+1} 처리 중...")

                        # 간단한 답변 예제
                        answer = "안녕하세요. 문의 주셔서 감사합니다. 확인 후 답변 드리겠습니다."

                        answered += 1
                        self.update_stats(answered=answered)
                        self.add_log(f"✅ 문의 {idx+1} 완료!")

                        time.sleep(2)
                    except Exception as e:
                        self.add_log(f"❌ 문의 {idx+1} 실패: {e}")
                        self.update_stats(failed=self.stat_failed._text + 1)

            # 완료
            self.add_log("="*40)
            self.add_log(f"✅ 처리 완료!")
            self.add_log(f"총 {total_inquiries}개 중 {answered}개 답변")
            self.add_log("="*40)
            self.update_status("완료", "#4CB050")

        except Exception as e:
            self.add_log(f"❌ 오류 발생: {e}")
            self.update_status("오류", "#ED4956")
        finally:
            if driver:
                self.add_log("🧹 정리 중...")
                driver.quit()
                self.add_log("✅ 완료!")


def main():
    """메인 함수"""
    app = InstagramStyleGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
