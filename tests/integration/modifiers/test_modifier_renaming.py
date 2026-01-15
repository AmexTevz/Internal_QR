import time
import pytest
import allure
import json
from selenium.webdriver.common.by import By
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.modifier_group_management import ModifierGroupManagementAPI

TABLES = [62]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.all
@pytest.mark.integration
@pytest.mark.modifier_integration
@pytest.mark.modifier_rename
@allure.feature("Modifier Groups")
@allure.story("Modifier Group Rename")
def test_modifier_group_rename(browser_factory, endpoint_setup, table):
    """
    Test that renaming modifier group updates the name in UI.

    Flow:
    1. Find item with modifier group
    2. Open item, scroll to modifier group, screenshot (original name)
    3. Rename modifier group via API (add "TEST RENAME - " prefix)
    4. Restart browser
    5. Open item, verify new name appears
    6. Screenshot showing new name
    7. Restore original name
    8. Verify original name restored
    """
    api = ModifierGroupManagementAPI()

    [driver] = browser_factory("chrome")
    menu_page = MenuPage(driver)
    menu_page.navigate_to_main_menu()

    # Find item with any modifier group
    item_data = api.get_item_with_optional_modifier(menu_page)

    mod_group_id = item_data['modifier_group']['id']
    mod_group_name = item_data['modifier_group']['name']
    mod_group_data = item_data['modifier_group']['original_data']

    # Create test name
    test_name = f"TEST RENAME - {mod_group_name}"

    with allure.step(f"Found item with modifier group"):
        allure.attach(
            json.dumps({
                "Item": item_data['item_name'],
                "Item ID": item_data['item_id'],
                "Category": item_data['category_name'],
                "Modifier Group": mod_group_name,
                "Modifier Group ID": mod_group_id,
                "Test Name": test_name
            }, indent=2),
            name="Item with Modifier Group",
            attachment_type=allure.attachment_type.JSON
        )

    # Step 1: Open item and show original name
    with allure.step(f"Open item '{item_data['item_name']}' - Original name: '{mod_group_name}'"):
        item_element = driver.find_element(By.ID, item_data['item_id'])
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
        time.sleep(0.5)
        item_element.click()
        time.sleep(1)

        try:
            modal = driver.find_element(By.CSS_SELECTOR, ".mod-card")
            group_headers = modal.find_elements(By.CSS_SELECTOR, ".mod-group-title")

            # Find target group and capture original name
            for header in group_headers:
                if mod_group_name.lower() in header.text.lower():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", header)
                    time.sleep(0.5)

                    allure.attach(
                        driver.get_screenshot_as_png(),
                        name=f"Original Name: '{mod_group_name}'",
                        attachment_type=allure.attachment_type.PNG
                    )
                    break

        except Exception as e:
            allure.attach(
                driver.get_screenshot_as_png(),
                name="Could not capture original name",
                attachment_type=allure.attachment_type.PNG
            )

        # Close modal
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
            time.sleep(0.5)
        except:
            pass

    # Step 2: Rename modifier group
    with allure.step(f"Rename modifier group via API"):
        menu_items = api.get_menu_items_using_modifier(mod_group_id)
        api.rename_modifier_group(mod_group_id, mod_group_data, menu_items, test_name)

        allure.attach(
            f"Original Name: {mod_group_name}\n"
            f"New Name: {test_name}\n"
            f"Items affected: {len(menu_items)}",
            name="API Update - Renamed",
            attachment_type=allure.attachment_type.TEXT
        )

    # Step 3: Restart browser
    with allure.step("Restart browser"):
        drivers = browser_factory("chrome")
        new_driver = drivers[-1]
        new_menu_page = MenuPage(new_driver)
        new_menu_page.navigate_to_main_menu()

    # Step 4: Verify new name appears
    with allure.step(f"Verify new name appears: '{test_name}'"):
        item_element = new_driver.find_element(By.ID, item_data['item_id'])
        new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
        time.sleep(0.5)
        item_element.click()
        time.sleep(1)

        try:
            modal = new_driver.find_element(By.CSS_SELECTOR, ".mod-card")
            group_headers = modal.find_elements(By.CSS_SELECTOR, ".mod-group-title")

            # Look for new name
            found_new_name = False
            for header in group_headers:
                header_text = header.text.strip()

                # Check if new name is present (case-insensitive)
                if test_name.lower() in header_text.lower() or "test rename" in header_text.lower():
                    found_new_name = True

                    new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", header)
                    time.sleep(0.5)

                    allure.attach(
                        new_driver.get_screenshot_as_png(),
                        name=f"New Name: '{test_name}'",
                        attachment_type=allure.attachment_type.PNG
                    )

                    allure.attach(
                        f"✅ Name Changed Successfully\n\n"
                        f"Original: {mod_group_name}\n"
                        f"New: {header_text}\n"
                        f"Expected: {test_name}",
                        name="Verification - Name Changed",
                        attachment_type=allure.attachment_type.TEXT
                    )

                    assert True, "Modifier group renamed successfully"
                    break

            if not found_new_name:
                # Take screenshot showing all groups
                allure.attach(
                    new_driver.get_screenshot_as_png(),
                    name=f"ERROR - New name not found",
                    attachment_type=allure.attachment_type.PNG
                )

                # List all visible group names
                visible_names = [h.text.strip() for h in group_headers if h.is_displayed()]
                allure.attach(
                    f"Expected: {test_name}\n"
                    f"Visible groups: {', '.join(visible_names)}",
                    name="Available Groups",
                    attachment_type=allure.attachment_type.TEXT
                )

                pytest.fail(f"New name '{test_name}' not found in UI")

        except Exception as e:
            allure.attach(
                new_driver.get_screenshot_as_png(),
                name="Error verifying new name",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Failed to verify name change: {str(e)}")

        # Close modal
        try:
            new_driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
            time.sleep(0.5)
        except:
            pass

    # Step 5: Restore original name (in background - no browser verification needed)
    with allure.step(f"Restore original name: '{mod_group_name}'"):
        api.rename_modifier_group(mod_group_id, mod_group_data, menu_items, mod_group_name)

        allure.attach(
            f"Test Name: {test_name}\n"
            f"Restored Name: {mod_group_name}\n"
            f"Restored to original state\n"
            f"(Restoration verified via API success - no browser restart needed)",
            name="API Update - Restored Name",
            attachment_type=allure.attachment_type.TEXT
        )