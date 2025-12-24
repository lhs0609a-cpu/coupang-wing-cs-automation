#!/bin/bash
# ====================================================================
# Coupang Wing CS 자동화 시스템 - 자동 설치 스크립트 (Mac/Linux)
# ====================================================================

set -e  # 에러 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "===================================================================="
echo "🚀 Coupang Wing CS 자동화 시스템 설치"
echo "===================================================================="
echo ""

# ====================================================================
# 1단계: Python 버전 확인
# ====================================================================
echo "[1/8] Python 버전 확인 중..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3이 설치되어 있지 않습니다.${NC}"
    echo ""
    echo "💡 Python 3.8 이상을 설치해주세요:"
    echo "   macOS: brew install python3"
    echo "   Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo "   CentOS/RHEL: sudo yum install python3 python3-pip"
    echo ""
    exit 1
fi

# Python 버전 출력
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python $PYTHON_VERSION 발견${NC}"

# 버전 확인 (3.8 이상)
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
    echo -e "${RED}❌ Python 3.8 이상이 필요합니다. 현재: $PYTHON_VERSION${NC}"
    exit 1
fi

# ====================================================================
# 2단계: pip 업그레이드
# ====================================================================
echo ""
echo "[2/8] pip 업그레이드 중..."
python3 -m pip install --upgrade pip --quiet 2>&1 || {
    echo -e "${YELLOW}⚠️  pip 업그레이드 실패 (계속 진행)${NC}"
}
echo -e "${GREEN}✅ pip 업그레이드 완료${NC}"

# ====================================================================
# 3단계: 가상환경 생성 (선택적)
# ====================================================================
echo ""
echo "[3/8] 가상환경 확인 중..."

if [ ! -d "backend/venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv backend/venv 2>&1 || {
        echo -e "${YELLOW}⚠️  가상환경 생성 실패 (전역 환경에 설치됩니다)${NC}"
    }

    if [ -d "backend/venv" ]; then
        echo -e "${GREEN}✅ 가상환경 생성 완료${NC}"
    fi
else
    echo -e "${GREEN}✅ 가상환경이 이미 존재합니다${NC}"
fi

# 가상환경 활성화 (있는 경우)
if [ -f "backend/venv/bin/activate" ]; then
    echo "🔧 가상환경 활성화 중..."
    source backend/venv/bin/activate
fi

# ====================================================================
# 4단계: 의존성 설치
# ====================================================================
echo ""
echo "[4/8] 패키지 설치 중..."
echo "   (시간이 걸릴 수 있습니다...)"

if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt 파일이 없습니다.${NC}"
    exit 1
fi

python3 -m pip install -r backend/requirements.txt --quiet 2>&1 || {
    echo -e "${RED}❌ 패키지 설치 실패${NC}"
    echo ""
    echo "💡 다시 시도하거나 수동으로 설치하세요:"
    echo "   pip3 install -r backend/requirements.txt"
    echo ""
    exit 1
}

echo -e "${GREEN}✅ 패키지 설치 완료${NC}"

# ====================================================================
# 5단계: 환경 변수 파일 생성
# ====================================================================
echo ""
echo "[5/8] 환경 설정 중..."

if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.example" ]; then
        echo "📝 .env 파일 생성 중..."
        cp backend/.env.example backend/.env
        echo -e "${GREEN}✅ .env 파일 생성 완료${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  중요: backend/.env 파일을 열어 다음 항목을 설정하세요:${NC}"
        echo "   - OPENAI_API_KEY: OpenAI API 키"
        echo "   - 기타 필요한 설정"
        echo ""
    else
        echo -e "${YELLOW}⚠️  .env.example 파일이 없습니다.${NC}"
        echo "   수동으로 .env 파일을 생성해주세요."
    fi
else
    echo -e "${GREEN}✅ .env 파일이 이미 존재합니다${NC}"
fi

# ====================================================================
# 6단계: 필수 폴더 생성
# ====================================================================
echo ""
echo "[6/8] 필수 폴더 생성 중..."

mkdir -p logs
mkdir -p data
mkdir -p error_reports
mkdir -p backend/logs

echo -e "${GREEN}✅ 폴더 생성 완료${NC}"

# ====================================================================
# 7단계: 데이터베이스 초기화
# ====================================================================
echo ""
echo "[7/8] 데이터베이스 초기화 중..."

# 데이터베이스가 없는 경우에만 초기화
if [ ! -f "backend/coupang_wing.db" ]; then
    python3 -c "import sys; sys.path.insert(0, 'backend'); from app.database import init_db; init_db()" 2>&1 || {
        echo -e "${YELLOW}⚠️  데이터베이스 초기화 실패 (나중에 자동으로 생성됩니다)${NC}"
    }

    if [ -f "backend/coupang_wing.db" ]; then
        echo -e "${GREEN}✅ 데이터베이스 초기화 완료${NC}"
    fi
else
    echo -e "${GREEN}✅ 데이터베이스가 이미 존재합니다${NC}"
fi

# ====================================================================
# 8단계: 자가 진단 실행
# ====================================================================
echo ""
echo "[8/8] 시스템 자가 진단 중..."

if [ -f "health_check.py" ]; then
    python3 health_check.py || {
        echo ""
        echo -e "${YELLOW}⚠️  자가 진단에서 일부 문제가 발견되었습니다.${NC}"
        echo "   health_check_report.txt를 확인하세요."
        echo ""
    }
else
    echo -e "${YELLOW}⚠️  health_check.py 파일이 없습니다. (건너뜀)${NC}"
fi

# ====================================================================
# 완료
# ====================================================================
echo ""
echo "===================================================================="
echo "✅ 설치 완료!"
echo "===================================================================="
echo ""
echo "다음 단계:"
echo "  1. backend/.env 파일을 열어 필요한 설정 입력"
echo "  2. ./run.sh 실행하여 서버 시작"
echo ""
echo "서버 실행 명령:"
echo "  ./run.sh"
echo ""
echo "또는 수동으로:"
echo "  cd backend"
echo "  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"
echo ""
echo "===================================================================="
echo ""
