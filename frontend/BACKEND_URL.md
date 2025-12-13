# 백엔드 URL 설정

## 현재 설정 (하드코딩)

백엔드 URL이 다음 파일들에 하드코딩되어 있습니다:

### 1. `src/App.jsx`
```javascript
const CLOUD_BACKEND_URL = 'https://coupang-wing-cs-backend.fly.dev/api'
```

### 2. `src/utils/apiConfig.js`
```javascript
const CLOUD_BACKEND_URL = 'https://coupang-wing-cs-backend.fly.dev'
```

## 백엔드 URL 변경 방법

백엔드 URL을 변경하려면 위 두 파일에서 URL을 직접 수정하세요.

**예시:**
```javascript
// 기존
const CLOUD_BACKEND_URL = 'https://coupang-wing-cs-backend.fly.dev/api'

// 변경
const CLOUD_BACKEND_URL = 'https://new-backend-url.fly.dev/api'
```

## 환경변수를 사용하지 않는 이유

환경변수 (`VITE_API_URL`)를 사용하면 Vercel 배포 시 설정 문제가 발생할 수 있습니다.
따라서 안정성을 위해 URL을 직접 하드코딩하여 사용합니다.

## 배포 후 확인

배포 후 브라우저 콘솔(F12)에서 다음 로그를 확인하세요:
- `현재 apiBaseUrl: https://coupang-wing-cs-backend.fly.dev/api`
- `클라우드 백엔드 자동 연결 시작`

## 현재 백엔드

- **백엔드 URL**: https://coupang-wing-cs-backend.fly.dev
- **API 엔드포인트**: https://coupang-wing-cs-backend.fly.dev/api
- **프론트엔드 URL**: https://frontend-i2kq7fo4h-fewfs-projects-83cc0821.vercel.app
