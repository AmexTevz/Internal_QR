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
        """
        Find an item with at least min_groups modifier groups.
        Randomly selects from available items.

        Args:
            menu_page: MenuPage instance
            min_groups: Minimum number of modifier groups required
            exclude_alcohol_categories: Exclude items from alcohol categories

        Returns:
            dict: {
                'item_id': str,
                'item_name': str,
                'category_id': str,
                'category_name': str,
                'modifier_groups': [
                    {
                        'id': str,
                        'name': str,
                        'sequence': int,
                        'required': bool,
                        'original_data': dict
                    }
                ]
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
            raise ValueError(f"No items found with at least {min_groups} modifier groups")

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