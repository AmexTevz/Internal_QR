import time
import pytest
import allure
import json
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.modifier_group_management import ModifierGroupManagementAPI
from datetime import datetime

TABLES = [70]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.all
@pytest.mark.integration
@pytest.mark.modifier_integration
@pytest.mark.modifier_item_inactive
@allure.feature("Modifier Management")
@allure.story("Modifier Item Active Status")
def test_modifier_item_hidden_when_inactive(browser_factory, endpoint_setup, table):
    """
    Test that individual modifier item hides when marked as inactive.

    Flow:
    1. Navigate to main menu
    2. Select random item with modifiers
    3. Add item to cart to open modifier modal
    4. Select random modifier from a modifier group
    5. Center and screenshot the modifier
    6. Make modifier inactive via API
    7. Restart browser and open same item again
    8. Verify modifier is no longer in the modifier group
    9. Restore modifier to active status
    10. Restart browser and verify modifier is visible again
    """

    api = ModifierGroupManagementAPI()
    timestamp = datetime.now().strftime("%B %d, %Y %H:%M")
    allure.dynamic.title(f"Modifier Item Active Status - {timestamp}")

    [driver] = browser_factory("chrome")
    menu_page = MenuPage(driver)
    menu_page.navigate_to_main_menu()

    # Get random item with modifiers
    item_data = api.get_item_with_optional_modifier(menu_page)

    with allure.step(f"Selected item: {item_data['item_name']}"):
        allure.attach(
            json.dumps({
                "Item Name": item_data['item_name'],
                "Item ID": item_data['item_id'],
                "Category": item_data['category_name'],
                "Modifier Group": item_data['modifier_group']['name']
            }, indent=2),
            name="Item Details",
            attachment_type=allure.attachment_type.JSON
        )

    with allure.step("Click item to open modifiers modal"):
        # Scroll to item
        try:
            category_section = driver.find_element("css selector",
                                                   f"section[data-categoryid='{item_data['category_id']}']")
            driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", category_section)
            time.sleep(0.5)

            item_element = driver.find_element(By.ID, item_data['item_id'])
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
            time.sleep(1)

            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Item: '{item_data['item_name']}'",
                attachment_type=allure.attachment_type.PNG
            )

            # Click item to open modal
            menu_page.click(item_element)
            time.sleep(1)

        except NoSuchElementException:
            pytest.fail(f"Could not find item element with ID: {item_data['item_id']}")

        # Modal should be open now
        try:
            modal = driver.find_element(By.CSS_SELECTOR, ".mod-card")
            allure.attach(
                driver.get_screenshot_as_png(),
                name="Modifier Modal Opened",
                attachment_type=allure.attachment_type.PNG
            )
        except:
            allure.attach(
                driver.get_screenshot_as_png(),
                name="Could not find modal",
                attachment_type=allure.attachment_type.PNG
            )

    # Get random modifier from this item
    modifier = api.get_random_modifier_from_item(item_data['item_id'])

    with allure.step(
            f"Selected modifier: '{modifier['modifier_name']}' from group '{modifier['modifier_group_name']}'"):
        allure.attach(
            json.dumps({
                "Modifier Name": modifier['modifier_name'],
                "Modifier ID": modifier['modifier_id'],
                "Modifier Group": modifier['modifier_group_name'],
                "Modifier Group ID": modifier['modifier_group_id'],
                "Original Active": modifier['original_active']
            }, indent=2),
            name="Modifier Details",
            attachment_type=allure.attachment_type.JSON
        )

        # Find and center the modifier
        try:
            # Find modifier by ID or text
            modifier_elements = driver.find_elements(By.CSS_SELECTOR, f"[data-modifierid='{modifier['modifier_id']}']")
            if not modifier_elements:
                # Fallback: search by text
                modifier_elements = driver.find_elements(By.XPATH,
                                                         f"//*[contains(text(), '{modifier['modifier_name']}')]")

            if modifier_elements:
                modifier_element = modifier_elements[0]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", modifier_element)
                time.sleep(0.5)

                allure.attach(
                    driver.get_screenshot_as_png(),
                    name=f"Modifier '{modifier['modifier_name']}' - Visible",
                    attachment_type=allure.attachment_type.PNG
                )
            else:
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name="Could not locate specific modifier element",
                    attachment_type=allure.attachment_type.PNG
                )
        except Exception as e:
            allure.attach(
                driver.get_screenshot_as_png(),
                name="Error locating modifier",
                attachment_type=allure.attachment_type.PNG
            )

    with allure.step(f"Make modifier '{modifier['modifier_name']}' inactive via API"):
        api.make_modifier_item_inactive(modifier['modifier_id'])
        time.sleep(3)  # Allow changes to propagate

        allure.attach(
            f"Modifier: {modifier['modifier_name']}\n"
            f"Modifier ID: {modifier['modifier_id']}\n"
            f"Status: Active → Inactive",
            name="API Update - Made Inactive",
            attachment_type=allure.attachment_type.TEXT
        )

    with allure.step("Close modal and restart browser"):
        # Close modal with ESC key
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
            time.sleep(0.5)
        except:
            pass

        # Restart browser
        drivers = browser_factory("chrome")
        new_driver = drivers[-1]
        new_menu_page = MenuPage(new_driver)
        new_menu_page.navigate_to_main_menu()

    with allure.step(f"Click item '{item_data['item_name']}' again and verify modifier is hidden"):
        # Scroll to item
        try:
            category_section = new_driver.find_element("css selector",
                                                       f"section[data-categoryid='{item_data['category_id']}']")
            new_driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", category_section)
            time.sleep(0.5)

            item_element = new_driver.find_element(By.ID, item_data['item_id'])
            new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
            time.sleep(1)
        except:
            pass

        # Click item to open modal
        try:
            item_element = new_driver.find_element(By.ID, item_data['item_id'])
            new_menu_page.click(item_element)
            time.sleep(1)
        except Exception as e:
            pytest.fail(f"Failed to click item: {str(e)}")

        # Check if modifier is present
        modifier_present = False
        try:
            # Try to find by ID
            modifier_elements = new_driver.find_elements(By.CSS_SELECTOR,
                                                         f"[data-modifierid='{modifier['modifier_id']}']")
            if not modifier_elements:
                # Try by text
                modifier_elements = new_driver.find_elements(By.XPATH,
                                                             f"//*[contains(text(), '{modifier['modifier_name']}')]")

            # Filter for visible elements
            visible_modifiers = [elem for elem in modifier_elements if elem.is_displayed()]

            if visible_modifiers:
                modifier_present = True

        except:
            pass

        # Take screenshot
        allure.attach(
            new_driver.get_screenshot_as_png(),
            name=f"Modifier '{modifier['modifier_name']}' - Should Be Hidden",
            attachment_type=allure.attachment_type.PNG
        )

        # Assert modifier is NOT present
        assert not modifier_present, \
            f"Modifier '{modifier['modifier_name']}' should be hidden but is still visible"

        allure.attach(
            f"✅ Modifier '{modifier['modifier_name']}' successfully hidden\n"
            f"Group: {modifier['modifier_group_name']}\n"
            f"Modifier not found in modal",
            name="Verification - Modifier Hidden",
            attachment_type=allure.attachment_type.TEXT
        )

    with allure.step(f"Restore modifier '{modifier['modifier_name']}' to active"):
        # Close modal with ESC key
        try:
            new_driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
            time.sleep(0.5)
        except:
            pass

        # Restore modifier
        api.make_modifier_item_active(modifier['modifier_id'])
        time.sleep(3)  # Allow changes to propagate

        allure.attach(
            f"Modifier: {modifier['modifier_name']}\n"
            f"Modifier ID: {modifier['modifier_id']}\n"
            f"Status: Inactive → Active",
            name="API Update - Restored Active",
            attachment_type=allure.attachment_type.TEXT
        )

        # Restart browser
        drivers = browser_factory("chrome")
        verify_driver = drivers[-1]
        verify_menu_page = MenuPage(verify_driver)
        verify_menu_page.navigate_to_main_menu()

        # Scroll to item
        try:
            category_section = verify_driver.find_element("css selector",
                                                          f"section[data-categoryid='{item_data['category_id']}']")
            verify_driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", category_section)
            time.sleep(0.5)

            item_element = verify_driver.find_element(By.ID, item_data['item_id'])
            verify_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
            time.sleep(1)
        except:
            pass

        # Click item to open modal
        try:
            item_element = verify_driver.find_element(By.ID, item_data['item_id'])
            verify_menu_page.click(item_element)
            time.sleep(1)
        except Exception as e:
            pytest.fail(f"Failed to click item: {str(e)}")

        # Verify modifier is visible again
        modifier_restored = False
        try:
            modifier_elements = verify_driver.find_elements(By.CSS_SELECTOR,
                                                            f"[data-modifierid='{modifier['modifier_id']}']")
            if not modifier_elements:
                modifier_elements = verify_driver.find_elements(By.XPATH,
                                                                f"//*[contains(text(), '{modifier['modifier_name']}')]")

            visible_modifiers = [elem for elem in modifier_elements if elem.is_displayed()]

            if visible_modifiers:
                modifier_restored = True
                # Center it
                verify_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", visible_modifiers[0])
                time.sleep(0.5)

        except:
            pass

        allure.attach(
            verify_driver.get_screenshot_as_png(),
            name=f"Modifier '{modifier['modifier_name']}' - Restored and Visible",
            attachment_type=allure.attachment_type.PNG
        )

        assert modifier_restored, \
            f"Modifier '{modifier['modifier_name']}' should be visible after restoration"

        allure.attach(
            f"✅ Modifier '{modifier['modifier_name']}' successfully restored\n"
            f"Group: {modifier['modifier_group_name']}\n"
            f"Modifier visible in modal",
            name="Verification - Modifier Restored",
            attachment_type=allure.attachment_type.TEXT
        )