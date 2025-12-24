"""
성능 모니터링 시스템
CPU, 메모리, API 응답 시간, 에러율 등을 실시간으로 추적
"""
import os
import sys
import time
import json
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import threading


class PerformanceMonitor:
    """성능 메트릭 수집 및 모니터링"""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        초기화

        Args:
            data_dir: 성능 데이터 저장 디렉토리
        """
        self.project_root = Path(__file__).parent
        self.data_dir = data_dir or self.project_root / "data" / "performance"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 메트릭 저장 (최근 N개)
        self.max_history = 1000
        self.cpu_history = deque(maxlen=self.max_history)
        self.memory_history = deque(maxlen=self.max_history)
        self.api_response_times = deque(maxlen=self.max_history)
        self.error_counts = deque(maxlen=self.max_history)

        # 임계값 설정 (환경변수 또는 기본값)
        self.cpu_threshold = float(os.getenv("PERF_CPU_THRESHOLD", "80"))  # %
        self.memory_threshold = float(os.getenv("PERF_MEMORY_THRESHOLD", "80"))  # %
        self.response_time_threshold = float(os.getenv("PERF_RESPONSE_TIME_THRESHOLD", "2.0"))  # seconds
        self.error_rate_threshold = float(os.getenv("PERF_ERROR_RATE_THRESHOLD", "5"))  # %

        # 모니터링 상태
        self.monitoring = False
        self.monitor_thread = None

        # 프로세스 정보
        self.process = psutil.Process()

    def collect_system_metrics(self) -> Dict:
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # 메모리 정보
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 디스크 정보
            disk = psutil.disk_usage(str(self.project_root))
            disk_percent = disk.percent

            # 프로세스별 정보
            process_cpu = self.process.cpu_percent(interval=0.1)
            process_memory = self.process.memory_info().rss / (1024 * 1024)  # MB

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'memory_available_mb': memory.available / (1024 * 1024),
                    'disk_percent': disk_percent,
                    'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                },
                'process': {
                    'cpu_percent': process_cpu,
                    'memory_mb': process_memory,
                    'threads': self.process.num_threads(),
                }
            }

            return metrics

        except Exception as e:
            print(f"⚠️  메트릭 수집 실패: {e}")
            return {}

    def record_api_request(self, endpoint: str, response_time: float, status_code: int):
        """
        API 요청 기록

        Args:
            endpoint: API 엔드포인트
            response_time: 응답 시간 (초)
            status_code: HTTP 상태 코드
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'response_time': response_time,
            'status_code': status_code,
            'is_error': status_code >= 400
        }

        self.api_response_times.append(record)

        # 에러 카운트
        if record['is_error']:
            self.error_counts.append(record)

    def get_statistics(self, window_minutes: int = 5) -> Dict:
        """
        통계 정보 계산

        Args:
            window_minutes: 계산 기간 (분)

        Returns:
            통계 정보
        """
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

        # API 응답 시간 통계
        recent_responses = [
            r for r in self.api_response_times
            if datetime.fromisoformat(r['timestamp']) > cutoff_time
        ]

        if recent_responses:
            response_times = [r['response_time'] for r in recent_responses]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            # 에러율 계산
            error_count = sum(1 for r in recent_responses if r['is_error'])
            total_requests = len(recent_responses)
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

        else:
            avg_response_time = 0
            max_response_time = 0
            min_response_time = 0
            error_count = 0
            total_requests = 0
            error_rate = 0

        # 시스템 메트릭 (현재 값)
        current_metrics = self.collect_system_metrics()

        stats = {
            'period_minutes': window_minutes,
            'timestamp': datetime.now().isoformat(),
            'api': {
                'total_requests': total_requests,
                'error_count': error_count,
                'error_rate_percent': error_rate,
                'avg_response_time': avg_response_time,
                'max_response_time': max_response_time,
                'min_response_time': min_response_time,
            },
            'system': current_metrics.get('system', {}),
            'process': current_metrics.get('process', {}),
        }

        return stats

    def check_thresholds(self, stats: Dict) -> List[Dict]:
        """
        임계값 초과 확인

        Returns:
            경고 목록
        """
        warnings = []

        # CPU 체크
        cpu = stats['system'].get('cpu_percent', 0)
        if cpu > self.cpu_threshold:
            warnings.append({
                'type': 'cpu',
                'level': 'warning',
                'message': f'CPU 사용률이 높습니다: {cpu:.1f}% (임계값: {self.cpu_threshold}%)',
                'value': cpu,
                'threshold': self.cpu_threshold
            })

        # 메모리 체크
        memory = stats['system'].get('memory_percent', 0)
        if memory > self.memory_threshold:
            warnings.append({
                'type': 'memory',
                'level': 'warning',
                'message': f'메모리 사용률이 높습니다: {memory:.1f}% (임계값: {self.memory_threshold}%)',
                'value': memory,
                'threshold': self.memory_threshold
            })

        # 응답 시간 체크
        avg_response = stats['api'].get('avg_response_time', 0)
        if avg_response > self.response_time_threshold:
            warnings.append({
                'type': 'response_time',
                'level': 'warning',
                'message': f'평균 응답 시간이 느립니다: {avg_response:.2f}s (임계값: {self.response_time_threshold}s)',
                'value': avg_response,
                'threshold': self.response_time_threshold
            })

        # 에러율 체크
        error_rate = stats['api'].get('error_rate_percent', 0)
        if error_rate > self.error_rate_threshold:
            warnings.append({
                'type': 'error_rate',
                'level': 'critical',
                'message': f'에러 발생률이 높습니다: {error_rate:.1f}% (임계값: {self.error_rate_threshold}%)',
                'value': error_rate,
                'threshold': self.error_rate_threshold
            })

        return warnings

    def save_report(self, stats: Dict, warnings: List[Dict]):
        """성능 리포트 저장"""
        report = {
            'statistics': stats,
            'warnings': warnings,
            'thresholds': {
                'cpu_percent': self.cpu_threshold,
                'memory_percent': self.memory_threshold,
                'response_time_seconds': self.response_time_threshold,
                'error_rate_percent': self.error_rate_threshold,
            }
        }

        # 리포트 파일명 (날짜별)
        date_str = datetime.now().strftime('%Y%m%d')
        report_file = self.data_dir / f"performance_report_{date_str}.json"

        # 기존 리포트 읽기 (있으면)
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                daily_reports = json.load(f)
        else:
            daily_reports = []

        # 새 리포트 추가
        daily_reports.append(report)

        # 저장
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(daily_reports, f, ensure_ascii=False, indent=2)

    def display_report(self, stats: Dict, warnings: List[Dict]):
        """리포트 콘솔 출력"""
        print("\n" + "=" * 70)
        print("📊 성능 모니터링 리포트")
        print("=" * 70)
        print(f"생성 시간: {stats['timestamp']}")
        print(f"측정 기간: 최근 {stats['period_minutes']}분")
        print()

        # 시스템 메트릭
        print("🖥️  시스템 메트릭")
        print("-" * 70)
        system = stats['system']
        print(f"  CPU 사용률: {system.get('cpu_percent', 0):.1f}%")
        print(f"  메모리 사용률: {system.get('memory_percent', 0):.1f}%")
        print(f"  사용 가능 메모리: {system.get('memory_available_mb', 0):.0f} MB")
        print(f"  디스크 사용률: {system.get('disk_percent', 0):.1f}%")
        print(f"  디스크 여유 공간: {system.get('disk_free_gb', 0):.2f} GB")
        print()

        # 프로세스 메트릭
        print("⚙️  프로세스 메트릭")
        print("-" * 70)
        process = stats['process']
        print(f"  프로세스 CPU: {process.get('cpu_percent', 0):.1f}%")
        print(f"  프로세스 메모리: {process.get('memory_mb', 0):.1f} MB")
        print(f"  스레드 수: {process.get('threads', 0)}")
        print()

        # API 메트릭
        print("🌐 API 메트릭")
        print("-" * 70)
        api = stats['api']
        print(f"  총 요청 수: {api.get('total_requests', 0)}")
        print(f"  에러 수: {api.get('error_count', 0)}")
        print(f"  에러율: {api.get('error_rate_percent', 0):.2f}%")
        print(f"  평균 응답 시간: {api.get('avg_response_time', 0):.3f}s")
        print(f"  최대 응답 시간: {api.get('max_response_time', 0):.3f}s")
        print(f"  최소 응답 시간: {api.get('min_response_time', 0):.3f}s")
        print()

        # 경고
        if warnings:
            print("⚠️  경고")
            print("-" * 70)
            for warning in warnings:
                level_icon = "🔴" if warning['level'] == 'critical' else "🟡"
                print(f"  {level_icon} {warning['message']}")
            print()
        else:
            print("✅ 모든 메트릭이 정상 범위 내에 있습니다.")
            print()

        print("=" * 70 + "\n")

    def generate_report(self, window_minutes: int = 5, save: bool = True, display: bool = True):
        """
        리포트 생성

        Args:
            window_minutes: 통계 계산 기간
            save: 파일로 저장 여부
            display: 콘솔 출력 여부
        """
        stats = self.get_statistics(window_minutes=window_minutes)
        warnings = self.check_thresholds(stats)

        if save:
            self.save_report(stats, warnings)

        if display:
            self.display_report(stats, warnings)

        return stats, warnings

    def start_monitoring(self, interval_seconds: int = 60):
        """
        백그라운드 모니터링 시작

        Args:
            interval_seconds: 모니터링 간격 (초)
        """
        if self.monitoring:
            print("⚠️  이미 모니터링이 실행 중입니다.")
            return

        self.monitoring = True

        def monitor_loop():
            print(f"🔍 성능 모니터링 시작 (간격: {interval_seconds}초)")
            while self.monitoring:
                try:
                    # 시스템 메트릭 수집
                    metrics = self.collect_system_metrics()
                    if metrics:
                        self.cpu_history.append(metrics['system']['cpu_percent'])
                        self.memory_history.append(metrics['system']['memory_percent'])

                    time.sleep(interval_seconds)

                except Exception as e:
                    print(f"⚠️  모니터링 오류: {e}")

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """백그라운드 모니터링 중지"""
        if not self.monitoring:
            print("⚠️  모니터링이 실행 중이 아닙니다.")
            return

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        print("⏹️  성능 모니터링 중지")


def main():
    """메인 함수 - CLI로 실행"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Coupang Wing CS 자동화 시스템 - 성능 모니터링'
    )
    parser.add_argument(
        '--window',
        type=int,
        default=5,
        help='통계 계산 기간 (분, 기본: 5)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='파일로 저장하지 않음'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='연속 모니터링 모드 (Ctrl+C로 중단)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='연속 모니터링 간격 (초, 기본: 60)'
    )

    args = parser.parse_args()

    monitor = PerformanceMonitor()

    try:
        if args.continuous:
            # 연속 모니터링 모드
            print("📊 연속 성능 모니터링 시작 (Ctrl+C로 중단)")
            print(f"리포트 생성 간격: {args.window}분")
            print(f"데이터 수집 간격: {args.interval}초")
            print()

            monitor.start_monitoring(interval_seconds=args.interval)

            while True:
                time.sleep(args.window * 60)
                monitor.generate_report(
                    window_minutes=args.window,
                    save=not args.no_save,
                    display=True
                )

        else:
            # 일회성 리포트 생성
            monitor.generate_report(
                window_minutes=args.window,
                save=not args.no_save,
                display=True
            )

    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다.")
        monitor.stop_monitoring()
        sys.exit(0)

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
