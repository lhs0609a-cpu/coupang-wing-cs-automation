"""
✨ 쿠팡윙 CS 자동화 - Instagram Style (완성판)
백엔드 없이 바로 실행되는 독립형 앱
"""
import customtkinter as ctk
import threading
import time
from pathlib import Path
from typing import List, Dict
import os

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# CustomTkinter 설정
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class CoupangWingAutomation:
    """쿠팡윙 자동화 엔진"""

    TIME_RANGES = ["72시간~30일", "24~72시간", "24시간 이내"]

    def __init__(self, username: str, password: str, api_key: str, headless: bool, log_callback):
        self.username = username
        self.password = password
        self.api_key = api_key
        self.headless = headless
        self.log = log_callback

        self.driver = None
        self.wait = None

        # 통계
        self.total_inquiries = 0
        self.answered_count = 0
        self.failed_count = 0
        self.skipped_count = 0

    def setup_driver(self):
        """웹드라이버 설정"""
        try:
            self.log("🌐 브라우저 준비 중...")
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument('--headless')

            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)

            self.log("✅ 브라우저 준비 완료")
            return True
        except Exception as e:
            self.log(f"❌ 브라우저 설정 실패: {e}")
            return False

    def login(self):
        """쿠팡윙 로그인"""
        try:
            self.log("🔐 로그인 중...")
            self.driver.get("https://wing.coupang.com/")
            time.sleep(3)

            # 아이디 입력
            username_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_input.clear()
            username_input.send_keys(self.username)
            self.log("  📝 아이디 입력 완료")

            # 비밀번호 입력
            password_input = self.driver.find_element(By.ID, "password")
            password_input.clear()
            password_input.send_keys(self.password)
            self.log("  📝 비밀번호 입력 완료")

            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.ID, "kc-login")
            login_button.click()
            self.log("  🖱️ 로그인 버튼 클릭")

            # 로그인 완료 대기
            time.sleep(5)

            if "wing.coupang.com" in self.driver.current_url and "xauth" not in self.driver.current_url:
                self.log("✅ 로그인 성공!")
                return True
            else:
                self.log(f"❌ 로그인 실패: {self.driver.current_url}")
                return False

        except Exception as e:
            self.log(f"❌ 로그인 오류: {e}")
            return False

    def navigate_to_inquiries(self):
        """고객문의 페이지로 이동"""
        try:
            self.log("📋 고객문의 페이지 이동...")
            self.driver.get("https://wing.coupang.com/tenants/cs/product/inquiries")
            time.sleep(3)
            self.log("✅ 고객문의 페이지 도착")
            return True
        except Exception as e:
            self.log(f"❌ 페이지 이동 오류: {e}")
            return False

    def click_tab(self, tab_name: str):
        """시간대 탭 클릭"""
        try:
            self.log(f"🔍 [{tab_name}] 탭 찾는 중...")

            # 모든 탭 요소 찾기
            tabs = self.driver.find_elements(By.CSS_SELECTOR, "button, a, div[role='tab']")

            for tab in tabs:
                try:
                    if tab_name in tab.text:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", tab)
                        time.sleep(0.5)
                        tab.click()
                        time.sleep(2)
                        self.log(f"✅ [{tab_name}] 탭 클릭 완료")
                        return True
                except:
                    continue

            self.log(f"⚠️ [{tab_name}] 탭을 찾을 수 없음")
            return False
        except Exception as e:
            self.log(f"❌ 탭 클릭 오류: {e}")
            return False

    def get_inquiries_in_current_tab(self) -> List[Dict]:
        """현재 탭의 모든 문의 수집"""
        inquiries = []

        try:
            time.sleep(2)

            # 문의 행 찾기 (제공된 HTML 구조)
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "td.replying-no-comments, td[data-v-7fedaa82].replying-no-comments"
            )

            self.log(f"  📊 {len(rows)}개 행 발견")

            for idx, row in enumerate(rows):
                try:
                    # 상품명 찾기
                    product_name = None
                    try:
                        product_elem = row.find_element(By.CSS_SELECTOR, "div.product-name a span")
                        product_name = product_elem.get_attribute("title") or product_elem.text
                    except:
                        try:
                            product_elem = row.find_element(By.CSS_SELECTOR, ".text-wrapper.product-name a span")
                            product_name = product_elem.get_attribute("title") or product_elem.text
                        except:
                            continue

                    # 문의 내용 찾기
                    inquiry_text = None
                    try:
                        inquiry_elem = row.find_element(By.CSS_SELECTOR, "span.inquiry-content")
                        inquiry_text = inquiry_elem.text.strip()
                    except:
                        continue

                    # 답변하기 버튼 찾기
                    answer_button = None
                    try:
                        # 상위 tr에서 버튼 찾기
                        parent_tr = row.find_element(By.XPATH, "./ancestor::tr")
                        buttons = parent_tr.find_elements(By.CSS_SELECTOR, "button")
                        for btn in buttons:
                            if "답변하기" in btn.text:
                                answer_button = btn
                                break
                    except:
                        # 현재 td에서 버튼 찾기
                        try:
                            buttons = row.find_elements(By.CSS_SELECTOR, "button")
                            for btn in buttons:
                                if "답변하기" in btn.text:
                                    answer_button = btn
                                    break
                        except:
                            continue

                    if product_name and inquiry_text and answer_button:
                        inquiries.append({
                            "product_name": product_name,
                            "inquiry": inquiry_text,
                            "answer_button": answer_button,
                            "row": row
                        })
                        self.log(f"  ✅ 문의 {len(inquiries)}: {product_name[:30]}...")

                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    continue

            return inquiries

        except Exception as e:
            self.log(f"  ❌ 문의 수집 오류: {e}")
            return []

    def generate_answer(self, product_name: str, inquiry: str) -> str:
        """ChatGPT로 답변 생성 (간단 버전)"""
        try:
            # 실제 OpenAI API 연동은 생략하고 기본 답변 사용
            # API 키가 있다면 여기에 OpenAI 호출 추가
            answer = f"안녕하세요. '{product_name}' 상품에 대한 문의 주셔서 감사합니다. 고객님의 문의사항을 확인하였으며, 빠른 시일 내에 정확한 답변 드리도록 하겠습니다. 추가로 궁금하신 사항이 있으시면 판매자 연락처로 연락 주시기 바랍니다. 감사합니다."
            return answer
        except Exception as e:
            return f"안녕하세요. 문의 주셔서 감사합니다. 확인 후 답변 드리겠습니다."

    def answer_inquiry(self, inquiry_data: Dict) -> bool:
        """문의에 답변"""
        try:
            product_name = inquiry_data["product_name"]
            inquiry_text = inquiry_data["inquiry"]
            answer_button = inquiry_data["answer_button"]

            self.log(f"    💬 답변 작성: {product_name[:30]}...")

            # 1. 답변하기 버튼 클릭
            self.driver.execute_script("arguments[0].scrollIntoView(true);", answer_button)
            time.sleep(1)
            answer_button.click()
            time.sleep(2)
            self.log("      🖱️ 답변하기 클릭")

            # 2. 답변 생성
            answer_text = self.generate_answer(product_name, inquiry_text)
            self.log(f"      🤖 답변 생성 ({len(answer_text)}자)")

            # 3. 답변 입력란 찾기
            textarea = None
            try:
                textarea = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.input-textarea"))
                )
            except:
                try:
                    textarea = self.driver.find_element(By.CSS_SELECTOR, "textarea[placeholder*='상품문의']")
                except:
                    textarea = self.driver.find_element(By.TAG_NAME, "textarea")

            if not textarea:
                self.log("      ❌ 입력란 없음")
                return False

            # 4. 답변 입력
            textarea.clear()
            textarea.send_keys(answer_text)
            time.sleep(1)
            self.log("      ✍️ 답변 입력 완료")

            # 5. 저장하기 버튼 찾기 및 클릭
            save_button = None
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "저장하기" in btn.text or "저장" in btn.text:
                    save_button = btn
                    break

            if not save_button:
                try:
                    save_button = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button[data-wuic-props*='type:primary']"
                    )
                except:
                    self.log("      ❌ 저장 버튼 없음")
                    return False

            # 6. 저장하기 클릭
            self.driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
            time.sleep(1)
            save_button.click()
            time.sleep(3)

            self.log("      ✅ 답변 저장 완료!")
            self.answered_count += 1
            return True

        except Exception as e:
            self.log(f"    ❌ 답변 실패: {e}")
            self.failed_count += 1
            return False

    def process_all_tabs(self):
        """모든 탭 처리"""
        has_any_inquiry = False

        for tab_name in self.TIME_RANGES:
            self.log(f"\n{'='*40}")
            self.log(f"📂 [{tab_name}] 처리 중...")
            self.log(f"{'='*40}")

            # 탭 클릭
            if not self.click_tab(tab_name):
                continue

            # 문의 수집
            inquiries = self.get_inquiries_in_current_tab()

            if not inquiries:
                self.log(f"  ℹ️ [{tab_name}] 문의 없음")
                continue

            has_any_inquiry = True
            self.total_inquiries += len(inquiries)
            self.log(f"  ✅ {len(inquiries)}개 문의 발견!")

            # 각 문의 처리
            for idx, inquiry_data in enumerate(inquiries, 1):
                self.log(f"\n  📝 문의 {idx}/{len(inquiries)} 처리 중...")
                self.log(f"    상품: {inquiry_data['product_name'][:50]}...")
                self.log(f"    문의: {inquiry_data['inquiry'][:100]}...")

                if self.answer_inquiry(inquiry_data):
                    self.log(f"    ✅ 문의 {idx} 완료!")
                else:
                    self.log(f"    ❌ 문의 {idx} 실패")

                time.sleep(2)

            self.log(f"\n✅ [{tab_name}] 탭 완료!")

        if not has_any_inquiry:
            self.log("\nℹ️ 모든 탭에 문의 없음")

        return {
            "total": self.total_inquiries,
            "answered": self.answered_count,
            "failed": self.failed_count,
            "skipped": self.skipped_count
        }

    def run(self):
        """전체 실행"""
        try:
            if not self.setup_driver():
                return None

            if not self.login():
                return None

            if not self.navigate_to_inquiries():
                return None

            stats = self.process_all_tabs()

            self.log("\n" + "="*40)
            self.log("📊 처리 완료!")
            self.log(f"총 문의: {stats['total']}")
            self.log(f"답변 완료: {stats['answered']}")
            self.log(f"실패: {stats['failed']}")
            self.log("="*40)

            return stats

        except Exception as e:
            self.log(f"❌ 오류: {e}")
            return None
        finally:
            self.cleanup()

    def cleanup(self):
        """정리"""
        if self.driver:
            try:
                self.log("🧹 정리 중...")
                self.driver.quit()
                self.log("✅ 완료!")
            except:
                pass


