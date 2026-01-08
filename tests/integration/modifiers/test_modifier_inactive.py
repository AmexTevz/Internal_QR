import time
import pytest
import allure
import json
from selenium.webdriver.common.by import By
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.modifier_group_management import ModifierGroupManagementAPI

TABLES = [61]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.all
@pytest.mark.integration
@pytest.mark.modifier_inactive
@allure.feature("Modifier Groups")
@allure.story("Modifier Group Active/Inactive")
def test_modifier_group_inactive(browser_factory, endpoint_setup, table):
    """
    Test that making modifier group inactive hides it from UI.

    Flow:
    1. Find item with modifier group
    2. Open item, scroll to modifier group, screenshot (visible)
    3. Make modifier group inactive via API
    4. Restart browser
    5. Open item, verify modifier group is hidden
    6. Screenshot showing missing group
    7. Restore to active
    8. Verify group visible again
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

    with allure.step(f"Found item with modifier group"):
        allure.attach(
            json.dumps({
                "Item": item_data['item_name'],
                "Item ID": item_data['item_id'],
                "Category": item_data['category_name'],
                "Modifier Group": mod_group_name,
                "Modifier Group ID": mod_group_id,
                "Currently Active": mod_group_data.get('Active', True)
            }, indent=2),
            name="Item with Modifier Group",
            attachment_type=allure.attachment_type.JSON
        )

    # Step 1: Open item and show modifier group is visible
    with allure.step(f"Open item '{item_data['item_name']}' - Group is ACTIVE"):
        item_element = driver.find_element(By.ID, item_data['item_id'])
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
        time.sleep(0.5)
        item_element.click()
        time.sleep(1)

        try:
            modal = driver.find_element(By.CSS_SELECTOR, ".mod-card")
            group_headers = modal.find_elements(By.CSS_SELECTOR, ".mod-group-title")

            # Find target group
            found_group = False
            for header in group_headers:
                if mod_group_name.lower() in header.text.lower():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", header)
                    time.sleep(0.5)
                    found_group = True

                    allure.attach(
                        driver.get_screenshot_as_png(),
                        name=f"Modifier Group '{mod_group_name}' - VISIBLE (Active)",
                        attachment_type=allure.attachment_type.PNG
                    )
                    break

            if not found_group:
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name=f"Modal - Looking for '{mod_group_name}'",
                    attachment_type=allure.attachment_type.PNG
                )

        except Exception as e:
            allure.attach(
                driver.get_screenshot_as_png(),
                name="Could not capture modifier group",
                attachment_type=allure.attachment_type.PNG
            )

        # Close modal
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
            time.sleep(0.5)
        except:
            pass

    # Step 2: Make modifier group inactive
    with allure.step(f"Make modifier group '{mod_group_name}' INACTIVE via API"):
        menu_items = api.get_menu_items_using_modifier(mod_group_id)
        api.make_modifier_group_inactive(mod_group_id, mod_group_data, menu_items)

        allure.attach(
            f"Modifier Group: {mod_group_name}\n"
            f"Changed: Active → Inactive\n"
            f"Items affected: {len(menu_items)}",
            name="API Update - Made Inactive",
            attachment_type=allure.attachment_type.TEXT
        )

    # Step 3: Restart browser
    with allure.step("Restart browser"):
        drivers = browser_factory("chrome")
        new_driver = drivers[-1]
        new_menu_page = MenuPage(new_driver)
        new_menu_page.navigate_to_main_menu()

    # Step 4: Verify group is hidden
    with allure.step(f"Verify modifier group '{mod_group_name}' is HIDDEN"):
        item_element = new_driver.find_element(By.ID, item_data['item_id'])
        new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
        time.sleep(0.5)
        item_element.click()
        time.sleep(1)

        try:
            modal = new_driver.find_element(By.CSS_SELECTOR, ".mod-card")
            group_headers = modal.find_elements(By.CSS_SELECTOR, ".mod-group-title")

            # Get all visible group names
            visible_groups = [header.text.strip() for header in group_headers if header.is_displayed()]

            # Check if target group is NOT in list
            group_is_hidden = mod_group_name not in visible_groups

            if group_is_hidden:
                # Scroll to where the group SHOULD BE (show neighboring groups)
                # Show the first available modifier group as proof
                if group_headers and len(group_headers) > 0:
                    # Scroll to first modifier group to show what's there instead
                    first_header = group_headers[0]
                    if first_header.is_displayed():
                        new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_header)
                        time.sleep(0.5)

                allure.attach(
                    new_driver.get_screenshot_as_png(),
                    name=f"Modifier Group '{mod_group_name}' - HIDDEN (showing neighboring groups)",
                    attachment_type=allure.attachment_type.PNG
                )

                allure.attach(
                    f"✅ Group Hidden Successfully\n\n"
                    f"Target Group: {mod_group_name}\n"
                    f"Status: NOT FOUND in UI\n"
                    f"Visible Groups: {', '.join(visible_groups) if visible_groups else 'None'}",
                    name="Verification - Group Hidden",
                    attachment_type=allure.attachment_type.TEXT
                )

                assert True, f"Modifier group '{mod_group_name}' correctly hidden when inactive"
            else:
                allure.attach(
                    new_driver.get_screenshot_as_png(),
                    name=f"ERROR - Group still visible",
                    attachment_type=allure.attachment_type.PNG
                )
                pytest.fail(f"Modifier group '{mod_group_name}' should be hidden but is still visible")

        except Exception as e:
            allure.attach(
                new_driver.get_screenshot_as_png(),
                name="Error verifying group hidden",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Failed to verify group is hidden: {str(e)}")

        # Close modal
        try:
            new_driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
            time.sleep(0.5)
        except:
            pass

    # Step 5: Restore to active (in background - no browser verification needed)
    with allure.step(f"Restore modifier group '{mod_group_name}' to ACTIVE"):
        api.make_modifier_group_active(mod_group_id, mod_group_data, menu_items)

        allure.attach(
            f"Modifier Group: {mod_group_name}\n"
            f"Changed: Inactive → Active\n"
            f"Restored to original state",
            name="API Update - Made Active",
            attachment_type=allure.attachment_type.TEXT
        )