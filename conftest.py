# import pytest
# from selenium import webdriver
# from selenium.webdriver.edge.service import Service as EdgeService
# from selenium.webdriver.edge.options import Options as EdgeOptions
# from selenium.webdriver.chrome.service import Service as ChromeService
# from selenium.webdriver.chrome.options import Options as ChromeOptions
# from selenium.webdriver.firefox.service import Service as FirefoxService
# from selenium.webdriver.firefox.options import Options as FirefoxOptions
# from webdriver_manager.microsoft import EdgeChromiumDriverManager
# from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.firefox import GeckoDriverManager
# from src.data.endpoints.combined import DigitalOrderAPI
# from src.utils.navigation import Navigation
# from src.data.table_config import DEFAULT_TABLE_NUMBER
#
#
# @pytest.fixture(scope="function")
# def table(request):
#     """
#     Fixture that provides table number.
#     Can be overridden by test function parameter or parametrize.
#
#     Usage:
#         def test_something(..., table=5):  # Uses table 5
#
#         @pytest.mark.parametrize("table", range(5, 11))
#         def test_something(..., table):  # Uses tables 5-10
#     """
#     # If parametrized, use that value
#     if hasattr(request, 'param'):
#         return request.param
#
#     # Otherwise, look for default value in test function
#     if hasattr(request, 'function'):
#         import inspect
#         sig = inspect.signature(request.function)
#         if 'table' in sig.parameters:
#             default_val = sig.parameters['table'].default
#             if default_val != inspect.Parameter.empty:
#                 return default_val
#
#     # Final fallback to default table
#     return DEFAULT_TABLE_NUMBER
#
#
# @pytest.fixture(scope="session")
# def api_setup():
#     """Session-scoped fixture for API setup."""
#     api = DigitalOrderAPI()
#     return api
#
#
# @pytest.fixture(scope="function")
# def endpoint_setup(table):
#     """
#     Function-scoped fixture that sets up table.
#     Automatically uses table number from 'table' fixture.
#     """
#     # Create API instance with specified table number
#     api = DigitalOrderAPI(table_number=table)
#     api_data = api.setup_table()
#
#     if not api_data:
#         pytest.fail(f"Failed to setup table {api.table_num}")
#
#     print(f"\n{'=' * 60}")
#     print(f"TEST SETUP: Using Table {api.table_num}")
#     print(f"{'=' * 60}\n")
#
#     return api, api_data
#
#
# @pytest.fixture
# def browser_factory(endpoint_setup):
#     """
#     Browser factory fixture that creates browser instances.
#     Automatically uses the table number from endpoint_setup.
#     """
#     api_setup, api_data = endpoint_setup
#     drivers = []
#
#     def _make_browser(browser_name):
#         if browser_name == "edge":
#             options = EdgeOptions()
#             # options.add_argument("--headless")
#             options.add_argument("--inprivate")
#             options.add_argument("--window-size=1920,1080")
#             options.add_argument("--disable-notifications")
#             options.add_argument("--disable-popup-blocking")
#             options.add_argument("--disable-infobars")
#             options.add_argument("--disable-extensions")
#             options.add_argument("--disable-gpu")
#             options.add_argument("--no-sandbox")
#             options.add_argument("--disable-dev-shm-usage")
#             options.add_argument("--disable-blink-features=AutomationControlled")
#             options.add_argument("--log-level=3")
#             options.add_argument("--silent")
#             options.add_argument("--disable-logging")
#             options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
#             options.add_experimental_option("useAutomationExtension", False)
#             driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
#         elif browser_name == "chrome":
#             options = ChromeOptions()
#             # options.add_argument("--headless")
#             options.add_argument("--window-size=1920,1080")
#             options.add_argument("--incognito")
#             options.add_argument("--disable-notifications")
#             options.add_argument("--disable-popup-blocking")
#             options.add_argument("--disable-infobars")
#             options.add_argument("--disable-extensions")
#             options.add_argument("--disable-gpu")
#             options.add_argument("--no-sandbox")
#             options.add_argument("--disable-dev-shm-usage")
#             options.add_argument("--disable-blink-features=AutomationControlled")
#             options.add_argument("--log-level=3")
#             options.add_argument("--silent")
#             options.add_argument("--disable-logging")
#             options.add_argument(f"--user-data-dir=/tmp/chrome_test_{id(options)}")
#             options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
#             options.add_experimental_option("useAutomationExtension", False)
#             driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
#         elif browser_name == "firefox":
#             options = FirefoxOptions()
#             # options.add_argument("--headless")
#             options.add_argument("--private-window")
#
#             # Disable notifications and popups
#             options.set_preference("dom.webnotifications.enabled", False)
#             options.set_preference("dom.push.enabled", False)
#             options.set_preference("dom.popup_allowed_events", "")
#
#             # Disable automation detection
#             options.set_preference("dom.webdriver.enabled", False)
#             options.set_preference("useAutomationExtension", False)
#             options.set_preference("marionette.logging", False)
#
#             # Performance optimizations
#             options.set_preference("browser.cache.disk.enable", False)
#             options.set_preference("browser.cache.memory.enable", False)
#             options.set_preference("browser.cache.offline.enable", False)
#             options.set_preference("network.http.use-cache", False)
#
#             # Disable logging
#             options.add_argument("--log-level=3")
#             options.set_preference("devtools.console.stdout.chrome", False)
#             options.set_preference("browser.dom.window.dump.enabled", False)
#
#             # Additional Firefox-specific optimizations
#             options.set_preference("media.volume_scale", "0.0")
#             options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)
#             options.set_preference("browser.safebrowsing.malware.enabled", False)
#             options.set_preference("browser.safebrowsing.phishing.enabled", False)
#
#             driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
#         else:
#             raise ValueError("Unknown browser: " + browser_name)
#
#         driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
#
#         # Navigate to the correct table
#         Navigation.navigate(driver, api_data["session_id"], api_setup.table_num)
#         drivers.append(driver)
#         return driver
#
#     def get_drivers(*browser_names):
#         return [_make_browser(name) for name in browser_names]
#
#     yield get_drivers
#
#     # Teardown: close all drivers that were created
#     for drv in drivers:
#         try:
#             drv.quit()
#         except Exception as e:
#             print(f"Error closing driver: {str(e)}")

