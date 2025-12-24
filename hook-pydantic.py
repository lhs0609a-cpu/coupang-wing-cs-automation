"""
PyInstaller runtime hook for Pydantic v2
Fixes the "unable to infer type for attribute" error
"""
import os
import sys

# Pydantic v2 환경 변수 설정
os.environ['PYDANTIC_V2'] = '1'
os.environ['PYDANTIC_SKIP_VALIDATING_CORE_SCHEMAS'] = '1'

# FastAPI와 Pydantic 호환성 설정
try:
    import pydantic
    # Pydantic v2 버전 확인
    if hasattr(pydantic, '__version__'):
        version = pydantic.__version__
        if version.startswith('2'):
            # Pydantic v2 설정
            os.environ['PYDANTIC_USE_DEPRECATED_JSON_ERRORS'] = '0'
except ImportError:
    pass
