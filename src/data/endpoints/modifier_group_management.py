"""
ModifierGroup Management API
Manages modifier group required/optional status for integration testing
"""
import requests
import json
from src.utils.logger import Logger


class ModifierGroupManagementAPI:
    """API client for managing modifier groups (required/optional status)"""

    def __init__(self):
        self.management_url = "https://digitalmwqa.azure-api.net/v2/internal/menu/management/ModifierGroups"
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

        self.session_id = None
        self.logger = Logger("ModifierGroupAPI")

    def authenticate(self, client_id="3289FE1A-A4CA-49DC-9CDF-C2831781E850",
                     username="internal", passkey="P455w0rd"):
        """Authenticate and get session ID"""
        if self.session_id:
            return self.session_id

        payload = {
            "ClientID": client_id,
            "username": username,
            "passkey": passkey
        }

        try:
            self.logger.info("Authenticating...")
            response = requests.post(self.auth_url, json=payload, headers=self.catalog_headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            self.session_id = data.get("SessionID")

            if not self.session_id:
                raise ValueError("No SessionID returned")

            self.logger.info(f"Authentication successful. SessionID: {self.session_id}")
            return self.session_id

        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise

    def get_all_menu_data(self, property_id="33", revenue_center_id="810",
                          client_id="3289FE1A-A4CA-49DC-9CDF-C2831781E850"):
        """Get full menu data including modifier groups"""
        if not self.session_id:
            self.authenticate(client_id=client_id)

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "ClientID": client_id,
            "SessionID": self.session_id
        }

        try:
            response = requests.post(self.catalog_url, json=payload, headers=self.catalog_headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get menu data: {str(e)}")
            raise

    def get_item_with_optional_modifier(self, menu_page, exclude_alcohol_categories=True):
        """
        Find an item with at least one OPTIONAL modifier group.
        Randomly selects from available items.

        Returns:
            dict: {
                'item_id': str,
                'item_name': str,
                'category_id': str,
                'category_name': str,
                'modifier_group': {
                    'id': str,
                    'name': str,
                    'required': bool,
                    'original_data': dict
                }
            }
        """
        import random

        menu_data = self.get_all_menu_data()
        items = menu_data.get('Items', [])

        # Get visible categories from UI
        visible_ui = menu_page.get_all_category_buttons()
        visible_category_names = [cat['name'] for cat in visible_ui]

        # Build category info
        category_info = {}
        for item in items:
            for category in item.get('Categories', []):
                cat_id = category.get('ID')
                cat_name = category.get('Name')
                if cat_name in visible_category_names:
                    category_info[cat_id] = {
                        'name': cat_name,
                        'is_alcohol': category.get('IsAlcohol', False)
                    }

        # Collect ALL items with optional modifier groups
        candidates = []

        for item in items:
            if not item.get('Active', False):
                continue
            if item.get('IsOutOfStock', False):
                continue

            # Check if item belongs to visible category
            item_categories = item.get('Categories', [])
            if not item_categories:
                continue

            for category in item_categories:
                cat_id = category.get('ID')
                if cat_id not in category_info:
                    continue
                if exclude_alcohol_categories and category_info[cat_id]['is_alcohol']:
                    continue

                # Check modifier groups
                mod_groups = item.get('ModifierGroups', [])
                for mod_group in mod_groups:
                    if not mod_group.get('Required', False):  # Optional modifier
                        candidates.append({
                            'item_id': item['ID'],
                            'item_name': item['Name'],
                            'category_id': cat_id,
                            'category_name': category_info[cat_id]['name'],
                            'modifier_group': {
                                'id': mod_group.get('Id'),
                                'name': mod_group.get('Name'),
                                'required': mod_group.get('Required', False),
                                'original_data': mod_group
                            }
                        })
                        break  # Only need one modifier per item
                break  # Only need one category per item

        if not candidates:
            raise ValueError("No items found with optional modifier groups")

        # Randomly select one
        selected = random.choice(candidates)

        self.logger.info(
            f"Randomly selected item: '{selected['item_name']}' "
            f"-> Modifier: '{selected['modifier_group']['name']}' "
            f"(from {len(candidates)} candidates)"
        )

        return selected

    def get_item_with_multiple_modifiers(self, menu_page, min_groups=2, exclude_alcohol_categories=True):

        import random

        menu_data = self.get_all_menu_data()
        items = menu_data.get('Items', [])

        # Get visible categories from UI
        visible_ui = menu_page.get_all_category_buttons()
        visible_category_names = [cat['name'] for cat in visible_ui]

        # Build category info
        category_info = {}
        for item in items:
            for category in item.get('Categories', []):
                cat_id = category.get('ID')
                cat_name = category.get('Name')
                if cat_name in visible_category_names:
                    category_info[cat_id] = {
                        'name': cat_name,
                        'is_alcohol': category.get('IsAlcohol', False)
                    }

        # Collect ALL items with multiple modifier groups
        candidates = []

        for item in items:
            if not item.get('Active', False):
                continue
            if item.get('IsOutOfStock', False):
                continue

            # Check if item belongs to visible category
            item_categories = item.get('Categories', [])
            if not item_categories:
                continue

            for category in item_categories:
                cat_id = category.get('ID')
                if cat_id not in category_info:
                    continue
                if exclude_alcohol_categories and category_info[cat_id]['is_alcohol']:
                    continue

                # Check modifier groups
                mod_groups = item.get('ModifierGroups', [])
                if len(mod_groups) >= min_groups:
                    # Sort by sequence to get original order
                    sorted_groups = sorted(mod_groups, key=lambda x: x.get('Sequence', 0))

                    modifier_groups_data = []
                    for mod_group in sorted_groups:
                        modifier_groups_data.append({
                            'id': mod_group.get('Id'),
                            'name': mod_group.get('Name'),
                            'sequence': mod_group.get('Sequence', 0),
                            'required': mod_group.get('Required', False),
                            'original_data': mod_group
                        })

                    candidates.append({
                        'item_id': item['ID'],
                        'item_name': item['Name'],
                        'category_id': cat_id,
                        'category_name': category_info[cat_id]['name'],
                        'modifier_groups': modifier_groups_data
                    })
                    break  # Only need one category per item

        if not candidates:
            # Provide detailed debugging info
            total_items = len(items)
            active_items = sum(1 for item in items if item.get('Active', False))
            items_in_visible_cats = 0
            items_with_enough_mods = 0

            for item in items:
                if not item.get('Active', False) or item.get('IsOutOfStock', False):
                    continue
                item_categories = item.get('Categories', [])
                for category in item_categories:
                    cat_id = category.get('ID')
                    if cat_id in category_info:
                        items_in_visible_cats += 1
                        mod_groups = item.get('ModifierGroups', [])
                        if len(mod_groups) >= min_groups:
                            items_with_enough_mods += 1
                        break

            error_msg = (
                f"No items found with at least {min_groups} modifier groups. "
                f"Debug info: Total items={total_items}, Active={active_items}, "
                f"In visible categories={items_in_visible_cats}, "
                f"With {min_groups}+ mod groups={items_with_enough_mods}, "
                f"Visible categories={visible_category_names}"
            )
            raise ValueError(error_msg)

        # Randomly select one
        selected = random.choice(candidates)

        self.logger.info(
            f"Randomly selected item: '{selected['item_name']}' "
            f"with {len(selected['modifier_groups'])} modifier groups "
            f"(from {len(candidates)} candidates)"
        )

        return selected

    def _build_modifier_payload(self, mod_group_data, menu_items_list, required):
        """Build payload for modifier group update"""

        # Extract modifiers
        modifiers = []
        for mod in mod_group_data.get('Modifiers', []):
            modifiers.append({
                "MaxQuantity": mod.get('MaxQuantity', 0),
                "Sequence": mod.get('Sequence', 0),
                "StartTime": "0001-01-01T00:00:00.0000000Z",
                "EndTime": "0001-01-01T00:00:00.0000000Z",
                "id": None,
                "MenuItemID": mod.get('ID'),
                "Name": mod.get('Name'),
                "Description": None,
                "Calories": None,
                "Image": None,
                "KioskImage": None,
                "Active": None,
                "PreparationTime": None,
                "Categories": None,
                "Upgrade": None,
                "Tags": None
            })

        payload = {
            "PropertyID": "33",
            "RevenueCenterID": "810",
            "ModifierGroups": [
                {
                    "id": None,
                    "ModifierGroupID": mod_group_data.get('Id'),
                    "Name": mod_group_data.get('Name'),
                    "Type": mod_group_data.get('Type'),
                    "Required": required,
                    "Active": mod_group_data.get('Active', True),
                    "PosId": 0,
                    "MaxQuantity": 1 if required else mod_group_data.get('MaxQuantity', 0),
                    "MinQuantity": 1 if required else mod_group_data.get('MinQuantity', 0),
                    "Sequence": mod_group_data.get('Sequence', 0),
                    "MenuItems": menu_items_list,
                    "Modifiers": modifiers
                }
            ],
            "UserName": "atevzadze"
        }

        return payload

    def make_modifier_required(self, modifier_group_id, mod_group_data, menu_items_list):
        """Make modifier group required"""
        payload = self._build_modifier_payload(mod_group_data, menu_items_list, required=True)

        try:
            response = requests.post(self.management_url, headers=self.management_headers,
                                    json=payload, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Made modifier group required: {mod_group_data.get('Name')}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to make modifier required: {str(e)}")
            raise

    def make_modifier_optional(self, modifier_group_id, mod_group_data, menu_items_list):
        """Make modifier group optional (restore)"""
        payload = self._build_modifier_payload(mod_group_data, menu_items_list, required=False)

        try:
            response = requests.post(self.management_url, headers=self.management_headers,
                                    json=payload, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Made modifier group optional: {mod_group_data.get('Name')}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to make modifier optional: {str(e)}")
            raise

    def get_menu_items_using_modifier(self, modifier_group_id):
        """Get list of all menu items that use this modifier group"""
        menu_data = self.get_all_menu_data()
        items = menu_data.get('Items', [])

        menu_items = []
        for item in items:
            for mod_group in item.get('ModifierGroups', []):
                if mod_group.get('Id') == modifier_group_id:
                    menu_items.append(item['ID'])
                    break

        return menu_items

    def update_modifier_sequences(self, modifier_updates):
        """
        Update sequences for multiple modifier groups at once.

        Args:
            modifier_updates: List of dicts with:
                {
                    'modifier_group_id': str,
                    'mod_group_data': dict,
                    'menu_items_list': list,
                    'new_sequence': int
                }

        Returns:
            List of responses
        """
        responses = []

        for update in modifier_updates:
            mod_group_data = update['mod_group_data']
            new_sequence = update['new_sequence']

            # Build payload with new sequence
            modifiers = []
            for mod in mod_group_data.get('Modifiers', []):
                modifiers.append({
                    "MaxQuantity": mod.get('MaxQuantity', 0),
                    "Sequence": mod.get('Sequence', 0),
                    "StartTime": "0001-01-01T00:00:00.0000000Z",
                    "EndTime": "0001-01-01T00:00:00.0000000Z",
                    "id": None,
                    "MenuItemID": mod.get('ID'),
                    "Name": mod.get('Name'),
                    "Description": None,
                    "Calories": None,
                    "Image": None,
                    "KioskImage": None,
                    "Active": None,
                    "PreparationTime": None,
                    "Categories": None,
                    "Upgrade": None,
                    "Tags": None
                })

            payload = {
                "PropertyID": "33",
                "RevenueCenterID": "810",
                "ModifierGroups": [
                    {
                        "id": None,
                        "ModifierGroupID": mod_group_data.get('Id'),
                        "Name": mod_group_data.get('Name'),
                        "Type": mod_group_data.get('Type'),
                        "Required": mod_group_data.get('Required', False),
                        "Active": mod_group_data.get('Active', True),
                        "PosId": 0,
                        "MaxQuantity": mod_group_data.get('MaxQuantity', 0),
                        "MinQuantity": mod_group_data.get('MinQuantity', 0),
                        "Sequence": new_sequence,  # New sequence value
                        "MenuItems": update['menu_items_list'],
                        "Modifiers": modifiers
                    }
                ],
                "UserName": "atevzadze"
            }

            try:
                response = requests.post(self.management_url, headers=self.management_headers,
                                        json=payload, timeout=30)
                response.raise_for_status()
                self.logger.info(
                    f"Updated sequence for '{mod_group_data.get('Name')}': "
                    f"{mod_group_data.get('Sequence')} → {new_sequence}"
                )
                responses.append(response.json())
            except Exception as e:
                self.logger.error(f"Failed to update sequence: {str(e)}")
                raise

        return responses

    def make_modifier_group_inactive(self, modifier_group_id, mod_group_data, menu_items_list):
        """Make modifier group inactive (hide from UI)"""
        payload = self._build_modifier_payload_full(mod_group_data, menu_items_list, active=False)

        try:
            response = requests.post(self.management_url, headers=self.management_headers,
                                    json=payload, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Made modifier group inactive: {mod_group_data.get('Name')}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to make modifier inactive: {str(e)}")
            raise

    def make_modifier_group_active(self, modifier_group_id, mod_group_data, menu_items_list):
        """Make modifier group active (show in UI)"""
        payload = self._build_modifier_payload_full(mod_group_data, menu_items_list, active=True)

        try:
            response = requests.post(self.management_url, headers=self.management_headers,
                                    json=payload, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Made modifier group active: {mod_group_data.get('Name')}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to make modifier active: {str(e)}")
            raise

    def rename_modifier_group(self, modifier_group_id, mod_group_data, menu_items_list, new_name):
        """Rename modifier group"""
        payload = self._build_modifier_payload_full(mod_group_data, menu_items_list,
                                                     active=True, new_name=new_name)

        try:
            response = requests.post(self.management_url, headers=self.management_headers,
                                    json=payload, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Renamed modifier group: '{mod_group_data.get('Name')}' → '{new_name}'")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to rename modifier: {str(e)}")
            raise

    def _build_modifier_payload_full(self, mod_group_data, menu_items_list, active=True, new_name=None):
        """Build full payload with optional active status and name change"""

        # Extract modifiers
        modifiers = []
        for mod in mod_group_data.get('Modifiers', []):
            modifiers.append({
                "MaxQuantity": mod.get('MaxQuantity', 0),
                "Sequence": mod.get('Sequence', 0),
                "StartTime": "0001-01-01T00:00:00.0000000Z",
                "EndTime": "0001-01-01T00:00:00.0000000Z",
                "id": None,
                "MenuItemID": mod.get('ID'),
                "Name": mod.get('Name'),
                "Description": None,
                "Calories": None,
                "Image": None,
                "KioskImage": None,
                "Active": None,
                "PreparationTime": None,
                "Categories": None,
                "Upgrade": None,
                "Tags": None
            })

        # Use new name if provided, otherwise keep original
        group_name = new_name if new_name else mod_group_data.get('Name')

        payload = {
            "PropertyID": "33",
            "RevenueCenterID": "810",
            "ModifierGroups": [
                {
                    "id": None,
                    "ModifierGroupID": mod_group_data.get('Id'),
                    "Name": group_name,
                    "Type": mod_group_data.get('Type'),
                    "Required": mod_group_data.get('Required', False),
                    "Active": active,
                    "PosId": 0,
                    "MaxQuantity": mod_group_data.get('MaxQuantity', 0),
                    "MinQuantity": mod_group_data.get('MinQuantity', 0),
                    "Sequence": mod_group_data.get('Sequence', 0),
                    "MenuItems": menu_items_list,
                    "Modifiers": modifiers
                }
            ],
            "UserName": "atevzadze"
        }

        return payload

    def get_item_with_modifiers(self, item_id):
        """
        Get item details including all modifier groups and their modifiers.

        Args:
            item_id: Item ID to get modifiers for

        Returns:
            dict: Item details with nested modifier structure
        """
        menu_data = self.get_all_menu_data()
        items_data = menu_data.get('Items', [])

        for item in items_data:
            if item['ID'] == item_id:
                return {
                    'item_id': item['ID'],
                    'item_name': item['Name'],
                    'modifier_groups': item.get('ModifierGroups', [])
                }

        raise ValueError(f"Item {item_id} not found")

    def get_random_modifier_from_item(self, item_id):
        """
        Get a random modifier from a random modifier group on an item.

        Args:
            item_id: Item ID to get modifier from

        Returns:
            dict: {
                'modifier_id': str,
                'modifier_name': str,
                'modifier_group_id': str,
                'modifier_group_name': str,
                'item_id': str,
                'item_name': str
            }
        """
        import random

        item_data = self.get_item_with_modifiers(item_id)
        modifier_groups = item_data['modifier_groups']

        if not modifier_groups:
            raise ValueError(f"Item {item_id} has no modifier groups")

        # Get groups that have modifiers
        groups_with_modifiers = [
            group for group in modifier_groups
            if group.get('Modifiers') and len(group['Modifiers']) > 0
        ]

        if not groups_with_modifiers:
            raise ValueError(f"Item {item_id} has no modifiers in any group")

        # Select random group
        selected_group = random.choice(groups_with_modifiers)

        # Select random modifier from that group
        selected_modifier = random.choice(selected_group['Modifiers'])

        self.logger.info(
            f"Selected modifier: '{selected_modifier['Name']}' "
            f"from group '{selected_group['Name']}' "
            f"on item '{item_data['item_name']}'"
        )

        return {
            'modifier_id': selected_modifier['ID'],
            'modifier_name': selected_modifier['Name'],
            'modifier_group_id': selected_group['Id'],  # ← Fixed: 'Id' not 'ID'
            'modifier_group_name': selected_group['Name'],
            'item_id': item_data['item_id'],
            'item_name': item_data['item_name'],
            'original_active': selected_modifier.get('Active', True)
        }


    def get_modifier_full_details(self, modifier_id):
        """
        Get complete details for a specific modifier item.
        Modifiers are nested inside Items -> ModifierGroups -> Modifiers.

        Args:
            modifier_id: Modifier item ID

        Returns:
            dict: Full modifier details from API
        """
        menu_data = self.get_all_menu_data()
        items_data = menu_data.get('Items', [])

        # Search through the nested structure
        for item in items_data:
            modifier_groups = item.get('ModifierGroups', [])
            for group in modifier_groups:
                modifiers = group.get('Modifiers', [])
                for modifier in modifiers:
                    if modifier.get('ID') == modifier_id:
                        self.logger.info(
                            f"Found modifier '{modifier.get('Name')}' "
                            f"in group '{group.get('Name')}' "
                            f"on item '{item.get('Name')}'"
                        )
                        return modifier

        raise ValueError(
            f"Modifier item {modifier_id} not found in menu data. "
            f"Searched {len(items_data)} items and their modifier groups."
        )

    def make_modifier_item_inactive(self, modifier_id, property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Make a single modifier item inactive.

        Args:
            modifier_id: Modifier item ID to make inactive
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            Response JSON
        """
        # Modifiers use the menuItems endpoint
        menu_items_url = "https://digitalmwqa.azure-api.net/v2/internal/menu/management/menuItems"

        # Fetch full details to preserve all fields
        modifier = self.get_modifier_full_details(modifier_id)

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "MenuItems": [
                {
                    "id": None,
                    "MenuItemID": modifier_id,
                    "Name": modifier.get('Name', ''),
                    "Description": modifier.get('Description', ''),
                    "Calories": modifier.get('Calories', ''),
                    "Image": modifier.get('ImageUrl'),  # Preserve image URL
                    "Active": False,  # Only change active status
                    "PreparationTime": int(modifier.get('PreparationTime', 0) if modifier.get('PreparationTime') is not None else 0),
                    "Categories": [],  # Modifiers don't have categories
                    "Upgrade": None,  # Modifiers don't have upgrades
                    "Tags": []  # Modifiers don't have tags
                }
            ],
            "UserName": username
        }

        try:
            response = requests.post(
                menu_items_url,
                headers=self.management_headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            self.logger.info(f"Made modifier {modifier_id} inactive with preserved details")
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to make modifier inactive: {str(e)}")
            raise

    def make_modifier_item_active(self, modifier_id, property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Make a single modifier item active (restore).

        Args:
            modifier_id: Modifier item ID to make active
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            Response JSON
        """
        # Modifiers use the menuItems endpoint
        menu_items_url = "https://digitalmwqa.azure-api.net/v2/internal/menu/management/menuItems"

        # Fetch full details to preserve all fields
        modifier = self.get_modifier_full_details(modifier_id)

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "MenuItems": [
                {
                    "id": None,
                    "MenuItemID": modifier_id,
                    "Name": modifier.get('Name', ''),
                    "Description": modifier.get('Description', ''),
                    "Calories": modifier.get('Calories', ''),
                    "Image": modifier.get('ImageUrl'),  # Preserve image URL
                    "Active": True,  # Only change active status
                    "PreparationTime": int(modifier.get('PreparationTime', 0) if modifier.get('PreparationTime') is not None else 0),
                    "Categories": [],  # Modifiers don't have categories
                    "Upgrade": None,  # Modifiers don't have upgrades
                    "Tags": []  # Modifiers don't have tags
                }
            ],
            "UserName": username
        }

        try:
            response = requests.post(
                menu_items_url,
                headers=self.management_headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            self.logger.info(f"Made modifier {modifier_id} active with preserved details")
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to make modifier active: {str(e)}")
            raise