import pytest
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
import inspect


@pytest.fixture(scope="function")
def table(request):
    """
    Table number fixture - supports parametrization and defaults.

    Usage:
        @pytest.mark.parametrize("table", [5, 6, 7])
        def test_foo(table): ...

        Or with default:
        def test_foo(table=10): ...
    """
    # If parametrized, use that value
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
    """
    Setup API endpoint for the specified table.

    This fixture:
    1. Creates API instance for the table
    2. Calls setup_table() (CREATE → if fail → GET)
    3. Registers API instance for this worker (set_current_api)
    4. Yields API instance
    5. Closes table on teardown

    Returns:
        DigitalOrderAPI: API instance with transaction_guid, session_id, etc.
    """
    print(f"\n{'=' * 60}")
    print(f"TEST SETUP: Initializing table {table}")
    print(f"{'=' * 60}")

    # Create API instance
    api = DigitalOrderAPI(table_number=table)

    # Setup table (CREATE → if fail → GET)
    api_data = api.setup_table()

    if not api_data:
        pytest.fail(f"Failed to setup table {table}")

    # Register this API instance for the current worker
    # This allows get_check_details() and close_table() to work without parameters
    set_current_api(api)

    print(f"✓ API registered for worker - standalone functions will work")
    print(f"  Table: {api.table_num}")
    print(f"  TransactionGuid: {api.transaction_guid}")
    print(f"  Session ID: {api.session_id}")
    print(f"{'=' * 60}\n")

    # Yield API instance to test
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
    """
    Browser factory fixture that creates browsers and navigates to table URL.

    Args:
        endpoint_setup: API instance from endpoint_setup fixture

    Usage:
        [chrome] = browser_factory("chrome")
        [chrome, firefox] = browser_factory("chrome", "firefox")
    """
    drivers = []
    api_setup = endpoint_setup  # API instance

    def _create_browsers(*browser_types):
        for browser_type in browser_types:
            if browser_type.lower() == "chrome":
                # YOUR ORIGINAL CHROME OPTIONS - ALL PRESERVED!
                options = ChromeOptions()
                # options.add_argument("--headless")  # ← Keep commented as you had it
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

    # Teardown: Close all browsers
    for driver in drivers:
        try:
            driver.quit()
        except Exception as e:
            print(f"Error closing browser: {str(e)}")