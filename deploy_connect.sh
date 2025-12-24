#!/bin/bash
# Vercel + Fly.io 자동 연결 배포 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "  Vercel ⭐⭐⭐⭐⭐ + Fly.io ⭐⭐⭐⭐⭐ 자동 연결 배포"
echo "========================================================================"
echo ""

# 1. 사전 확인
echo -e "${BLUE}[1/5]${NC} 사전 확인 중..."
echo ""

# Fly CLI 확인
if ! command -v fly &> /dev/null; then
    echo -e "${RED}[오류]${NC} Fly CLI가 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo "  curl -L https://fly.io/install.sh | sh"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓${NC} Fly CLI 설치됨"

# Vercel CLI 확인
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}[오류]${NC} Vercel CLI가 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo "  npm install -g vercel"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓${NC} Vercel CLI 설치됨"
echo ""

# 2. Fly.io 로그인 확인
echo -e "${BLUE}[2/5]${NC} Fly.io 로그인 확인 중..."
echo ""

if ! fly auth whoami &> /dev/null; then
    echo "Fly.io에 로그인되어 있지 않습니다."
    echo "브라우저가 열립니다. 로그인해주세요."
    echo ""
    fly auth login
fi
echo -e "${GREEN}✓${NC} Fly.io 로그인됨"
echo ""

# 3. 백엔드 배포 (Fly.io)
echo -e "${BLUE}[3/5]${NC} 백엔드를 Fly.io에 배포 중..."
echo "========================================================================"
echo ""

cd backend

# 환경변수 설정
echo "환경변수를 설정해야 합니다."
echo ""
read -p "OpenAI API Key를 입력하세요 (sk-...): " OPENAI_KEY

if [ -z "$OPENAI_KEY" ]; then
    echo -e "${RED}[오류]${NC} OpenAI API Key가 필요합니다."
    exit 1
fi

echo ""
echo "환경변수 설정 중..."
fly secrets set OPENAI_API_KEY="$OPENAI_KEY"
fly secrets set DATABASE_URL="sqlite:///./database/coupang_cs.db"
fly secrets set SECRET_KEY="change-this-super-secret-key-in-production"
fly secrets set ENVIRONMENT="production"
fly secrets set LOG_LEVEL="INFO"

echo ""
echo "백엔드 배포 중... (5-10분 소요될 수 있습니다)"
echo ""

fly deploy

echo ""
echo -e "${GREEN}✓${NC} 백엔드 배포 완료!"
echo ""

# 백엔드 URL 확인
BACKEND_URL=$(fly status --json | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4)

if [ -z "$BACKEND_URL" ]; then
    echo "배포된 백엔드 URL을 입력하세요."
    echo "예: coupang-wing-cs.fly.dev (https:// 제외, 끝의 / 제외)"
    read -p "백엔드 URL: " BACKEND_URL
fi

echo ""
echo "백엔드 URL: https://$BACKEND_URL"
echo ""

cd ..

# 4. 프론트엔드 설정 업데이트
echo -e "${BLUE}[4/5]${NC} 프론트엔드 설정 업데이트 중..."
echo ""

cd frontend

# .env.production 업데이트
echo "VITE_API_URL=https://$BACKEND_URL" > .env.production
echo -e "${GREEN}✓${NC} .env.production 업데이트 완료"

# vercel.json 업데이트
echo ""
echo "vercel.json 파일 업데이트 중..."

# macOS와 Linux에서 다른 sed 문법 사용
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|https://your-backend-app.fly.dev|https://$BACKEND_URL|g" vercel.json
else
    # Linux
    sed -i "s|https://your-backend-app.fly.dev|https://$BACKEND_URL|g" vercel.json
fi

echo -e "${GREEN}✓${NC} vercel.json 업데이트 완료"

# 빌드 테스트
echo ""
echo "프론트엔드 빌드 테스트 중..."
npm run build

echo -e "${GREEN}✓${NC} 빌드 성공"
echo ""

# 5. Vercel 배포
echo -e "${BLUE}[5/5]${NC} 프론트엔드를 Vercel에 배포 중..."
echo "========================================================================"
echo ""

# Vercel 로그인 확인
if ! vercel whoami &> /dev/null; then
    echo "Vercel에 로그인되어 있지 않습니다."
    echo "브라우저가 열립니다. 로그인해주세요."
    echo ""
    vercel login
fi

echo "프론트엔드 배포 중..."
echo ""

vercel --prod

echo ""
echo -e "${GREEN}✓${NC} 프론트엔드 배포 완료!"
echo ""

cd ..

# 완료
echo "========================================================================"
echo "  배포 완료!"
echo "========================================================================"
echo ""
echo "백엔드 URL:"
echo "  - 메인: https://$BACKEND_URL"
echo "  - 헬스체크: https://$BACKEND_URL/health"
echo "  - API 문서: https://$BACKEND_URL/docs"
echo ""
echo "프론트엔드 URL:"
echo "  - 위의 Vercel 출력에서 확인하세요"
echo ""
echo "다음 단계:"
echo "  1. 프론트엔드 URL로 접속"
echo "  2. ChatGPT 연결 상태 확인"
echo "  3. 모든 페이지 테스트"
echo ""
echo "Vercel Dashboard에서 환경변수도 추가하세요:"
echo "  https://vercel.com/dashboard"
echo "  Settings > Environment Variables"
echo "  VITE_API_URL = https://$BACKEND_URL"
echo ""
echo "========================================================================"
echo ""
