"""
Performance report generation for Allure
"""
import json
import allure
from typing import Dict, Any, List
from src.utils.performance_metrics import PerformanceCollector


class PerformanceReporter:
    """Generate performance reports for Allure"""

    @staticmethod
    def attach_statistics(metrics_dict: Dict[str, Any], name: str = "Performance Statistics"):
        """Attach statistics as JSON to Allure"""
        allure.attach(
            json.dumps(metrics_dict, indent=2),
            name=name,
            attachment_type=allure.attachment_type.JSON
        )

    @staticmethod
    def attach_summary_table(summary_text: str, name: str = "Performance Summary"):
        """Attach summary table as text to Allure"""
        allure.attach(
            summary_text,
            name=name,
            attachment_type=allure.attachment_type.TEXT
        )

    @staticmethod
    def attach_slowest_requests(requests: List[Dict[str, Any]], n: int = 10):
        """Attach slowest requests to Allure"""
        lines = [
            f"TOP {n} SLOWEST REQUESTS",
            "=" * 70,
        ]

        for i, req in enumerate(requests[:n], 1):
            duration_ms = req['duration'] * 1000
            metadata = {k: v for k, v in req.items() if k not in ['duration', 'timestamp']}

            lines.append(
                f"{i}. {duration_ms:.0f}ms - {metadata}"
            )

        allure.attach(
            '\n'.join(lines),
            name=f"Top {n} Slowest Requests",
            attachment_type=allure.attachment_type.TEXT
        )

    @staticmethod
    def attach_collector_report(collector: PerformanceCollector):
        """Attach complete collector report to Allure"""

        # Attach comparison table
        table = collector.format_comparison_table()
        PerformanceReporter.attach_summary_table(table, "Performance Comparison")

        # Attach all statistics as JSON
        all_stats = collector.get_all_statistics()
        PerformanceReporter.attach_statistics(all_stats, "All Metrics")

        # Attach individual metric summaries
        for name, metrics in collector.metrics.items():
            summary = metrics.format_summary()
            PerformanceReporter.attach_summary_table(
                summary,
                f"{name} - Detailed Stats"
            )

            # Attach slowest requests if available
            if metrics.requests:
                slowest = metrics.get_slowest_requests(10)
                PerformanceReporter.attach_slowest_requests(slowest)

    @staticmethod
    def create_performance_step(name: str, duration: float, threshold: float = None):
        """Create Allure step with performance annotation"""
        duration_ms = duration * 1000

        step_name = f"{name}: {duration_ms:.0f}ms"

        if threshold:
            threshold_ms = threshold * 1000
            if duration > threshold:
                step_name += f" ⚠️ (> {threshold_ms:.0f}ms threshold)"
            else:
                step_name += f" ✅ (< {threshold_ms:.0f}ms threshold)"

        return allure.step(step_name)