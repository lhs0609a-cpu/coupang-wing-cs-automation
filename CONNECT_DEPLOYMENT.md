# 🚀 Vercel ⭐⭐⭐⭐⭐ + Fly.io ⭐⭐⭐⭐⭐ 연결 가이드

프론트엔드(Vercel)와 백엔드(Fly.io)를 완벽하게 연결하는 단계별 가이드입니다.

---

## 📋 전체 프로세스

```
1. Fly.io에 백엔드 배포 → URL 획득
2. 백엔드 URL로 프론트엔드 설정 업데이트
3. Vercel에 프론트엔드 배포
4. 연결 테스트
```

---

## 🎯 1단계: Fly.io 백엔드 배포

### 1-1. Fly.io CLI 설치 (아직 안 했다면)

**Windows (PowerShell 관리자 권한):**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

**macOS/Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

설치 확인:
```bash
fly version
```

### 1-2. Fly.io 로그인

```bash
fly auth login
```

브라우저가 열리면 로그인합니다.

### 1-3. 백엔드 디렉토리로 이동

```bash
cd backend
```

### 1-4. Fly.io 앱 생성

```bash
fly launch
```

질문에 답변:
- **App Name**: `coupang-wing-cs` (또는 원하는 이름)
- **Region**: `nrt` (도쿄 - 한국과 가까움)
- **PostgreSQL**: `No`
- **Redis**: `No`
- **Deploy now**: `No` (환경변수 먼저 설정)

생성된 앱 이름을 기억하세요! 예: `coupang-wing-cs`

### 1-5. 환경변수 설정 ⚠️ **중요!**

```bash
# OpenAI API Key (필수)
fly secrets set OPENAI_API_KEY="sk-your-openai-api-key-here"

# 데이터베이스 URL
fly secrets set DATABASE_URL="sqlite:///./database/coupang_cs.db"

# Secret Key (JWT 토큰용)
fly secrets set SECRET_KEY="your-super-secret-key-change-this-in-production"

# 환경 설정
fly secrets set ENVIRONMENT="production"
fly secrets set LOG_LEVEL="INFO"

# Coupang API (있다면 설정)
fly secrets set COUPANG_ACCESS_KEY="your-access-key"
fly secrets set COUPANG_SECRET_KEY="your-secret-key"
fly secrets set COUPANG_VENDOR_ID="your-vendor-id"
```

### 1-6. 배포 실행! 🚀

```bash
fly deploy
```

배포가 완료되면 다음과 같은 메시지가 표시됩니다:
```
Visit your newly deployed app at https://coupang-wing-cs.fly.dev
```

**이 URL을 복사하세요!** 예: `https://coupang-wing-cs.fly.dev`

### 1-7. 백엔드 배포 확인

```bash
# 헬스체크
fly status

# 로그 확인
fly logs

# 브라우저에서 확인
# https://coupang-wing-cs.fly.dev/health
# https://coupang-wing-cs.fly.dev/docs
```

---

## 🔗 2단계: 프론트엔드 설정 업데이트

백엔드 URL을 획득했으므로 이제 프론트엔드 설정을 업데이트합니다.

### 2-1. 프론트엔드 디렉토리로 이동

```bash
cd ../frontend
```

### 2-2. .env.production 파일 업데이트

파일 열기: `frontend/.env.production`

내용 수정:
```env
# 백엔드 URL로 변경 (예시)
VITE_API_URL=https://coupang-wing-cs.fly.dev
```

**⚠️ `https://`를 포함하고, 끝에 `/`를 제거하세요!**

### 2-3. vercel.json 파일 업데이트

파일 열기: `frontend/vercel.json`

8번째 줄과 19번째 줄의 URL을 변경:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://coupang-wing-cs.fly.dev/api/:path*"
    },
    ...
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://coupang-wing-cs.fly.dev/api/$1"
    },
    ...
  ]
}
```

### 2-4. 로컬 빌드 테스트 (선택사항)

```bash
npm run build
```

오류 없이 빌드되면 OK!

---

## 🌐 3단계: Vercel 프론트엔드 배포

### 3-1. Vercel CLI 설치 (아직 안 했다면)

```bash
npm install -g vercel
```

### 3-2. Vercel 로그인

```bash
vercel login
```

이메일 또는 GitHub로 로그인합니다.

### 3-3. 프론트엔드 배포! 🚀

```bash
# 첫 배포
vercel

# 프로덕션 배포
vercel --prod
```

질문에 답변:
- **Set up and deploy**: `Y`
- **Which scope**: 본인 계정 선택
- **Link to existing project**: `N`
- **Project name**: `coupang-wing-cs-frontend`
- **Directory**: `.` (현재 디렉토리)
- **Override settings**: `N`

배포 완료 후 URL이 표시됩니다:
```
🎉 Production: https://coupang-wing-cs-frontend.vercel.app
```

### 3-4. Vercel 환경변수 설정 (Dashboard)

1. https://vercel.com/dashboard 접속
2. 프로젝트 (`coupang-wing-cs-frontend`) 선택
3. **Settings** > **Environment Variables** 클릭
4. 환경변수 추가:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://coupang-wing-cs.fly.dev`
   - **Environment**: Production, Preview, Development 모두 체크
