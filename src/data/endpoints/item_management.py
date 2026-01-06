"""
Item Management API
Manages menu item active/inactive status for integration testing
"""
import requests
import json
from src.utils.logger import Logger


class ItemManagementAPI:
    """API client for managing menu items (active/inactive status)"""

    def __init__(self):
        self.base_url = "https://digitalmwqa.azure-api.net/v2/internal/menu/management/menuItems"
        self.catalog_url = "https://digitalmwqa.azure-api.net/v2/catalog/menuitems/modifiergroups/byrevenuecenter"
        self.auth_url = "https://digitalmwqa.azure-api.net/v2/catalog/session/begin"

        self.management_headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": "595b23ca9ae84b119faf95ad990593ad"
        }

        self.catalog_headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": "bf837e849a7948308c103d08c3b731ce"
        }

        self.logger = Logger("ItemManagementAPI")
        self.session_id = None

    def authenticate(self, client_id="3289FE1A-A4CA-49DC-9CDF-C2831781E850",
                     username="internal", passkey="P455w0rd"):
        """Authenticate and get a fresh session ID"""
        payload = {
            "ClientID": client_id,
            "username": username,
            "passkey": passkey
        }

        try:
            response = requests.post(self.auth_url, json=payload, headers=self.catalog_headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            self.session_id = data.get("SessionID")

            if not self.session_id:
                raise ValueError("No SessionID returned from authentication")

            self.logger.info(f"Authentication successful. SessionID: {self.session_id}")
            return self.session_id

        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise

    def get_all_menu_data(self, property_id="33", revenue_center_id="810",
                          client_id="3289FE1A-A4CA-49DC-9CDF-C2831781E850"):
        """Get full menu data including items and categories"""
        if not self.session_id:
            self.logger.info("No session ID found, authenticating...")
            self.authenticate(client_id=client_id)

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "ClientID": client_id,  # ← ADD THIS
            "SessionID": self.session_id
        }

        try:
            response = requests.post(self.catalog_url, json=payload, headers=self.catalog_headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get menu data: {str(e)}")
            raise

    def get_category_with_least_items(self, menu_page, exclude_alcohol=True):
        """
        Find the category with the least number of active items.
        Only considers categories that are currently visible in UI.

        Returns:
            dict: {
                'category_id': str,
                'category_name': str,
                'items': list of item dicts,
                'item_count': int,
                'neighbor_id': str,
                'neighbor_name': str
            }
        """
        menu_data = self.get_all_menu_data()
        items_data = menu_data.get('Items', [])

        # Get visible categories from UI
        visible_ui = menu_page.get_all_category_buttons()
        visible_names = [cat['name'] for cat in visible_ui]

        # First, extract all unique categories from items
        all_categories = {}
        for item in items_data:
            item_categories = item.get('Categories', [])
            for category in item_categories:
                cat_id = category.get('ID')
                cat_name = category.get('Name')

                if cat_name and cat_id and cat_name not in all_categories:
                    all_categories[cat_name] = {
                        'id': cat_id,
                        'name': cat_name,
                        'active': category.get('Active', False),
                        'is_alcohol': category.get('IsAlcohol', False)
                    }

        # Filter to only visible, active, non-alcohol categories
        valid_categories = {}
        for cat_name, cat_info in all_categories.items():
            if cat_name in visible_names:
                if not cat_info['active']:
                    continue
                if exclude_alcohol and cat_info['is_alcohol']:
                    continue

                valid_categories[cat_info['id']] = {
                    'name': cat_name,
                    'items': []
                }

        # Now assign active items to categories
        for item in items_data:
            if not item.get('Active', False):
                continue
            if item.get('IsOutOfStock', False):
                continue

            item_cats = item.get('Categories', [])
            for item_cat in item_cats:
                cat_id = item_cat.get('ID')
                if cat_id in valid_categories:
                    valid_categories[cat_id]['items'].append({
                        'id': item['ID'],
                        'name': item['Name'],
                        'active': item.get('Active', False)
                    })

        # Find category with least items (but at least 1 item)
        categories_with_items = {k: v for k, v in valid_categories.items() if len(v['items']) > 0}

        if not categories_with_items:
            raise ValueError("No valid categories found with active items")

        min_cat_id = min(categories_with_items.keys(), key=lambda k: len(categories_with_items[k]['items']))
        min_cat = categories_with_items[min_cat_id]

        # Get neighbor category for verification
        category_index = visible_names.index(min_cat['name'])
        neighbor_id = None
        neighbor_name = None

        category_id_map = {cat['name']: cat['id'] for cat in visible_ui}

        if category_index > 0:
            neighbor_name = visible_names[category_index - 1]
            neighbor_id = category_id_map.get(neighbor_name)
        elif category_index < len(visible_names) - 1:
            neighbor_name = visible_names[category_index + 1]
            neighbor_id = category_id_map.get(neighbor_name)

        self.logger.info(f"Category with least items: '{min_cat['name']}' with {len(min_cat['items'])} items")

        return {
            'category_id': min_cat_id,
            'category_name': min_cat['name'],
            'items': min_cat['items'],
            'item_count': len(min_cat['items']),
            'neighbor_id': neighbor_id,
            'neighbor_name': neighbor_name
        }

    def make_items_inactive(self, item_ids, property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Make multiple items inactive via API.

        Args:
            item_ids: List of item IDs to make inactive
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            Response JSON
        """
        menu_items = []
        for item_id in item_ids:
            menu_items.append({
                "id": None,
                "MenuItemID": item_id,
                "Name": "",
                "Description": "",
                "Calories": "",
                "Image": None,
                "Active": False,
                "PreparationTime": 0,
                "Categories": "",
                "Upgrade": None,
                "Tags": []
            })

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "MenuItems": menu_items,
            "UserName": username
        }

        try:
            response = requests.post(self.base_url, headers=self.management_headers, json=payload, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Successfully made {len(item_ids)} items inactive")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to make items inactive: {str(e)}")
            raise

    def make_items_active(self, item_ids, property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Make multiple items active via API (restore).

        Args:
            item_ids: List of item IDs to make active
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            Response JSON
        """
        menu_items = []
        for item_id in item_ids:
            menu_items.append({
                "id": None,
                "MenuItemID": item_id,
                "Name": "",
                "Description": "",
                "Calories": "",
                "Image": None,
                "Active": True,
                "PreparationTime": 0,
                "Categories": "",
                "Upgrade": None,
                "Tags": []
            })

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "MenuItems": menu_items,
            "UserName": username
        }

        try:
            response = requests.post(self.base_url, headers=self.management_headers, json=payload, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Successfully restored {len(item_ids)} items to active")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to restore items to active: {str(e)}")
            raise

    def get_random_visible_item(self, menu_page, exclude_alcohol_categories=True):
        """
        Get a random item that's currently visible in the UI.

        Args:
            menu_page: MenuPage instance
            exclude_alcohol_categories: Exclude items from alcohol categories

        Returns:
            dict: {
                'item_id': str,
                'item_name': str,
                'category_id': str,
                'category_name': str,
                'price': float,
                'original_active': bool
            }
        """
        menu_data = self.get_all_menu_data()
        items_data = menu_data.get('Items', [])

        # Get visible categories from UI
        visible_ui = menu_page.get_all_category_buttons()
        visible_category_names = [cat['name'] for cat in visible_ui]

        # Build list of category IDs and their alcohol status
        category_info = {}
        for item in items_data:
            for category in item.get('Categories', []):
                cat_id = category.get('ID')
                cat_name = category.get('Name')
                if cat_name in visible_category_names:
                    category_info[cat_id] = {
                        'name': cat_name,
                        'is_alcohol': category.get('IsAlcohol', False)
                    }

        # Get all active, in-stock items from visible categories
        available_items = []
        for item in items_data:
            if not item.get('Active', False):
                continue
            if item.get('IsOutOfStock', False):
                continue

            # Check if item belongs to any visible category
            for category in item.get('Categories', []):
                cat_id = category.get('ID')
                if cat_id in category_info:
                    if exclude_alcohol_categories and category_info[cat_id]['is_alcohol']:
                        continue

                    available_items.append({
                        'item_id': item['ID'],
                        'item_name': item['Name'],
                        'category_id': cat_id,
                        'category_name': category_info[cat_id]['name'],
                        'price': item.get('Price', 0.0),
                        'original_active': item.get('Active', True)
                    })
                    break  # Only need one category per item

        if not available_items:
            raise ValueError("No visible items found")

        import random
        selected_item = random.choice(available_items)

        self.logger.info(
            f"Selected item: '{selected_item['item_name']}' "
            f"from category '{selected_item['category_name']}'"
        )

        return selected_item

    def get_item_with_categories(self, item_id):
        """
        Get full details of an item including all its categories.

        Args:
            item_id: Item ID to look up

        Returns:
            dict: Item details with categories
        """
        menu_data = self.get_all_menu_data()
        items_data = menu_data.get('Items', [])

        for item in items_data:
            if item['ID'] == item_id:
                return {
                    'item_id': item['ID'],
                    'item_name': item['Name'],
                    'active': item.get('Active', True),
                    'categories': item.get('Categories', []),
                    'price': item.get('Price', 0.0),
                    'description': item.get('Description', ''),
                    'calories': item.get('Calories', ''),
                    'image': item.get('ImageUrl'),
                    'preparation_time': item.get('PreparationTime', 0)
                }

        raise ValueError(f"Item {item_id} not found in menu data")

    def remove_item_from_all_categories(self, item_id, property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Remove item from all categories by setting Categories: [].
        Item will disappear from UI. If item is only item in a category, category will also disappear.

        Args:
            item_id: Item ID to remove from categories
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            Response JSON
        """
        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "MenuItems": [
                {
                    "id": None,
                    "MenuItemID": item_id,
                    "Name": "",
                    "Description": "",
                    "Calories": "",
                    "Image": None,
                    "Active": True,
                    "PreparationTime": 0,
                    "Categories": [],  # Empty = remove from all categories
                    "Upgrade": None,
                    "Tags": []
                }
            ],
            "UserName": username
        }

        try:
            response = requests.post(self.base_url, headers=self.management_headers, json=payload, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Successfully removed item {item_id} from all categories")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to remove item from categories: {str(e)}")
            raise

    def restore_item_to_categories(self, item_id, category_ids, property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Restore item to its original categories.

        Args:
            item_id: Item ID to restore
            category_ids: List of category IDs (strings) - NOT full category objects
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            Response JSON
        """
        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "MenuItems": [
                {
                    "id": None,
                    "MenuItemID": item_id,
                    "Name": "",
                    "Description": "",
                    "Calories": "",
                    "Image": None,
                    "Active": True,
                    "PreparationTime": 0,
                    "Categories": category_ids,  # Just list of ID strings
                    "Upgrade": None,
                    "Tags": []
                }
            ],
            "UserName": username
        }

        try:
            response = requests.post(self.base_url, headers=self.management_headers, json=payload, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Successfully restored item {item_id} to {len(category_ids)} categories")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to restore item to categories: {str(e)}")
            raise

    def get_item_full_details(self, item_id):
        """
        Get complete details for a specific item including all categories.

        Args:
            item_id: Item ID

        Returns:
            dict: Full item details from API
        """
        menu_data = self.get_all_menu_data()
        items_data = menu_data.get('Items', [])

        for item in items_data:
            if item['ID'] == item_id:
                return item

        raise ValueError(f"Item {item_id} not found in menu data")

    def remove_item_from_category(self, item_id, category_id_to_remove,
                                   property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Remove an item from a specific category.

        Args:
            item_id: Item ID
            category_id_to_remove: Category ID to remove item from
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            dict: {
                'removed_from': str (category name),
                'remaining_categories': list of category IDs,
                'response': API response
            }
        """
        # Get current item details
        item = self.get_item_full_details(item_id)
        current_categories = item.get('Categories', [])

        # Find the category being removed
        removed_category_name = None
        new_category_ids = []

        for cat in current_categories:
            cat_id = cat.get('ID')
            if cat_id == category_id_to_remove:
                removed_category_name = cat.get('Name')
            else:
                new_category_ids.append(cat_id)

        if not removed_category_name:
            raise ValueError(f"Category {category_id_to_remove} not found in item's categories")

        # Build comma-separated category IDs string
        categories_string = ",".join(new_category_ids) if new_category_ids else ""

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "MenuItems": [
                {
                    "id": None,
                    "MenuItemID": item_id,
                    "Name": item.get('Name', ''),
                    "Description": item.get('Description', ''),
                    "Calories": item.get('Calories', ''),
                    "Image": item.get('ImageUrl'),
                    "Active": item.get('Active', True),
                    "PreparationTime": item.get('PreparationTime', 0),
                    "Categories": categories_string,
                    "Upgrade": item.get('Upgrade'),
                    "Tags": item.get('Tags', [])
                }
            ],
            "UserName": username
        }

        try:
            response = requests.post(self.base_url, headers=self.management_headers, json=payload, timeout=30)
            response.raise_for_status()

            self.logger.info(
                f"Removed item '{item['Name']}' from category '{removed_category_name}'. "
                f"Remaining categories: {len(new_category_ids)}"
            )

            return {
                'removed_from': removed_category_name,
                'remaining_categories': new_category_ids,
                'response': response.json()
            }
        except Exception as e:
            self.logger.error(f"Failed to remove item from category: {str(e)}")
            raise

    def restore_item_to_category(self, item_id, category_id_to_add,
                                  property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Restore an item to a specific category.

        Args:
            item_id: Item ID
            category_id_to_add: Category ID to add item back to
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            Response JSON
        """
        # Get current item details
        item = self.get_item_full_details(item_id)
        current_categories = item.get('Categories', [])

        # Build list of category IDs including the one to add back
        category_ids = [cat.get('ID') for cat in current_categories]

        if category_id_to_add not in category_ids:
            category_ids.append(category_id_to_add)

        # Build comma-separated category IDs string
        categories_string = ",".join(category_ids)

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "MenuItems": [
                {
                    "id": None,
                    "MenuItemID": item_id,
                    "Name": item.get('Name', ''),
                    "Description": item.get('Description', ''),
                    "Calories": item.get('Calories', ''),
                    "Image": item.get('ImageUrl'),
                    "Active": item.get('Active', True),
                    "PreparationTime": item.get('PreparationTime', 0),
                    "Categories": categories_string,
                    "Upgrade": item.get('Upgrade'),
                    "Tags": item.get('Tags', [])
                }
            ],
            "UserName": username
        }

        try:
            response = requests.post(self.base_url, headers=self.management_headers, json=payload, timeout=30)
            response.raise_for_status()

            self.logger.info(f"Restored item '{item['Name']}' to category")

            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to restore item to category: {str(e)}")
            raise