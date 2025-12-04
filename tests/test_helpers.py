"""
Test helper functions - Updated for no JSON files

These functions help with:
- Getting fresh check details
- Attaching data to Allure reports
- Utility functions for tests
"""

import json
import random
import allure
from src.data.endpoints.get_details import get_check_details
from src.data.endpoints.combined import get_current_api


def attach_check_details(name="Current Check Details"):
    """
    Attach current check details to Allure report.

    Gets fresh data from API and attaches as JSON to Allure report.
    This replaces the old attach_session_data_json() function.

    Args:
        name: Name for the Allure attachment

    Example:
        with allure.step("Verify order"):
            attach_check_details("Check Details After Order")
    """
    try:
        # Get fresh data from API
        data = get_check_details()

        if data:
            # Attach to Allure
            allure.attach(
                json.dumps(data, indent=2),
                name=name,
                attachment_type=allure.attachment_type.JSON
            )
            print(f"✓ Attached check details to Allure: {name}")
        else:
            print(f"✗ Failed to get check details for Allure attachment")

    except Exception as e:
        print(f"Error attaching check details: {str(e)}")


def attach_api_state(name="API State"):
    """
    Attach current API state to Allure report.

    Shows the internal state of the API instance (table, guid, session, etc.)
    Useful for debugging.

    Args:
        name: Name for the Allure attachment

    Example:
        with allure.step("Setup"):
            attach_api_state("Initial API State")
    """
    try:
        api = get_current_api()

        state = {
            'table_number': api.table_num,
            'transaction_guid': api.transaction_guid,
            'transaction_number': api.transaction_number,
            'session_id': api.session_id,
            'property_id': api.property_id,
            'revenue_center_id': api.revenue_center_id
        }

        allure.attach(
            json.dumps(state, indent=2),
            name=name,
            attachment_type=allure.attachment_type.JSON
        )
        print(f"✓ Attached API state to Allure: {name}")

    except Exception as e:
        print(f"Error attaching API state: {str(e)}")


def attach_note(note_text, name="Note"):
    """
    Attach a text note to Allure report.

    Args:
        note_text: Text content to attach
        name: Name for the attachment

    Example:
        attach_note("Customer placed 5 items", "Order Summary")
    """
    allure.attach(
        note_text,
        name=name,
        attachment_type=allure.attachment_type.TEXT
    )


def get_transaction_info():
    """
    Get transaction information from current API instance.

    Returns:
        dict: {
            'transaction_guid': '1803-794473459',
            'transaction_number': '1803',
            'table_number': 8
        }

    Example:
        info = get_transaction_info()
        print(f"Testing table {info['table_number']}")
    """
    try:
        api = get_current_api()
        return {
            'transaction_guid': api.transaction_guid,
            'transaction_number': api.transaction_number,
            'table_number': api.table_num
        }
    except Exception as e:
        print(f"Error getting transaction info: {str(e)}")
        return None


def menu_item_number():
    """
    Generate random number of menu items.

    Returns:
        int: Random number between 2 and 5

    Example:
        count = menu_item_number()
        menu_page.select_random_menu_items(count)
    """
    return random.randint(2, 5)


# =============================================================================
# LEGACY FUNCTIONS - Deprecated but kept for compatibility
# =============================================================================

def get_session_data(file_path=None):
    """
    DEPRECATED: Use get_check_details() instead.

    This function is kept for backward compatibility but now calls
    get_check_details() which gets fresh data from API.
    """
    print("Warning: get_session_data() is deprecated. Use get_check_details() instead.")
    return get_check_details()


def get_session_value(file_path=None, key=None, default=None):
    """
    DEPRECATED: Use get_check_details() and access keys directly.

    Example:
        # Old way:
        value = get_session_value(path, 'transaction_number')

        # New way:
        data = get_check_details()
        value = data['TransactionNumber']
    """
    print("Warning: get_session_value() is deprecated. Use get_check_details() instead.")

    if key:
        data = get_check_details()
        if data:
            # Try to map old key names to new ones
            key_mapping = {
                'transaction_number': 'TransactionNumber',
                'transaction_guid': 'TransactionGuid',
                'table_number': 'TableNumber',
                'subtotal': 'Subtotal',
                'tax': 'TotalTax',
                'amount_due_total': 'AmountDueTotal'
            }

            new_key = key_mapping.get(key, key)
            return data.get(new_key, default)

    return default


def attach_session_data_json(session_data_path=None, name="Session Data"):
    """
    DEPRECATED: Use attach_check_details() instead.

    This function is kept for backward compatibility but now calls
    attach_check_details() which gets fresh data from API.
    """
    print("Warning: attach_session_data_json() is deprecated. Use attach_check_details() instead.")
    attach_check_details(name)