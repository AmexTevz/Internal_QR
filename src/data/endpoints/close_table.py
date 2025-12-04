# import requests
# import json
# import sys
# import os
#
# def close_table():
#     SESSION_DATA_PATH = os.path.join(os.path.dirname(__file__), 'session_data.json')
#     with open(SESSION_DATA_PATH, 'r') as f:
#         session_data = json.load(f)
#
#     session_id = session_data.get('session_id')
#     client_id = session_data.get('client_id')
#     transaction_guid = session_data.get('transaction_guid')
#     subscription_key = session_data.get('subscription_key')
#     property_id = session_data.get('property_id')
#     rvc = session_data.get('revenue_center_id')
#     table_number = session_data.get('table_number', 0)
#     amount = session_data.get('amount_due_total', 0.0)
#     url = session_data.get('base_url', 'https://digitalmwqa.azure-api.net') + '/v2/order/fullcart/checks/close'
#
#     # Headers
#     headers = {
#         'Content-Type': 'application/json',
#         'Ocp-Apim-Subscription-Key': subscription_key
#     }
#
#     payload = {
#         "PropertyID": property_id,
#         "RevenueCenterID": rvc,
#         "ClientID": client_id,
#         "SessionID": session_id,
#         "TableNumber": table_number,
#         "TransactionGuid": transaction_guid,
#         "ServiceCharges": [],
#         "Payments": [
#             {
#                 "Amount": 500.00,
#                 "TenderType": "2001002"
#             }
#         ]
#     }
#
#     try:
#         print("Closing table...")
#         print(f"Using URL: {url}")
#         print(f"Payload: {json.dumps(payload, indent=2)}")
#
#         response = requests.post(url, headers=headers, json=payload)
#
#         if response.status_code != 200:
#             print(f"Error: Failed to close table. Status code: {response.status_code}")
#             print(f"Response: {response.text}")
#             return False
#
#         response_data = response.json()
#         print("Table closed successfully:")
#         print(json.dumps(response_data, indent=4))
#         return True
#
#     except Exception as e:
#         print(f"Error closing table: {str(e)}")
#         return False
#
#
# if __name__ == "__main__":
#     success = close_table()
#     if success:
#         print("Table closed successfully!")
#     else:
#         print("Failed to close table.")
#         sys.exit(1)

"""
Close table - Uses current API instance (parallel-safe, no JSON files)

Usage:
    from src.data.endpoints.close_table import close_table

    # In tests or fixtures - just call it!
    close_table()

    # Uses TransactionGuid automatically (fast!)
"""

from src.data.endpoints.combined import get_current_api


def close_table():
    """
    Close the current table/check.
    Safe to call multiple times - won't error if already closed.

    Automatically uses the correct API instance for this worker/table.
    Uses TransactionGuid for fast operation (not TableNumber).

    Returns:
        bool: True if successful, False otherwise, None if API not initialized

    Example:
        # In test teardown:
        success = close_table()
        if success:
            print("Table closed")

        # In fixture:
        yield api
        close_table()  # Cleanup
    """
    try:
        # Get the API instance for this worker
        api = get_current_api()

        # Check if already closed
        if api.table_closed:
            print(f"Table {api.table_num} already closed, skipping")
            return True

        # Call the API method (uses TransactionGuid internally)
        success = api.close_table()

        if success:
            print(f"✓ close_table: Successfully closed table {api.table_num}")
            return True
        else:
            print(f"✗ close_table: Failed to close table {api.table_num}")
            return False

    except RuntimeError:
        # API not initialized yet (called at import time or before fixture)
        # This is OK - just return None silently
        return None
    except Exception as e:
        print(f"Error in close_table: {str(e)}")
        import traceback
        traceback.print_exc()
        return False