"""
배포 패키지 생성 스크립트
"""
import shutil
import codecs
from pathlib import Path

def create_deployment():
    # 원본 및 배포 폴더
    project_root = Path(__file__).parent
    deploy_folder = project_root.parent / 'CoupangWingCS_Deploy'

    # 배포 폴더 생성
    if deploy_folder.exists():
        print(f'Removing existing folder: {deploy_folder}')
        shutil.rmtree(deploy_folder)

    deploy_folder.mkdir()
    print(f'Created deployment folder: {deploy_folder}')
    print('=' * 70)

    # 복사할 항목들
    items_to_copy = [
        'backend',
        'version.txt',
        'CHANGELOG.md',
        'README.md',
        'README_INSTALL.md',
        'IMPROVEMENTS.md',
        'DEVELOPER_GUIDE.md',
        'auto_deploy.py',
        'health_check.py',
        'error_handler.py',
        'update_checker.py',
        'performance_monitor.py',
        'backup_system.py',
        'log_rotation.py',
        'docker-compose.dev.yml',
    ]

    # 제외할 패턴
    exclude_dirs = {
        '__pycache__', '.pytest_cache', 'venv', 'env', '.git',
        'logs', 'data', 'error_reports', 'htmlcov', '.coverage',
        'backups', 'Release'
    }

    print('\nCopying files...')
    copied = 0
    for item in items_to_copy:
        src = project_root / item
        if not src.exists():
            print(f'  Skip: {item} (not found)')
            continue

        dst = deploy_folder / item

        try:
            if src.is_dir():
                shutil.copytree(
                    src, dst,
                    ignore=lambda dir, files: [
                        f for f in files
                        if any(excl in Path(dir, f).parts for excl in exclude_dirs)
                    ]
                )
                print(f'  OK: {item}/')
            else:
                shutil.copy2(src, dst)
                print(f'  OK: {item}')
            copied += 1
        except Exception as e:
            print(f'  FAIL: {item} - {e}')

    # 민감한 파일 제거
    print('\nRemoving sensitive files...')
    sensitive = ['backend/.env', 'backend/coupang_cs.db', 'backend/coupang_wing.db']
    for file_path in sensitive:
        full_path = deploy_folder / file_path
        if full_path.exists():
            full_path.unlink()
            print(f'  Removed: {file_path}')

    # 필수 폴더 생성
    print('\nCreating required folders...')
    for folder in ['logs', 'data', 'error_reports', 'backend/logs', 'backups']:
        (deploy_folder / folder).mkdir(parents=True, exist_ok=True)
    print('  OK: All folders created')

    print('\n' + '=' * 70)
    print(f'SUCCESS!')
    print(f'Location: {deploy_folder}')
    print(f'Total items: {copied}')
    print('=' * 70)

    return deploy_folder

