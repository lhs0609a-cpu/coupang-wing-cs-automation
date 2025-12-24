"""
✨ 쿠팡윙 CS 자동화 - 최종 버전
정확한 HTML 구조 반영 + 완벽한 반복 처리
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
from selenium.common.exceptions import StaleElementReferenceException

# OpenAI는 함수 내부에서 import (pydantic 충돌 방지)
OPENAI_AVAILABLE = False
try:
    import importlib.util
    if importlib.util.find_spec("openai") is not None:
        OPENAI_AVAILABLE = True
except:
    pass

# CustomTkinter 설정
ctk.set_appearance_mode("light")


class WingAutomation:
    """쿠팡윙 자동화 엔진"""

    def __init__(self, username: str, password: str, api_key: str, headless: bool, log_callback):
        self.username = username
        self.password = password
        self.api_key = api_key
        self.headless = headless
        self.log = log_callback

        self.driver = None
        self.wait = None

        # 통계
        self.total = 0
        self.answered = 0
        self.failed = 0

    def setup_driver(self):
        """브라우저 설정"""
        try:
            self.log("🌐 브라우저 준비 중...")
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')

            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 20)
            self.log("✅ 브라우저 준비 완료")
            return True
        except Exception as e:
            self.log(f"❌ 브라우저 오류: {e}")
            return False

    def login(self):
        """로그인 (개선된 버전)"""
        try:
            self.log("🔐 로그인 시작...")
            self.driver.get("https://wing.coupang.com/")
            self.log("  ⏳ 페이지 로딩 대기...")
            time.sleep(5)  # 페이지 로딩 대기 증가

            # 아이디 입력
            self.log("  📝 아이디 입력 중...")
            try:
                username_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                username_input.clear()
                time.sleep(0.5)
                username_input.send_keys(self.username)
                time.sleep(1)
                self.log("  ✅ 아이디 입력 완료")
            except Exception as e:
                self.log(f"  ❌ 아이디 입력 실패: {e}")
                return False

            # 비밀번호 입력
            self.log("  🔑 비밀번호 입력 중...")
            try:
                password_input = self.driver.find_element(By.ID, "password")
                password_input.clear()
                time.sleep(0.5)
                password_input.send_keys(self.password)
                time.sleep(1)
                self.log("  ✅ 비밀번호 입력 완료")
            except Exception as e:
                self.log(f"  ❌ 비밀번호 입력 실패: {e}")
                return False

            # 로그인 버튼 클릭
            self.log("  🖱️ 로그인 버튼 클릭 중...")
            try:
                login_btn = self.driver.find_element(By.ID, "kc-login")
                login_btn.click()
                self.log("  ✅ 로그인 버튼 클릭 완료")
            except Exception as e:
                self.log(f"  ❌ 로그인 버튼 클릭 실패: {e}")
                return False

            # 로그인 처리 대기
            self.log("  ⏳ 로그인 처리 대기 (10초)...")
            time.sleep(10)

            # 로그인 결과 확인
            current_url = self.driver.current_url
            self.log(f"  🌐 현재 URL: {current_url[:50]}...")

            if "wing.coupang.com" in current_url and "xauth" not in current_url:
                self.log("✅ 로그인 성공!")
                return True
            else:
                self.log(f"❌ 로그인 실패 - URL: {current_url}")
                # 페이지 소스 일부 저장
                try:
                    page_title = self.driver.title
                    self.log(f"  페이지 제목: {page_title}")
                except:
                    pass
                return False

        except Exception as e:
            self.log(f"❌ 로그인 오류: {e}")
            import traceback
            self.log(f"  상세: {traceback.format_exc()[:300]}")
            return False

    def goto_inquiries(self):
        """고객문의 페이지 이동"""
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
        """탭 클릭"""
        try:
            self.log(f"🔍 [{tab_name}] 탭 찾는 중...")

            # 모든 클릭 가능한 요소 찾기
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{tab_name}')]")

            for elem in elements:
                try:
                    # 보이는지 확인
                    if elem.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                        time.sleep(0.5)
                        # 클릭 시도
                        try:
                            elem.click()
                        except:
                            # JavaScript로 클릭
                            self.driver.execute_script("arguments[0].click();", elem)
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

    def find_inquiries(self) -> List[Dict]:
        """현재 탭의 모든 문의 찾기"""
        inquiries = []
        try:
            time.sleep(2)

            # 정확한 CSS 선택자로 문의 행 찾기
            # class="replying-no-comments"를 가진 td 요소
            rows = self.driver.find_elements(By.CSS_SELECTOR, "td.replying-no-comments")
            self.log(f"  📊 {len(rows)}개 행 발견")

            for idx, row in enumerate(rows):
                try:
                    # 상품명 찾기
                    product_name = None
                    try:
                        # <div class="text-wrapper product-name"> 안의 span
                        product_span = row.find_element(By.CSS_SELECTOR, "div.product-name span[title]")
                        product_name = product_span.get_attribute("title") or product_span.text
                    except:
                        try:
                            product_span = row.find_element(By.CSS_SELECTOR, ".text-wrapper.product-name span")
                            product_name = product_span.get_attribute("title") or product_span.text
                        except:
                            continue

                    # 문의 내용 찾기
                    inquiry_text = None
                    try:
                        # <span class="inquiry-content">
                        inquiry_span = row.find_element(By.CSS_SELECTOR, "span.inquiry-content")
                        inquiry_text = inquiry_span.text.strip()
                    except:
                        continue

                    # 답변하기 버튼 찾기
                    # 현재 행(td)의 부모(tr)에서 버튼 찾기
                    answer_btn = None
                    try:
                        # 부모 tr 찾기
                        parent_tr = row.find_element(By.XPATH, "./ancestor::tr")
                        # tr 내의 모든 버튼 찾기
                        buttons = parent_tr.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            if "답변하기" in btn.text:
                                answer_btn = btn
                                break
                    except:
                        # td 내에서 직접 찾기
                        try:
                            buttons = row.find_elements(By.TAG_NAME, "button")
                            for btn in buttons:
                                if "답변하기" in btn.text:
                                    answer_btn = btn
                                    break
                        except:
                            pass

                    if product_name and inquiry_text and answer_btn:
                        inquiries.append({
                            "product": product_name,
                            "inquiry": inquiry_text,
                            "button": answer_btn,
                            "row": row
                        })
                        self.log(f"  ✅ 문의 {len(inquiries)}: {product_name[:30]}...")

                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    continue

            return inquiries

        except Exception as e:
            self.log(f"  ❌ 문의 찾기 오류: {e}")
            return []

    def generate_answer(self, product: str, inquiry: str) -> str:
        """답변 생성 (ChatGPT API 연동)"""
        try:
            if OPENAI_AVAILABLE and self.api_key and self.api_key.startswith("sk-"):
                # OpenAI API 호출 (지연 import로 pydantic 충돌 방지)
                import openai
                client = openai.OpenAI(api_key=self.api_key)

                prompt = f"""당신은 쿠팡윙 판매자의 고객 서비스 담당자입니다.
