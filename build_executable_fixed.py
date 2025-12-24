#!/usr/bin/env python3
"""
PyInstaller Build Script - FIXED VERSION
Includes all FastAPI middleware modules to fix import errors
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path


def print_step(step_num, total_steps, title):
    """Print formatted step header"""
    print("\n" + "=" * 70)
    print(f"  [{step_num}/{total_steps}] {title}")
    print("=" * 70 + "\n")


def clean_previous_build():
    """Remove previous build artifacts"""
    print_step(1, 7, "Cleaning previous build")

    folders = ['build', 'dist', '__pycache__']
    files = ['CoupangWingCS.spec']

    for folder in folders:
        folder_path = Path(folder)
        if folder_path.exists():
            print(f"  Removing: {folder}/")
            shutil.rmtree(folder_path)

    for file in files:
        file_path = Path(file)
        if file_path.exists():
            print(f"  Removing: {file}")
            file_path.unlink()

    print("  Done!")


def check_requirements():
    """Check Python and backend folder"""
    print_step(2, 7, "Checking requirements")

    # Check Python version
    print(f"  Python version: {sys.version.split()[0]}")

    # Check backend folder
    backend_path = Path('backend')
    if not backend_path.exists():
        print("\n  ERROR: backend folder not found!")
        print("  Please make sure 'backend' folder is in the same directory")
        print("  as this build script.")
        return False

    print(f"  Backend folder: Found ({len(list(backend_path.rglob('*')))} files)")

    # Check PyInstaller
    try:
        import PyInstaller
        print(f"  PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print("  PyInstaller: Not found, will install...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"
            ])
            print("  PyInstaller: Installed successfully")
        except subprocess.CalledProcessError:
            print("\n  ERROR: Failed to install PyInstaller")
            return False

    print("\n  All requirements met!")
    return True


def create_spec_file():
    """Create PyInstaller spec file with FIXED hidden imports"""
    print_step(3, 7, "Creating spec file (with FastAPI fix)")

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],  # Empty - we'll copy backend manually
    hiddenimports=[
        # Uvicorn
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # FastAPI - FIXED: Added all middleware modules
        'fastapi',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.middleware.gzip',
        'fastapi.middleware.httpsredirect',
        'fastapi.middleware.trustedhost',
        'fastapi.responses',
        'fastapi.routing',
        'fastapi.encoders',
        'fastapi.exceptions',
        'fastapi.param_functions',
        'fastapi.utils',
        # Starlette (FastAPI dependency)
        'starlette',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.middleware.gzip',
        'starlette.middleware.httpsredirect',
        'starlette.middleware.trustedhost',
        'starlette.routing',
        'starlette.responses',
        'starlette.exceptions',
        # SQLAlchemy
        'sqlalchemy',
        'sqlalchemy.ext',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.sql',
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.orm',
        'sqlalchemy.engine',
        # Pydantic
        'pydantic',
        'pydantic.fields',
        'pydantic.main',
        'pydantic.types',
        'pydantic.networks',
        'pydantic_settings',
        # Other dependencies
        'multipart',
        'email_validator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CoupangWingCS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CoupangWingCS',
)
'''

    with open('CoupangWingCS.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("  Spec file created: CoupangWingCS.spec")
    print("  FIXED: Added fastapi.middleware.cors and related modules")


def run_pyinstaller():
    """Run PyInstaller to build executable"""
    print_step(4, 7, "Building executable")
    print("  This may take 5-10 minutes, please wait...")
    print()

    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "CoupangWingCS.spec"],
            check=True,
            capture_output=True,
            text=True
        )

        # Show last few lines of output
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[-10:]:
                if line.strip():
                    print(f"    {line}")

        print("\n  Build completed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n  ERROR: Build failed!")
        if e.stdout:
            print("\n  Output:")
            print(e.stdout)
        if e.stderr:
            print("\n  Errors:")
            print(e.stderr)
        return False


def copy_backend_folder():
    """Manually copy backend folder to dist"""
    print_step(5, 7, "Copying backend folder")

    src = Path('backend')
    dst = Path('dist') / 'CoupangWingCS' / 'backend'

    if not src.exists():
        print("  ERROR: Source backend folder not found!")
        return False

    if dst.exists():
        print("  Removing old backend folder...")
        shutil.rmtree(dst)

    print(f"  Copying: {src} -> {dst}")

    # Copy entire backend folder
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.db',
        '*.db-shm',
        '*.db-wal'
    ))

    # Count files
    file_count = len(list(dst.rglob('*')))
    print(f"  Copied {file_count} files")
    print("  Done!")
    return True


def copy_additional_files():
    """Copy .env.example and create README"""
    print_step(6, 7, "Adding additional files")

    dist_path = Path('dist') / 'CoupangWingCS'

    # Copy .env.example
    env_example = Path('backend') / '.env.example'
    if env_example.exists():
        dst = dist_path / '.env.example'
        shutil.copy2(env_example, dst)
        print("  Copied: .env.example")

    # Create README
    readme_content = """Coupang Wing CS Automation System v1.0.0
