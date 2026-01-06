import time
import pytest
import allure
import json
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.item_management import ItemManagementAPI
from datetime import datetime

TABLES = [27]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.integration
@pytest.mark.item_categories
@allure.feature("Item Management")
@allure.story("Item Hidden When Removed From All Categories")
def test_item_hidden_when_removed_from_categories(browser_factory, endpoint_setup, table):
    api = ItemManagementAPI()

    [driver] = browser_factory("chrome")
    menu_page = MenuPage(driver)
    menu_page.navigate_to_main_menu()

    # Get random item
    item = api.get_random_visible_item(menu_page)

    # Get full item details including all categories
    item_details = api.get_item_with_categories(item['item_id'])

    with allure.step(f"Selected item: {item['item_name']}"):
        category_names = [cat['Name'] for cat in item_details['categories']]

        allure.attach(
            json.dumps({
                "Item Name": item['item_name'],
                "Item ID": item['item_id'],
                "Price": f"${item['price']:.2f}",
                "Categories": category_names,
                "Number of Categories": len(item_details['categories']),
                "Original Active Status": item_details['active']
            }, indent=2),
            name="Item Details - Before",
            attachment_type=allure.attachment_type.JSON
        )

        # Scroll to the item in its first category
        try:
            item_element = driver.find_element(By.ID, item['item_id'])
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
            time.sleep(1)

            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Item '{item['item_name']}' - Visible in {category_names[0]}",
                attachment_type=allure.attachment_type.PNG
            )
        except NoSuchElementException:
            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Item '{item['item_name']}' - Could not find element",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Could not find item element with ID: {item['item_id']}")

    with allure.step(f"Remove item '{item['item_name']}' from all {len(category_names)} categories"):
        api.remove_item_from_all_categories(item['item_id'])
        time.sleep(3)

    with allure.step("Restart browser"):
        drivers = browser_factory("chrome")
        new_driver = drivers[-1]
        new_menu_page = MenuPage(new_driver)
        new_menu_page.navigate_to_main_menu()

    with allure.step(f"Verify item '{item['item_name']}' is hidden from all categories"):
        # Check all categories where item was previously visible
        for category in item_details['categories']:
            category_name = category['Name']
            category_id = category['ID']

            with allure.step(f"Check category: {category_name}"):
                try:
                    # Try to find the category
                    category_section = new_driver.find_element(
                        By.CSS_SELECTOR,
                        f"section[data-categoryid='{category_id}']"
                    )
                    new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", category_section)
                    time.sleep(1)

                    # Category exists - verify item is not in it
                    item_elements = new_driver.find_elements(By.ID, item['item_id'])
                    visible_items = [elem for elem in item_elements if elem.is_displayed()]

                    assert len(visible_items) == 0, \
                        f"Item '{item['item_name']}' should be hidden in category '{category_name}'"

                    allure.attach(
                        new_driver.get_screenshot_as_png(),
                        name=f"Category '{category_name}' - Item Hidden",
                        attachment_type=allure.attachment_type.PNG
                    )

                except NoSuchElementException:
                    # Category itself disappeared (item was only item in category)
                    allure.attach(
                        new_driver.get_screenshot_as_png(),
                        name=f"Category '{category_name}' - Also Hidden (item was only item)",
                        attachment_type=allure.attachment_type.PNG
                    )
                    # This is expected behavior - category disappears if it has no items

        # Global check - item should not be visible anywhere
        all_item_elements = new_driver.find_elements(By.ID, item['item_id'])
        visible_anywhere = [elem for elem in all_item_elements if elem.is_displayed()]

        assert len(visible_anywhere) == 0, \
            f"Item '{item['item_name']}' should not be visible anywhere, but found {len(visible_anywhere)} visible instances"

    with allure.step(f"Restore item '{item['item_name']}' to original categories"):
        # Extract just the category IDs (not full objects)
        category_ids = [cat['ID'] for cat in item_details['categories']]

        api.restore_item_to_categories(item['item_id'], category_ids)
        time.sleep(3)

        drivers = browser_factory("chrome")
        verify_driver = drivers[-1]
        verify_menu_page = MenuPage(verify_driver)
        verify_menu_page.navigate_to_main_menu()

        # Verify item is visible again in at least one category
        try:
            restored_item = verify_driver.find_element(By.ID, item['item_id'])
            verify_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", restored_item)
            time.sleep(1)

            assert restored_item.is_displayed(), \
                f"Item '{item['item_name']}' should be visible after restoration"

            allure.attach(
                verify_driver.get_screenshot_as_png(),
                name=f"Item '{item['item_name']}' - Restored and Visible",
                attachment_type=allure.attachment_type.PNG
            )

        except NoSuchElementException:
            allure.attach(
                verify_driver.get_screenshot_as_png(),
                name=f"Item '{item['item_name']}' - NOT FOUND after restoration",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Item '{item['item_name']}' not found after restoration to categories")