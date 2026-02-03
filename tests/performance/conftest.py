"""
Performance test fixtures and configuration
"""
import pytest
import allure
from src.utils.performance_metrics import PerformanceCollector
from src.utils.performance_reporter import PerformanceReporter
from src.utils.network_tracker import NetworkTracker


@pytest.fixture(scope="session")
def performance_collector():
    """Session-scoped performance collector"""
    return PerformanceCollector()


@pytest.fixture(scope="function")
def performance_reporter():
    """Function-scoped performance reporter"""
    return PerformanceReporter()


@pytest.fixture(scope="function")
def network_tracker(browser_factory):
    """
    Network tracker fixture - automatically captures API calls
    """
    trackers = []

    yield trackers

    # After test: capture and report all trackers
    for tracker in trackers:
        try:
            tracker.capture()
            tracker.attach_to_allure()
        except Exception as e:
            print(f"⚠️  Failed to capture network performance: {e}")


@pytest.fixture(scope="function")
def table():
    """Override table fixture to use table 51 for performance tests"""
    return 51


# Performance test configuration
PERFORMANCE_TABLE = 51
ITERATIONS = 10

# SLA Thresholds (in seconds)
SLA_THRESHOLDS = {
    'navigate_to_menu': 5.0,
    'add_item': 3.0,
    'navigate_to_cart': 2.0,
    'payment_processing': 4.0,
    'full_checkout_flow': 20.0,
}


def get_sla_threshold(operation_name: str) -> float:
    """Get SLA threshold for operation"""
    return SLA_THRESHOLDS.get(operation_name, 5.0)