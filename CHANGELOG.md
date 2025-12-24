# 변경 이력 (Changelog)

모든 중요한 변경사항이 이 파일에 기록됩니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 따르며,
이 프로젝트는 [Semantic Versioning](https://semver.org/lang/ko/)을 준수합니다.

---

## [1.0.0] - 2025-01-15

### 추가됨 (Added)
- ✨ 초기 릴리스
- 🎯 Coupang Wing CS 자동화 시스템 핵심 기능
- 🤖 AI 기반 자동 응답 생성
- 📊 실시간 모니터링 시스템
- 🔒 보안 미들웨어 (Rate Limiting, Security Headers)
- 💾 캐싱 시스템
- 📈 배치 작업 진행률 추적
- 🧪 자동화된 테스트 프레임워크
- 📦 Docker 개발 환경
- 🔔 WebSocket 실시간 알림
- 🔍 고급 검색 및 필터링
- 👥 사용자 역할 및 권한 관리
- 💬 내부 메모 및 댓글 시스템
- 📤 Excel/CSV Import/Export
- 🎨 스마트 템플릿 추천 AI
- 😊 감정 분석 및 시각화
- 🧪 A/B 테스트 시스템
- 🔗 Webhook 통합
- 🔐 민감정보 마스킹
- 📝 감사 로그 및 보안

### API 엔드포인트
- `/api/inquiries` - 문의 관리
- `/api/responses` - 응답 관리
- `/api/monitoring` - 모니터링
- `/api/batch` - 배치 작업 추적
- `/api/ux/*` - UX 기능 (검색, 일괄작업, 템플릿 추천 등)
- `/ws/notifications` - WebSocket 알림

### 기술 스택
- **Backend**: FastAPI 0.104.1, Python 3.11+
- **Database**: SQLAlchemy 2.0+, SQLite
- **AI**: OpenAI GPT-4
- **Web Automation**: Selenium 4.15+
- **Testing**: pytest 7.4.3
- **Monitoring**: Loguru, psutil
- **Security**: bcrypt, passlib

---

## [Unreleased]

### 계획됨 (Planned)
- 🌐 프론트엔드 대시보드
- 🔄 CI/CD 파이프라인
- 📧 이메일/Slack 알림
- 🗄️ PostgreSQL 지원
- 🌍 다국어 지원
- 📱 모바일 앱

---

## 버전 번호 규칙

**MAJOR.MINOR.PATCH** 형식을 따릅니다:

- **MAJOR**: 호환되지 않는 API 변경
- **MINOR**: 하위 호환성을 유지하면서 기능 추가
- **PATCH**: 하위 호환성을 유지하는 버그 수정

### 예시
- `1.0.0` → `1.0.1`: 버그 수정
- `1.0.0` → `1.1.0`: 새로운 기능 추가
- `1.0.0` → `2.0.0`: 중대한 변경 (Breaking Changes)

---

## 변경사항 카테고리

- `추가됨 (Added)`: 새로운 기능
- `변경됨 (Changed)`: 기존 기능의 변경
- `더 이상 사용되지 않음 (Deprecated)`: 곧 제거될 기능
- `제거됨 (Removed)`: 제거된 기능
- `수정됨 (Fixed)`: 버그 수정
- `보안 (Security)`: 보안 취약점 수정

---

마지막 업데이트: 2025-01-15
