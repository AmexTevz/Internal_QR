import pytest
import allure
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from src.data.endpoints.combined import DigitalOrderAPI, set_current_api
from src.utils.navigation import Navigation
from src.data.table_config import DEFAULT_TABLE_NUMBER
from src.utils.console_monitor import ConsoleMonitor  # ← NEW: Console monitoring
import inspect


@pytest.fixture(scope="function")
def table(request):
    if hasattr(request, 'param'):
        return request.param

    # Otherwise look for default in test function signature
    if hasattr(request, 'function'):
        sig = inspect.signature(request.function)
        if 'table' in sig.parameters:
            default_val = sig.parameters['table'].default
            if default_val != inspect.Parameter.empty:
                return default_val

    # Final fallback
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

    # Teardown: Close table
    print(f"\n{'=' * 60}")
    print(f"TEST TEARDOWN: Closing table {table}")
    print(f"{'=' * 60}")

    try:
        api.close_table()
        print(f"✓ Table {table} closed successfully")
    except Exception as e:
        print(f"✗ Error closing table {table}: {str(e)}")

    print(f"{'=' * 60}\n")


@pytest.fixture(scope="function")
def browser_factory(endpoint_setup):

    drivers = []
    api_setup = endpoint_setup  # API instance

    def _create_browsers(*browser_types):
        for browser_type in browser_types:
            if browser_type.lower() == "chrome":
                options = ChromeOptions()
                # options.add_argument("--headless")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--incognito")
                options.add_argument("--disable-notifications")
                options.add_argument("--disable-popup-blocking")
                options.add_argument("--disable-infobars")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--log-level=3")
                options.add_argument("--silent")
                options.add_argument("--disable-logging")
                options.add_argument(f"--user-data-dir=/tmp/chrome_test_{id(options)}")
                options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
                options.add_experimental_option("useAutomationExtension", False)

                # ← NEW: Enable console logging for monitoring
                options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)

            elif browser_type.lower() == "firefox":
                options = webdriver.FirefoxOptions()
                options.set_preference("dom.webdriver.enabled", False)
                options.set_preference('useAutomationExtension', False)
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)

            elif browser_type.lower() == "edge":
                options = webdriver.EdgeOptions()
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)

                # ← NEW: Enable console logging for monitoring
                options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

                service = EdgeService(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=options)

            else:
                raise ValueError(f"Unsupported browser type: {browser_type}")

            driver.maximize_window()

            # Navigate to table URL
            Navigation.navigate(driver, api_setup.session_id, api_setup.table_num)

            drivers.append(driver)

        return drivers

    yield _create_browsers


    for driver in drivers:
        try:
            with allure.step("🔍 Automatic Console Safety Check"):
                monitor = ConsoleMonitor(driver)
                results = monitor.check_all()

                # Report to Allure
                monitor.report_to_allure()

                # If violations found, fail the test
                if results['has_issues']:
                    summary = f"⚠️ CONSOLE ISSUES DETECTED\n"
                    summary += f"Errors: {len(results['errors'])}\n"
                    summary += f"PII Violations: {len(results['pii_violations'])}\n"

                    allure.attach(
                        summary,
                        name="Console Issues Summary",
                        attachment_type=allure.attachment_type.TEXT
                    )

                    # Fail the test
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

    for driver in drivers:
        try:
            driver.quit()
        except Exception as e:
            print(f"Error closing browser: {str(e)}")