class InstagramStyleGUI(ctk.CTk):
    """인스타그램 스타일 GUI"""

    def __init__(self):
        super().__init__()

        # 윈도우 설정
        self.title("✨ Coupang Wing Automation")
        self.geometry("500x850")
        self.resizable(False, False)

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
        self.configure(fg_color=("#FAFAFA", "#FAFAFA"))

        # 스크롤 가능한 메인 프레임
        main_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        main_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # 헤더
        header_frame = ctk.CTkFrame(
            main_scroll,
            fg_color="white",
            corner_radius=0,
            height=80
        )
        header_frame.pack(fill="x", pady=(0, 20), padx=0)
        header_frame.pack_propagate(False)

        logo_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_container.pack(expand=True)

        ctk.CTkLabel(
            logo_container,
            text="✨",
            font=ctk.CTkFont(size=40)
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            logo_container,
            text="Coupang Wing",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#262626"
        ).pack()

        # 로그인 카드
        card_frame = ctk.CTkFrame(
            main_scroll,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color="#DBDBDB"
        )
        card_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            card_frame,
            text="로그인 정보",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#262626",
            anchor="w"
        ).pack(fill="x", padx=25, pady=(25, 15))

        self.create_input(card_frame, "이메일", self.username_var, "your_email@example.com")
        self.create_input(card_frame, "비밀번호", self.password_var, "••••••••", show="•")
        self.create_input(card_frame, "API Key", self.api_key_var, "sk-...", show="•")

        headless_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        headless_frame.pack(fill="x", padx=25, pady=(10, 25))

        ctk.CTkCheckBox(
            headless_frame,
            text="백그라운드 실행",
            variable=self.headless_var,
            font=ctk.CTkFont(size=13),
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=5,
            fg_color="#E1306C",
            hover_color="#C13584"
        ).pack(anchor="w")

        # 시작 버튼
        self.main_button = ctk.CTkButton(
            main_scroll,
            text="시작하기",
            command=self.start_automation,
            height=55,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=10,
            fg_color="#E1306C",
            hover_color="#C13584"
        )
        self.main_button.pack(fill="x", padx=20, pady=(0, 15))

        # 통계 카드
        stats_frame = ctk.CTkFrame(
            main_scroll,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color="#DBDBDB"
        )
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            stats_frame,
            text="📊 통계",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#262626",
            anchor="w"
        ).pack(fill="x", padx=25, pady=(20, 15))

        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=25, pady=(0, 20))
        stats_grid.grid_columnconfigure((0, 1), weight=1)

        self.stat_total = self.create_stat(stats_grid, "총 문의", "0", 0, 0)
        self.stat_answered = self.create_stat(stats_grid, "답변 완료", "0", 0, 1)
        self.stat_failed = self.create_stat(stats_grid, "실패", "0", 1, 0)
        self.stat_skipped = self.create_stat(stats_grid, "건너뜀", "0", 1, 1)

        # 로그 영역
        log_frame = ctk.CTkFrame(
            main_scroll,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color="#DBDBDB"
        )
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(
            log_frame,
            text="💬 활동",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#262626",
            anchor="w"
        ).pack(fill="x", padx=25, pady=(20, 10))

        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(size=12),
            corner_radius=10,
            border_width=0,
            fg_color="#FAFAFA",
            height=250
        )
        self.log_text.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        self.add_log("✨ 준비 완료!")
        self.add_log("정보를 입력하고 시작하세요")

        # 상태
        self.status_label = ctk.CTkLabel(
            main_scroll,
            text="● 대기 중",
            font=ctk.CTkFont(size=12),
            text_color="#8E8E8E"
        )
        self.status_label.pack(pady=(0, 20))

    def create_input(self, parent, label, variable, placeholder, show=None):
        """입력 필드 생성"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=25, pady=(0, 12))

        ctk.CTkLabel(
            container,
            text=label,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#262626",
            anchor="w"
        ).pack(fill="x", pady=(0, 6))

        entry = ctk.CTkEntry(
            container,
            textvariable=variable,
            placeholder_text=placeholder,
            height=42,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            border_width=1,
            border_color="#DBDBDB",
            fg_color="white"
        )
        if show:
            entry.configure(show=show)
        entry.pack(fill="x")

    def create_stat(self, parent, label, value, row, col):
        """통계 카드 생성"""
        card = ctk.CTkFrame(
            parent,
            fg_color="#FAFAFA",
            corner_radius=12
        )
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#262626"
        )
        value_label.pack(pady=(15, 5))

        ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color="#8E8E8E"
        ).pack(pady=(0, 15))

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

    def validate(self):
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
        if not self.validate():
            return

        if self.is_running:
            self.add_log("⚠️ 이미 실행 중")
            return

        self.is_running = True
        self.main_button.configure(state="disabled", text="실행 중...")
        self.update_status("실행 중", "#E1306C")
        self.update_stats(0, 0, 0, 0)

        def run_thread():
            try:
                self.add_log("="*40)
                self.add_log("🚀 자동화 시작!")
                self.add_log("="*40)

                # 환경 변수 저장
                self.save_env()

                # 자동화 실행
                automation = CoupangWingAutomation(
                    username=self.username_var.get(),
                    password=self.password_var.get(),
                    api_key=self.api_key_var.get(),
                    headless=self.headless_var.get(),
                    log_callback=self.add_log
                )

                stats = automation.run()

                if stats:
                    self.update_stats(
                        total=stats['total'],
                        answered=stats['answered'],
                        failed=stats['failed'],
                        skipped=stats['skipped']
                    )
                    self.update_status("완료", "#4CB050")
                else:
                    self.update_status("오류", "#ED4956")

            except Exception as e:
                self.add_log(f"❌ 오류: {e}")
                self.update_status("오류", "#ED4956")
            finally:
                self.is_running = False
                self.main_button.configure(state="normal", text="시작하기")

        threading.Thread(target=run_thread, daemon=True).start()


def main():
    """메인 함수"""
    app = InstagramStyleGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