5. **Save** 클릭

### 3-5. 재배포

환경변수 설정 후 재배포:
```bash
vercel --prod
```

---

## ✅ 4단계: 연결 테스트

### 4-1. 백엔드 테스트

브라우저에서:
```
https://coupang-wing-cs.fly.dev/health
https://coupang-wing-cs.fly.dev/docs
```

터미널에서:
```bash
# 헬스체크
curl https://coupang-wing-cs.fly.dev/health

# ChatGPT 연결 상태
curl https://coupang-wing-cs.fly.dev/api/automation/chatgpt/status
```

### 4-2. 프론트엔드 테스트

브라우저에서 다음 URL들을 **직접 입력**:
```
✅ https://coupang-wing-cs-frontend.vercel.app/
✅ https://coupang-wing-cs-frontend.vercel.app/dashboard
✅ https://coupang-wing-cs-frontend.vercel.app/inquiries
✅ https://coupang-wing-cs-frontend.vercel.app/automation
```

모든 페이지가 정상 작동해야 합니다!

### 4-3. 프론트엔드 ↔ 백엔드 연결 테스트

1. 프론트엔드 접속
2. **대시보드**에서 **ChatGPT 연결 상태** 카드 확인
3. 연결 안됨으로 표시되면 **"자동 연결 시도"** 버튼 클릭
4. API 통신이 정상적으로 작동하는지 확인

### 4-4. 브라우저 개발자 도구로 확인

1. F12 키 → 개발자 도구 열기
2. **Network** 탭 확인
3. `/api/` 요청들이 백엔드로 전달되는지 확인
4. **Console** 탭에서 오류 확인

---

## 🎉 성공!

모든 테스트를 통과했다면 성공입니다!

### 최종 확인 체크리스트

- [ ] 백엔드 헬스체크 통과
- [ ] 백엔드 API 문서 접속 가능
- [ ] 프론트엔드 모든 페이지 접속 가능
- [ ] ChatGPT 연결 상태 표시
- [ ] API 통신 정상 작동
- [ ] 브라우저 콘솔에 오류 없음

---

## 📊 배포된 URL 정리

### 백엔드 (Fly.io)
- **메인**: `https://coupang-wing-cs.fly.dev`
- **헬스체크**: `https://coupang-wing-cs.fly.dev/health`
- **API 문서**: `https://coupang-wing-cs.fly.dev/docs`
- **ChatGPT 상태**: `https://coupang-wing-cs.fly.dev/api/automation/chatgpt/status`

### 프론트엔드 (Vercel)
- **메인**: `https://coupang-wing-cs-frontend.vercel.app`
- **대시보드**: `https://coupang-wing-cs-frontend.vercel.app/dashboard`
- **문의 관리**: `https://coupang-wing-cs-frontend.vercel.app/inquiries`

---

## 🔧 문제 해결

### 백엔드 문제

#### 배포 실패
```bash
fly logs
fly status
fly deploy --force
```

#### 환경변수 확인
```bash
fly secrets list
```

#### 메모리 부족
`backend/fly.toml` 수정:
```toml
[[vm]]
  memory_mb = 512  # 256 → 512로 증가
```

### 프론트엔드 문제

#### 404 오류
→ `404_FIX_GUIDE.md` 참고

#### API 연결 실패
1. `.env.production` 확인
2. `vercel.json` URL 확인
3. Vercel Dashboard 환경변수 확인
4. CORS 설정 확인 (`backend/app/main.py`)

#### 빌드 오류
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

---

## 🚀 자동 배포 스크립트

전체 과정을 자동화:

**Windows:**
```bash
deploy.bat
```

**Linux/macOS:**
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 💡 다음 단계

배포 완료 후:

1. **커스텀 도메인 연결** (선택)
   - Vercel: `www.yourdomain.com`
   - Fly.io: `api.yourdomain.com`

2. **모니터링 설정**
   - Fly.io Dashboard
   - Vercel Analytics

3. **CI/CD 파이프라인**
   - GitHub Actions
   - 자동 배포 설정

4. **데이터베이스 백업**
   - Fly.io Volumes
   - 정기 백업 스크립트

---

## 📞 추가 지원

- **Fly.io 문서**: https://fly.io/docs
- **Vercel 문서**: https://vercel.com/docs
- **배포 가이드**: `DEPLOYMENT_GUIDE.md`
- **404 해결**: `404_FIX_GUIDE.md`

---

**배포 성공을 축하합니다! 🎉🚀**
