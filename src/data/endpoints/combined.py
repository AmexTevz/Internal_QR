

import requests
import json
import os
import sys
from src.data.table_config import DEFAULT_TABLE_NUMBER

# =============================================================================
# MODULE-LEVEL API REGISTRY (safe for parallel execution)
# Each pytest-xdist worker is a separate process with its own memory
# =============================================================================
_current_api = None


def set_current_api(api):
    """
    Set the current API instance for this worker.
    Called by fixture after setup.
    """
    global _current_api
    _current_api = api


def get_current_api():
    """
    Get the current API instance for this worker.
    Used by standalone functions (get_check_details, close_table, etc.)

    Raises:
        RuntimeError: If API not initialized (fixture not called)
    """
    if _current_api is None:
        raise RuntimeError(
            "API not initialized. Make sure you're using the endpoint_setup fixture."
        )
    return _current_api


# =============================================================================
# API Configuration
# =============================================================================
employee = 90004
property_id = '33'
rvc = '810'
table_num = DEFAULT_TABLE_NUMBER


# =============================================================================
# Main API Class
# =============================================================================
class DigitalOrderAPI:
    def __init__(self, table_number=None):
        """
        Initialize DigitalOrderAPI.

        Args:
            table_number: Optional table number (1-100). If None, uses default table 10.
        """
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.api_key = 'bf837e849a7948308c103d08c3b731ce'
        self.client_id = '3289FE1A-A4CA-49DC-9CDF-C2831781E850'
        self.base_url = 'https://digitalmwqa.azure-api.net'

        # Session data stored in memory (no JSON files!)
        self.session_id = None
        self.transaction_guid = None
        self.transaction_number = None

        # Table configuration
        self.table_num = table_number if table_number is not None else table_num
        self.property_id = property_id
        self.revenue_center_id = rvc

        # Track if table is closed
        self.table_closed = False

    def setup_table(self):
        """
        Setup table: CREATE → if fail → GET

        Returns:
            dict: Table data including transaction_guid, session_id, etc.
            None: If setup fails
        """
        try:
            # Step 1: Authenticate
            auth_url = f'{self.base_url}/v2/catalog/session/begin'
            auth_headers = {
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': self.api_key
            }
            auth_payload = {
                'ClientID': self.client_id,
                'username': 'internal',
                'passkey': 'P455w0rd'
            }

            print(f"Authenticating with API for table {self.table_num}...")
            auth_response = requests.post(auth_url, headers=auth_headers, json=auth_payload)

            if auth_response.status_code != 200:
                print(f"Error: Failed to authenticate. Status code: {auth_response.status_code}")
                print(f"Response: {auth_response.text}")
                return None

            self.session_id = auth_response.json().get('SessionID')
            print(f"Successfully authenticated. Session ID: {self.session_id}")

            # Step 2: Try CREATE
            create_url = f'{self.base_url}/v2/order/fullcart/opencheck/create'
            create_headers = {
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': self.api_key
            }
            create_payload = {
                "PropertyID": self.property_id,
                "RevenueCenterID": self.revenue_center_id,
                "ClientID": self.client_id,
                "SessionID": self.session_id,
                "TableNumber": self.table_num,
                "OrderTypeIdRef": 1,
                "EmployeeNumber": employee,
                "GuestCheckRef": "",
                "cart": {
                    "items": []
                }
            }

            print(f"Attempting to CREATE check for table {self.table_num}...")
            create_response = requests.post(create_url, headers=create_headers, json=create_payload)

            # Step 3: Handle CREATE response
            if create_response.status_code == 200:
                # CREATE succeeded
                create_data = create_response.json()

                if create_data.get('Status') == 'SUCCESS' and create_data.get('Order'):
                    # Extract from Order object
                    self.transaction_guid = create_data['Order'].get('TransactionGuid')
                    self.transaction_number = create_data['Order'].get('TransactionNumber')

                    print(f"✓ CREATE successful for table {self.table_num}")
                    print(f"  TransactionGuid: {self.transaction_guid}")
                    print(f"  TransactionNumber: {self.transaction_number}")
                else:
                    print(f"Warning: CREATE returned 200 but Status is not SUCCESS")
                    print(f"Response: {json.dumps(create_data, indent=2)}")
                    # Fall through to GET
                    self.transaction_guid = None
            else:
                # CREATE failed - table might already be open
                print(f"CREATE failed with status {create_response.status_code}")
                print(f"Response: {create_response.text}")
                print(f"This is OK - table might already be open. Trying GET...")
                self.transaction_guid = None

            # Step 4: If CREATE didn't give us TransactionGuid, call GET
            if not self.transaction_guid:
                print(f"Calling GET to discover check for table {self.table_num}...")

                get_url = f'{self.base_url}/v2/order/fullcart/opencheck/get'
                get_headers = {
                    'Content-Type': 'application/json',
                    'Ocp-Apim-Subscription-Key': self.api_key
                }
                get_payload = {
                    "PropertyID": self.property_id,
                    "RevenueCenterID": self.revenue_center_id,
                    "ClientID": self.client_id,
                    "SessionID": self.session_id,
                    "TableNumber": self.table_num
                }

                get_response = requests.post(get_url, headers=get_headers, json=get_payload)

                if get_response.status_code != 200:
                    print(f"Error: GET failed. Status code: {get_response.status_code}")
                    print(f"Response: {get_response.text}")
                    return None

                get_data = get_response.json()

                if get_data.get('Status') != 'SUCCESS':
                    print(f"Error: GET returned non-SUCCESS status")
                    print(f"Response: {json.dumps(get_data, indent=2)}")
                    return None

                # Extract from GET response
                self.transaction_guid = get_data.get('TransactionGuid')
                self.transaction_number = get_data.get('TransactionNumber')

                print(f"✓ GET successful for table {self.table_num}")
                print(f"  TransactionGuid: {self.transaction_guid}")
                print(f"  TransactionNumber: {self.transaction_number}")

            # Step 5: Verify we have required data
            if not self.transaction_guid or not self.transaction_number:
                print("Error: Failed to obtain TransactionGuid or TransactionNumber")
                return None

            # Step 6: Return data dict (for fixture/test use)
            data = {
                "session_id": self.session_id,
                "transaction_guid": self.transaction_guid,
                "transaction_number": self.transaction_number,
                "table_number": self.table_num,
                "property_id": self.property_id,
                "revenue_center_id": self.revenue_center_id,
                "client_id": self.client_id,
                "subscription_key": self.api_key,
                "base_url": self.base_url
            }

            print(f"✓ Table {self.table_num} setup complete")
            print(f"  All future API calls will use TransactionGuid (fast!)")

            return data

        except Exception as e:
            print(f"Error in setup_table: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def get_check_details(self):
        """
        Get current check details using TransactionGuid (fast!).

        Returns:
            dict: Check details from API
            None: If call fails
        """
        if not self.transaction_guid:
            print("Error: TransactionGuid not set. Call setup_table() first.")
            return None

        try:
            url = f'{self.base_url}/v2/order/fullcart/opencheck/get'
            headers = {
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': self.api_key
            }
            payload = {
                "PropertyID": self.property_id,
                "RevenueCenterID": self.revenue_center_id,
                "ClientID": self.client_id,
                "SessionID": self.session_id,
                "TransactionGuid": self.transaction_guid  # ← Uses GUID (fast!)
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                print(f"Error: Failed to get check details. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return None

            data = response.json()

            if data.get('Status') != 'SUCCESS':
                print(f"Error: Get check details returned non-SUCCESS status")
                return None

            return data

        except Exception as e:
            print(f"Error in get_check_details: {str(e)}")
            return None

    def close_table(self):
        """
        Close the table using TransactionGuid with Payment object.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.transaction_guid:
            print("Error: TransactionGuid not set. Cannot close table.")
            return False

        if self.table_closed:
            print(f"Table {self.table_num} already closed, skipping")
            return True

        try:
            url = f'{self.base_url}/v2/order/fullcart/opencheck/close'
            headers = {
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': self.api_key
            }

            # Get current check details to calculate total amount
            print(f"Getting check details before closing table {self.table_num}...")
            check_data = self.get_check_details()
            if not check_data:
                print("Warning: Could not get check details, using default payment amount")
                total_amount = 10000.0  # Default large amount
            else:
                # Get total amount from check
                total_amount = check_data.get('AmountDueTotal', 0)
                if total_amount == 0:
                    total_amount = check_data.get('TotalPrice', 0)

                # If still 0, use large default
                if total_amount == 0:
                    total_amount = 10000.0

            payload = {
                "PropertyID": self.property_id,
                "RevenueCenterID": self.revenue_center_id,
                "ClientID": self.client_id,
                "SessionID": self.session_id,
                "TableNumber": self.table_num,
                "TransactionGuid": self.transaction_guid,
                "Tip": 0,
                "Payment": {
                    "Amount": total_amount,
                    "CardNumber": "33333",
                    "TenderType": "2001001",
                    "AuthCode": "67890",
                    "PaymentToken": "testTransaction"
                }
            }

            print(f"Closing table {self.table_num} (TransactionGuid: {self.transaction_guid})...")
            print(f"Payment amount: ${total_amount}")

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                print(f"Error: Failed to close table. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False

            data = response.json()

            if data.get('Status') != 'SUCCESS':
                print(f"Error: Close table returned non-SUCCESS status")
                print(f"Response: {json.dumps(data, indent=2)}")
                return False

            print(f"✓ Successfully closed table {self.table_num}")
            self.table_closed = True  # Mark as closed
            return True

        except Exception as e:
            print(f"Error in close_table: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


# If this script is run directly, execute the setup process
if __name__ == "__main__":
    api = DigitalOrderAPI()
    result = api.setup_table()
    if not result:
        sys.exit(1)