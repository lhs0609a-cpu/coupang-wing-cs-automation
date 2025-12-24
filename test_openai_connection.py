"""
OpenAI API 연결 테스트 스크립트
"""
import os
import sys
from pathlib import Path

# UTF-8 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# backend 경로를 sys.path에 추가
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# .env 파일이 있는 디렉토리로 작업 디렉토리 변경
os.chdir(backend_path)

try:
    from app.config import settings
    from openai import OpenAI

    print("=" * 50)
    print("OpenAI API 연결 테스트")
    print("=" * 50)

    # API 키 확인
    print(f"\n1. API 키 설정 확인:")
    if settings.OPENAI_API_KEY:
        masked_key = settings.OPENAI_API_KEY[:20] + "..." + settings.OPENAI_API_KEY[-10:]
        print(f"   [OK] API 키 설정됨: {masked_key}")
    else:
        print(f"   [FAIL] API 키가 설정되지 않았습니다")
        sys.exit(1)

    print(f"   모델: {settings.OPENAI_MODEL}")

    # OpenAI 클라이언트 초기화
    print(f"\n2. OpenAI 클라이언트 초기화:")
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        print(f"   [OK] 클라이언트 초기화 성공")
    except Exception as e:
        print(f"   [FAIL] 클라이언트 초기화 실패: {e}")
        sys.exit(1)

    # 간단한 API 호출 테스트
    print(f"\n3. API 호출 테스트:")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 테스트 도우미입니다."},
                {"role": "user", "content": "안녕하세요"}
            ],
            max_tokens=50
        )

        print(f"   [OK] API 호출 성공")
        print(f"   응답: {response.choices[0].message.content[:100]}")
        print(f"   사용된 토큰: {response.usage.total_tokens}")

    except Exception as e:
        print(f"   [FAIL] API 호출 실패: {e}")
        print(f"   에러 타입: {type(e).__name__}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("[SUCCESS] 모든 테스트 통과!")
    print("=" * 50)

except Exception as e:
    print(f"\n[ERROR] 테스트 중 오류 발생:")
    print(f"   {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
