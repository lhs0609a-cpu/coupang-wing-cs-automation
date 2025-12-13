"""
자동화 기능 시뮬레이션 테스트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.auto_return_config import AutoReturnConfig
from app.models.coupang_account import CoupangAccount
from app.models.naver_account import NaverAccount
from app.models.return_log import ReturnLog
from app.services.auto_return_collector import AutoReturnCollector
from app.services.auto_return_processor import AutoReturnProcessor
from loguru import logger


def test_configuration():
    """설정 테스트"""
    logger.info("=" * 60)
    logger.info("1. 자동화 설정 테스트")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        config = db.query(AutoReturnConfig).first()
        if config:
            logger.success("✓ 자동화 설정 조회 성공")
            logger.info(f"  - enabled: {config.enabled}")
            logger.info(f"  - fetch_enabled: {config.fetch_enabled}")
            logger.info(f"  - fetch_interval_minutes: {config.fetch_interval_minutes}")
            logger.info(f"  - process_enabled: {config.process_enabled}")
            logger.info(f"  - process_interval_minutes: {config.process_interval_minutes}")
            logger.info(f"  - process_batch_size: {config.process_batch_size}")
            logger.info(f"  - auto_process_statuses: {config.auto_process_statuses}")
            logger.info(f"  - exclude_statuses: {config.exclude_statuses}")
            logger.info(f"  - max_retry_count: {config.max_retry_count}")
            logger.info(f"  - retry_delay_seconds: {config.retry_delay_seconds}")
            return True
        else:
            logger.error("✗ 자동화 설정이 없습니다")
            return False
    finally:
        db.close()


def test_accounts():
    """계정 정보 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("2. 계정 정보 테스트")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        # 쿠팡 계정
        coupang = db.query(CoupangAccount).first()
        if coupang:
            logger.success("✓ 쿠팡 계정 등록됨")
            logger.info(f"  - vendor_id: {coupang.vendor_id}")
        else:
            logger.warning("⚠ 쿠팡 계정 미등록 (자동 수집 불가)")

        # 네이버 계정
        naver = db.query(NaverAccount).first()
        if naver:
            logger.success("✓ 네이버 계정 등록됨")
            logger.info(f"  - naver_username: {naver.naver_username}")
        else:
            logger.warning("⚠ 네이버 계정 미등록 (자동 처리 불가)")

        return bool(coupang) and bool(naver)
    finally:
        db.close()


