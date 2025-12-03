import requests
import json
import os
import sys

property_id = 33
rvc = 810
item = "811705004-1"


def add_items_to_check(session_id=None, transaction_guid=None):

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # If session_id is not provided, try to read it from file
    if session_id is None:
        session_id_path = os.path.join(script_dir, 'session_data.json')
        try:
            with open(session_id_path, 'r') as f:
                session_data = json.load(f)
                session_id = session_data.get('session_id')
                transaction_guid = session_data.get('transaction_guid')
                table_num = session_data.get('table_number')
        except FileNotFoundError:
            return False

    # API endpoint
    url = 'https://digitalmwqa.azure-api.net/v2/order/fullcart/opencheck/add'

    # Headers
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': 'bf837e849a7948308c103d08c3b731ce'
    }

    # Request payload
    payload = {
        "PropertyID": property_id,
        "RevenueCenterID": rvc,
        "ClientID": "3289FE1A-A4CA-49DC-9CDF-C2831781E850",
        "SessionID": session_id,
        "TableNumber": table_num,
        "TransactionGuid": transaction_guid,
        "cart": {
            "items": [
                {
                    "ID": item,
                    "Price": 14.99,
                    "Quantity": 1,
                    "FreeText": None,
                    "Name": "Just Bacon Burger",
                    "Modifiers": [
                    ]
                }
            ]
        }
    }

    try:
        print("Adding items to check...")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"Error: Failed to add items. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        response_data = response.json()
        print("Items added successfully:")
        print(json.dumps(response_data, indent=4))
        return True

    except Exception as e:
        print(f"Error adding items: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_items_to_check()
    if success:
        print("Items added successfully!")
    else:
        print("Failed to add items.")
        sys.exit(1)