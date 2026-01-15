import time
import pytest
import allure
import json
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.item_management import ItemManagementAPI
from datetime import datetime

TABLES = [59]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.all
@pytest.mark.integration
@pytest.mark.item_integration
@pytest.mark.item_inactive
@allure.feature("Item Management")
@allure.story("Item Hidden When Inactive")
def test_item_hidden_when_inactive(browser_factory, endpoint_setup, table):
    """
    Test that individual item hides when marked as inactive.

    Flow:
    1. Navigate to main menu
    2. Select random visible item
    3. Scroll to item and capture original state
    4. Make item inactive via API (Active: false)
    5. Restart browser
    6. Scroll to category where item was located
    7. Verify item is hidden (element not found or not displayed)
    8. Restore item to active via API
    9. Restart browser and verify item is visible again
    """

    api = ItemManagementAPI()
    timestamp = datetime.now().strftime("%B %d, %Y %H:%M")
    allure.dynamic.title(f"Test Item Hidden When Inactive - {timestamp}")
    [driver] = browser_factory("chrome")
    menu_page = MenuPage(driver)
    menu_page.navigate_to_main_menu()

    # Get random item
    item = api.get_random_visible_item(menu_page)

    with allure.step(f"Selected item: {item['item_name']} from {item['category_name']}"):
        allure.attach(
            json.dumps({
                "Item Name": item['item_name'],
                "Item ID": item['item_id'],
                "Category": item['category_name'],
                "Category ID": item['category_id'],
                "Price": f"${item['price']:.2f}",
                "Original Active Status": item['original_active']
            }, indent=2),
            name="Item Details - Before",
            attachment_type=allure.attachment_type.JSON
        )

        # Scroll to the item
        try:
            item_element = driver.find_element(By.ID, item['item_id'])
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
            time.sleep(1)

            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Item '{item['item_name']}' - Visible and Active",
                attachment_type=allure.attachment_type.PNG
            )
        except NoSuchElementException:
            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Item '{item['item_name']}' - Could not find element",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Could not find item element with ID: {item['item_id']}")

    with allure.step(f"Make item '{item['item_name']}' inactive"):
        api.make_items_inactive([item['item_id']])  # Just pass list with one item
        time.sleep(3)

    with allure.step("Restart browser"):
        drivers = browser_factory("chrome")
        new_driver = drivers[-1]
        new_menu_page = MenuPage(new_driver)
        new_menu_page.navigate_to_main_menu()

    with allure.step(f"Verify item '{item['item_name']}' is hidden"):
        # Scroll to the category where item was
        try:
            category_section = new_driver.find_element(
                By.CSS_SELECTOR,
                f"section[data-categoryid='{item['category_id']}']"
            )
            new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", category_section)
            time.sleep(1)
        except NoSuchElementException:
            pass

        # Try to find the item - should NOT exist
        item_elements = new_driver.find_elements(By.ID, item['item_id'])

        # Filter to only visible elements
        visible_items = [elem for elem in item_elements if elem.is_displayed()]

        assert len(visible_items) == 0, \
            f"Item '{item['item_name']}' should be hidden when inactive, but found {len(visible_items)} visible instances"

        allure.attach(
            new_driver.get_screenshot_as_png(),
            name=f"Item '{item['item_name']}' - Hidden (Category: {item['category_name']})",
            attachment_type=allure.attachment_type.PNG
        )

    with allure.step(f"Restore item '{item['item_name']}' to active"):
        api.make_items_active([item['item_id']])  # Just pass list with one item
        time.sleep(3)

        drivers = browser_factory("chrome")
        verify_driver = drivers[-1]
        verify_menu_page = MenuPage(verify_driver)
        verify_menu_page.navigate_to_main_menu()

        # Scroll to the restored item
        try:
            restored_item = verify_driver.find_element(By.ID, item['item_id'])
            verify_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", restored_item)
            time.sleep(1)

            allure.attach(
                verify_driver.get_screenshot_as_png(),
                name=f"Item '{item['item_name']}' - Restored and Visible",
                attachment_type=allure.attachment_type.PNG
            )

            # Verify it's actually visible
            assert restored_item.is_displayed(), \
                f"Item '{item['item_name']}' should be visible after restoration"

        except NoSuchElementException:
            allure.attach(
                verify_driver.get_screenshot_as_png(),
                name=f"Item '{item['item_name']}' - NOT FOUND after restoration",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Item '{item['item_name']}' not found after restoration")