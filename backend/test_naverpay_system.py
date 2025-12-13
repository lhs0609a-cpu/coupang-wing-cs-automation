"""
네이버페이 기반 반품 시스템 테스트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models.return_log import ReturnLog
from app.services.naver_pay_automation import NaverPayAutomation
from loguru import logger
from sqlalchemy import text


def test_db_migration():
    """DB 마이그레이션 확인"""
    logger.info("=" * 60)
    logger.info("1. DB 마이그레이션 테스트")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        # 테이블 구조 확인
        result = db.execute(text("PRAGMA table_info(return_logs)")).fetchall()

        columns = {row[1]: row[2] for row in result}

        if "receiver_name" in columns:
            logger.success("✓ receiver_name 컬럼 존재")
        else:
            logger.error("✗ receiver_name 컬럼 없음")
            return False

        if "receiver_phone" in columns:
            logger.success("✓ receiver_phone 컬럼 존재")
        else:
            logger.error("✗ receiver_phone 컬럼 없음")
            return False

        logger.info("\n전체 컬럼 목록:")
        for col_name, col_type in columns.items():
            logger.info(f"  - {col_name}: {col_type}")

        return True

    finally:
        db.close()


def test_sample_data():
    """샘플 데이터 생성 및 조회"""
    logger.info("\n" + "=" * 60)
    logger.info("2. 샘플 데이터 테스트")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        # 기존 테스트 데이터 삭제
        db.query(ReturnLog).filter(
            ReturnLog.coupang_receipt_id >= 999990
        ).delete()
        db.commit()

        # 샘플 데이터 생성
        sample_returns = [
            {
                "coupang_receipt_id": 999991,
                "coupang_order_id": "TEST-ORDER-001",
                "product_name": "갤럭시 S24 투명 케이스",
                "receiver_name": "홍길동",
                "receiver_phone": "010-1234-5678",
                "receipt_type": "RETURN",
                "receipt_status": "RETURNS_UNCHECKED",
                "status": "pending",
            },
            {
                "coupang_receipt_id": 999992,
                "coupang_order_id": "TEST-ORDER-002",
                "product_name": "에어팟 프로 2세대",
                "receiver_name": "김철수",
                "receiver_phone": "010-9876-5432",
                "receipt_type": "RETURN",
                "receipt_status": "RETURNS_UNCHECKED",
                "status": "pending",
            },
            {
                "coupang_receipt_id": 999993,
                "coupang_order_id": "TEST-ORDER-003",
                "product_name": "아이폰 15 프로 케이스",
                "receiver_name": "이영희",
                "receiver_phone": "010-5555-6666",
                "receipt_type": "RETURN",
                "receipt_status": "RETURNS_UNCHECKED",
                "status": "pending",
            },
        ]

        for data in sample_returns:
            return_log = ReturnLog(**data)
            db.add(return_log)

        db.commit()
        logger.success(f"✓ {len(sample_returns)}건의 샘플 데이터 생성 완료")

        # 조회 테스트
        results = db.query(ReturnLog).filter(
            ReturnLog.coupang_receipt_id >= 999990
        ).all()

        logger.info("\n생성된 샘플 데이터:")
        for r in results:
            logger.info(f"  {r.id}. {r.product_name}")
            logger.info(f"     수령인: {r.receiver_name}")
            logger.info(f"     전화: {r.receiver_phone}")
            logger.info(f"     상태: {r.status}")
            logger.info("")

        return True

    except Exception as e:
        logger.error(f"✗ 샘플 데이터 생성 실패: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def test_naverpay_automation_structure():
    """네이버페이 자동화 클래스 구조 테스트"""
    logger.info("=" * 60)
    logger.info("3. 네이버페이 자동화 클래스 테스트")
    logger.info("=" * 60)

    try:
        # 인스턴스 생성
        automation = NaverPayAutomation(headless=True, timeout=30)
        logger.success("✓ NaverPayAutomation 인스턴스 생성 성공")

        # 메서드 확인
        required_methods = [
            'setup_driver',
            'login',
            'navigate_to_payment_history',
            'search_order',
            'process_return',
            'process_return_batch',
            'close',
        ]

        for method in required_methods:
            if hasattr(automation, method):
                logger.success(f"✓ {method} 메서드 존재")
            else:
                logger.error(f"✗ {method} 메서드 없음")
                return False

        logger.info("\n네이버페이 자동화 설정:")
        logger.info(f"  - headless: {automation.headless}")
        logger.info(f"  - timeout: {automation.timeout}")

        return True

    except Exception as e:
        logger.error(f"✗ 자동화 클래스 테스트 실패: {str(e)}")
        return False


def test_api_integration():
    """API 통합 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("4. API 통합 테스트")
    logger.info("=" * 60)

    try:
        from app.routers.return_management import router
        from app.services.auto_return_collector import AutoReturnCollector
        from app.services.auto_return_processor import AutoReturnProcessor

        logger.success("✓ 모든 모듈 import 성공")

        # AutoReturnCollector 테스트
        db = SessionLocal()
        try:
            collector = AutoReturnCollector(db)
            logger.success("✓ AutoReturnCollector 인스턴스 생성 성공")

            # get_pending_returns 테스트
            pending = collector.get_pending_returns(limit=10)
            logger.success(f"✓ get_pending_returns 실행 성공 ({len(pending)}건)")

            if pending:
                logger.info("\n대기 중인 반품 (상위 3건):")
                for r in pending[:3]:
                    logger.info(f"  - {r.product_name}")
                    logger.info(f"    수령인: {r.receiver_name or 'N/A'}")

            # AutoReturnProcessor 테스트
            processor = AutoReturnProcessor(db)
            logger.success("✓ AutoReturnProcessor 인스턴스 생성 성공")

            # 통계 조회
            stats = processor.get_processing_statistics()
            logger.success("✓ 통계 조회 성공")
            logger.info(f"  - 전체: {stats['total']}건")
            logger.info(f"  - 대기: {stats['pending']}건")

        finally:
            db.close()

        return True

    except Exception as e:
        logger.error(f"✗ API 통합 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def print_coupang_api_guide():
    """쿠팡 API 응답 확인 가이드"""
    logger.info("\n" + "=" * 60)
    logger.info("5. 쿠팡 API 응답 구조 확인 가이드")
    logger.info("=" * 60)

    guide = """
실제 쿠팡 API를 호출하여 수령인 정보 필드를 확인해야 합니다.

방법 1: Swagger UI 사용
-----------------------
1. http://localhost:8000/docs 접속
2. GET /returns/fetch-from-coupang 실행
3. 응답의 raw_data 필드 확인

방법 2: 직접 DB 조회
-----------------------
cd backend
../venv/Scripts/python.exe -c "
from app.database import SessionLocal
from app.models.return_log import ReturnLog
import json

db = SessionLocal()
log = db.query(ReturnLog).first()
if log and log.raw_data:
    print(json.dumps(log.raw_data, indent=2, ensure_ascii=False))
db.close()
"

확인해야 할 필드:
-----------------
✓ shippingTo.name
✓ shippingTo.phoneNumber
✓ receiverInfo.receiverName
✓ receiverInfo.receiverPhone
✓ returnItems[].receiverName
✓ returnItems[].receiverPhone

만약 다른 필드명이면:
-----------------------
backend/app/services/auto_return_collector.py 수정
→ _create_return_log() 메서드의 수령인 정보 추출 로직
"""

    logger.info(guide)


def print_naverpay_html_guide():
    """네이버페이 HTML 구조 확인 가이드"""
    logger.info("\n" + "=" * 60)
    logger.info("6. 네이버페이 HTML 구조 확인 가이드")
    logger.info("=" * 60)

    guide = """
실제 네이버페이 페이지에서 HTML 구조를 확인해야 합니다.

확인 절차:
----------
1. https://pay.naver.com/pc/history?page=1 접속
2. F12 (개발자 도구) 열기
3. Elements 탭에서 주문 항목 확인
4. 다음 요소들의 클래스명/속성 확인:

필수 확인 요소:
--------------
□ 주문 항목 컨테이너 (현재: .history_item)
□ 상품명 (현재: .product_name)
□ 수령인 이름 (현재: .receiver_name)
□ 반품 버튼 (현재: button[contains(text(), '반품')])
□ 반품 사유 선택 (현재: select[name='returnReason'])
□ 반품 신청 버튼 (현재: button[contains(text(), '신청')])

만약 클래스명이 다르면:
-----------------------
backend/app/services/naver_pay_automation.py 수정
→ search_order() 메서드의 선택자
→ process_return() 메서드의 선택자

예시 코드 위치:
--------------
# 상품명 추출
product_elem = item.find_element(By.CLASS_NAME, "product_name")  ← 여기 수정

# 수령인 추출
receiver_elem = item.find_element(By.CLASS_NAME, "receiver_name")  ← 여기 수정

# 반품 버튼
return_button = item.find_element(By.XPATH, ".//button[contains(text(), '반품')]")  ← 여기 수정
"""

    logger.info(guide)


def main():
    """전체 테스트 실행"""
    logger.info("\n" + "=" * 80)
    logger.info("네이버페이 기반 반품 자동 처리 시스템 테스트")
    logger.info("=" * 80 + "\n")

    results = []

    # 1. DB 마이그레이션
    results.append(("DB 마이그레이션", test_db_migration()))

    # 2. 샘플 데이터
    results.append(("샘플 데이터", test_sample_data()))

    # 3. 네이버페이 자동화
    results.append(("네이버페이 자동화", test_naverpay_automation_structure()))

    # 4. API 통합
    results.append(("API 통합", test_api_integration()))

    # 가이드 출력
    print_coupang_api_guide()
    print_naverpay_html_guide()

    # 결과 요약
    logger.info("\n" + "=" * 80)
    logger.info("테스트 결과 요약")
    logger.info("=" * 80)

    for name, result in results:
        status = "✓ 통과" if result else "✗ 실패"
        logger.info(f"{name:20s}: {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    logger.info(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")

    if passed == total:
        logger.success("\n모든 테스트 통과! 시스템이 정상 작동합니다.")
        logger.info("\n다음 단계:")
        logger.info("1. 쿠팡 계정 등록 및 실제 반품 조회")
        logger.info("2. 쿠팡 API 응답에서 수령인 필드명 확인")
        logger.info("3. 네이버페이 HTML 구조 확인")
        logger.info("4. 테스트 데이터로 실제 반품 처리 시뮬레이션")
    else:
        logger.warning("\n일부 테스트 실패. 위 오류를 확인하세요.")


if __name__ == "__main__":
    main()
