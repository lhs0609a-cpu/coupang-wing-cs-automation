# ⚡ 빠른 404 해결 방법

## 1단계: 파일 확인

다음 파일들이 제대로 생성되었는지 확인:

✅ `frontend/vercel.json` - SPA 라우팅 설정
✅ `frontend/public/_redirects` - 리다이렉트 규칙

## 2단계: 백엔드 URL 업데이트

**중요!** 다음 파일에서 `your-backend-app.fly.dev`를 실제 Fly.io URL로 변경:

### `frontend/vercel.json`
```json
"destination": "https://실제백엔드URL.fly.dev/api/:path*"
```

### `frontend/.env.production`
```env
VITE_API_URL=https://실제백엔드URL.fly.dev
```

## 3단계: 재배포

### 옵션 A: Git으로 자동 배포
```bash
git add .
git commit -m "Fix 404 - SPA routing"
git push
```

### 옵션 B: Vercel CLI
```bash
cd frontend
vercel --prod
```

## 4단계: 확인

브라우저에서 테스트:
```
https://your-app.vercel.app/
https://your-app.vercel.app/dashboard
https://your-app.vercel.app/inquiries
```

## ✅ 성공!

모든 URL이 정상 작동하면 완료!

---

**여전히 404가 나온다면?**
→ `404_FIX_GUIDE.md` 파일 참고
