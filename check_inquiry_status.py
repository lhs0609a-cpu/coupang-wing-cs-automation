"""
문의 상태 확인 스크립트
데이터베이스에서 미처리 문의를 분석합니다.
"""
import sys
import os
sys.path.append('backend')

# UTF-8 출력 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger
import json

# 데이터베이스 연결
DATABASE_URL = "sqlite:///backend/coupang_cs.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def analyze_inquiries():
    """문의 상태 분석"""
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("문의 상태 분석 리포트")
        print("="*80 + "\n")

        # 1. 전체 통계
        print("📊 [전체 통계]")
        total_count = db.execute(text("SELECT COUNT(*) FROM inquiries")).scalar()
        print(f"   총 문의 개수: {total_count}")

        # 상태별 개수
        status_counts = db.execute(text("""
            SELECT status, COUNT(*) as count
            FROM inquiries
            GROUP BY status
        """)).fetchall()

        print("\n   상태별 분류:")
        for status, count in status_counts:
            print(f"   - {status}: {count}개")

        # 2. 미처리 문의 (pending, processing)
        print("\n\n🔍 [미처리 문의 분석]")
        pending_inquiries = db.execute(text("""
            SELECT
                id,
                coupang_inquiry_id,
                inquiry_text,
                inquiry_date,
                created_at,
                status,
                requires_human,
                is_urgent
            FROM inquiries
            WHERE status IN ('pending', 'processing')
            ORDER BY inquiry_date ASC
        """)).fetchall()

        print(f"   미처리 문의 총 {len(pending_inquiries)}개\n")

        if pending_inquiries:
            # 시간 경과 분석
            now = datetime.utcnow()

            old_inquiries = []  # 24시간 이상 지난 문의
            urgent_inquiries = []  # 긴급 문의

            for inq in pending_inquiries:
                inq_id, coupang_id, text_content, inq_date, created, status, req_human, is_urgent = inq

                # inquiry_date 파싱
                try:
                    if isinstance(inq_date, str):
                        inq_datetime = datetime.fromisoformat(inq_date.replace('Z', '+00:00'))
                    else:
                        inq_datetime = inq_date
                except:
                    inq_datetime = datetime.fromisoformat(created.replace('Z', '+00:00'))

                time_diff = now - inq_datetime
                hours_old = time_diff.total_seconds() / 3600

                if hours_old > 24:
                    old_inquiries.append({
                        'id': inq_id,
                        'coupang_id': coupang_id,
                        'hours_old': hours_old,
                        'status': status,
                        'requires_human': req_human,
                        'is_urgent': is_urgent,
                        'text': text_content[:100] if text_content else ""
                    })

                if is_urgent:
                    urgent_inquiries.append({
                        'id': inq_id,
                        'coupang_id': coupang_id,
                        'hours_old': hours_old,
                        'status': status
                    })

            # 24시간 이상 지난 문의
            print(f"   ⏰ 24시간 이상 경과: {len(old_inquiries)}개")
            if old_inquiries:
                print("\n   [시간 지난 문의 목록]")
                for idx, inq in enumerate(old_inquiries[:10], 1):
                    days = int(inq['hours_old'] // 24)
                    hours = int(inq['hours_old'] % 24)
                    print(f"   {idx}. ID: {inq['id']} (쿠팡ID: {inq['coupang_id']})")
                    print(f"      경과시간: {days}일 {hours}시간")
                    print(f"      상태: {inq['status']}")
                    print(f"      사람검토필요: {inq['requires_human']}")
                    print(f"      긴급: {inq['is_urgent']}")
                    print(f"      내용: {inq['text']}")
                    print()

                if len(old_inquiries) > 10:
                    print(f"   ... 외 {len(old_inquiries) - 10}개 더 있음\n")

            # 긴급 문의
            print(f"\n   🚨 긴급 문의: {len(urgent_inquiries)}개")

            # 사람 검토 필요
            human_review = db.execute(text("""
                SELECT COUNT(*)
                FROM inquiries
                WHERE requires_human = 1 AND status NOT IN ('processed', 'failed')
            """)).scalar()
            print(f"   👤 사람 검토 필요: {human_review}개")

        # 3. API 호출 로그 확인
        print("\n\n📡 [API 호출 이력]")
        recent_collection = db.execute(text("""
            SELECT
                action,
                created_at,
                status,
                error_message
            FROM activity_logs
            WHERE action = 'inquiry_collected'
            ORDER BY created_at DESC
            LIMIT 5
        """)).fetchall()

        if recent_collection:
            print("   최근 수집 이력:")
            for action, created, status, error in recent_collection:
                print(f"   - {created}: {status}")
                if error:
                    print(f"     에러: {error}")
        else:
            print("   ⚠️  수집 이력이 없습니다!")

        # 4. 실패한 문의
        print("\n\n❌ [처리 실패 문의]")
        failed_count = db.execute(text("""
            SELECT COUNT(*)
            FROM inquiries
            WHERE status = 'failed'
        """)).scalar()
        print(f"   실패한 문의: {failed_count}개")

        if failed_count > 0:
            failed_inquiries = db.execute(text("""
                SELECT
                    id,
                    coupang_inquiry_id,
                    inquiry_date,
                    inquiry_text
                FROM inquiries
                WHERE status = 'failed'
                ORDER BY inquiry_date DESC
                LIMIT 5
            """)).fetchall()

            print("\n   최근 실패 문의:")
            for inq_id, coupang_id, inq_date, text_content in failed_inquiries:
                print(f"   - ID: {inq_id} (쿠팡ID: {coupang_id})")
                print(f"     날짜: {inq_date}")
                print(f"     내용: {text_content[:80] if text_content else '없음'}...")
                print()

        # 5. Response 테이블 확인
        print("\n📝 [응답 생성 상태]")
        response_stats = db.execute(text("""
            SELECT
                status,
                COUNT(*) as count
            FROM responses
            GROUP BY status
        """)).fetchall()

        if response_stats:
            print("   응답 상태별 개수:")
            for status, count in response_stats:
                print(f"   - {status}: {count}개")
        else:
            print("   ⚠️  생성된 응답이 없습니다!")

        # 6. 스케줄러 작동 확인
        print("\n\n⚙️  [자동화 시스템 체크]")
        last_auto_collect = db.execute(text("""
            SELECT created_at
            FROM activity_logs
            WHERE action LIKE '%collect%'
            ORDER BY created_at DESC
            LIMIT 1
        """)).scalar()

        if last_auto_collect:
            last_time = datetime.fromisoformat(last_auto_collect.replace('Z', '+00:00'))
            time_since = datetime.utcnow() - last_time
            print(f"   마지막 자동 수집: {last_auto_collect}")
            print(f"   경과 시간: {int(time_since.total_seconds() / 60)}분 전")

            if time_since.total_seconds() > 1800:  # 30분 이상
                print("   ⚠️  경고: 30분 이상 수집이 없습니다!")
        else:
            print("   ⚠️  경고: 자동 수집 이력이 없습니다!")

        print("\n" + "="*80)

    except Exception as e:
        logger.error(f"분석 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    analyze_inquiries()
