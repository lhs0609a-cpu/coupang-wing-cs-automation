"""
Automated Scheduler Service
Runs background tasks on schedule
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from loguru import logger
from typing import Optional

from .database import SessionLocal
from .services.auto_workflow import AutoWorkflow
from .services.inquiry_collector import InquiryCollector
from .services.auto_return_collector import AutoReturnCollector
from .services.auto_return_processor import AutoReturnProcessor
from .services.coupon_auto_sync_service import CouponAutoSyncService
from .config import settings


class AutomationScheduler:
    """
    Manages scheduled automation tasks
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        logger.info("Starting automation scheduler...")

        # Task 1: Auto-collect inquiries every 30 minutes
        self.scheduler.add_job(
            func=self.auto_collect_inquiries,
            trigger=IntervalTrigger(minutes=30),
            id='auto_collect',
            name='Auto Collect Inquiries',
            replace_existing=True
        )

        # Task 2: Auto-process inquiries every 15 minutes
        self.scheduler.add_job(
            func=self.auto_process_inquiries,
            trigger=IntervalTrigger(minutes=15),
            id='auto_process',
            name='Auto Process Inquiries',
            replace_existing=True
        )

        # Task 3: Morning report at 9 AM
        self.scheduler.add_job(
            func=self.send_morning_report,
            trigger=CronTrigger(hour=9, minute=0),
            id='morning_report',
            name='Daily Morning Report',
            replace_existing=True
        )

        # Task 4: Evening report at 6 PM
        self.scheduler.add_job(
            func=self.send_evening_report,
            trigger=CronTrigger(hour=18, minute=0),
            id='evening_report',
            name='Daily Evening Report',
            replace_existing=True
        )

        # Task 5: Process pending approvals every hour
        self.scheduler.add_job(
            func=self.process_pending_approvals,
            trigger=IntervalTrigger(hours=1),
            id='pending_approvals',
            name='Process Pending Approvals',
            replace_existing=True
        )

        # Task 6: Cleanup old logs daily at midnight
        self.scheduler.add_job(
            func=self.cleanup_old_logs,
            trigger=CronTrigger(hour=0, minute=0),
            id='cleanup_logs',
            name='Cleanup Old Logs',
            replace_existing=True
        )

        # Task 7: Auto-fetch Coupang returns every 15 minutes
        self.scheduler.add_job(
            func=self.auto_fetch_returns,
            trigger=IntervalTrigger(minutes=15),
            id='auto_fetch_returns',
            name='Auto Fetch Coupang Returns',
            replace_existing=True
        )

        # Task 8: Auto-process Naver returns every 20 minutes
        self.scheduler.add_job(
            func=self.auto_process_returns,
            trigger=IntervalTrigger(minutes=20),
            id='auto_process_returns',
            name='Auto Process Naver Returns',
            replace_existing=True
        )

        # Task 9: Auto-apply coupons to new products every hour
        self.scheduler.add_job(
            func=self.auto_apply_coupons,
            trigger=IntervalTrigger(hours=1),
            id='auto_apply_coupons',
            name='Auto Apply Coupons to New Products',
            replace_existing=True
        )

        # Task 10: Detect new products for coupon tracking every 6 hours
        self.scheduler.add_job(
            func=self.auto_detect_new_products,
            trigger=IntervalTrigger(hours=6),
            id='auto_detect_products',
            name='Auto Detect New Products for Coupon',
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True
        logger.success("Scheduler started successfully")

    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return

        logger.info("Stopping scheduler...")
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")

    def auto_collect_inquiries(self):
        """
        Automatically collect new inquiries from Coupang Wing
        """
        logger.info("Starting scheduled inquiry collection...")
        db = SessionLocal()
        try:
            collector = InquiryCollector(db)
            inquiries = collector.collect_new_inquiries()
            logger.success(f"Collected {len(inquiries)} new inquiries")
        except Exception as e:
            logger.error(f"Error in auto_collect_inquiries: {str(e)}")
        finally:
            db.close()

    def auto_process_inquiries(self):
        """
        Automatically process inquiries and submit safe responses
        """
        logger.info("Starting scheduled inquiry processing...")
        db = SessionLocal()
        try:
            workflow = AutoWorkflow(db)
            results = workflow.run_full_auto_workflow(
                limit=20,
                auto_submit=True
            )

            logger.success(
                f"Auto-processing complete: "
                f"Generated: {results['generated']}, "
                f"Auto-approved: {results['auto_approved']}, "
                f"Submitted: {results['submitted']}"
            )

            # Send alert if there are many items requiring human review
            if results['requires_human'] > 5:
                self._send_alert(
                    f"⚠️ {results['requires_human']} inquiries require human review",
                    level="warning"
                )

        except Exception as e:
            logger.error(f"Error in auto_process_inquiries: {str(e)}")
            self._send_alert(f"❌ Auto-processing failed: {str(e)}", level="error")
        finally:
            db.close()

    def process_pending_approvals(self):
        """
        Process pending approvals
        """
        logger.info("Processing pending approvals...")
        db = SessionLocal()
        try:
            workflow = AutoWorkflow(db)
            results = workflow.process_pending_approvals()

            if results['auto_approved'] > 0:
                logger.success(
                    f"Processed {results['processed']} pending responses, "
                    f"auto-approved {results['auto_approved']}, "
                    f"submitted {results['submitted']}"
                )
        except Exception as e:
            logger.error(f"Error processing pending approvals: {str(e)}")
        finally:
            db.close()

    def send_morning_report(self):
        """
        Send morning daily report
        """
        logger.info("Generating morning report...")
        db = SessionLocal()
        try:
            from .services.reporting import ReportingService
            reporting = ReportingService(db)
            report = reporting.generate_daily_report()

            # Send via notification system
            from .services.notification import NotificationService
            notifier = NotificationService()
            notifier.send_daily_report(report, time='morning')

            logger.success("Morning report sent")
        except Exception as e:
            logger.error(f"Error sending morning report: {str(e)}")
        finally:
            db.close()

    def send_evening_report(self):
        """
        Send evening daily report
        """
        logger.info("Generating evening report...")
        db = SessionLocal()
        try:
            from .services.reporting import ReportingService
            reporting = ReportingService(db)
            report = reporting.generate_daily_report()

            # Send via notification system
            from .services.notification import NotificationService
            notifier = NotificationService()
            notifier.send_daily_report(report, time='evening')

            logger.success("Evening report sent")
        except Exception as e:
            logger.error(f"Error sending evening report: {str(e)}")
        finally:
            db.close()

    def cleanup_old_logs(self):
        """
        Clean up old activity logs (older than 90 days)
        """
        logger.info("Cleaning up old logs...")
        db = SessionLocal()
        try:
            from .models import ActivityLog
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=90)
            deleted = db.query(ActivityLog).filter(
                ActivityLog.created_at < cutoff_date
            ).delete()

            db.commit()
            logger.success(f"Cleaned up {deleted} old log entries")
        except Exception as e:
            logger.error(f"Error cleaning up logs: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def auto_fetch_returns(self):
        """
        Automatically fetch returns from Coupang API
        """
        logger.info("Starting scheduled return collection...")
        db = SessionLocal()
        try:
            collector = AutoReturnCollector(db)
            result = collector.collect_returns()

            if result['success']:
                logger.success(
                    f"Collected {result['total_fetched']} returns "
                    f"(New: {result['saved']}, Updated: {result['updated']})"
                )
            else:
                logger.warning(f"Return collection failed: {result['message']}")

        except Exception as e:
            logger.error(f"Error in auto_fetch_returns: {str(e)}")
            self._send_alert(f"❌ Auto-fetch returns failed: {str(e)}", level="error")
        finally:
            db.close()

    def auto_process_returns(self):
        """
        Automatically process pending returns on Naver SmartStore
        """
        logger.info("Starting scheduled return processing...")
        db = SessionLocal()
        try:
            processor = AutoReturnProcessor(db)
            result = processor.process_pending_returns()

            if result['success']:
                logger.success(
                    f"Processed {result['processed']} returns, "
                    f"Failed: {result['failed']}"
                )

                # Send alert if there are many failures
                if result['failed'] > 5:
                    self._send_alert(
                        f"⚠️ {result['failed']} returns failed to process",
                        level="warning"
                    )
            else:
                logger.warning(f"Return processing skipped: {result['message']}")

        except Exception as e:
            logger.error(f"Error in auto_process_returns: {str(e)}")
            self._send_alert(f"❌ Auto-process returns failed: {str(e)}", level="error")
        finally:
            db.close()

    def auto_apply_coupons(self):
        """
        Automatically apply coupons to products that are ready (past apply delay)
        """
        logger.info("Starting scheduled coupon application...")
        db = SessionLocal()
        try:
            service = CouponAutoSyncService(db)
            service.run_auto_sync_all_accounts()
            logger.success("Coupon auto-sync completed for all enabled accounts")
        except Exception as e:
            logger.error(f"Error in auto_apply_coupons: {str(e)}")
            self._send_alert(f"❌ Auto-apply coupons failed: {str(e)}", level="error")
        finally:
            db.close()

    def auto_detect_new_products(self):
        """
        Detect newly registered products and register them for coupon tracking
        """
        logger.info("Starting scheduled new product detection...")
        db = SessionLocal()
        try:
            from .models import CoupangAccount, CouponAutoSyncConfig

            # Get all enabled coupon configs
            configs = db.query(CouponAutoSyncConfig).filter(
                CouponAutoSyncConfig.is_enabled == True
            ).all()

            total_detected = 0
            total_registered = 0

            for config in configs:
                try:
                    service = CouponAutoSyncService(db)

                    # Detect new products
                    detect_result = service.detect_new_products(config.coupang_account_id)
                    if detect_result.get("success"):
                        new_products = detect_result.get("new_products", [])
                        if new_products:
                            # Register for tracking
                            register_result = service.register_products_for_tracking(
                                config.coupang_account_id,
                                new_products
                            )
                            total_detected += len(new_products)
                            total_registered += register_result.get("registered", 0)

                except Exception as e:
                    logger.error(f"Error detecting products for account {config.coupang_account_id}: {str(e)}")

            logger.success(f"New product detection completed: Detected {total_detected}, Registered {total_registered}")

        except Exception as e:
            logger.error(f"Error in auto_detect_new_products: {str(e)}")
            self._send_alert(f"❌ Auto-detect new products failed: {str(e)}", level="error")
        finally:
            db.close()

    def _send_alert(self, message: str, level: str = "info"):
        """
        Send alert notification
        """
        try:
            from .services.notification import NotificationService
            notifier = NotificationService()
            notifier.send_alert(message, level)
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")

    # ========== NaverPay Delivery Scraping ==========

    def auto_scrape_naverpay(self):
        """
        Automatically scrape NaverPay delivery information
        """
        import asyncio
        logger.info("Starting scheduled NaverPay delivery scraping...")
        db = SessionLocal()
        try:
            from .services.naverpay_scraper import get_scraper
            from .models.delivery import NaverPayDelivery
            from .services.delivery_tracker import normalize_courier_name
            from datetime import date

            async def do_scrape():
                scraper = await get_scraper()

                # 쿠키로 로그인 상태 복원 시도
                if not await scraper.ensure_logged_in():
                    logger.warning("NaverPay: 로그인이 필요합니다. 스케줄 건너뜀.")
                    return {'success': False, 'reason': 'not_logged_in'}

                # 스크래핑 실행
                deliveries = await scraper.scrape_deliveries_sync()

                today = date.today().isoformat()
                saved_count = 0

                for delivery in deliveries:
                    # 중복 체크
                    existing = db.query(NaverPayDelivery).filter(
                        NaverPayDelivery.tracking_number == delivery["tracking_number"],
                        NaverPayDelivery.collected_date == today
                    ).first()

                    if not existing:
                        new_delivery = NaverPayDelivery(
                            recipient=delivery["recipient"],
                            courier=normalize_courier_name(delivery["courier"]),
                            tracking_number=delivery["tracking_number"],
                            product_name=delivery.get("product_name"),
                            order_date=delivery.get("order_date"),
                            collected_date=today
                        )
                        db.add(new_delivery)
                        saved_count += 1

                db.commit()
                return {
                    'success': True,
                    'total_found': len(deliveries),
                    'new_saved': saved_count
                }

            # 비동기 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(do_scrape())
            loop.close()

            if result['success']:
                logger.success(
                    f"NaverPay scraping completed: Found {result['total_found']}, "
                    f"New saved {result['new_saved']}"
                )

                # 실행 이력 저장
                self._save_naverpay_history(result)
            else:
                logger.warning(f"NaverPay scraping skipped: {result.get('reason', 'unknown')}")

        except Exception as e:
            logger.error(f"Error in auto_scrape_naverpay: {str(e)}")
            self._send_alert(f"❌ NaverPay scraping failed: {str(e)}", level="error")
        finally:
            db.close()

    def _save_naverpay_history(self, result: dict):
        """NaverPay 스크래핑 실행 이력 저장"""
        try:
            from .database import SessionLocal
            from .models.delivery import NaverPayScheduleHistory

            db = SessionLocal()
            history = NaverPayScheduleHistory(
                total_found=result.get('total_found', 0),
                new_saved=result.get('new_saved', 0),
                status='success' if result.get('success') else 'failed',
                error_message=result.get('error')
            )
            db.add(history)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to save NaverPay history: {e}")

    # ========== Dynamic Schedule Management ==========

    def add_naverpay_schedule(self, job_id: str, schedule_type: str,
                              interval_minutes: int = None, cron_expression: str = None) -> bool:
        """
        NaverPay 스크래핑 스케줄 동적 추가

        Args:
            job_id: 고유 작업 ID
            schedule_type: 'interval' 또는 'cron'
            interval_minutes: 간격 (분), schedule_type이 'interval'일 때 필수
            cron_expression: Cron 표현식, schedule_type이 'cron'일 때 필수
        """
        try:
            if schedule_type == 'interval' and interval_minutes:
                trigger = IntervalTrigger(minutes=interval_minutes)
            elif schedule_type == 'cron' and cron_expression:
                # cron_expression 파싱: "0 9,18 * * *" (분 시 일 월 요일)
                parts = cron_expression.split()
                if len(parts) >= 5:
                    trigger = CronTrigger(
                        minute=parts[0],
                        hour=parts[1],
                        day=parts[2] if parts[2] != '*' else None,
                        month=parts[3] if parts[3] != '*' else None,
                        day_of_week=parts[4] if parts[4] != '*' else None
                    )
                else:
                    logger.error(f"Invalid cron expression: {cron_expression}")
                    return False
            else:
                logger.error("Invalid schedule configuration")
                return False

            self.scheduler.add_job(
                func=self.auto_scrape_naverpay,
                trigger=trigger,
                id=job_id,
                name=f'NaverPay Scraping ({job_id})',
                replace_existing=True
            )

            logger.success(f"NaverPay schedule added: {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add NaverPay schedule: {e}")
            return False

    def remove_naverpay_schedule(self, job_id: str) -> bool:
        """NaverPay 스케줄 제거"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"NaverPay schedule removed: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove NaverPay schedule: {e}")
            return False

    def pause_naverpay_schedule(self, job_id: str) -> bool:
        """NaverPay 스케줄 일시정지"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"NaverPay schedule paused: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause NaverPay schedule: {e}")
            return False

    def resume_naverpay_schedule(self, job_id: str) -> bool:
        """NaverPay 스케줄 재개"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"NaverPay schedule resumed: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume NaverPay schedule: {e}")
            return False

    def get_naverpay_schedules(self) -> list:
        """NaverPay 관련 스케줄만 조회"""
        jobs = []
        for job in self.scheduler.get_jobs():
            if 'naverpay' in job.id.lower():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'is_paused': job.next_run_time is None
                })
        return jobs

    def get_job_status(self):
        """
        Get status of all scheduled jobs
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return {
            'running': self.is_running,
            'jobs': jobs
        }


# Global scheduler instance
scheduler_instance: Optional[AutomationScheduler] = None


def get_scheduler() -> AutomationScheduler:
    """Get or create scheduler instance"""
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = AutomationScheduler()
    return scheduler_instance
