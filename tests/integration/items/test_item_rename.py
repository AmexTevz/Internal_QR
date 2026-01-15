import time
import pytest
import allure
import json
from selenium.webdriver.common.by import By
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.item_management import ItemManagementAPI
from datetime import datetime

TABLES = [70]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.all
@pytest.mark.integration
@pytest.mark.item_integration
@pytest.mark.item_rename
@allure.feature("Item Management")
@allure.story("Item Rename")
def test_item_rename(browser_factory, endpoint_setup, table):
    """
    Test that renaming menu item updates the name in UI.

    Flow:
    1. Navigate to main menu
    2. Select random visible item
    3. Scroll to item and capture original name
    4. Rename item via API (add "TEST RENAME - " prefix)
    5. Restart browser
    6. Scroll to item and verify new name appears
    7. Restore original name via API
    """
    api = ItemManagementAPI()
    timestamp = datetime.now().strftime("%B %d, %Y %H:%M")
    allure.dynamic.title(f"Item Rename - {timestamp}")
    [driver] = browser_factory("chrome")
    menu_page = MenuPage(driver)
    menu_page.navigate_to_main_menu()

    # Get random item (exclude items with upgrades to avoid API issues)
    item = api.get_random_visible_item(menu_page, exclude_items_with_upgrades=True)

    original_name = item['item_name']
    test_name = f"TEST RENAME - {original_name}"

    with allure.step(f"Selected item: {original_name}"):
        allure.attach(
            json.dumps({
                "Original Name": original_name,
                "Item ID": item['item_id'],
                "Category": item['category_name'],
                "Test Name": test_name
            }, indent=2),
            name="Item Details",
            attachment_type=allure.attachment_type.JSON
        )

        # Scroll to item and show original name
        try:
            item_element = driver.find_element(By.ID, item['item_id'])
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
            time.sleep(1)

            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Original Name: '{original_name}'",
                attachment_type=allure.attachment_type.PNG
            )
        except Exception as e:
            allure.attach(
                driver.get_screenshot_as_png(),
                name="Could not capture original name",
                attachment_type=allure.attachment_type.PNG
            )

    with allure.step(f"Rename item via API"):
        api.rename_item(item['item_id'], test_name)

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
            # Scroll to category where item is located
            category_section = new_driver.find_element(
                By.CSS_SELECTOR,
                f"section[data-categoryid='{item['category_id']}']"
            )
            new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", category_section)
            time.sleep(1)

            # Find the item and check its name
            item_element = new_driver.find_element(By.ID, item['item_id'])

            # Get the item name from the element
            # Item name is typically in a div with class containing 'item-name' or similar
            item_name_element = item_element.find_element(By.CSS_SELECTOR, "[class*='item-name'], .item-title, h3, h4")
            displayed_name = item_name_element.text.strip()

            # Check if new name appears
            found_new_name = test_name.lower() in displayed_name.lower() or "test rename" in displayed_name.lower()

            if found_new_name:
                new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
                time.sleep(0.5)

                allure.attach(
                    new_driver.get_screenshot_as_png(),
                    name=f"New Name: '{test_name}'",
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

                assert True, "Item renamed successfully"
            else:
                allure.attach(
                    new_driver.get_screenshot_as_png(),
                    name=f"ERROR - New name not found",
                    attachment_type=allure.attachment_type.PNG
                )

                allure.attach(
                    f"Expected: {test_name}\n"
                    f"Displayed: {displayed_name}",
                    name="Name Mismatch",
                    attachment_type=allure.attachment_type.TEXT
                )

                pytest.fail(f"New name '{test_name}' not found in UI. Displayed: '{displayed_name}'")

        except Exception as e:
            allure.attach(
                new_driver.get_screenshot_as_png(),
                name="Error verifying new name",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Failed to verify name change: {str(e)}")

    with allure.step(f"Restore original name: '{original_name}'"):
        api.rename_item(item['item_id'], original_name)

        allure.attach(
            f"Test Name: {test_name}\n"
            f"Restored Name: {original_name}\n"
            f"Restored to original state\n",
            name="API Update - Restored Name",
            attachment_type=allure.attachment_type.TEXT
        )