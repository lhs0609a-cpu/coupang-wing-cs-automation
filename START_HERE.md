# 🚀 빠른 시작 가이드

## 1️⃣ 백엔드 시작 (필수)

### 터미널 1 열기

```bash
# 프로젝트 폴더로 이동
cd C:\Users\u\coupang-wing-cs-automation\backend

# 가상환경 활성화
venv\Scripts\activate

# 서버 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

✅ **성공 확인**: `http://localhost:8080` 메시지가 보이면 성공

---

## 2️⃣ 프론트엔드 시작 (필수)

### 터미널 2 열기 (새 터미널)

```bash
# 프로젝트 폴더로 이동
cd C:\Users\u\coupang-wing-cs-automation\frontend

# 개발 서버 실행
npm run dev
```

✅ **성공 확인**: `http://localhost:3030` 메시지가 보이면 성공

---

## 3️⃣ 브라우저에서 접속

브라우저를 열고 다음 주소로 이동:

```
http://localhost:3030
```

---

## 4️⃣ 사용 방법

### 🚀 완전 자동 모드

1. **"🚀 AI 자동 처리 + 제출"** 버튼 클릭
2. AI가 자동으로:
   - 쿠팡에서 문의 수집
   - ChatGPT로 답변 생성
   - 검증 수행
   - 안전한 답변은 쿠팡에 자동 제출
3. 끝! 😎

### 👤 수동 검토 모드

1. **"🔄 새로고침"** 버튼으로 대기중인 답변 확인
2. AI가 생성한 답변 검토
3. 필요시 **"✎ 수정"** 버튼으로 수정
4. **"✓ 승인 & 자동 제출"** 버튼으로 쿠팡에 즉시 제출

---

## ⚙️ 설정 확인

### OpenAI API 키 확인

`backend\.env` 파일 확인:

```env
OPENAI_API_KEY=sk-proj-your_openai_api_key_here
```

✅ 이미 설정되어 있습니다!

### 쿠팡 API 키 설정

`backend\.env` 파일에서 다음 항목을 실제 값으로 교체:

```env
COUPANG_ACCESS_KEY=실제_액세스_키
COUPANG_SECRET_KEY=실제_시크릿_키
COUPANG_VENDOR_ID=실제_벤더_ID
COUPANG_WING_ID=실제_윙_ID
```

---

## 🎨 화면 설명

### 메인 대시보드

- **통계 카드**: 실시간 문의 처리 현황
- **자동 승인률**: AI가 자동으로 처리한 비율
- **자동 제출률**: 쿠팡에 자동 제출된 비율

### 답변 카드

각 답변 카드에는 다음 정보가 표시됩니다:

- 🎯 **신뢰도**: AI 답변의 신뢰도 점수
- ⚠ **위험도**: 낮음/보통/높음
- ✓ **검증 상태**: 통과/실패

---

## 💡 팁

### 자동화율 높이기

1. 처음에는 답변을 직접 검토하세요
2. AI가 잘 대응하는 문의 유형을 파악하세요
3. 템플릿을 개선하세요 (`backend/knowledge_base/templates/`)
4. 정책 파일을 업데이트하세요 (`backend/knowledge_base/policies/`)

### 비용 절감

- 간단한 문의는 템플릿 사용 (무료)
- 복잡한 문의만 AI 사용
- GPT-4o-mini 사용 (GPT-4 대비 저렴)

---

## 🔥 자주 묻는 질문

### Q: 백엔드가 시작되지 않아요

```bash
# 가상환경이 활성화되었는지 확인
venv\Scripts\activate

# 패키지가 설치되었는지 확인
pip install -r requirements.txt

# OpenAI 패키지 설치
pip install openai
```

### Q: 프론트엔드가 시작되지 않아요

```bash
# node_modules 삭제 후 재설치
rd /s /q node_modules
npm install
npm run dev
```

### Q: "AI 자동 처리"를 눌렀는데 아무 일도 안 일어나요

→ 쿠팡 API 키가 설정되어 있는지 확인하세요

### Q: 답변이 이상해요

→ `backend/knowledge_base/` 폴더의 템플릿과 정책을 확인하고 개선하세요

---

## 📊 예상 결과

### 처음 실행 시

```
✅ 수집: 5건
🤖 AI 생성: 5건
✓ 자동 승인: 2건
🚀 자동 제출: 2건
⚠️ 사람 검토 필요: 3건
```

### 학습 후 (1개월)

```
✅ 수집: 20건
🤖 AI 생성: 20건
✓ 자동 승인: 12건
🚀 자동 제출: 12건
⚠️ 사람 검토 필요: 8건
```

**자동화율: 60%!** 🎉

---

## 🆘 문제 발생 시

1. **백엔드 로그 확인**: `backend/logs/app.log`
2. **브라우저 콘솔 확인**: F12 → Console 탭
3. **API 테스트**: http://localhost:8080/docs

---

## 🎯 다음 단계

1. ✅ 시스템 실행
2. ✅ 쿠팡 API 키 설정
3. ✅ 템플릿 커스터마이징
4. ✅ 테스트 실행
5. ✅ 점진적 자동화 확대

**즐거운 자동화 되세요!** 🚀