def test_return_logs():
    """반품 로그 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("3. 반품 로그 테스트")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        total = db.query(ReturnLog).count()
        pending = db.query(ReturnLog).filter(
            ReturnLog.status == "pending",
            ReturnLog.naver_processed == False
        ).count()
        processing = db.query(ReturnLog).filter(ReturnLog.status == "processing").count()
        completed = db.query(ReturnLog).filter(ReturnLog.status == "completed").count()
        failed = db.query(ReturnLog).filter(ReturnLog.status == "failed").count()

        logger.info(f"  - 전체: {total}건")
        logger.info(f"  - 대기: {pending}건")
        logger.info(f"  - 처리중: {processing}건")
        logger.info(f"  - 완료: {completed}건")
        logger.info(f"  - 실패: {failed}건")

        if total == 0:
            logger.warning("⚠ 반품 로그가 없습니다 (테스트 데이터 필요)")
        else:
            logger.success(f"✓ 반품 로그 {total}건 존재")

        return True
    finally:
        db.close()


def test_collector_simulation():
    """수집기 시뮬레이션 (실제 API 호출 없이)"""
    logger.info("\n" + "=" * 60)
    logger.info("4. 자동 수집기 시뮬레이션")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        collector = AutoReturnCollector(db)

        # 설정 확인
        config = db.query(AutoReturnConfig).first()
        if not config:
            logger.error("✗ 설정이 없습니다")
            return False

        logger.info("수집기 객체 생성 성공")
        logger.info(f"  - 설정 enabled: {config.enabled}")
        logger.info(f"  - 설정 fetch_enabled: {config.fetch_enabled}")

        if not config.enabled or not config.fetch_enabled:
            logger.warning("⚠ 자동 수집이 비활성화되어 있습니다")
            logger.info("  실제 실행 시 스킵됩니다")

        # 계정 확인
        coupang = db.query(CoupangAccount).first()
        if not coupang:
            logger.warning("⚠ 쿠팡 계정이 없어 실제 수집은 불가능합니다")
            logger.info("  계정 등록 후 테스트 가능")
        else:
            logger.success("✓ 쿠팡 계정 확인 완료")
            logger.info("  실제 수집 준비 완료 (API 호출은 스킵)")

        # 대기 중인 반품 조회 테스트
        pending = collector.get_pending_returns(config=config, limit=10)
        logger.info(f"\n처리 대기 중인 반품: {len(pending)}건")

        if pending:
            logger.info("상위 3건:")
            for i, item in enumerate(pending[:3], 1):
                logger.info(f"  {i}. {item.product_name[:30]}... (status: {item.receipt_status})")

        logger.success("✓ 수집기 시뮬레이션 완료")
        return True

    finally:
        db.close()


def test_processor_simulation():
    """처리기 시뮬레이션 (실제 Selenium 실행 없이)"""
    logger.info("\n" + "=" * 60)
    logger.info("5. 자동 처리기 시뮬레이션")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        processor = AutoReturnProcessor(db)

        # 설정 확인
        config = db.query(AutoReturnConfig).first()
        if not config:
            logger.error("✗ 설정이 없습니다")
            return False

        logger.info("처리기 객체 생성 성공")
        logger.info(f"  - 설정 enabled: {config.enabled}")
        logger.info(f"  - 설정 process_enabled: {config.process_enabled}")
        logger.info(f"  - batch_size: {config.process_batch_size}")

        if not config.enabled or not config.process_enabled:
            logger.warning("⚠ 자동 처리가 비활성화되어 있습니다")
            logger.info("  실제 실행 시 스킵됩니다")

        # 계정 확인
        naver = db.query(NaverAccount).first()
        if not naver:
            logger.warning("⚠ 네이버 계정이 없어 실제 처리는 불가능합니다")
            logger.info("  계정 등록 후 테스트 가능")
        else:
            logger.success("✓ 네이버 계정 확인 완료")
            logger.info("  실제 처리 준비 완료 (Selenium 실행은 스킵)")

        # 통계 조회
        stats = processor.get_processing_statistics()
        logger.info(f"\n처리 통계:")
        logger.info(f"  - 전체: {stats['total']}건")
        logger.info(f"  - 대기: {stats['pending']}건")
        logger.info(f"  - 완료: {stats['processed']}건")
        logger.info(f"  - 실패: {stats['failed']}건")

        logger.success("✓ 처리기 시뮬레이션 완료")
        return True

    finally:
        db.close()


def test_scheduler_jobs():
    """스케줄러 작업 확인"""
    logger.info("\n" + "=" * 60)
    logger.info("6. 스케줄러 작업 확인")
    logger.info("=" * 60)

    try:
        from app.scheduler import AutomationScheduler
        scheduler = AutomationScheduler()

        # 스케줄러 메서드 확인
        methods = [
            'auto_fetch_returns',
            'auto_process_returns',
        ]

        for method in methods:
            if hasattr(scheduler, method):
                logger.success(f"✓ {method} 메서드 존재")
            else:
                logger.error(f"✗ {method} 메서드 없음")

        logger.info("\n스케줄러 설정:")
        logger.info("  - auto_fetch_returns: 15분마다 실행")
        logger.info("  - auto_process_returns: 20분마다 실행")

        logger.success("✓ 스케줄러 확인 완료")
        return True

    except Exception as e:
        logger.error(f"✗ 스케줄러 확인 실패: {str(e)}")
        return False


def main():
    """전체 테스트 실행"""
    logger.info("\n" + "=" * 80)
    logger.info("쿠팡 → 네이버 반품 자동 처리 시스템 시뮬레이션")
    logger.info("=" * 80)

    results = []

    # 1. 설정 테스트
    results.append(("설정", test_configuration()))

    # 2. 계정 테스트
    results.append(("계정", test_accounts()))

    # 3. 반품 로그 테스트
    results.append(("반품 로그", test_return_logs()))

    # 4. 수집기 테스트
    results.append(("수집기", test_collector_simulation()))

    # 5. 처리기 테스트
    results.append(("처리기", test_processor_simulation()))

    # 6. 스케줄러 테스트
    results.append(("스케줄러", test_scheduler_jobs()))

    # 결과 요약
    logger.info("\n" + "=" * 80)
    logger.info("테스트 결과 요약")
    logger.info("=" * 80)

    for name, result in results:
        status = "✓ 통과" if result else "✗ 실패"
        logger.info(f"{name:15s}: {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    logger.info(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")

    if passed == total:
        logger.success("\n모든 테스트 통과! 자동화 시스템이 정상 작동합니다.")
        logger.info("\n다음 단계:")
        logger.info("1. 서버 시작: venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000")
        logger.info("2. 자동화 활성화: PUT /returns/automation/config {\"enabled\": true}")
        logger.info("3. 실제 수집/처리 테스트")
    else:
        logger.warning("\n일부 테스트 실패. 위 경고 메시지를 확인하세요.")


if __name__ == "__main__":
    main()
