# -*- coding: utf-8 -*-
"""
프론트엔드-백엔드 연결 테스트 스크립트
"""
import requests
import time
import sys

def test_backend(port=8001, max_retries=10):
    """백엔드 연결 테스트"""
    print(f"\n[TEST] Testing backend connection on port {port}...")

    for i in range(1, max_retries + 1):
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"[OK] Backend is UP! (attempt {i}/{max_retries})")
                print(f"     Response: {response.json()}")
                return True
        except requests.exceptions.RequestException as e:
            print(f"[WAIT] Attempt {i}/{max_retries} - Backend not ready yet...")
            if i < max_retries:
                time.sleep(2)

    print(f"[FAIL] Backend connection failed after {max_retries} attempts")
    return False

def test_frontend(port=3000, max_retries=10):
    """프론트엔드 연결 테스트"""
    print(f"\n[TEST] Testing frontend connection on port {port}...")

    for i in range(1, max_retries + 1):
        try:
            response = requests.get(f"http://localhost:{port}", timeout=5)
            if response.status_code in [200, 304]:
                print(f"[OK] Frontend is UP! (attempt {i}/{max_retries})")
                return True
        except requests.exceptions.RequestException as e:
            print(f"[WAIT] Attempt {i}/{max_retries} - Frontend not ready yet...")
            if i < max_retries:
                time.sleep(2)

    print(f"[FAIL] Frontend connection failed after {max_retries} attempts")
    return False

def test_api_endpoint(backend_port=8001):
    """백엔드 API 엔드포인트 테스트"""
    print(f"\n[TEST] Testing backend API endpoint...")

    try:
        response = requests.get(f"http://localhost:{backend_port}/api/system/stats", timeout=5)
        if response.status_code == 200:
            print(f"[OK] API endpoint is working!")
            print(f"     Response: {response.json()}")
            return True
        else:
            print(f"[INFO] API returned status code: {response.status_code}")
            return True  # Still connected, just different response
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] API endpoint test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Connection Test - Coupang Wing CS")
    print("=" * 60)

    backend_success = test_backend(8001)
    frontend_success = test_frontend(3000)

    if backend_success:
        api_success = test_api_endpoint(8001)

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    print(f"Backend (port 8001):  {'[OK]' if backend_success else '[FAIL]'}")
    print(f"Frontend (port 3000): {'[OK]' if frontend_success else '[FAIL]'}")
    if backend_success:
        print(f"API Endpoint:         {'[OK]' if api_success else '[FAIL]'}")
    print("=" * 60)

    if backend_success and frontend_success:
        print("\n[SUCCESS] All servers are connected and working!")
        print(f"\nYou can access:")
        print(f"  - Frontend:  http://localhost:3000")
        print(f"  - Backend:   http://localhost:8001")
        print(f"  - API Docs:  http://localhost:8001/docs")
        return True
    else:
        print("\n[FAIL] Some servers are not connected properly")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
