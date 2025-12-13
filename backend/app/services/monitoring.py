"""
Comprehensive System Monitoring Service
포괄적인 시스템 모니터링 서비스
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import time
import psutil
import threading
from collections import deque
from dataclasses import dataclass, asdict
from enum import Enum


class MonitoringLevel(Enum):
    """모니터링 레벨"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MonitoringEvent:
    """모니터링 이벤트"""
    timestamp: datetime
    category: str
    event_type: str
    level: MonitoringLevel
    message: str
    metadata: Dict[str, Any]
    duration_ms: Optional[float] = None


class SystemMonitor:
    """
    시스템 모니터링 서비스
    """

    def __init__(self, max_events: int = 10000):
        self.events: deque = deque(maxlen=max_events)
        self.metrics: Dict[str, Any] = {}
        self.alerts: List[Dict] = []
        self.start_time = datetime.utcnow()

        # Performance tracking
        self.request_times: deque = deque(maxlen=1000)
        self.error_count = 0
        self.success_count = 0

        # Thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'response_time_ms': 1000,
            'error_rate': 0.05  # 5%
        }

    # =====================
    # 1. 네트워크 연결 상태
    # =====================

    def log_network_connection_attempt(self, target: str, **metadata):
        """서버 연결 시도 시작"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="network",
            event_type="connection_attempt",
            level=MonitoringLevel.INFO,
            message=f"Attempting to connect to {target}",
            metadata={"target": target, **metadata}
        )
        self._record_event(event)
        logger.info(f"Network: Connecting to {target}")

    def log_network_connection_success(self, target: str, duration_ms: float, **metadata):
        """서버 연결 성공"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="network",
            event_type="connection_success",
            level=MonitoringLevel.INFO,
            message=f"Successfully connected to {target}",
            metadata={"target": target, **metadata},
            duration_ms=duration_ms
        )
        self._record_event(event)
        logger.success(f"Network: Connected to {target} in {duration_ms:.2f}ms")

    def log_network_connection_failure(self, target: str, error: str, **metadata):
        """서버 연결 실패"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="network",
            event_type="connection_failure",
            level=MonitoringLevel.ERROR,
            message=f"Failed to connect to {target}: {error}",
            metadata={"target": target, "error": error, **metadata}
        )
        self._record_event(event)
        self.error_count += 1
        logger.error(f"Network: Connection failed to {target} - {error}")

    def log_network_timeout(self, target: str, timeout_seconds: float):
        """연결 타임아웃 발생"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="network",
            event_type="connection_timeout",
            level=MonitoringLevel.WARNING,
            message=f"Connection timeout to {target} after {timeout_seconds}s",
            metadata={"target": target, "timeout": timeout_seconds}
        )
        self._record_event(event)
        logger.warning(f"Network: Timeout to {target}")

    def log_api_request(self, method: str, url: str, **metadata):
        """API 요청 시작"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="api",
            event_type="request_start",
            level=MonitoringLevel.DEBUG,
            message=f"{method} {url}",
            metadata={"method": method, "url": url, **metadata}
        )
        self._record_event(event)

    def log_api_response(
        self,
        method: str,
        url: str,
        status_code: int,
        duration_ms: float,
        **metadata
    ):
        """API 응답 완료"""
        level = MonitoringLevel.INFO if 200 <= status_code < 400 else MonitoringLevel.ERROR

        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="api",
            event_type="request_complete",
            level=level,
            message=f"{method} {url} - {status_code} ({duration_ms:.2f}ms)",
            metadata={
                "method": method,
                "url": url,
                "status_code": status_code,
                **metadata
            },
            duration_ms=duration_ms
        )
        self._record_event(event)
        self.request_times.append(duration_ms)

        if 200 <= status_code < 400:
            self.success_count += 1
        else:
            self.error_count += 1

        # Check response time threshold
        if duration_ms > self.thresholds['response_time_ms']:
            self._create_alert(
                "high_response_time",
                f"API response time {duration_ms:.2f}ms exceeds threshold",
                {"url": url, "duration_ms": duration_ms}
            )

    # =====================
    # 2. 인증/로그인 프로세스
    # =====================

    def log_login_attempt(self, username: str, ip_address: str = None):
        """로그인 시도 시작"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="auth",
            event_type="login_attempt",
            level=MonitoringLevel.INFO,
            message=f"Login attempt for user: {username}",
            metadata={"username": username, "ip_address": ip_address}
        )
        self._record_event(event)
        logger.info(f"Auth: Login attempt - {username} from {ip_address}")

    def log_login_success(self, username: str, ip_address: str = None):
        """로그인 성공"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="auth",
            event_type="login_success",
            level=MonitoringLevel.INFO,
            message=f"Login successful: {username}",
            metadata={"username": username, "ip_address": ip_address}
        )
        self._record_event(event)
        logger.success(f"Auth: Login successful - {username}")

    def log_login_failure(self, username: str, reason: str, ip_address: str = None):
        """로그인 실패"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="auth",
            event_type="login_failure",
            level=MonitoringLevel.WARNING,
            message=f"Login failed for {username}: {reason}",
            metadata={"username": username, "reason": reason, "ip_address": ip_address}
        )
        self._record_event(event)
        logger.warning(f"Auth: Login failed - {username} - {reason}")

    def log_token_issued(self, username: str, token_type: str = "access"):
        """토큰 발급 성공"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="auth",
            event_type="token_issued",
            level=MonitoringLevel.INFO,
            message=f"Token issued for {username}",
            metadata={"username": username, "token_type": token_type}
        )
        self._record_event(event)

    def log_token_expired(self, username: str):
        """토큰 만료 감지"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="auth",
            event_type="token_expired",
            level=MonitoringLevel.INFO,
            message=f"Token expired for {username}",
            metadata={"username": username}
        )
        self._record_event(event)

    def log_logout(self, username: str):
        """로그아웃 처리"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="auth",
            event_type="logout",
            level=MonitoringLevel.INFO,
            message=f"User logged out: {username}",
            metadata={"username": username}
        )
        self._record_event(event)

    # =====================
    # 3. 데이터베이스 연결
    # =====================

    def log_db_pool_init(self, pool_size: int, **metadata):
        """DB 연결 풀 초기화"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="database",
            event_type="pool_init",
            level=MonitoringLevel.INFO,
            message=f"Database pool initialized with size {pool_size}",
            metadata={"pool_size": pool_size, **metadata}
        )
        self._record_event(event)
        logger.info(f"DB: Pool initialized - size {pool_size}")

    def log_db_connection_attempt(self):
        """DB 연결 시도"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="database",
            event_type="connection_attempt",
            level=MonitoringLevel.DEBUG,
            message="Attempting database connection",
            metadata={}
        )
        self._record_event(event)

    def log_db_connection_success(self, duration_ms: float):
        """DB 연결 성공"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="database",
            event_type="connection_success",
            level=MonitoringLevel.INFO,
            message=f"Database connected in {duration_ms:.2f}ms",
            metadata={},
            duration_ms=duration_ms
        )
        self._record_event(event)

    def log_db_connection_failure(self, error: str):
        """DB 연결 실패"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="database",
            event_type="connection_failure",
            level=MonitoringLevel.ERROR,
            message=f"Database connection failed: {error}",
            metadata={"error": error}
        )
        self._record_event(event)
        self._create_alert("db_connection_failure", error, {})

    def log_db_query(self, query_type: str, table: str, duration_ms: float):
        """쿼리 실행"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="database",
            event_type="query_executed",
            level=MonitoringLevel.DEBUG,
            message=f"{query_type} query on {table}",
            metadata={"query_type": query_type, "table": table},
            duration_ms=duration_ms
        )
        self._record_event(event)

        # Slow query detection
        if duration_ms > 1000:  # > 1 second
            logger.warning(f"DB: Slow query detected - {query_type} on {table} ({duration_ms:.2f}ms)")

    def log_db_transaction(self, action: str, **metadata):
        """트랜잭션 처리"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="database",
            event_type=f"transaction_{action}",
            level=MonitoringLevel.DEBUG,
            message=f"Transaction {action}",
            metadata=metadata
        )
        self._record_event(event)

    # =====================
    # 4. 파일 시스템 작업
    # =====================

    def log_file_operation(
        self,
        operation: str,
        file_path: str,
        success: bool,
        error: str = None,
        size_bytes: int = None
    ):
        """파일 작업 로그"""
        level = MonitoringLevel.INFO if success else MonitoringLevel.ERROR

        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="filesystem",
            event_type=f"file_{operation}",
            level=level,
            message=f"File {operation}: {file_path}",
            metadata={
                "operation": operation,
                "file_path": file_path,
                "success": success,
                "error": error,
                "size_bytes": size_bytes
            }
        )
        self._record_event(event)

    def log_disk_space_warning(self, path: str, free_percent: float):
        """디스크 용량 경고"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="filesystem",
            event_type="disk_space_low",
            level=MonitoringLevel.WARNING,
            message=f"Low disk space on {path}: {free_percent:.1f}% free",
            metadata={"path": path, "free_percent": free_percent}
        )
        self._record_event(event)
        self._create_alert("disk_space_low", f"{path} has {free_percent:.1f}% free", {})

    # =====================
    # 5. 메모리 & 리소스
    # =====================

    def log_memory_usage(self):
        """메모리 사용량 로그"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="resources",
            event_type="memory_usage",
            level=MonitoringLevel.INFO,
            message=f"Memory usage: {memory_percent:.1f}%",
            metadata={
                "percent": memory_percent,
                "used_mb": memory.used / (1024 ** 2),
                "available_mb": memory.available / (1024 ** 2)
            }
        )
        self._record_event(event)

        # Check threshold
        if memory_percent > self.thresholds['memory_percent']:
            self._create_alert(
                "high_memory_usage",
                f"Memory usage {memory_percent:.1f}% exceeds threshold",
                {"percent": memory_percent}
            )

    def log_cpu_usage(self):
        """CPU 사용량 로그"""
        cpu_percent = psutil.cpu_percent(interval=1)

        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="resources",
            event_type="cpu_usage",
            level=MonitoringLevel.INFO,
            message=f"CPU usage: {cpu_percent:.1f}%",
            metadata={"percent": cpu_percent}
        )
        self._record_event(event)

        # Check threshold
        if cpu_percent > self.thresholds['cpu_percent']:
            self._create_alert(
                "high_cpu_usage",
                f"CPU usage {cpu_percent:.1f}% exceeds threshold",
                {"percent": cpu_percent}
            )

    def log_thread_activity(self, action: str, thread_name: str):
        """스레드 활동 로그"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="resources",
            event_type=f"thread_{action}",
            level=MonitoringLevel.DEBUG,
            message=f"Thread {action}: {thread_name}",
            metadata={"action": action, "thread_name": thread_name}
        )
        self._record_event(event)

    # =====================
    # 6. 외부 서비스 연동
    # =====================

    def log_external_api_call(
        self,
        service_name: str,
        endpoint: str,
        success: bool,
        duration_ms: float,
        error: str = None
    ):
        """외부 API 호출"""
        level = MonitoringLevel.INFO if success else MonitoringLevel.ERROR

        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="external_service",
            event_type="api_call",
            level=level,
            message=f"{service_name} API call: {endpoint}",
            metadata={
                "service": service_name,
                "endpoint": endpoint,
                "success": success,
                "error": error
            },
            duration_ms=duration_ms
        )
        self._record_event(event)

    def log_webhook_event(self, direction: str, event_type: str, **metadata):
        """웹훅 수신/발송"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="webhook",
            event_type=f"webhook_{direction}",
            level=MonitoringLevel.INFO,
            message=f"Webhook {direction}: {event_type}",
            metadata={"direction": direction, "event_type": event_type, **metadata}
        )
        self._record_event(event)

    # =====================
    # 7. 애플리케이션 상태
    # =====================

    def log_app_startup(self, version: str = None):
        """앱 시작"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="application",
            event_type="startup",
            level=MonitoringLevel.INFO,
            message=f"Application starting (version: {version})",
            metadata={"version": version}
        )
        self._record_event(event)
        logger.success(f"App: Starting version {version}")

    def log_app_ready(self):
        """앱 초기화 완료"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="application",
            event_type="ready",
            level=MonitoringLevel.INFO,
            message="Application ready to serve requests",
            metadata={}
        )
        self._record_event(event)
        logger.success("App: Ready")

    def log_app_shutdown(self, graceful: bool = True):
        """앱 종료"""
        level = MonitoringLevel.INFO if graceful else MonitoringLevel.ERROR

        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="application",
            event_type="shutdown",
            level=level,
            message="Application shutting down" + (" gracefully" if graceful else " (crash)"),
            metadata={"graceful": graceful}
        )
        self._record_event(event)

    def log_health_check(self, healthy: bool, details: Dict = None):
        """헬스체크"""
        level = MonitoringLevel.INFO if healthy else MonitoringLevel.WARNING

        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="health",
            event_type="health_check",
            level=level,
            message=f"Health check: {'healthy' if healthy else 'unhealthy'}",
            metadata={"healthy": healthy, "details": details or {}}
        )
        self._record_event(event)

    # =====================
    # 8. 에러 & 예외
    # =====================

    def log_exception(
        self,
        exception_type: str,
        message: str,
        stack_trace: str = None,
        **metadata
    ):
        """예외 발생"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="error",
            event_type="exception",
            level=MonitoringLevel.ERROR,
            message=f"{exception_type}: {message}",
            metadata={
                "exception_type": exception_type,
                "stack_trace": stack_trace,
                **metadata
            }
        )
        self._record_event(event)
        self.error_count += 1
        logger.error(f"Exception: {exception_type} - {message}")

    def log_retry_attempt(self, operation: str, attempt: int, max_attempts: int):
        """재시도 로직"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="error",
            event_type="retry_attempt",
            level=MonitoringLevel.WARNING,
            message=f"Retrying {operation} (attempt {attempt}/{max_attempts})",
            metadata={
                "operation": operation,
                "attempt": attempt,
                "max_attempts": max_attempts
            }
        )
        self._record_event(event)

    # =====================
    # 9. 사용자 액션
    # =====================

    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str = None,
        **metadata
    ):
        """사용자 액션"""
        event = MonitoringEvent(
            timestamp=datetime.utcnow(),
            category="user_action",
            event_type=action,
            level=MonitoringLevel.INFO,
            message=f"User {user_id} performed {action}",
            metadata={
                "user_id": user_id,
                "action": action,
                "resource": resource,
                **metadata
            }
        )
        self._record_event(event)

    # =====================
    # 10. 성능 메트릭
    # =====================

    def get_performance_metrics(self) -> Dict:
        """성능 메트릭 조회"""
        total_requests = self.success_count + self.error_count
        error_rate = self.error_count / total_requests if total_requests > 0 else 0

        avg_response_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0

        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "error_rate": round(error_rate, 4),
            "avg_response_time_ms": round(avg_response_time, 2),
            "memory_percent": psutil.virtual_memory().percent,
            "cpu_percent": psutil.cpu_percent(interval=0),
            "active_threads": threading.active_count()
        }

    # =====================
    # Internal Methods
    # =====================

    def _record_event(self, event: MonitoringEvent):
        """이벤트 기록"""
        self.events.append(event)

        # Log based on level
        if event.level == MonitoringLevel.ERROR or event.level == MonitoringLevel.CRITICAL:
            logger.error(f"[{event.category}] {event.message}")
        elif event.level == MonitoringLevel.WARNING:
            logger.warning(f"[{event.category}] {event.message}")
        elif event.level == MonitoringLevel.INFO:
            logger.info(f"[{event.category}] {event.message}")
        else:
            logger.debug(f"[{event.category}] {event.message}")

    def _create_alert(self, alert_type: str, message: str, metadata: Dict):
        """알림 생성"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": alert_type,
            "message": message,
            "metadata": metadata
        }
        self.alerts.append(alert)
        logger.warning(f"ALERT: {alert_type} - {message}")

    def get_recent_events(
        self,
        category: str = None,
        level: MonitoringLevel = None,
        limit: int = 100
    ) -> List[Dict]:
        """최근 이벤트 조회"""
        events = list(self.events)

        if category:
            events = [e for e in events if e.category == category]

        if level:
            events = [e for e in events if e.level == level]

        # Convert to dict
        return [
            {
                **asdict(e),
                "timestamp": e.timestamp.isoformat(),
                "level": e.level.value
            }
            for e in list(reversed(events))[:limit]
        ]

    def get_alerts(self, hours: int = 24) -> List[Dict]:
        """최근 알림 조회"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff
        ]


# Global monitor instance
_monitor: Optional[SystemMonitor] = None


def get_monitor() -> SystemMonitor:
    """Get global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor()
    return _monitor
