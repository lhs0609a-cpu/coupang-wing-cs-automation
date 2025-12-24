#!/bin/bash
# 자동 배포 스크립트

set -e  # 오류 발생 시 스크립트 중단

echo "========================================"
echo "  쿠팡 윙 CS 자동화 - 자동 배포 스크립트"
echo "========================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수: 단계 출력
print_step() {
    echo -e "\n${GREEN}[단계 $1/$2]${NC} $3"
}

# 함수: 에러 출력
print_error() {
    echo -e "${RED}[오류]${NC} $1"
}

# 함수: 경고 출력
print_warning() {
    echo -e "${YELLOW}[경고]${NC} $1"
}

# 1. 사전 확인
print_step 1 6 "사전 확인 중..."

# Git 확인
if ! command -v git &> /dev/null; then
    print_error "Git이 설치되어 있지 않습니다."
    exit 1
fi

# Fly CLI 확인
if ! command -v fly &> /dev/null; then
    print_error "Fly CLI가 설치되어 있지 않습니다."
    echo "설치: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Vercel CLI 확인
if ! command -v vercel &> /dev/null; then
    print_error "Vercel CLI가 설치되어 있지 않습니다."
    echo "설치: npm install -g vercel"
    exit 1
fi

echo "✓ 모든 필수 도구가 설치되어 있습니다."

# 2. 백엔드 배포 (Fly.io)
print_step 2 6 "백엔드를 Fly.io에 배포 중..."

cd backend

# Fly.io 로그인 확인
if ! fly auth whoami &> /dev/null; then
    print_warning "Fly.io에 로그인되어 있지 않습니다."
    echo "로그인 중..."
    fly auth login
fi

# 배포 실행
echo "백엔드 배포 중..."
if fly deploy; then
    echo "✓ 백엔드 배포 완료!"
    BACKEND_URL=$(fly status --json | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4)
    echo "백엔드 URL: https://$BACKEND_URL"
else
    print_error "백엔드 배포 실패!"
    exit 1
fi

cd ..

# 3. 프론트엔드 환경변수 업데이트
print_step 3 6 "프론트엔드 환경변수 업데이트 중..."

cd frontend

# .env.production 업데이트
if [ -n "$BACKEND_URL" ]; then
    echo "VITE_API_URL=https://$BACKEND_URL" > .env.production
    echo "✓ 환경변수 업데이트 완료"
else
    print_warning ".env.production 파일을 수동으로 확인하세요."
fi

# 4. 프론트엔드 빌드 테스트
print_step 4 6 "프론트엔드 빌드 테스트 중..."

if npm run build; then
    echo "✓ 빌드 성공!"
else
    print_error "빌드 실패!"
    exit 1
fi

# 5. 프론트엔드 배포 (Vercel)
print_step 5 6 "프론트엔드를 Vercel에 배포 중..."

# Vercel 로그인 확인
if ! vercel whoami &> /dev/null; then
    print_warning "Vercel에 로그인되어 있지 않습니다."
    echo "로그인 중..."
    vercel login
fi

# 프로덕션 배포
echo "프론트엔드 배포 중..."
if vercel --prod; then
    echo "✓ 프론트엔드 배포 완료!"
else
    print_error "프론트엔드 배포 실패!"
    exit 1
fi

cd ..

# 6. 배포 확인
print_step 6 6 "배포 확인 중..."

echo ""
echo "========================================"
echo "  배포 완료!"
echo "========================================"
echo ""
echo "백엔드 URL: https://$BACKEND_URL"
echo "프론트엔드 URL: 위의 Vercel 출력에서 확인"
echo ""
echo "다음 단계:"
echo "1. 프론트엔드 URL로 접속하여 테스트"
echo "2. ChatGPT 연결 상태 확인"
echo "3. API 문서 확인: https://$BACKEND_URL/docs"
echo ""
echo "========================================"
