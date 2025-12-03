import requests
import json
import sys
import os

def close_table():
    SESSION_DATA_PATH = os.path.join(os.path.dirname(__file__), 'session_data.json')
    with open(SESSION_DATA_PATH, 'r') as f:
        session_data = json.load(f)

    session_id = session_data.get('session_id')
    client_id = session_data.get('client_id')
    transaction_guid = session_data.get('transaction_guid')
    subscription_key = session_data.get('subscription_key')
    property_id = session_data.get('property_id')
    rvc = session_data.get('revenue_center_id')
    table_number = session_data.get('table_number', 0)
    amount = session_data.get('amount_due_total', 0.0)
    url = session_data.get('base_url', 'https://digitalmwqa.azure-api.net') + '/v2/order/fullcart/checks/close'

    # Headers
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': subscription_key
    }

    payload = {
        "PropertyID": property_id,
        "RevenueCenterID": rvc,
        "ClientID": client_id,
        "SessionID": session_id,
        "TableNumber": table_number,
        "TransactionGuid": transaction_guid,
        "ServiceCharges": [],
        "Payments": [
            {
                "Amount": 500.00,
                "TenderType": "2001002"
            }
        ]
    }

    try:
        print("Closing table...")
        print(f"Using URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"Error: Failed to close table. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        response_data = response.json()
        print("Table closed successfully:")
        print(json.dumps(response_data, indent=4))
        return True

    except Exception as e:
        print(f"Error closing table: {str(e)}")
        return False


if __name__ == "__main__":
    success = close_table()
    if success:
        print("Table closed successfully!")
    else:
        print("Failed to close table.")
        sys.exit(1)