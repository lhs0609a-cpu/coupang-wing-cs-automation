# 🚀 Vercel & Fly.io 배포 가이드

쿠팡 윙 CS 자동화 시스템을 Vercel (프론트엔드)과 Fly.io (백엔드)에 배포하는 완벽 가이드입니다.

---

## 📋 목차

1. [사전 준비](#사전-준비)
2. [백엔드 배포 (Fly.io)](#백엔드-배포-flyio)
3. [프론트엔드 배포 (Vercel)](#프론트엔드-배포-vercel)
4. [환경변수 설정](#환경변수-설정)
5. [배포 확인](#배포-확인)
6. [문제 해결](#문제-해결)

---

## 사전 준비

### 필수 도구 설치

1. **Git** 설치
   ```bash
   git --version
   ```

2. **Node.js & npm** 설치 (v18 이상)
   ```bash
   node --version
   npm --version
   ```

3. **Fly.io CLI** 설치
   - Windows (PowerShell):
     ```powershell
     iwr https://fly.io/install.ps1 -useb | iex
     ```
   - macOS/Linux:
     ```bash
     curl -L https://fly.io/install.sh | sh
     ```

4. **Vercel CLI** 설치
   ```bash
   npm install -g vercel
   ```

### 계정 생성

1. **Fly.io 계정**: https://fly.io/app/sign-up
2. **Vercel 계정**: https://vercel.com/signup
3. **GitHub 계정**: https://github.com/signup (선택사항, 권장)

---

## 백엔드 배포 (Fly.io)

### 1단계: Fly.io 로그인

```bash
fly auth login
```

브라우저가 자동으로 열리고 로그인 페이지가 표시됩니다.

### 2단계: Fly.io 앱 생성

백엔드 디렉토리로 이동:
```bash
cd backend
```

앱 초기화:
```bash
fly launch
```

다음 질문들에 답변:
- **App Name**: `coupang-wing-cs-backend` (또는 원하는 이름)
- **Region**: `nrt` (도쿄 - 한국과 가까움)
- **Would you like to set up a PostgreSQL database?**: `No`
- **Would you like to set up an Upstash Redis database?**: `No`
- **Would you like to deploy now?**: `No` (환경변수 설정 후 배포)

### 3단계: 환경변수 설정

```bash
# OpenAI API Key 설정
fly secrets set OPENAI_API_KEY="your-openai-api-key"

# Coupang API 설정 (있는 경우)
fly secrets set COUPANG_ACCESS_KEY="your-access-key"
fly secrets set COUPANG_SECRET_KEY="your-secret-key"
fly secrets set COUPANG_VENDOR_ID="your-vendor-id"

# 데이터베이스 URL (SQLite 사용)
fly secrets set DATABASE_URL="sqlite:///./database/coupang_cs.db"

# 시크릿 키
fly secrets set SECRET_KEY="your-secret-key-change-this"
```

### 4단계: 배포 실행

```bash
fly deploy
```

배포가 완료되면 URL이 표시됩니다:
```
https://coupang-wing-cs-backend.fly.dev
```

### 5단계: 배포 확인

```bash
# 헬스체크
curl https://coupang-wing-cs-backend.fly.dev/health

# API 문서 확인
open https://coupang-wing-cs-backend.fly.dev/docs
```

### 6단계: 로그 확인

```bash
# 실시간 로그
fly logs

# 최근 로그
fly logs --recent
```

---

## 프론트엔드 배포 (Vercel)

### 1단계: 백엔드 URL 업데이트

프론트엔드 디렉토리로 이동:
```bash
cd ../frontend
```

`.env.production` 파일 수정:
```env
VITE_API_URL=https://coupang-wing-cs-backend.fly.dev
```

`vercel.json` 파일에서 백엔드 URL 업데이트:
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://coupang-wing-cs-backend.fly.dev/api/:path*"
    }
  ]
}
```

### 2단계: Vercel 로그인

```bash
vercel login
```

이메일 또는 GitHub로 로그인합니다.

### 3단계: 배포 실행

```bash
# 첫 배포
vercel

# 프로덕션 배포
vercel --prod
```

질문에 답변:
- **Set up and deploy?**: `Y`
- **Which scope?**: 본인 계정 선택
- **Link to existing project?**: `N`
- **Project name**: `coupang-wing-cs-frontend`
- **Directory**: `.` (현재 디렉토리)
- **Override settings?**: `N`

### 4단계: 환경변수 설정 (Vercel Dashboard)

1. https://vercel.com/dashboard 접속
2. 프로젝트 선택
3. **Settings** > **Environment Variables** 클릭
4. 환경변수 추가:
   - Key: `VITE_API_URL`
   - Value: `https://coupang-wing-cs-backend.fly.dev`
   - Environment: `Production`, `Preview`, `Development` 모두 체크

### 5단계: 재배포

환경변수 설정 후 재배포:
```bash
vercel --prod
```

배포가 완료되면 URL이 표시됩니다:
```
https://coupang-wing-cs-frontend.vercel.app
```

---

## 환경변수 설정

### 백엔드 (Fly.io)

필수 환경변수:
```bash
OPENAI_API_KEY=sk-...                    # OpenAI API 키
DATABASE_URL=sqlite:///./database/...    # 데이터베이스 URL
SECRET_KEY=your-secret-key               # JWT 시크릿 키
ENVIRONMENT=production                   # 환경
LOG_LEVEL=INFO                          # 로그 레벨
```

선택 환경변수:
```bash
COUPANG_ACCESS_KEY=...
COUPANG_SECRET_KEY=...
COUPANG_VENDOR_ID=...
SMTP_HOST=...
SMTP_USER=...
SLACK_WEBHOOK_URL=...
```

### 프론트엔드 (Vercel)

필수 환경변수:
```bash
VITE_API_URL=https://your-backend.fly.dev
```

---

## 배포 확인

### 1. 백엔드 확인

```bash
# 헬스체크
curl https://coupang-wing-cs-backend.fly.dev/health

# API 문서
open https://coupang-wing-cs-backend.fly.dev/docs

# ChatGPT 연결 상태
curl https://coupang-wing-cs-backend.fly.dev/api/automation/chatgpt/status
```

### 2. 프론트엔드 확인

브라우저에서 확인:
```
https://coupang-wing-cs-frontend.vercel.app
```

확인 사항:
- [ ] 대시보드 로딩
- [ ] ChatGPT 연결 상태 표시
- [ ] API 통신 정상 작동

### 3. 전체 시스템 확인

1. **프론트엔드 접속**: Vercel URL로 접속
2. **ChatGPT 상태 확인**: 대시보드에서 연결 상태 확인
3. **API 테스트**: API 문서에서 엔드포인트 테스트
4. **로그 확인**:
   ```bash
   fly logs  # 백엔드 로그
   vercel logs  # 프론트엔드 로그
   ```

---

## 문제 해결

### 백엔드 문제

#### 1. 배포 실패
```bash
# 로그 확인
fly logs

# 상태 확인
fly status

# 재배포
fly deploy --force
```

#### 2. 데이터베이스 오류
```bash
# Volume 생성 (영구 저장소)
fly volumes create coupang_data --region nrt --size 1

# fly.toml에 Volume 마운트 추가
[mounts]
  source = "coupang_data"
  destination = "/app/database"
```

#### 3. 메모리 부족
```bash
# fly.toml에서 메모리 증가
[[vm]]
  memory_mb = 512  # 256 -> 512로 증가
```

### 프론트엔드 문제

#### 1. API 연결 실패
- `.env.production` 파일의 `VITE_API_URL` 확인
- `vercel.json`의 `rewrites` 설정 확인
- Vercel Dashboard에서 환경변수 확인

#### 2. 빌드 오류
```bash
# 로컬에서 빌드 테스트
npm run build

# 캐시 삭제 후 재빌드
rm -rf node_modules .next
npm install
npm run build
```

#### 3. CORS 오류
백엔드 `app/main.py`에서 CORS 설정 확인:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://coupang-wing-cs-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 유용한 명령어

### Fly.io

```bash
# 앱 상태 확인
fly status

# 로그 보기
fly logs

# SSH 접속
fly ssh console

# 스케일 조정
fly scale count 2

# 앱 재시작
fly apps restart

# 환경변수 확인
fly secrets list

# 앱 삭제
fly apps destroy coupang-wing-cs-backend
```

### Vercel

```bash
# 배포 목록
vercel list

# 로그 보기
vercel logs

# 환경변수 추가
vercel env add VITE_API_URL

# 프로젝트 삭제
vercel remove coupang-wing-cs-frontend
```

---

## 비용 최적화

### Fly.io (백엔드)
- **무료 티어**: 3개의 공유 CPU 머신, 3GB RAM
- **최적화**: `auto_stop_machines = true` (사용하지 않을 때 자동 중지)
- **권장 설정**: 1 CPU, 256MB RAM (기본 사용에 충분)

### Vercel (프론트엔드)
- **무료 티어**: Hobby 플랜 (무제한 배포, 100GB 대역폭/월)
- **최적화**: 빌드 최적화, 이미지 최적화 활용
- **권장**: 무료 플랜으로 충분

---

## 다음 단계

배포 완료 후:

1. **도메인 연결** (선택사항)
   - Vercel: 커스텀 도메인 추가
   - Fly.io: DNS 설정

2. **모니터링 설정**
   - Fly.io 대시보드에서 메트릭 확인
   - Vercel Analytics 활성화

3. **자동 배포 설정**
   - GitHub 연동
   - Git push 시 자동 배포

4. **백업 설정**
   - 데이터베이스 정기 백업
   - 로그 보관 정책 설정

---

## 지원

문제가 발생하면:
1. 이 가이드의 문제 해결 섹션 확인
2. Fly.io 문서: https://fly.io/docs
3. Vercel 문서: https://vercel.com/docs
4. GitHub Issues 제출

---

**배포 성공을 기원합니다! 🎉**
