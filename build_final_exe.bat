@echo off
echo ====================================
echo Building Final Executable
echo ====================================
echo.

echo [1] Installing PyInstaller...
venv\Scripts\python.exe -m pip install pyinstaller -q
echo [OK] PyInstaller ready

echo.
echo [2] Building executable...
venv\Scripts\pyinstaller.exe --onefile --name "최종실행파일" --icon=NONE --console "최종실행파일.py"

echo.
echo [3] Checking build result...
if exist "dist\최종실행파일.exe" (
    echo [SUCCESS] Executable built successfully!
    echo.
    echo Location: dist\최종실행파일.exe
    echo.
    echo You can now run: dist\최종실행파일.exe
) else (
    echo [FAIL] Build failed. Please check the errors above.
)

echo.
echo ====================================
echo Build Complete
echo ====================================
pause
