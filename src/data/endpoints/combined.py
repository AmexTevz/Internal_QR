import requests
import json
import os
import sys
from src.utils.json_storage import JsonStorage
from src.data.table_config import DEFAULT_TABLE_NUMBER

employee = 90004
property_id = '33'
rvc = '810'
# Keep default table for backward compatibility
table_num = DEFAULT_TABLE_NUMBER


class DigitalOrderAPI:
    def __init__(self, table_number=None):
        """
        Initialize DigitalOrderAPI.

        Args:
            table_number: Optional table number (1-10). If None, uses default table 10.
        """
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.api_key = 'bf837e849a7948308c103d08c3b731ce'
        self.client_id = '3289FE1A-A4CA-49DC-9CDF-C2831781E850'
        self.base_url = 'https://digitalmwqa.azure-api.net'
        self.session_id = None
        self.transaction_guid = None
        # Use provided table_number or default to table 10
        self.table_num = table_number if table_number is not None else table_num
        self.property_id = property_id
        self.revenue_center_id = rvc
        self.json_storage = JsonStorage(os.path.join(self.script_dir, 'session_data.json'))

    def setup_table(self):
        try:
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

            # Step 2: Create check
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

            print(f"Creating check for table {self.table_num}...")
            create_response = requests.post(create_url, headers=create_headers, json=create_payload)

            # Step 3: Get table status and transaction data
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
                print(f"Error: Failed to verify table open status. Status code: {get_response.status_code}")
                print(f"Response: {get_response.text}")
                return None

            get_data = get_response.json()
            if get_data.get('Status') != 'SUCCESS':
                print("Error: Table open verification failed. Status is not SUCCESS.")
                print(json.dumps(get_data, indent=4))
                return None

            # Extract all necessary data with proper error handling
            subtotal = get_data.get('Subtotal', 0.0)  # Default to 0.0 if not found
            self.transaction_guid = get_data.get('TransactionGuid')
            transaction_number = get_data.get('TransactionNumber')
            amount_due_total = get_data.get('AmountDueTotal', 0.0)  # Default to 0.0 if not found
            tax = get_data.get('TotalTax', 0.0)
            auto_service_charge = get_data.get('AutoServiceChargeTotal', 0.0)

            if not self.transaction_guid or not transaction_number:
                print("Error: TransactionGuid or TransactionNumber not found in verification response.")
                print(json.dumps(get_data, indent=4))
                return None

            print(f"Transaction GUID: {self.transaction_guid}")
            print(f"Transaction Number: {transaction_number}")
            print(f"Amount Due Total: {amount_due_total}")
            print(f"Subtotal: {subtotal}")

            # Save all data to JSON file
            data = {
                "session_id": self.session_id,
                "transaction_guid": self.transaction_guid,
                "transaction_number": transaction_number,
                "amount_due_total": amount_due_total,
                "subtotal": subtotal,
                "tax": tax,
                "auto_service_charge": auto_service_charge,
                "table_number": self.table_num,
                "property_id": self.property_id,
                "revenue_center_id": self.revenue_center_id,
                "client_id": self.client_id,
                "subscription_key": self.api_key,
                "base_url": self.base_url
            }
            self.json_storage.save_data(data)
            print(f"All data saved to JSON file for table {self.table_num}")

            return data

        except Exception as e:
            print(f"Error in setup_table: {str(e)}")
            return None


# If this script is run directly, execute the setup process
if __name__ == "__main__":
    api = DigitalOrderAPI()

    # Run the setup process
    result = api.setup_table()
    if not result:
        sys.exit(1)