"""
Monitoring API Router
모니터링 API 라우터
"""
from fastapi import APIRouter, Query
from typing import Optional, List, Dict
from datetime import datetime

from ..services.monitoring import get_monitor, MonitoringLevel

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/health")
def health_check():
    """
    헬스체크 엔드포인트
    """
    monitor = get_monitor()
    metrics = monitor.get_performance_metrics()

    healthy = (
        metrics['error_rate'] < 0.1 and
        metrics['memory_percent'] < 90 and
        metrics['cpu_percent'] < 90
    )

    monitor.log_health_check(healthy, metrics)

    return {
        "status": "healthy" if healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics
    }


@router.get("/metrics")
def get_metrics():
    """
    성능 메트릭 조회
    """
    monitor = get_monitor()
    return monitor.get_performance_metrics()


@router.get("/events")
def get_events(
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    이벤트 로그 조회
    """
    monitor = get_monitor()

    # Convert level string to enum
    level_enum = None
    if level:
        try:
            level_enum = MonitoringLevel(level.lower())
        except ValueError:
            pass

    events = monitor.get_recent_events(
        category=category,
        level=level_enum,
        limit=limit
    )

    return {
        "events": events,
        "count": len(events)
    }


@router.get("/events/categories")
def get_event_categories():
    """
    이벤트 카테고리 목록
    """
    return {
        "categories": [
            "network",
            "api",
            "auth",
            "database",
            "filesystem",
            "resources",
            "external_service",
            "webhook",
            "application",
            "health",
            "error",
            "user_action"
        ]
    }


@router.get("/alerts")
def get_alerts(hours: int = Query(24, ge=1, le=168)):
    """
    알림 목록 조회
    """
    monitor = get_monitor()
    alerts = monitor.get_alerts(hours)

    return {
        "alerts": alerts,
        "count": len(alerts)
    }


@router.get("/stats/errors")
def get_error_stats():
    """
    에러 통계
    """
    monitor = get_monitor()
    metrics = monitor.get_performance_metrics()

    return {
        "total_errors": monitor.error_count,
        "total_requests": metrics['total_requests'],
        "error_rate": metrics['error_rate'],
        "success_rate": 1 - metrics['error_rate']
    }


@router.get("/stats/performance")
def get_performance_stats():
    """
    성능 통계
    """
    monitor = get_monitor()

    # Get recent response times
    recent_times = list(monitor.request_times)

    if recent_times:
        avg_time = sum(recent_times) / len(recent_times)
        min_time = min(recent_times)
        max_time = max(recent_times)

        # Calculate percentiles
        sorted_times = sorted(recent_times)
        p50_idx = int(len(sorted_times) * 0.5)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)

        return {
            "avg_response_time_ms": round(avg_time, 2),
            "min_response_time_ms": round(min_time, 2),
            "max_response_time_ms": round(max_time, 2),
            "p50_response_time_ms": round(sorted_times[p50_idx], 2),
            "p95_response_time_ms": round(sorted_times[p95_idx], 2),
            "p99_response_time_ms": round(sorted_times[p99_idx], 2),
            "sample_size": len(recent_times)
        }
    else:
        return {
            "message": "No performance data available yet"
        }


@router.get("/stats/system")
def get_system_stats():
    """
    시스템 리소스 통계
    """
    import psutil

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    cpu_count = psutil.cpu_count()

    # Memory
    memory = psutil.virtual_memory()

    # Disk
    disk = psutil.disk_usage('/')

    return {
        "cpu": {
            "count": cpu_count,
            "percent_total": psutil.cpu_percent(interval=0),
            "percent_per_cpu": cpu_percent
        },
        "memory": {
            "total_mb": round(memory.total / (1024 ** 2), 2),
            "available_mb": round(memory.available / (1024 ** 2), 2),
            "used_mb": round(memory.used / (1024 ** 2), 2),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "percent": disk.percent
        }
    }


@router.post("/test/log-event")
def test_log_event(
    category: str,
    event_type: str,
    message: str,
    level: str = "info"
):
    """
    테스트용 이벤트 로그
    """
    monitor = get_monitor()

    try:
        level_enum = MonitoringLevel(level.lower())
    except ValueError:
        level_enum = MonitoringLevel.INFO

    from ..services.monitoring import MonitoringEvent

    event = MonitoringEvent(
        timestamp=datetime.utcnow(),
        category=category,
        event_type=event_type,
        level=level_enum,
        message=message,
        metadata={}
    )

    monitor._record_event(event)

    return {"success": True, "event": event_type}
