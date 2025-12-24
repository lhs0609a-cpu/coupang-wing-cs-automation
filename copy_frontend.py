#!/usr/bin/env python3
"""프론트엔드 빌드 파일을 백엔드로 복사"""
import shutil
import os
from pathlib import Path

# 경로 설정
frontend_dist = Path('frontend/dist')
backend_static = Path('backend/static')

# 기존 static 폴더 제거
if backend_static.exists():
    print(f"기존 static 폴더 제거 중: {backend_static}")
    shutil.rmtree(backend_static)

# 새로운 빌드 파일 복사
print(f"프론트엔드 빌드 파일 복사 중: {frontend_dist} -> {backend_static}")
shutil.copytree(frontend_dist, backend_static)

# 복사된 파일 확인
file_count = len(list(backend_static.rglob('*')))
print(f"✓ 복사 완료! ({file_count}개 파일)")
print(f"  위치: {backend_static.absolute()}")
