# -*- coding: utf-8 -*-
"""
웹드라이버 테스트
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

print("=" * 80)
print("웹드라이버 테스트 (Selenium 4 자동 관리)")
print("=" * 80)

try:
    print("\n1. Chrome 옵션 설정 중...")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    # headless 모드 추가 (백그라운드 실행)
    # chrome_options.add_argument('--headless')

    print("✓ Chrome 옵션 설정 완료")

    print("\n2. 웹드라이버 초기화 중 (Selenium이 자동으로 ChromeDriver 관리)...")
    driver = webdriver.Chrome(options=chrome_options)
    print("✓ 웹드라이버 초기화 완료")

    print("\n4. 테스트 페이지 로드 중...")
    driver.get("https://www.google.com")
    print(f"✓ 페이지 로드 완료: {driver.title}")

    print("\n5. 웹드라이버 종료 중...")
    driver.quit()
    print("✓ 웹드라이버 종료 완료")

    print("\n" + "=" * 80)
    print("✅ 웹드라이버 테스트 성공!")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ 웹드라이버 테스트 실패: {str(e)}")
    import traceback
    print("\n상세 에러:")
    traceback.print_exc()
    print("\n" + "=" * 80)