if __name__ == '__main__':
    deploy_folder = create_deployment()

    # 배치 파일 생성 (영어만 사용)
    print('\nCreating batch files...')

    # install.bat
    install_bat_content = '''@echo off
chcp 65001 > nul

echo.
echo ====================================================================
echo  Coupang Wing CS Automation - Installation
echo ====================================================================
echo.

echo [1/8] Checking Python...
python --version > nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo OK

echo [2/8] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo OK

echo [3/8] Creating virtual environment...
if not exist "backend\\venv" (
    python -m venv backend\\venv
)
if exist "backend\\venv\\Scripts\\activate.bat" (
    call backend\\venv\\Scripts\\activate.bat
)
echo OK

echo [4/8] Installing packages...
python -m pip install -r backend\\requirements.txt --quiet
if %errorLevel% neq 0 (
    echo ERROR: Installation failed
    pause
    exit /b 1
)
echo OK

echo [5/8] Setting up environment...
if not exist "backend\\.env" (
    if exist "backend\\.env.example" (
        copy "backend\\.env.example" "backend\\.env" > nul
        echo IMPORTANT: Edit backend\\.env and set OPENAI_API_KEY
    )
)
echo OK

echo [6/8] Creating folders...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "error_reports" mkdir error_reports
if not exist "backend\\logs" mkdir backend\\logs
echo OK

echo [7/8] Initializing database...
if not exist "backend\\coupang_wing.db" (
    python -c "import sys; sys.path.insert(0, 'backend'); from app.database import init_db; init_db()"
)
echo OK

echo [8/8] Health check...
if exist "health_check.py" (
    python health_check.py
)
echo OK

echo.
echo ====================================================================
echo  Installation Complete!
echo ====================================================================
echo.
echo Next steps:
echo   1. Edit backend\\.env and set OPENAI_API_KEY
echo   2. Run: run.bat
echo.
echo ====================================================================
pause
'''

    # run.bat
    run_bat_content = '''@echo off
chcp 65001 > nul

echo.
echo ====================================================================
echo  Coupang Wing CS Automation - Starting Server
echo ====================================================================
echo.

if exist "backend\\venv\\Scripts\\activate.bat" (
    call backend\\venv\\Scripts\\activate.bat
)

if not exist "backend\\.env" (
    echo ERROR: backend\\.env not found. Run install.bat first.
    pause
    exit /b 1
)

echo Server starting...
echo   URL: http://localhost:8080
echo   API Docs: http://localhost:8080/docs
echo   Stop: Ctrl+C
echo.

cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

pause
'''

    # 파일 저장 (UTF-8 BOM)
    with open(deploy_folder / 'install.bat', 'w', encoding='utf-8-sig') as f:
        f.write(install_bat_content)
    print('  Created: install.bat')

    with open(deploy_folder / 'run.bat', 'w', encoding='utf-8-sig') as f:
        f.write(run_bat_content)
    print('  Created: run.bat')

    # install.sh
    install_sh_content = '''#!/bin/bash
echo ""
echo "===================================================================="
echo " Coupang Wing CS Automation - Installation"
echo "===================================================================="
echo ""

echo "[1/8] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found"
    exit 1
fi
echo "OK"

echo "[2/8] Upgrading pip..."
python3 -m pip install --upgrade pip --quiet
echo "OK"

echo "[3/8] Creating virtual environment..."
if [ ! -d "backend/venv" ]; then
    python3 -m venv backend/venv
fi
if [ -f "backend/venv/bin/activate" ]; then
    source backend/venv/bin/activate
fi
echo "OK"

echo "[4/8] Installing packages..."
python3 -m pip install -r backend/requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "ERROR: Installation failed"
    exit 1
fi
echo "OK"

echo "[5/8] Setting up environment..."
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo "IMPORTANT: Edit backend/.env and set OPENAI_API_KEY"
    fi
fi
echo "OK"

echo "[6/8] Creating folders..."
mkdir -p logs data error_reports backend/logs
echo "OK"

echo "[7/8] Initializing database..."
if [ ! -f "backend/coupang_wing.db" ]; then
    python3 -c "import sys; sys.path.insert(0, 'backend'); from app.database import init_db; init_db()"
fi
echo "OK"

echo "[8/8] Health check..."
if [ -f "health_check.py" ]; then
    python3 health_check.py
fi
echo "OK"

echo ""
echo "===================================================================="
echo " Installation Complete!"
echo "===================================================================="
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env and set OPENAI_API_KEY"
echo "  2. Run: ./run.sh"
echo ""
echo "===================================================================="
'''

    # run.sh
    run_sh_content = '''#!/bin/bash
echo ""
echo "===================================================================="
echo " Coupang Wing CS Automation - Starting Server"
echo "===================================================================="
echo ""

if [ -f "backend/venv/bin/activate" ]; then
    source backend/venv/bin/activate
fi

if [ ! -f "backend/.env" ]; then
    echo "ERROR: backend/.env not found. Run ./install.sh first."
    exit 1
fi

echo "Server starting..."
echo "  URL: http://localhost:8080"
echo "  API Docs: http://localhost:8080/docs"
echo "  Stop: Ctrl+C"
echo ""

cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
'''

    with open(deploy_folder / 'install.sh', 'w', encoding='utf-8', newline='\n') as f:
        f.write(install_sh_content)
    print('  Created: install.sh')

    with open(deploy_folder / 'run.sh', 'w', encoding='utf-8', newline='\n') as f:
        f.write(run_sh_content)
    print('  Created: run.sh')

    # README 생성
    readme_content = '''# Coupang Wing CS Automation System

## Quick Start

### Windows
1. Run: `install.bat`
2. Edit: `backend\\.env` (set OPENAI_API_KEY)
3. Run: `run.bat`

### Mac/Linux
1. Run: `chmod +x install.sh run.sh`
2. Run: `./install.sh`
3. Edit: `backend/.env` (set OPENAI_API_KEY)
4. Run: `./run.sh`

## Access
- Main: http://localhost:8080
- API Docs: http://localhost:8080/docs

## Documentation
- Installation Guide: README_INSTALL.md
- Developer Guide: DEVELOPER_GUIDE.md
- Changelog: CHANGELOG.md

## Version
v1.0.0
'''

    with open(deploy_folder / 'START_HERE.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print('  Created: START_HERE.md')

    print('\n' + '=' * 70)
    print('DEPLOYMENT PACKAGE READY!')
    print(f'Location: {deploy_folder}')
    print('=' * 70)

create_deployment()
