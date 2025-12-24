# 🔧 404 오류 해결 가이드

Vercel 배포 후 404 NOT_FOUND 오류가 발생하는 경우 해결 방법입니다.

---

## 🎯 문제 원인

React Router를 사용하는 Single Page Application (SPA)에서 Vercel이 URL 라우팅을 올바르게 처리하지 못해 발생합니다.

예시:
- `https://your-app.vercel.app/` ✅ 작동
- `https://your-app.vercel.app/dashboard` ❌ 404 오류
- `https://your-app.vercel.app/inquiries` ❌ 404 오류

---

## ✅ 해결 방법

### 방법 1: vercel.json 수정 (이미 적용됨)

`frontend/vercel.json` 파일이 다음과 같이 설정되어 있는지 확인:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend-app.fly.dev/api/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://your-backend-app.fly.dev/api/$1"
    },
    {
      "handle": "filesystem"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

**설명:**
- `/api/*` 경로는 백엔드로 프록시
- 나머지 모든 경로는 `index.html`로 리다이렉트 (SPA 라우팅)

### 방법 2: _redirects 파일 추가 (이미 적용됨)

`frontend/public/_redirects` 파일 생성:

```
/*    /index.html   200
```

이 파일은 빌드 시 `dist` 폴더에 자동으로 복사됩니다.

---

## 🚀 재배포 방법

### 1. Git 커밋 및 푸시 (자동 배포)

Vercel에서 GitHub 연동이 되어 있다면:

```bash
git add .
git commit -m "Fix: 404 오류 해결 - SPA 라우팅 설정 추가"
git push origin main
```

Vercel이 자동으로 재배포합니다.

### 2. Vercel CLI로 수동 배포

```bash
cd frontend
vercel --prod
```

### 3. Vercel Dashboard에서 재배포

1. https://vercel.com/dashboard 접속
2. 프로젝트 선택
3. **Deployments** 탭
4. 최신 배포의 **⋯** (더보기) 클릭
5. **Redeploy** 선택

---

## 🧪 테스트 방법

재배포 후 다음 URL들을 브라우저에서 직접 입력하여 테스트:

```
https://your-app.vercel.app/
https://your-app.vercel.app/dashboard
https://your-app.vercel.app/inquiries
https://your-app.vercel.app/automation
```

**모든 URL이 정상적으로 로드되어야 합니다!**

---

## 📋 체크리스트

배포 전 확인사항:

- [ ] `frontend/vercel.json` 파일에 `rewrites`와 `routes` 설정 추가
- [ ] `frontend/public/_redirects` 파일 생성
- [ ] 백엔드 URL 업데이트 (`your-backend-app.fly.dev` → 실제 URL)
- [ ] `.env.production` 파일의 `VITE_API_URL` 확인
- [ ] Git 커밋 및 푸시 또는 `vercel --prod` 실행

---

## 🔍 추가 확인사항

### 1. 빌드 로그 확인

Vercel Dashboard > Deployments > 최신 배포 > View Build Logs

확인할 내용:
- 빌드 성공 여부
- `dist` 폴더 생성 확인
- `_redirects` 파일 포함 확인

### 2. 프로덕션 URL 테스트

브라우저 개발자 도구 (F12) 열기:
- **Network** 탭에서 요청 확인
- **Console** 탭에서 오류 확인

### 3. API 프록시 테스트

```bash
# 프론트엔드에서 API 호출 테스트
curl https://your-app.vercel.app/api/health

# 백엔드 직접 호출
curl https://your-backend-app.fly.dev/health
```

둘 다 정상 응답이 와야 합니다.

---

## 🐛 여전히 404 오류가 발생한다면?

### 옵션 1: vercel.json 간소화

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

이 설정으로 재배포 후 테스트.

### 옵션 2: Vite 설정 확인

`frontend/vite.config.js` 파일 확인:

```javascript
export default defineConfig({
  plugins: [react()],
  base: './',  // 중요: 상대 경로 사용
  build: {
    outDir: 'dist'
  }
})
```

### 옵션 3: Vercel 프레임워크 설정 확인

Vercel Dashboard > Project Settings > Build & Development Settings

- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

---

## 💡 추가 팁

### SPA 라우팅 동작 원리

1. 사용자가 `https://your-app.vercel.app/dashboard` 접속
2. Vercel이 `/dashboard` 파일을 찾음 → 없음!
3. `vercel.json`의 `rewrites` 규칙 적용
4. `/(.*)`가 매칭되어 `/index.html`로 리다이렉트
5. React 앱이 로드되고 React Router가 `/dashboard` 라우트 처리
6. 정상적으로 Dashboard 페이지 표시

### API 프록시 동작 원리

1. 프론트엔드에서 `/api/health` 요청
2. Vercel이 `/api/*` 규칙 매칭
3. `https://your-backend-app.fly.dev/api/health`로 프록시
4. 백엔드 응답을 프론트엔드로 전달

---

## 📞 지원

문제가 계속되면:

1. **Vercel 문서**: https://vercel.com/docs/configuration
2. **Vite 문서**: https://vitejs.dev/guide/static-deploy.html
3. **React Router 문서**: https://reactrouter.com/en/main/start/tutorial

---

**404 오류 해결 성공을 기원합니다! 🎉**
