# # check_order.py
# import requests
# import json
# import os
# import logging
#
# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# def get_check_details():
#     """Function to get check details and update session data"""
#     logger.info("Starting get_check_details() function")
#
#     SESSION_DATA_PATH = os.path.join(os.path.dirname(__file__), 'session_data.json')
#     logger.info(f"Loading session data from: {SESSION_DATA_PATH}")
#
#     try:
#         with open(SESSION_DATA_PATH, 'r') as f:
#             session_data = json.load(f)
#         logger.info("Successfully loaded session data")
#     except Exception as e:
#         logger.error(f"Failed to load session data: {str(e)}")
#         return False, f"Failed to load session data: {str(e)}"
#
#     session_id = session_data.get('session_id')
#     client_id = session_data.get('client_id')
#     subscription_key = session_data.get('subscription_key')
#     property_id = session_data.get('property_id')
#     rvc = session_data.get('revenue_center_id')
#     table_number = session_data.get('table_number', 0)
#     base_url = session_data.get('base_url', 'https://digitalmwqa.azure-api.net')
#
#     logger.info(f"Using session_id: {session_id}")
#     logger.info(f"Using table_number: {table_number}")
#
#     url = base_url + '/v2/order/fullcart/opencheck/get'
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
#         "TableNumber": table_number
#     }
#
#     logger.info(f"Making API request to: {url}")
#     logger.info(f"Payload: {json.dumps(payload, indent=2)}")
#
#     try:
#         response = requests.post(url, headers=headers, json=payload, timeout=30)
#         logger.info(f"API response status code: {response.status_code}")
#
#         if response.status_code != 200:
#             logger.error(f"API request failed with status {response.status_code}: {response.text}")
#             return False, f"Error: Status code {response.status_code}: {response.text}"
#
#         data = response.json()
#         logger.info(f"API response data: {json.dumps(data, indent=2)}")
#
#         # Update session_data.json
#         original_subtotal = session_data.get('subtotal', 0.0)
#         original_amount_due = session_data.get('amount_due_total', 0.0)
#
#         if 'Subtotal' in data:
#             session_data['subtotal'] = data['Subtotal']
#             logger.info(f"Updated subtotal from {original_subtotal} to {data['Subtotal']}")
#         if 'AmountDueTotal' in data:
#             session_data['amount_due_total'] = data['AmountDueTotal']
#             logger.info(f"Updated amount_due_total from {original_amount_due} to {data['AmountDueTotal']}")
#         if 'TransactionGuid' in data:
#             session_data['transaction_guid'] = data['TransactionGuid']
#             logger.info(f"Updated transaction_guid to {data['TransactionGuid']}")
#         if 'TransactionNumber' in data:
#             session_data['transaction_number'] = data['TransactionNumber']
#             logger.info(f"Updated transaction_number to {data['TransactionNumber']}")
#         if 'TotalTax' in data:
#             session_data['tax'] = data['TotalTax']
#             logger.info(f"Updated tax to {data['TotalTax']}")
#         if 'AutoServiceChargeTotal' in data:
#             session_data['auto_service_charge'] = data['AutoServiceChargeTotal']
#             logger.info(f"Updated auto_service_charge to {data['AutoServiceChargeTotal']}")
#
#         logger.info(f"Writing updated session data to {SESSION_DATA_PATH}")
#         with open(SESSION_DATA_PATH, 'w') as f:
#             json.dump(session_data, f, indent=2)
#         logger.info("Successfully updated session_data.json")
#
#         return True, data
#     except Exception as e:
#         logger.error(f"Exception in get_check_details: {str(e)}")
#         return False, f"Error: {str(e)}"
#
#
# def force_refresh_session():
#     """Force refresh the session by calling the API setup again"""
#     logger.info("Force refreshing session data...")
#     try:
#         from src.data.endpoints.combined import DigitalOrderAPI
#         api = DigitalOrderAPI()
#         result = api.setup_table()
#         if result:
#             logger.info("Successfully refreshed session data")
#             return True, result
#         else:
#             logger.error("Failed to refresh session data")
#             return False, "Failed to refresh session data"
#     except Exception as e:
#         logger.error(f"Exception while refreshing session: {str(e)}")
#         return False, f"Exception while refreshing session: {str(e)}"
#
#
#
#
#
# if __name__ == "__main__":
#     print("Getting latest check/order details...")
#     success, result = get_check_details()
#     if success:
#         print("Response:")
#         print(json.dumps(result, indent=2))
#         print("session_data.json updated with latest details.")
#     else:
#         print(result)

"""
Get check details - Uses current API instance (parallel-safe, no JSON files)

Usage:
    from src.data.endpoints.get_details import get_check_details

    # In pages or tests - just call it!
    data = get_check_details()

    # Returns fresh data from API using TransactionGuid (fast!)
"""

import requests
import json
from src.data.endpoints.combined import get_current_api


def get_check_details():
    """
    Get current check details for the active table.

    Automatically uses the correct API instance for this worker/table.
    Uses TransactionGuid for fast lookups (not TableNumber).

    Returns:
        dict: Check details from API with keys like:
            - TransactionGuid
            - TransactionNumber
            - TableNumber
            - TotalPrice
            - TotalTax
            - AmountDueTotal
            - Subtotal
            - Items
            - etc.
        None: If call fails OR if called before endpoint_setup fixture runs

    Example:
        # In MenuPage:
        data = get_check_details()
        if data:  # Check if API is ready
            transaction_number = data['TransactionNumber']
            total = data['TotalPrice']

        # In test:
        data = get_check_details()
        assert data is not None
        assert data['Status'] == 'SUCCESS'
    """
    try:
        # Get the API instance for this worker
        api = get_current_api()

        # Call the API method (uses TransactionGuid internally)
        data = api.get_check_details()

        if data:
            print(f"✓ get_check_details: Retrieved data for table {api.table_num}")
            print(f"  TransactionGuid: {api.transaction_guid}")
            return data
        else:
            print(f"✗ get_check_details: Failed to retrieve data")
            return None

    except RuntimeError:
        # API not initialized yet (called at import time or before fixture)
        # This is OK - just return None silently
        return None
    except Exception as e:
        print(f"Error in get_check_details: {str(e)}")
        return None


# Backward compatibility
def get_check_details_legacy():
    """
    Legacy function name for backward compatibility.
    Use get_check_details() instead.
    """
    return get_check_details()