==========================================

HOW TO RUN:
1. Double-click CoupangWingCS.exe
2. Server will start and browser will open automatically
3. Access the API documentation at http://localhost:8080/docs

CONFIGURATION:
- On first run, a .env file will be created automatically
- Edit .env to add your API keys

REQUIREMENTS:
- Windows 10/11
- No Python installation needed!

FOLDER STRUCTURE:
CoupangWingCS/
├── CoupangWingCS.exe  (Main executable)
├── backend/           (Application files - DO NOT DELETE)
├── _internal/         (Python runtime - DO NOT DELETE)
└── .env.example       (Configuration template)

IMPORTANT:
- When sharing, copy the ENTIRE CoupangWingCS folder
- Do NOT copy just the .exe file alone
- The backend folder must be in the same directory as the .exe

TROUBLESHOOTING:
- "backend folder not found": Make sure the entire folder was copied
- "Port 8080 in use": Close other instances or programs using port 8080
- Antivirus blocking: Add to exceptions (this is a false positive)

To stop the server: Press Ctrl+C in the console window

For more information, visit the project repository.
"""

    readme_file = dist_path / 'README.txt'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("  Created: README.txt")

    print("  Done!")
    return True


def verify_build():
    """Verify the build was successful"""
    print_step(7, 7, "Verifying build")

    dist_path = Path('dist') / 'CoupangWingCS'
    exe_file = dist_path / 'CoupangWingCS.exe'
    backend_folder = dist_path / 'backend'
    internal_folder = dist_path / '_internal'

    checks = [
        (exe_file, "CoupangWingCS.exe"),
        (backend_folder, "backend folder"),
        (internal_folder, "_internal folder"),
    ]

    all_good = True
    for path, name in checks:
        if path.exists():
            if path.is_dir():
                count = len(list(path.rglob('*')))
                print(f"  ✓ {name}: Found ({count} items)")
            else:
                size = path.stat().st_size / (1024 * 1024)
                print(f"  ✓ {name}: Found ({size:.1f} MB)")
        else:
            print(f"  ✗ {name}: NOT FOUND")
            all_good = False

    if all_good:
        print("\n  All checks passed!")
        return True
    else:
        print("\n  Some files are missing!")
        return False


def main():
    """Main build process"""
    print("\n" + "=" * 70)
    print("  Coupang Wing CS - Executable Builder v2.1 (FIXED)")
    print("  Fixed: FastAPI middleware import errors")
    print("=" * 70)

    # Step 1: Clean
    clean_previous_build()

    # Step 2: Check requirements
    if not check_requirements():
        input("\nPress Enter to exit...")
        return

    # Step 3: Create spec
    create_spec_file()

    # Step 4: Build with PyInstaller
    if not run_pyinstaller():
        input("\nPress Enter to exit...")
        return

    # Step 5: Copy backend folder
    if not copy_backend_folder():
        input("\nPress Enter to exit...")
        return

    # Step 6: Copy additional files
    copy_additional_files()

    # Step 7: Verify
    verify_build()

    # Success message
    print("\n" + "=" * 70)
    print("  BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("  Output location: dist/CoupangWingCS/")
    print()
    print("  FIXED: All FastAPI middleware modules are now included")
    print()
    print("  Next steps:")
    print("  1. Test: Go to dist/CoupangWingCS/ and run CoupangWingCS.exe")
    print("  2. If it works, compress the entire CoupangWingCS folder to ZIP")
    print("  3. Share the ZIP file")
    print()
    print("  REMEMBER: Share the ENTIRE folder, not just the .exe file!")
    print()
    print("=" * 70)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
