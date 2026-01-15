import random

import pytest
import allure
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from src.data.endpoints.category_management import CategoryManagementAPI
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from src.data.endpoints.combined import DigitalOrderAPI, set_current_api
from src.utils.navigation import Navigation
from src.data.table_config import DEFAULT_TABLE_NUMBER
from src.utils.console_monitor import ConsoleMonitor
import inspect
import shutil
import os


@pytest.fixture(scope="function")
def table(request):
    if hasattr(request, 'param'):
        return request.param

    if hasattr(request, 'function'):
        sig = inspect.signature(request.function)
        if 'table' in sig.parameters:
            default_val = sig.parameters['table'].default
            if default_val != inspect.Parameter.empty:
                return default_val

    return DEFAULT_TABLE_NUMBER


@pytest.fixture(scope="function")
def endpoint_setup(table):
    print(f"\n{'=' * 60}")
    print(f"TEST SETUP: Initializing table {table}")
    print(f"{'=' * 60}")

    api = DigitalOrderAPI(table_number=table)
    api_data = api.setup_table()

    if not api_data:
        pytest.fail(f"Failed to setup table {table}")
    set_current_api(api)

    print(f"✓ API registered for worker - standalone functions will work")
    print(f"  Table: {api.table_num}")
    print(f"  TransactionGuid: {api.transaction_guid}")
    print(f"  Session ID: {api.session_id}")
    print(f"{'=' * 60}\n")

    yield api

    print(f"\n{'=' * 60}")
    print(f"TEST TEARDOWN: Closing table {table}")
    print(f"{'=' * 60}")

    try:
        api.close_table()
        print(f"✓ Table {table} closed successfully")
    except Exception as e:
        pass

    print(f"{'=' * 60}\n")


@pytest.fixture(scope="function")
def browser_factory(endpoint_setup):
    drivers = []
    temp_dirs = []  # ← NEW: Track temp directories for cleanup
    api_setup = endpoint_setup

    def _create_browsers(*browser_types):
        for browser_type in browser_types:
            if browser_type.lower() == "chrome":
                options = ChromeOptions()
                # options.add_argument("--headless")
                # options.add_argument("--window-size=800,600")
                options.add_argument("--incognito")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--log-level=3")
                options.add_argument("--silent")
                options.add_argument("--disable-logging")

                # ← NEW: Track the temp directory path
                temp_dir = f"/tmp/chrome_test_{id(options)}"
                options.add_argument(f"--user-data-dir={temp_dir}")
                temp_dirs.append(temp_dir)  # ← NEW: Add to cleanup list

                options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)

            elif browser_type.lower() == "edge":
                options = webdriver.EdgeOptions()
                options.add_argument("--disable-blink-features=AutomationControlled")

                # ← NEW: Track the temp directory path
                temp_dir = f"/tmp/edge_test_{id(options)}"
                options.add_argument(f"--user-data-dir={temp_dir}")
                temp_dirs.append(temp_dir)  # ← NEW: Add to cleanup list

                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

                service = EdgeService(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=options)

            else:
                raise ValueError(f"Unsupported browser type: {browser_type}")

            # Navigate to table URL
            Navigation.navigate(driver, api_setup.session_id, api_setup.table_num)
            drivers.append(driver)

        return drivers

    yield _create_browsers

    # ========================================================================
    # TEARDOWN: Console check, quit drivers, cleanup temp directories
    # ========================================================================

    # Console safety check
    for drv in drivers:
        try:
            with allure.step("🔍 Automatic Console Safety Check"):
                monitor = ConsoleMonitor(drv)
                results = monitor.check_all()
                monitor.report_to_allure()

                if results['has_issues']:
                    summary = f"⚠️ CONSOLE ISSUES DETECTED\n"
                    summary += f"Errors: {len(results['errors'])}\n"
                    summary += f"PII Violations: {len(results['pii_violations'])}\n"

                    allure.attach(
                        summary,
                        name="Console Issues Summary",
                        attachment_type=allure.attachment_type.TEXT
                    )

                    pytest.fail(
                        f"Console violations detected: "
                        f"{len(results['errors'])} errors, "
                        f"{len(results['pii_violations'])} PII violations"
                    )
                else:
                    allure.attach(
                        "✅ No console issues detected",
                        name="Console Clean",
                        attachment_type=allure.attachment_type.TEXT
                    )

        except Exception as e:
            print(f"Warning: Could not perform console check: {str(e)}")

    # Quit all drivers
    for drv in drivers:
        try:
            drv.quit()
        except Exception as e:
            print(f"Error closing browser: {str(e)}")

    # ← NEW: Clean up temp directories
    print(f"\n{'=' * 60}")
    print(f"CLEANUP: Removing temporary browser profiles")
    print(f"{'=' * 60}")

    for temp_dir in temp_dirs:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"✓ Removed: {temp_dir}")
            else:
                print(f"⚠ Not found: {temp_dir}")
        except Exception as e:
            print(f"✗ Failed to remove {temp_dir}: {str(e)}")

    print(f"{'=' * 60}\n")


