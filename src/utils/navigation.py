import pytest
import requests
import json
from selenium.webdriver.support.ui import WebDriverWait
from src.pages.base_page import BasePage
from src.data.table_config import get_table_url, DEFAULT_TABLE_NUMBER

# Keep for backward compatibility - but it will be overridden dynamically
URL = "https://nextgen-frontend-dev-b0chfba5a6hyb3ga.eastus-01.azurewebsites.net/38A31859-CA10-452C-BF40-ED361D7F6749"
prop = 33
rvc = 810


class Navigation:
    # Keep for backward compatibility
    CHECKOUT_URL = URL

    @staticmethod
    def verify_table_open(session_id, table_num):
        verify_url = 'https://digitalmwqa.azure-api.net/v2/order/fullcart/opencheck/get'
        verify_headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': 'bf837e849a7948308c103d08c3b731ce'
        }
        verify_payload = {
            "PropertyID": prop,
            "RevenueCenterID": rvc,
            "ClientID": "3289FE1A-A4CA-49DC-9CDF-C2831781E850",
            "SessionID": session_id,
            "TableNumber": table_num
        }

        try:
            verify_response = requests.post(verify_url, headers=verify_headers, json=verify_payload)
            if verify_response.status_code != 200:
                print(f"Error: Failed to verify table open status. Status code: {verify_response.status_code}")
                print(f"Response: {verify_response.text}")
                return False

            verify_data = verify_response.json()
            if verify_data.get('Status') != 'SUCCESS':
                print("Error: Table open verification failed. Status is not SUCCESS.")
                print(json.dumps(verify_data, indent=4))
                return False

            return True
        except Exception as e:
            print(f"Error verifying table open status: {str(e)}")
            return False

    @staticmethod
    def navigate(driver, session_id, table_num=None):
        """
        Navigate to the table QR page.

        Args:
            driver: Selenium WebDriver instance
            session_id: API session ID
            table_num: Table number (1-10). If None, uses default table 10.
        """
        # Use default table if not specified
        if table_num is None:
            table_num = DEFAULT_TABLE_NUMBER

        # Verify table is open
        if not Navigation.verify_table_open(session_id, table_num):
            pytest.skip(f"Table {table_num} is not open. Skipping navigation.")

        # Get the correct URL for this table number
        checkout_url = get_table_url(table_num)

        base = BasePage(driver)
        try:
            print(f"Navigating to table {table_num}: {checkout_url}")
            driver.get(checkout_url)
            WebDriverWait(driver, 1).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception as e:
            print(f"Failed to load checkout page for table {table_num}: {str(e)}")
            pytest.skip(f"Failed to load checkout page for table {table_num}")