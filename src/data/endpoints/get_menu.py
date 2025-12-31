
import requests
import json
from src.data.endpoints.combined import get_current_api


def get_full_menu():

    try:

        api = get_current_api()

        url = f'{api.base_url}/v2/catalog/menuitems/modifiergroups/byrevenuecenter'

        # Prepare headers with subscription key
        headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': api.api_key
        }


        payload = {
            "PropertyID": api.property_id,
            "RevenueCenterID": api.revenue_center_id,
            "ClientID": api.client_id,
            "SessionID": api.session_id
        }

        print(f"Fetching full menu for Property: {api.property_id}, RevenueCenterID: {api.revenue_center_id}...")

        response = requests.post(url, headers=headers, json=payload)


        if response.status_code != 200:
            print(f"✗ Failed to get menu. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None

        data = response.json()

        if 'Items' not in data:
            print(f"✗ Unexpected response structure - 'Items' field not found")
            print(f"Response keys: {data.keys()}")
            return None

        # Count categories and items for logging
        items_count = len(data.get('Items', []))
        categories = set()

        for item in data.get('Items', []):
            for category in item.get('Categories', []):
                categories.add(category.get('Name'))

        print(f"✓ Successfully retrieved menu:")
        print(f"  - Total Items: {items_count}")
        print(f"  - Unique Categories: {len(categories)}")

        return data

    except RuntimeError as e:
        # API not initialized yet (called before fixture)
        print(f"✗ API not initialized: {str(e)}")
        print("  Make sure you're using the endpoint_setup fixture")
        return None

    except Exception as e:
        print(f"✗ Error in get_full_menu: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_menu_categories():
    """
    Extract and return just the categories from the full menu.

    This is a convenience function that fetches the full menu and extracts
    unique categories with their properties.

    Returns:
        list: List of unique category dictionaries with properties:
            - ID: Category unique identifier
            - Name: Category name
            - DisplayOrder: Order in which category appears
            - IsAlcohol: Boolean indicating if category contains alcohol
            - Active: Boolean indicating if category is active
            - Other category properties
        None: If the request fails
    """
    try:
        # Get full menu first
        menu_data = get_full_menu()

        if not menu_data:
            return None

        # Extract unique categories
        categories_dict = {}

        for item in menu_data.get('Items', []):
            for category in item.get('Categories', []):
                category_id = category.get('ID')
                if category_id and category_id not in categories_dict:
                    categories_dict[category_id] = category

        # Convert to list and sort by DisplayOrder
        categories_list = sorted(
            categories_dict.values(),
            key=lambda x: x.get('DisplayOrder', 999)
        )

        print(f"✓ Extracted {len(categories_list)} unique categories")

        return categories_list

    except Exception as e:
        print(f"✗ Error in get_menu_categories: {str(e)}")
        return None


def get_items_by_category(category_name):
    """
    Get all menu items that belong to a specific category.

    Args:
        category_name (str): Name of the category to filter by

    Returns:
        list: List of items in the specified category
        None: If the request fails
    """
    try:
        # Get full menu first
        menu_data = get_full_menu()

        if not menu_data:
            return None

        # Filter items by category name
        items_in_category = []

        for item in menu_data.get('Items', []):
            for category in item.get('Categories', []):
                if category.get('Name', '').lower() == category_name.lower():
                    items_in_category.append(item)
                    break  # Don't add the same item twice if it appears in multiple matching categories

        print(f"✓ Found {len(items_in_category)} items in category '{category_name}'")

        return items_in_category

    except Exception as e:
        print(f"✗ Error in get_items_by_category: {str(e)}")
        return None


def get_active_categories():
    """
    Get only active categories from the menu.

    Returns:
        list: List of active category dictionaries
        None: If the request fails
    """
    try:
        categories = get_menu_categories()

        if not categories:
            return None

        # Filter for active categories only
        active_categories = [cat for cat in categories if cat.get('Active', False)]

        print(f"✓ Found {len(active_categories)} active categories out of {len(categories)} total")

        return active_categories

    except Exception as e:
        print(f"✗ Error in get_active_categories: {str(e)}")
        return None


# Backward compatibility function
def get_menu_legacy():
    """
    Legacy function name for backward compatibility.
    Use get_full_menu() instead.
    """
    return get_full_menu()


if __name__ == "__main__":
    """
    Direct execution for testing/debugging.
    Note: This requires a valid session setup first via combined.py
    """
    print("=" * 60)
    print("MENU ENDPOINT TEST")
    print("=" * 60)

    # This will fail if run directly without proper setup
    # In actual usage, the endpoint_setup fixture handles initialization
    try:
        menu = get_full_menu()
        if menu:
            print("\n✓ Menu retrieved successfully!")
            print(f"\nFirst item sample:")
            print(json.dumps(menu['Items'][0], indent=2))
        else:
            print("\n✗ Failed to retrieve menu")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nNote: This script requires proper API initialization via endpoint_setup fixture")