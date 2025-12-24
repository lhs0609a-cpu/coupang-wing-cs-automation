#!/usr/bin/env python3
"""
수정된 파일들을 OneDrive 바탕화면 폴더로 복사
"""

import shutil
from pathlib import Path

# 소스와 대상 경로
source_dir = Path(r"C:\Users\u\coupang-wing-cs-automation")
target_dir = Path(r"C:\Users\u\OneDrive\바탕 화면\마케팅 프로그램\CoupangWingCS_Final_v1.0.0")

# 복사할 파일 목록
files_to_copy = [
    "launcher.py",
    "build_executable.py",
    "BUILD_EXECUTABLE.bat",
]

print("=" * 60)
print("파일 복사 중...")
print("=" * 60)
print()

# 대상 폴더 확인
if not target_dir.exists():
    print(f"❌ 대상 폴더가 없습니다: {target_dir}")
    print("\n폴더를 생성하시겠습니까? (y/n): ", end="")
    response = input().strip().lower()
    if response == 'y':
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 폴더 생성: {target_dir}")
    else:
        print("취소되었습니다.")
        exit(1)

# 파일 복사
for filename in files_to_copy:
    source_file = source_dir / filename
    target_file = target_dir / filename

    if source_file.exists():
        try:
            shutil.copy2(source_file, target_file)
            print(f"✅ 복사 완료: {filename}")
        except Exception as e:
            print(f"❌ 복사 실패: {filename} - {e}")
    else:
        print(f"⚠️  파일 없음: {filename}")

print()
print("=" * 60)
print("복사 완료!")
print(f"대상 폴더: {target_dir}")
print()
print("다음 단계:")
print("1. 대상 폴더로 이동")
print("2. BUILD_EXECUTABLE.bat 실행")
print("=" * 60)
