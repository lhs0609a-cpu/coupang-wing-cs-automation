"""
Performance Monitoring Service
"""
import time
import psutil
from typing import Dict
from datetime import datetime
from loguru import logger
from functools import wraps


class PerformanceMonitor:
    """
    Service for monitoring system performance
    """

    def __init__(self):
        self.metrics = []

    def get_system_stats(self) -> Dict:
        """
        Get current system statistics

        Returns:
            System stats dictionary
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count()
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            }
        }

    def track_execution_time(self, func_name: str = None):
        """
        Decorator to track function execution time

        Args:
            func_name: Function name (optional)
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                name = func_name or func.__name__
                logger.debug(f"{name} executed in {execution_time:.3f}s")

                self.metrics.append({
                    'function': name,
                    'execution_time': execution_time,
                    'timestamp': datetime.utcnow().isoformat()
                })

                return result
            return wrapper
        return decorator

    def get_performance_report(self) -> Dict:
        """
        Get performance report

        Returns:
            Performance report
        """
        if not self.metrics:
            return {'message': 'No metrics available'}

        # Group by function
        function_stats = {}
        for metric in self.metrics:
            func = metric['function']
            if func not in function_stats:
                function_stats[func] = []
            function_stats[func].append(metric['execution_time'])

        # Calculate averages
        report = {}
        for func, times in function_stats.items():
            report[func] = {
                'count': len(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times)
            }

        return {
            'function_stats': report,
            'system_stats': self.get_system_stats()
        }
