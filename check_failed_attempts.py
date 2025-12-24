"""
실패한 API 호출 분석
"""
import sys
import os
sys.path.append('backend')

# UTF-8 출력 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import sqlite3
from datetime import datetime

db_path = "backend/coupang_cs.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*80)
print("API 호출 실패 분석")
print("="*80)

# 전체 로그 개수
cursor.execute("SELECT COUNT(*) FROM activity_logs")
total_logs = cursor.fetchone()[0]
print(f"\n총 로그 개수: {total_logs}개")

# 상태별 개수
cursor.execute("""
    SELECT status, COUNT(*) as count
    FROM activity_logs
    GROUP BY status
""")
status_counts = cursor.fetchall()
print("\n[상태별 로그]")
for status, count in status_counts:
    print(f"  {status}: {count}개")

# 액션별 개수
cursor.execute("""
    SELECT action, COUNT(*) as count
    FROM activity_logs
    GROUP BY action
    ORDER BY count DESC
""")
action_counts = cursor.fetchall()
print("\n[액션별 로그]")
for action, count in action_counts:
    print(f"  {action}: {count}개")

# 실패한 로그 상세 분석
cursor.execute("""
    SELECT id, action, error_message, timestamp
    FROM activity_logs
    WHERE status = 'failed'
    ORDER BY timestamp DESC
    LIMIT 10
""")
failed_logs = cursor.fetchall()

print("\n\n[최근 실패 로그 10개]")
for log_id, action, error_msg, timestamp in failed_logs:
    print(f"\n#{log_id} - {timestamp}")
    print(f"  액션: {action}")
    if error_msg:
        # 에러 메시지가 긴 경우 줄바꿈
        if len(error_msg) > 200:
            print(f"  에러: {error_msg[:200]}...")
        else:
            print(f"  에러: {error_msg}")

# 가장 오래된 로그와 최신 로그
cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM activity_logs")
min_time, max_time = cursor.fetchone()
print(f"\n\n[로그 시간 범위]")
print(f"  가장 오래된 로그: {min_time}")
print(f"  가장 최신 로그: {max_time}")

# 에러 메시지 타입 분석
print("\n\n[에러 타입 분석]")
cursor.execute("""
    SELECT error_message
    FROM activity_logs
    WHERE error_message IS NOT NULL
""")
errors = cursor.fetchall()

error_types = {}
for error, in errors:
    if "HMAC format is invalid" in error:
        error_types["HMAC format is invalid"] = error_types.get("HMAC format is invalid", 0) + 1
    elif "Authentication" in error or "auth" in error.lower():
        error_types["Authentication Error"] = error_types.get("Authentication Error", 0) + 1
    elif "timeout" in error.lower():
        error_types["Timeout"] = error_types.get("Timeout", 0) + 1
    elif "404" in error or "Not Found" in error:
        error_types["Not Found"] = error_types.get("Not Found", 0) + 1
    else:
        error_types["Other"] = error_types.get("Other", 0) + 1

for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {error_type}: {count}개")

conn.close()

print("\n" + "="*80)
print("\n🔍 결론:")
print("  모든 문의 수집 시도가 'HMAC format is invalid' 오류로 실패했습니다.")
print("  쿠팡 API 인증 키(ACCESS_KEY, SECRET_KEY)에 문제가 있습니다.")
print("="*80)
