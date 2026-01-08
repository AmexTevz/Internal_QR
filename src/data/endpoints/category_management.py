"""
Category Management API
Manages category availability times for integration testing
"""
import requests
import json
from datetime import datetime, timedelta
import pytz
from src.utils.logger import Logger


class CategoryManagementAPI:
    """API client for managing menu categories (availability times, etc.)"""

    def __init__(self):
        self.base_url = "https://digitalmwqa.azure-api.net/v2/internal/menu/management"
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

        self.logger = Logger("CategoryManagementAPI")

        # API timezone is Eastern
        self.api_timezone = pytz.timezone('US/Eastern')

        # Session ID (obtained from authentication)
        self.session_id = None

    def authenticate(self, client_id="3289FE1A-A4CA-49DC-9CDF-C2831781E850",
                     username="internal", passkey="P455w0rd"):
        """
        Authenticate and get a fresh session ID.

        Args:
            client_id: Client ID for authentication
            username: API username
            passkey: API password

        Returns:
            str: Session ID
        """
        payload = {
            "ClientID": client_id,
            "username": username,
            "passkey": passkey
        }

        try:
            response = requests.post(
                self.auth_url,
                headers=self.catalog_headers,
                json=payload,
                timeout=30
            )
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

    def get_all_categories_from_menu(self, property_id="33", revenue_center_id="810",
                                      client_id="3289FE1A-A4CA-49DC-9CDF-C2831781E850"):
        """
        Get all categories dynamically from the menu items API.
        Authenticates first if needed.

        Returns:
            tuple: (categories_dict, category_details_dict)
        """
        # Authenticate if we don't have a session ID
        if not self.session_id:
            self.logger.info("No session ID found, authenticating...")
            self.authenticate(client_id=client_id)

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "ClientID": client_id,
            "SessionID": self.session_id
        }

        try:
            response = requests.post(
                self.catalog_url,
                headers=self.catalog_headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("Items", [])

            # Extract unique categories with full details
            categories = {}
            category_details = {}

            for item in items:
                item_categories = item.get("Categories", [])
                for category in item_categories:
                    category_name = category.get("Name")
                    category_id = category.get("ID")

                    if category_name and category_id and category_name not in categories:
                        categories[category_name] = category_id
                        category_details[category_id] = {
                            "ID": category_id,
                            "Name": category_name,
                            "DisplayOrder": category.get("DisplayOrder", 999),
                            "Active": category.get("Active", True),
                            "IsAlcohol": category.get("IsAlcohol", False),
                            "OpenTime": category.get("OpenTime", "00:00:00"),
                            "CloseTime": category.get("CloseTime", "23:59:59"),
                            "Description": category.get("Description", ""),
                            "ImageUrl": category.get("ImageUrl", ""),
                            "KioskImageUrl": category.get("KioskImageUrl"),
                            "PromptAtCheckout": category.get("PromptAtCheckout", False)
                        }

            self.logger.info(f"Retrieved {len(categories)} categories from menu API")
            return categories, category_details

        except Exception as e:
            self.logger.error(f"Failed to get categories from menu: {str(e)}")
            raise

    def update_category_times(self, category_id, category_details, open_time, close_time,
                              property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Update category availability times.

        Args:
            category_id: Category UUID
            category_details: Full category details dict (from get_all_categories_from_menu)
            open_time: OpenTime in HH:MM:SS format (e.g., "13:00:00")
            close_time: CloseTime in HH:MM:SS format (e.g., "23:59:59")
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            Response JSON
        """
        details = category_details[category_id]

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "Categories": [
                {
                    "id": None,
                    "CategoryID": category_id,
                    "Name": details["Name"],
                    "Description": details["Description"],
                    "OpenTime": open_time,
                    "CloseTime": close_time,
                    "DisplayOrder": details["DisplayOrder"],
                    "ImageUrl": details["ImageUrl"],
                    "KioskImageUrl": details["KioskImageUrl"],
                    "Active": details["Active"],
                    "IsAlcohol": details["IsAlcohol"],
                    "PromptAtCheckout": details["PromptAtCheckout"],
                    "Children": None,
                    "Tags": []
                }
            ],
            "UserName": username
        }

        try:
            url = f"{self.base_url}/categories"
            response = requests.post(
                url,
                headers=self.management_headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()

            self.logger.info(
                f"Updated category '{details['Name']}' times: "
                f"OpenTime={open_time}, CloseTime={close_time}"
            )

            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to update category times: {str(e)}")
            raise

    def make_category_unavailable(self, category_id, category_details,
                                   property_id="33", revenue_center_id="810"):
        """
        Make a category unavailable by setting it to have closed 1 hour ago.

        Args:
            category_id: Category UUID
            category_details: Full category details dict
            property_id: Property ID
            revenue_center_id: Revenue Center ID

        Returns:
            Response JSON
        """
        # Get current time in API timezone (Eastern)
        current_time = datetime.now(self.api_timezone)

        # Set category to have closed 1 hour ago
        close_time = (current_time - timedelta(hours=1)).strftime("%H:%M:%S")
        open_time = "00:00:00"  # Opens at midnight

        self.logger.info(
            f"Making category '{category_details[category_id]['Name']}' unavailable. "
            f"Current time: {current_time.strftime('%H:%M:%S')} ET, "
            f"Setting CloseTime to: {close_time}"
        )

        return self.update_category_times(
            category_id=category_id,
            category_details=category_details,
            open_time=open_time,
            close_time=close_time,
            property_id=property_id,
            revenue_center_id=revenue_center_id
        )

    def restore_category_times(self, category_id, category_details, original_open_time,
                                original_close_time, property_id="33", revenue_center_id="810"):
        """
        Restore category to original availability times.

        Args:
            category_id: Category UUID
            category_details: Full category details dict
            original_open_time: Original OpenTime
            original_close_time: Original CloseTime
            property_id: Property ID
            revenue_center_id: Revenue Center ID

        Returns:
            Response JSON
        """
        self.logger.info(
            f"Restoring category '{category_details[category_id]['Name']}' to original times: "
            f"OpenTime={original_open_time}, CloseTime={original_close_time}"
        )

        return self.update_category_times(
            category_id=category_id,
            category_details=category_details,
            open_time=original_open_time,
            close_time=original_close_time,
            property_id=property_id,
            revenue_center_id=revenue_center_id
        )

    def set_category_active_status(self, category_id, category_details, active_status,
                                    property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Set category active/inactive status.

        Args:
            category_id: Category UUID
            category_details: Full category details dict
            active_status: True to activate, False to deactivate
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            Response JSON
        """
        details = category_details[category_id]

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "Categories": [
                {
                    "id": None,
                    "CategoryID": category_id,
                    "Name": details["Name"],
                    "Description": details["Description"],
                    "OpenTime": details["OpenTime"],
                    "CloseTime": details["CloseTime"],
                    "DisplayOrder": details["DisplayOrder"],
                    "ImageUrl": details["ImageUrl"],
                    "KioskImageUrl": details["KioskImageUrl"],
                    "Active": active_status,  # ← Change active status
                    "IsAlcohol": details["IsAlcohol"],
                    "PromptAtCheckout": details["PromptAtCheckout"],
                    "Children": None,
                    "Tags": []
                }
            ],
            "UserName": username
        }

        try:
            url = f"{self.base_url}/categories"
            response = requests.post(
                url,
                headers=self.management_headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()

            status_text = "active" if active_status else "inactive"
            self.logger.info(
                f"Set category '{details['Name']}' to {status_text}"
            )

            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to set category active status: {str(e)}")
            raise

    def make_category_inactive(self, category_id, category_details,
                                property_id="33", revenue_center_id="810"):
        """
        Make a category inactive (Active = false).

        Args:
            category_id: Category UUID
            category_details: Full category details dict
            property_id: Property ID
            revenue_center_id: Revenue Center ID

        Returns:
            Response JSON
        """
        self.logger.info(
            f"Making category '{category_details[category_id]['Name']}' inactive"
        )

        return self.set_category_active_status(
            category_id=category_id,
            category_details=category_details,
            active_status=False,
            property_id=property_id,
            revenue_center_id=revenue_center_id
        )

    def restore_category_active_status(self, category_id, category_details, original_active_status,
                                        property_id="33", revenue_center_id="810"):
        status_text = "active" if original_active_status else "inactive"
        self.logger.info(
            f"Restoring category '{category_details[category_id]['Name']}' to original status: {status_text}"
        )

        return self.set_category_active_status(
            category_id=category_id,
            category_details=category_details,
            active_status=original_active_status,
            property_id=property_id,
            revenue_center_id=revenue_center_id
        )

    def get_random_visible_category(self, menu_page, exclude_alcohol=True):
        categories, category_details = self.get_all_categories_from_menu()

        visible_ui = menu_page.get_all_category_buttons()
        visible_names = [cat['name'] for cat in visible_ui]

        testable = {
            name: categories[name] for name in visible_names
            if name in categories
            and category_details[categories[name]]["Active"]
            and (not exclude_alcohol or not category_details[categories[name]]["IsAlcohol"])
        }

        if not testable:
            raise ValueError("No testable categories found")

        import random
        category_name = random.choice(list(testable.keys()))
        category_id = testable[category_name]

        category_index = visible_names.index(category_name)
        neighbor_id = None
        neighbor_name = None

        if category_index > 0:
            neighbor_name = visible_names[category_index - 1]
            neighbor_id = categories.get(neighbor_name)
        elif category_index < len(visible_names) - 1:
            neighbor_name = visible_names[category_index + 1]
            neighbor_id = categories.get(neighbor_name)

        return {
            'id': category_id,
            'name': category_name,
            'details': category_details,
            'original_open_time': category_details[category_id]["OpenTime"],
            'original_close_time': category_details[category_id]["CloseTime"],
            'original_active': category_details[category_id]["Active"],
            'neighbor_id': neighbor_id,
            'neighbor_name': neighbor_name
        }

    def get_category_api_details(self, category_id, category_details):
        details = category_details[category_id]
        return {
            "CategoryID": category_id,
            "Name": details["Name"],
            "Active": details["Active"],
            "OpenTime": details["OpenTime"],
            "CloseTime": details["CloseTime"],
            "IsAlcohol": details["IsAlcohol"],
            "DisplayOrder": details["DisplayOrder"],
            "Description": details["Description"]
        }

    def rename_category(self, category_id, category_details, new_name,
                        property_id="33", revenue_center_id="810", username="atevzadze"):
        """
        Rename a category.

        Args:
            category_id: Category UUID
            category_details: Full category details dict
            new_name: New name for the category
            property_id: Property ID
            revenue_center_id: Revenue Center ID
            username: Username for audit trail

        Returns:
            Response JSON
        """
        details = category_details[category_id]

        payload = {
            "PropertyID": property_id,
            "RevenueCenterID": revenue_center_id,
            "Categories": [
                {
                    "id": None,
                    "CategoryID": category_id,
                    "Name": new_name,  # ← New name
                    "Active": details["Active"],
                    "DisplayOrder": details["DisplayOrder"],
                    "OpenTime": details["OpenTime"],
                    "CloseTime": details["CloseTime"],
                    "Description": details["Description"],
                    "IsAlcohol": details["IsAlcohol"],
                    "Tags": []
                }
            ],
            "UserName": username
        }

        try:
            response = requests.post(
                f"{self.base_url}/Categories",
                headers=self.management_headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            self.logger.info(f"Renamed category: '{details['Name']}' → '{new_name}'")

            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to rename category: {str(e)}")
            raise