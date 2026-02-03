"""
Performance metrics collection and analysis utilities
"""
import time
import statistics
import json
from typing import List, Dict, Any
from functools import wraps
from src.utils.logger import Logger


class PerformanceMetrics:
    """Collect and analyze performance metrics"""

    def __init__(self, name: str):
        self.name = name
        self.logger = Logger(f"Performance-{name}")
        self.timings: List[float] = []
        self.requests: List[Dict[str, Any]] = []

    def add_timing(self, duration: float, metadata: Dict = None):
        """Add a timing measurement"""
        self.timings.append(duration)

        if metadata:
            self.requests.append({
                'duration': duration,
                'timestamp': time.time(),
                **metadata
            })

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from collected timings"""
        if not self.timings:
            return {}

        sorted_timings = sorted(self.timings)
        n = len(sorted_timings)

        stats = {
            'name': self.name,
            'count': n,
            'min': min(sorted_timings),
            'max': max(sorted_timings),
            'mean': statistics.mean(sorted_timings),
            'median': statistics.median(sorted_timings),
            'stdev': statistics.stdev(sorted_timings) if n > 1 else 0,
            'p50': self._percentile(sorted_timings, 0.50),
            'p75': self._percentile(sorted_timings, 0.75),
            'p90': self._percentile(sorted_timings, 0.90),
            'p95': self._percentile(sorted_timings, 0.95),
            'p99': self._percentile(sorted_timings, 0.99),
        }

        self.logger.info(
            f"{self.name} - Count: {n}, "
            f"Min: {stats['min'] * 1000:.0f}ms, "
            f"Avg: {stats['mean'] * 1000:.0f}ms, "
            f"p95: {stats['p95'] * 1000:.0f}ms, "
            f"Max: {stats['max'] * 1000:.0f}ms"
        )

        return stats

    def _percentile(self, sorted_data: List[float], percentile: float) -> float:
        """Calculate percentile from sorted data"""
        if not sorted_data:
            return 0

        k = (len(sorted_data) - 1) * percentile
        f = int(k)
        c = f + 1

        if c >= len(sorted_data):
            return sorted_data[-1]

        d0 = sorted_data[f] * (c - k)
        d1 = sorted_data[c] * (k - f)

        return d0 + d1

    def get_slowest_requests(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get the N slowest requests"""
        sorted_requests = sorted(
            self.requests,
            key=lambda x: x['duration'],
            reverse=True
        )
        return sorted_requests[:n]

    def format_summary(self) -> str:
        """Format statistics as readable text"""
        stats = self.get_statistics()

        if not stats:
            return f"{self.name}: No data collected"

        summary = [
            f"{'=' * 70}",
            f"{self.name.upper()} - PERFORMANCE SUMMARY",
            f"{'=' * 70}",
            f"Total Requests:     {stats['count']}",
            f"",
            f"Response Times:",
            f"  Min:              {stats['min'] * 1000:>8.0f}ms",
            f"  Mean:             {stats['mean'] * 1000:>8.0f}ms",
            f"  Median (p50):     {stats['median'] * 1000:>8.0f}ms",
            f"  p95:              {stats['p95'] * 1000:>8.0f}ms",
            f"  p99:              {stats['p99'] * 1000:>8.0f}ms",
            f"  Max:              {stats['max'] * 1000:>8.0f}ms",
            f"  Std Dev:          {stats['stdev'] * 1000:>8.0f}ms",
            f"{'=' * 70}",
        ]

        return '\n'.join(summary)

    def to_dict(self) -> Dict[str, Any]:
        """Export all data as dictionary"""
        return {
            'name': self.name,
            'statistics': self.get_statistics(),
            'timings': self.timings,
            'requests': self.requests
        }


class PerformanceTimer:
    """Context manager for timing code blocks"""

    def __init__(self, metrics: PerformanceMetrics, metadata: Dict = None):
        self.metrics = metrics
        self.metadata = metadata or {}
        self.start_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        self.metrics.add_timing(self.duration, self.metadata)
        return False


def measure_time(metrics: PerformanceMetrics):
    """Decorator to measure function execution time"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start

            metadata = {
                'function': func.__name__,
                'args': str(args)[:100],  # Truncate long args
            }
            metrics.add_timing(duration, metadata)

            return result

        return wrapper

    return decorator


class PerformanceCollector:
    """Collect metrics from multiple sources"""

    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.logger = Logger("PerformanceCollector")

    def get_or_create(self, name: str) -> PerformanceMetrics:
        """Get existing metrics or create new"""
        if name not in self.metrics:
            self.metrics[name] = PerformanceMetrics(name)
        return self.metrics[name]

    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics from all metrics"""
        return {
            name: metrics.get_statistics()
            for name, metrics in self.metrics.items()
        }

    def format_comparison_table(self) -> str:
        """Format comparison table of all metrics"""
        all_stats = self.get_all_statistics()

        if not all_stats:
            return "No performance data collected"

        lines = [
            "=" * 100,
            f"{'Endpoint/Action':<40} {'Count':<10} {'Min':<10} {'Avg':<10} {'p95':<10} {'Max':<10}",
            "=" * 100,
        ]

        for name, stats in all_stats.items():
            if not stats:
                continue

            lines.append(
                f"{name:<40} "
                f"{stats['count']:<10} "
                f"{stats['min'] * 1000:<10.0f} "
                f"{stats['mean'] * 1000:<10.0f} "
                f"{stats['p95'] * 1000:<10.0f} "
                f"{stats['max'] * 1000:<10.0f}"
            )

        lines.append("=" * 100)

        return '\n'.join(lines)

    def export_json(self, filepath: str):
        """Export all metrics to JSON file"""
        data = {
            name: metrics.to_dict()
            for name, metrics in self.metrics.items()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Exported metrics to {filepath}")