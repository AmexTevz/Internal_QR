import time
import pytest
import allure
import json
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.category_management import CategoryManagementAPI
from datetime import datetime

TABLES = [71]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.all
@pytest.mark.integration
@pytest.mark.category_integration
@pytest.mark.category_rename
@allure.feature("Category Management")
@allure.story("Category Rename")
def test_category_rename(browser_factory, endpoint_setup, table):
    """
    Test that renaming category updates the name in UI navigation.

    Flow:
    1. Navigate to main menu
    2. Select random visible category
    3. Capture original category name in navigation
    4. Rename category via API (add "TEST RENAME - " prefix)
    5. Restart browser
    6. Verify new name appears in category navigation
    7. Restore original name via API
    """
    api = CategoryManagementAPI()
    timestamp = datetime.now().strftime("%B %d, %Y %H:%M")
    allure.dynamic.title(f"Category Rename - {timestamp}")
    [driver] = browser_factory("chrome")
    menu_page = MenuPage(driver)
    menu_page.navigate_to_main_menu()

    # Get random category
    category = api.get_random_visible_category(menu_page)

    original_name = category['name']
    test_name = f"TEST RENAME - {original_name}"

    with allure.step(f"Selected category: {original_name}"):
        api_details = api.get_category_api_details(category['id'], category['details'])
        allure.attach(
            json.dumps({
                "Original Name": original_name,
                "Category ID": category['id'],
                "Test Name": test_name,
                "Active": api_details['Active'],
                "DisplayOrder": api_details['DisplayOrder']
            }, indent=2),
            name="Category Details",
            attachment_type=allure.attachment_type.JSON
        )

        # Find category section by data-categoryid and scroll to it
        try:
            category_section = driver.find_element("css selector", f"section[data-categoryid='{category['id']}']")
            driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", category_section)
            time.sleep(1)

            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Original Name: '{original_name}' (Section)",
                attachment_type=allure.attachment_type.PNG
            )
        except Exception as e:
            allure.attach(
                driver.get_screenshot_as_png(),
                name="Could not capture original name",
                attachment_type=allure.attachment_type.PNG
            )

    with allure.step(f"Rename category via API"):
        api.rename_category(category['id'], category['details'], test_name)

        allure.attach(
            f"Original Name: {original_name}\n"
            f"New Name: {test_name}",
            name="API Update - Renamed",
            attachment_type=allure.attachment_type.TEXT
        )

    with allure.step("Restart browser"):
        drivers = browser_factory("chrome")
        new_driver = drivers[-1]
        new_menu_page = MenuPage(new_driver)
        new_menu_page.navigate_to_main_menu()

    with allure.step(f"Verify new name appears: '{test_name}'"):
        try:
            # Get all category buttons to verify name changed
            all_categories = new_menu_page.get_all_category_buttons()
            category_names = [cat['name'] for cat in all_categories]

            # Check if new name appears
            found_new_name = False
            displayed_name = None

            for cat_name in category_names:
                if "test rename" in cat_name.lower() and original_name.lower() in cat_name.lower():
                    found_new_name = True
                    displayed_name = cat_name
                    break

            if found_new_name:
                # Find category section by data-categoryid and scroll to it
                renamed_category_section = new_driver.find_element("css selector",
                                                                   f"section[data-categoryid='{category['id']}']")
                new_driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", renamed_category_section)
                time.sleep(2)

                allure.attach(
                    new_driver.get_screenshot_as_png(),
                    name=f"New Name: '{test_name}' (Section)",
                    attachment_type=allure.attachment_type.PNG
                )

                allure.attach(
                    f"✅ Name Changed Successfully\n\n"
                    f"Original: {original_name}\n"
                    f"New: {displayed_name}\n"
                    f"Expected: {test_name}",
                    name="Verification - Name Changed",
                    attachment_type=allure.attachment_type.TEXT
                )

                assert True, "Category renamed successfully"
            else:
                allure.attach(
                    new_driver.get_screenshot_as_png(),
                    name=f"ERROR - New name not found",
                    attachment_type=allure.attachment_type.PNG
                )

                allure.attach(
                    f"Expected: {test_name}\n"
                    f"Available categories: {', '.join(category_names)}",
                    name="Available Categories",
                    attachment_type=allure.attachment_type.TEXT
                )

                pytest.fail(f"New name '{test_name}' not found in category navigation")

        except Exception as e:
            allure.attach(
                new_driver.get_screenshot_as_png(),
                name="Error verifying new name",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Failed to verify name change: {str(e)}")

    with allure.step(f"Restore original name: '{original_name}'"):
        api.rename_category(category['id'], category['details'], original_name)

        allure.attach(
            f"Test Name: {test_name}\n"
            f"Restored Name: {original_name}\n"
            f"Restored to original state\n",
            name="API Update - Restored Name",
            attachment_type=allure.attachment_type.TEXT
        )