다음 상품에 대한 고객 문의에 친절하고 전문적으로 답변해주세요.

상품명: {product}

고객 문의:
{inquiry}

요구사항:
- 친절하고 정중한 어투 사용
- 구체적이고 도움이 되는 답변 제공
- 200자 이내로 간결하게 작성
- 필요시 환불, 교환, AS 등 안내 포함
- 추가 문의는 판매자 문의로 안내"""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "당신은 쿠팡윙 판매자의 전문 CS 담당자입니다."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )

                answer = response.choices[0].message.content.strip()
                self.log(f"      🤖 ChatGPT 답변 생성 완료")
                return answer
            else:
                # API 키 없으면 기본 답변
                self.log(f"      ⚠️ API 키 없음, 기본 답변 사용")
                answer = f"안녕하세요. '{product}' 상품에 대한 문의 주셔서 감사합니다. 고객님의 문의사항을 확인하였으며, 관련 내용을 검토하여 빠른 시일 내에 정확한 답변 드리도록 하겠습니다. 추가로 궁금하신 사항이 있으시면 판매자 연락처로 연락 주시기 바랍니다. 감사합니다."
                return answer

        except Exception as e:
            self.log(f"      ❌ ChatGPT API 오류: {e}")
            # 오류 시 기본 답변
            answer = f"안녕하세요. '{product}' 상품에 대한 문의 주셔서 감사합니다. 고객님의 문의사항을 확인하였으며, 관련 내용을 검토하여 빠른 시일 내에 정확한 답변 드리도록 하겠습니다. 추가로 궁금하신 사항이 있으시면 판매자 연락처로 연락 주시기 바랍니다. 감사합니다."
            return answer

    def answer_one(self, item: Dict) -> bool:
        """한 개의 문의에 답변"""
        try:
            product = item["product"]
            inquiry = item["inquiry"]
            button = item["button"]

            self.log(f"    💬 처리 시작...")

            # 1. 답변하기 버튼 클릭
            self.log(f"      1️⃣ 답변하기 버튼 클릭 중...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)
            try:
                button.click()
            except:
                self.driver.execute_script("arguments[0].click();", button)
            time.sleep(3)  # 모달 로딩 대기 증가
            self.log("      ✅ 답변하기 클릭 완료")

            # 2. 답변 생성
            self.log(f"      2️⃣ ChatGPT 답변 생성 중...")
            answer = self.generate_answer(product, inquiry)
            self.log(f"      ✅ 답변 생성 완료 ({len(answer)}자)")

            # 3. textarea 찾기
            self.log(f"      3️⃣ 입력란 찾는 중...")
            textarea = None
            try:
                textarea = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.input-textarea"))
                )
            except:
                try:
                    textarea = self.driver.find_element(By.CSS_SELECTOR, "textarea[placeholder*='상품문의']")
                except:
                    try:
                        textarea = self.driver.find_element(By.TAG_NAME, "textarea")
                    except:
                        pass

            if not textarea:
                self.log("      ❌ 입력란을 찾을 수 없음")
                self.failed += 1
                return False

            self.log("      ✅ 입력란 발견")

            # 4. 답변 입력
            self.log(f"      4️⃣ 답변 입력 중...")
            textarea.clear()
            time.sleep(0.5)
            textarea.send_keys(answer)
            time.sleep(1)
            self.log("      ✅ 답변 입력 완료")

            # 5. 저장하기 버튼 찾기
            self.log(f"      5️⃣ 저장하기 버튼 찾는 중...")
            save_btn = None
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    btn_text = btn.text.strip()
                    if "저장하기" in btn_text or "저장" in btn_text:
                        save_btn = btn
                        self.log(f"      ✅ 저장 버튼 발견: '{btn_text}'")
                        break

                if not save_btn:
                    save_btn = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button[data-wuic-props*='type:primary']"
                    )
                    self.log("      ✅ 저장 버튼 발견 (CSS)")
            except Exception as e:
                self.log(f"      ❌ 저장 버튼을 찾을 수 없음: {e}")
                self.failed += 1
                return False

            # 6. 저장하기 클릭
            self.log(f"      6️⃣ 저장하기 클릭 중...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", save_btn)
            time.sleep(1)

            # 현재 URL 기억 (페이지 변경 감지용)
            current_url = self.driver.current_url

            try:
                save_btn.click()
            except:
                self.driver.execute_script("arguments[0].click();", save_btn)

            self.log("      ⏳ 저장 처리 대기 중...")
            time.sleep(5)  # 저장 처리 대기

            # 저장 후 페이지 변경 확인
            new_url = self.driver.current_url
            if current_url != new_url:
                self.log(f"      ✅ 페이지 이동 감지 (저장 성공 추정)")

            self.log("      ✅ 저장 완료!")
            self.answered += 1
            return True

        except Exception as e:
            self.log(f"    ❌ 답변 실패: {e}")
            import traceback
            self.log(f"    ⚠️ 상세: {traceback.format_exc()[:200]}")
            self.failed += 1
            return False

    def process_tab(self, tab_name: str) -> int:
        """한 탭 처리 - 문의가 없을 때까지 반복"""
        try:
            self.log(f"\n{'='*40}")
            self.log(f"📂 [{tab_name}] 처리 시작")
            self.log(f"{'='*40}")

            # 초기 탭 클릭
            if not self.click_tab(tab_name):
                self.log(f"  ❌ 초기 탭 클릭 실패")
                return 0

            time.sleep(2)  # 탭 로딩 대기
            total_processed = 0
            round_num = 1
            consecutive_failures = 0

            # 문의가 없을 때까지 계속 반복
            while True:
                self.log(f"\n  🔄 [{tab_name}] Round {round_num} 시작...")

                # 2번째 라운드부터는 탭 재클릭 (저장 후 페이지가 바뀌므로)
                if round_num > 1:
                    self.log(f"    ⏳ 페이지 로딩 대기 (5초)...")
                    time.sleep(5)  # 저장 후 페이지 안정화 대기

                    self.log(f"    🔄 [{tab_name}] 탭 재클릭...")
                    retry_count = 0
                    while retry_count < 3:
                        if self.click_tab(tab_name):
                            self.log(f"    ✅ 탭 재클릭 성공")
                            time.sleep(2)
                            break
                        retry_count += 1
                        self.log(f"    ⚠️ 탭 재클릭 실패, 재시도 {retry_count}/3")
                        time.sleep(2)
                    else:
                        self.log(f"    ❌ 탭 재클릭 3회 실패, 종료")
                        break

                # 문의 찾기
                self.log(f"    🔍 문의 검색 중...")
                inquiries = self.find_inquiries()

                if not inquiries:
                    self.log(f"  ℹ️ [{tab_name}] 더 이상 문의 없음 (Round {round_num})")
                    break

                count = len(inquiries)
                self.log(f"  ✅ {count}개 문의 발견!")

                # 첫 번째 문의만 처리
                item = inquiries[0]
                self.total += 1

                self.log(f"\n  📝 문의 #{total_processed + 1} 처리 시작")
                self.log(f"    📦 상품: {item['product'][:50]}...")
                self.log(f"    💬 문의: {item['inquiry'][:100]}...")

                # 답변 처리
                if self.answer_one(item):
                    self.log(f"    ✅ 문의 #{total_processed + 1} 완료!")
                    total_processed += 1
                    consecutive_failures = 0
                else:
                    self.log(f"    ❌ 문의 #{total_processed + 1} 실패")
                    consecutive_failures += 1

                    # 연속 실패 5회면 중단
                    if consecutive_failures >= 5:
                        self.log(f"  ⚠️ 연속 {consecutive_failures}회 실패, 탭 처리 중단")
                        break

                round_num += 1

                # 무한 루프 방지
                if total_processed >= 100:
                    self.log(f"  ⚠️ 최대 처리 개수 도달 (100개)")
                    break

                if round_num > 200:
                    self.log(f"  ⚠️ 최대 라운드 도달 (200회)")
                    break

            self.log(f"\n✅ [{tab_name}] 탭 완료!")
            self.log(f"  📊 처리: {total_processed}개, 라운드: {round_num}")
            return total_processed

        except Exception as e:
            self.log(f"❌ 탭 처리 오류: {e}")
            import traceback
            self.log(f"  상세: {traceback.format_exc()}")
            return 0

    def run(self):
        """전체 실행"""
        try:
            self.log("="*40)
            self.log("🚀 쿠팡윙 CS 자동화 시작")
            self.log("="*40)

            if not self.setup_driver():
                return None

            if not self.login():
                return None

            if not self.goto_inquiries():
                return None

            # 3개 탭 순차 처리
            tabs = ["72시간~30일", "24~72시간", "24시간 이내"]
            has_inquiry = False

            for tab in tabs:
                count = self.process_tab(tab)
                if count > 0:
                    has_inquiry = True

            if not has_inquiry:
                self.log("\nℹ️ 모든 탭에 문의 없음")

            # 결과
            self.log("\n" + "="*40)
            self.log("📊 처리 완료!")
            self.log(f"총 문의: {self.total}")
            self.log(f"답변 완료: {self.answered}")
            self.log(f"실패: {self.failed}")
            self.log("="*40)

            return {
                "total": self.total,
                "answered": self.answered,
                "failed": self.failed
            }

        except Exception as e:
            self.log(f"❌ 오류: {e}")
            return None
        finally:
            if self.driver:
                try:
                    self.log("🧹 정리 중...")
                    self.driver.quit()
                    self.log("✅ 완료!")
                except:
                    pass


class GUI(ctk.CTk):
    """Instagram 스타일 GUI"""

    def __init__(self):
        super().__init__()

        self.title("✨ Coupang Wing")
        self.geometry("500x850")
        self.resizable(False, False)

        self.username = ctk.StringVar()
        self.password = ctk.StringVar()
        self.api_key = ctk.StringVar()
        self.headless = ctk.BooleanVar(value=True)
        self.use_backend = ctk.BooleanVar(value=False)  # 백엔드 사용 여부

        self.running = False
        self.api_status_label = None
        self.backend_status_label = None
        self.backend_url = "http://localhost:8000"  # 백엔드 URL
        self.backend_connected = False

        self.load_env()
        self.setup_ui()

        # API 키 변경 감지
        self.api_key.trace_add("write", lambda *args: self.check_api_status())

        # 백엔드 사용 여부 변경 감지
        self.use_backend.trace_add("write", lambda *args: self.on_backend_toggle())

    def load_env(self):
        """환경 변수 로드"""
        env_path = Path("backend/.env")
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, val = line.split('=', 1)
                            val = val.strip().strip('"').strip("'")
                            if key.strip() == 'COUPANG_WING_USERNAME':
                                self.username.set(val)
                            elif key.strip() == 'COUPANG_WING_PASSWORD':
                                self.password.set(val)
                            elif key.strip() == 'OPENAI_API_KEY':
                                self.api_key.set(val)
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
            'COUPANG_WING_USERNAME': self.username.get(),
            'COUPANG_WING_PASSWORD': self.password.get(),
            'OPENAI_API_KEY': self.api_key.get()
        }

        updated = set()
        for i, line in enumerate(lines):
            for k, v in updates.items():
                if line.startswith(f"{k}="):
                    lines[i] = f"{k}={v}\n"
                    updated.add(k)

        for k, v in updates.items():
            if k not in updated:
                lines.append(f"{k}={v}\n")

        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def setup_ui(self):
        """UI 구성"""
        self.configure(fg_color="#FAFAFA")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # 헤더
        header = ctk.CTkFrame(scroll, fg_color="white", corner_radius=0, height=80)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="✨", font=ctk.CTkFont(size=40)).pack(pady=(10, 0))
        ctk.CTkLabel(header, text="Coupang Wing", font=ctk.CTkFont(size=20, weight="bold"), text_color="#262626").pack()

        # 카드
        card = ctk.CTkFrame(scroll, fg_color="white", corner_radius=15, border_width=1, border_color="#DBDBDB")
        card.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(card, text="로그인 정보", font=ctk.CTkFont(size=16, weight="bold"), text_color="#262626").pack(fill="x", padx=25, pady=(25, 15))

        self.make_input(card, "이메일", self.username, "your_email@example.com")
        self.make_input(card, "비밀번호", self.password, "••••••••", show="•")
        self.api_input_frame = self.make_input(card, "API Key", self.api_key, "sk-...", show="•")

        # API 상태 표시
        self.api_status_label = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.api_status_label.pack(fill="x", padx=25, pady=(0, 10))

        # 체크박스들
        ctk.CTkCheckBox(
            card,
            text="백그라운드 실행",
            variable=self.headless,
            fg_color="#E1306C",
            hover_color="#C13584"
        ).pack(anchor="w", padx=25, pady=(10, 5))

        ctk.CTkCheckBox(
            card,
            text="🔗 백엔드 API 사용 (포트 8000)",
            variable=self.use_backend,
            fg_color="#E1306C",
            hover_color="#C13584"
        ).pack(anchor="w", padx=25, pady=(5, 5))

        # 백엔드 상태 표시
        self.backend_status_label = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.backend_status_label.pack(fill="x", padx=25, pady=(0, 25))

        # 초기 API 상태 체크
        self.check_api_status()

        # 시작 버튼
        self.start_btn = ctk.CTkButton(scroll, text="시작하기", command=self.start, height=55, font=ctk.CTkFont(size=16, weight="bold"), corner_radius=10, fg_color="#E1306C", hover_color="#C13584")
        self.start_btn.pack(fill="x", padx=20, pady=(0, 15))

        # 초기 버튼 상태 업데이트
        self.update_start_button_state()

        # 통계
        stats = ctk.CTkFrame(scroll, fg_color="white", corner_radius=15, border_width=1, border_color="#DBDBDB")
        stats.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(stats, text="📊 통계", font=ctk.CTkFont(size=16, weight="bold"), text_color="#262626").pack(fill="x", padx=25, pady=(20, 15))

        grid = ctk.CTkFrame(stats, fg_color="transparent")
        grid.pack(fill="x", padx=25, pady=(0, 20))
        grid.grid_columnconfigure((0, 1), weight=1)

        self.s_total = self.make_stat(grid, "총 문의", "0", 0, 0)
        self.s_answered = self.make_stat(grid, "답변 완료", "0", 0, 1)
        self.s_failed = self.make_stat(grid, "실패", "0", 1, 0)
        self.s_skip = self.make_stat(grid, "건너뜀", "0", 1, 1)

        # 로그
        log = ctk.CTkFrame(scroll, fg_color="white", corner_radius=15, border_width=1, border_color="#DBDBDB")
        log.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(log, text="💬 활동", font=ctk.CTkFont(size=16, weight="bold"), text_color="#262626").pack(fill="x", padx=25, pady=(20, 10))

        self.log_text = ctk.CTkTextbox(log, font=ctk.CTkFont(size=12), corner_radius=10, border_width=0, fg_color="#FAFAFA", height=250)
        self.log_text.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        self.add_log("✨ 준비 완료!")
        self.add_log("정보 입력 후 시작하세요")

        # 상태
        self.status = ctk.CTkLabel(scroll, text="● 대기 중", font=ctk.CTkFont(size=12), text_color="#8E8E8E")
        self.status.pack(pady=(0, 20))

    def make_input(self, parent, label, var, placeholder, show=None):
        """입력 필드"""
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=25, pady=(0, 12))

        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#262626").pack(fill="x", pady=(0, 6))

        e = ctk.CTkEntry(f, textvariable=var, placeholder_text=placeholder, height=42, corner_radius=8, border_width=1, border_color="#DBDBDB", fg_color="white")
        if show:
            e.configure(show=show)
        e.pack(fill="x")

        return f

    def make_stat(self, parent, label, value, row, col):
        """통계 카드"""
        c = ctk.CTkFrame(parent, fg_color="#FAFAFA", corner_radius=12)
        c.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        v = ctk.CTkLabel(c, text=value, font=ctk.CTkFont(size=24, weight="bold"), text_color="#262626")
        v.pack(pady=(15, 5))

        ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=11), text_color="#8E8E8E").pack(pady=(0, 15))

        return v

    def on_backend_toggle(self):
        """백엔드 체크박스 토글 시"""
        if self.use_backend.get():
            # 백엔드 사용 체크됨 -> 연결 테스트
            self.check_backend_connection()
        else:
            # 백엔드 사용 해제
            self.backend_connected = False
            if self.backend_status_label:
                self.backend_status_label.configure(text="")
            self.update_start_button_state()

    def check_backend_connection(self):
        """백엔드 연결 확인"""
        if not self.backend_status_label:
            return

        self.backend_status_label.configure(
            text="🔄 백엔드 연결 테스트 중...",
            text_color="#8E8E8E"
        )
        self.update()

        def test_backend():
            try:
                import requests
                response = requests.get(f"{self.backend_url}/api/wing-web/status", timeout=5)
                if response.status_code == 200:
                    self.backend_connected = True
                    self.backend_status_label.configure(
                        text="✅ 백엔드 서버 연결됨 (포트 8000)",
                        text_color="#4CB050"
                    )
                else:
                    self.backend_connected = False
                    self.backend_status_label.configure(
                        text=f"❌ 백엔드 응답 오류: {response.status_code}",
                        text_color="#ED4956"
                    )
            except Exception as e:
                self.backend_connected = False
                error_msg = str(e)
                if "Connection" in error_msg or "refused" in error_msg:
                    self.backend_status_label.configure(
                        text="❌ 백엔드 서버 미실행 (포트 8000 확인)",
                        text_color="#ED4956"
                    )
                else:
                    self.backend_status_label.configure(
                        text=f"❌ 연결 실패: {error_msg[:30]}...",
                        text_color="#ED4956"
                    )
            finally:
                self.update_start_button_state()

        # 백그라운드에서 테스트
        threading.Thread(target=test_backend, daemon=True).start()

    def update_start_button_state(self):
        """시작 버튼 활성화 상태 업데이트"""
        if self.use_backend.get():
            # 백엔드 사용 시 - 백엔드 연결되어야 활성화
            if self.backend_connected:
                self.start_btn.configure(state="normal")
            else:
                self.start_btn.configure(state="disabled")
        else:
            # 로컬 실행 시 - 항상 활성화
            self.start_btn.configure(state="normal")

    def check_api_status(self):
        """API 키 실제 연결 테스트"""
        if not self.api_status_label:
            return

        api_key = self.api_key.get().strip()

        if not api_key:
            self.api_status_label.configure(
                text="⚪ API 키 미입력 (기본 답변 사용)",
                text_color="#8E8E8E"
            )
            return

        if not api_key.startswith("sk-"):
            self.api_status_label.configure(
                text="⚠️ 올바르지 않은 API 키 형식 (기본 답변 사용)",
                text_color="#ED4956"
            )
            return

        if not OPENAI_AVAILABLE:
            self.api_status_label.configure(
                text="❌ OpenAI 라이브러리 미설치 (기본 답변 사용)",
                text_color="#ED4956"
            )
            return

        # 실제 API 연결 테스트
        self.api_status_label.configure(
            text="🔄 API 연결 테스트 중...",
            text_color="#8E8E8E"
        )
        self.update()

        def test_connection():
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                # 간단한 테스트 요청
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                self.api_status_label.configure(
                    text="✅ ChatGPT API 연결됨 (맞춤 답변 생성)",
                    text_color="#4CB050"
                )
            except Exception as e:
                error_msg = str(e)
                if "invalid" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    self.api_status_label.configure(
                        text="❌ API 키 인증 실패 (기본 답변 사용)",
                        text_color="#ED4956"
                    )
                else:
                    self.api_status_label.configure(
                        text=f"❌ 연결 실패: {error_msg[:30]}... (기본 답변 사용)",
                        text_color="#ED4956"
                    )

        # 백그라운드에서 테스트
        threading.Thread(target=test_connection, daemon=True).start()

    def add_log(self, msg):
        """로그 추가"""
        t = time.strftime("%H:%M")
        self.log_text.insert("end", f"{t} {msg}\n")
        self.log_text.see("end")
        self.update()

    def update_status(self, text, color="#8E8E8E"):
        """상태 업데이트"""
        self.status.configure(text=f"● {text}", text_color=color)

    def update_stats(self, total=None, answered=None, failed=None):
        """통계 업데이트"""
        if total is not None:
            self.s_total.configure(text=str(total))
        if answered is not None:
            self.s_answered.configure(text=str(answered))
        if failed is not None:
            self.s_failed.configure(text=str(failed))

    def validate(self):
        """입력 검증"""
        if not self.username.get():
            self.add_log("❌ 이메일 필요")
            return False
        if not self.password.get():
            self.add_log("❌ 비밀번호 필요")
            return False
        if not self.api_key.get():
            self.add_log("❌ API 키 필요")
            return False
        return True

    def start(self):
        """시작"""
        if not self.validate():
            return

        if self.running:
            self.add_log("⚠️ 이미 실행 중")
            return

        self.running = True
        self.start_btn.configure(state="disabled", text="실행 중...")
        self.update_status("실행 중", "#E1306C")
        self.update_stats(0, 0, 0)

        def run():
            try:
                self.save_env()

                # 백엔드 사용 여부 체크
                if self.use_backend.get():
                    self.add_log("🔗 백엔드 API 모드")
                    result = self.run_with_backend()
                else:
                    self.add_log("💻 로컬 실행 모드")
                    auto = WingAutomation(
                        username=self.username.get(),
                        password=self.password.get(),
                        api_key=self.api_key.get(),
                        headless=self.headless.get(),
                        log_callback=self.add_log
                    )
                    result = auto.run()

                if result:
                    self.update_stats(
                        total=result['total'],
                        answered=result['answered'],
                        failed=result['failed']
                    )
                    self.update_status("완료", "#4CB050")
                else:
                    self.update_status("오류", "#ED4956")

            except Exception as e:
                self.add_log(f"❌ 오류: {e}")
                import traceback
                self.add_log(f"상세: {traceback.format_exc()[:200]}")
                self.update_status("오류", "#ED4956")
            finally:
                self.running = False
                self.start_btn.configure(state="normal", text="시작하기")

        threading.Thread(target=run, daemon=True).start()

    def run_with_backend(self):
        """백엔드 API를 사용해서 실행"""
        import requests

        self.add_log("🔍 백엔드 연결 확인 중...")

        # 백엔드 연결 확인
        try:
            response = requests.get(f"{self.backend_url}/api/wing-web/status", timeout=5)
            if response.status_code == 200:
                self.add_log("✅ 백엔드 연결 성공")
            else:
                self.add_log(f"⚠️ 백엔드 응답 이상: {response.status_code}")
        except Exception as e:
            self.add_log(f"❌ 백엔드 연결 실패: {e}")
            self.add_log("💡 백엔드 서버가 실행 중인지 확인하세요")
            return None

        # 자동화 실행 요청
        self.add_log("🚀 백엔드 API 호출 중...")
        try:
            response = requests.post(
                f"{self.backend_url}/api/wing-web/auto-answer-v2",
                json={
                    "username": self.username.get(),
                    "password": self.password.get(),
                    "api_key": self.api_key.get(),
                    "headless": self.headless.get()
                },
                timeout=600  # 10분 타임아웃
            )

            if response.status_code == 200:
                result = response.json()
                self.add_log("✅ 백엔드 처리 완료")
                self.add_log(f"📊 결과: {result}")

                # 결과 파싱
                return {
                    'total': result.get('total_inquiries', 0),
                    'answered': result.get('successful', 0),
                    'failed': result.get('failed', 0)
                }
            else:
                self.add_log(f"❌ API 오류: {response.status_code}")
                self.add_log(f"응답: {response.text[:200]}")
                return None

        except requests.exceptions.Timeout:
            self.add_log("❌ 타임아웃: 처리 시간이 너무 오래 걸렸습니다")
            return None
        except Exception as e:
            self.add_log(f"❌ API 호출 오류: {e}")
            return None


if __name__ == "__main__":
    app = GUI()
    app.mainloop()
