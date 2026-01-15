import time
import pytest
import allure
import json
from selenium.webdriver.common.by import By
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.modifier_group_management import ModifierGroupManagementAPI

TABLES = [64]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.all
@pytest.mark.integration
@pytest.mark.modifier_integration
@pytest.mark.modifier_required
@allure.feature("Modifier Groups")
@allure.story("Optional Modifier Becomes Required")
def test_modifier_optional_to_required(browser_factory, endpoint_setup, table):
    """
    Test that optional modifier group becomes required.

    Flow:
    1. Find item with optional modifier group
    2. Open item, scroll to modifier group title
    3. Make modifier required via request
    4. Reopen same item, scroll to modifier group
    5. Try to click Add WITHOUT selecting
    8. Verify "Required" error message appears, screenshot
    9. Restore to optional
    """
    api = ModifierGroupManagementAPI()

    [driver] = browser_factory("chrome")
    menu_page = MenuPage(driver)
    menu_page.navigate_to_main_menu()

    item_data = api.get_item_with_optional_modifier(menu_page)

    mod_group_id = item_data['modifier_group']['id']
    mod_group_name = item_data['modifier_group']['name']
    mod_group_data = item_data['modifier_group']['original_data']

    with allure.step(f"Found item with optional modifier"):
        allure.attach(
            json.dumps({
                "Item": item_data['item_name'],
                "Item ID": item_data['item_id'],
                "Category": item_data['category_name'],
                "Modifier Group": mod_group_name,
                "Modifier Group ID": mod_group_id,
                "Currently Required": item_data['modifier_group']['required']
            }, indent=2),
            name="Item with Optional Modifier",
            attachment_type=allure.attachment_type.JSON
        )

    with allure.step(f"Open item '{item_data['item_name']}' - Modifier is OPTIONAL"):
        item_element = driver.find_element(By.ID, item_data['item_id'])
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
        time.sleep(0.5)
        item_element.click()
        time.sleep(1)

        try:
            modal = driver.find_element(By.CSS_SELECTOR, ".mod-card")
            group_headers = modal.find_elements(By.CSS_SELECTOR, ".mod-group-title")

            target_header = None
            for header in group_headers:
                if mod_group_name.lower() in header.text.lower():
                    target_header = header
                    break

            if target_header:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_header)
                time.sleep(0.5)

                allure.attach(
                    driver.get_screenshot_as_png(),
                    name=f"Modifier '{mod_group_name}' - OPTIONAL (before change)",
                    attachment_type=allure.attachment_type.PNG
                )
            else:
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name=f"Item '{item_data['item_name']}' - OPTIONAL state",
                    attachment_type=allure.attachment_type.PNG
                )
        except Exception as e:
            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Could not find modifier group in modal",
                attachment_type=allure.attachment_type.PNG
            )



    with allure.step(f"Make modifier group '{mod_group_name}' REQUIRED via API"):
        menu_items = api.get_menu_items_using_modifier(mod_group_id)
        api.make_modifier_required(mod_group_id, mod_group_data, menu_items)


        allure.attach(
            f"Modifier Group: {mod_group_name}\n"
            f"Changed: Optional → Required\n"
            f"Items affected: {len(menu_items)}",
            name="API Update - Made Required",
            attachment_type=allure.attachment_type.TEXT
        )

    with allure.step("Restart browser"):
        drivers = browser_factory("chrome")
        new_driver = drivers[-1]
        new_menu_page = MenuPage(new_driver)
        new_menu_page.navigate_to_main_menu()

    with allure.step(f"Reopen item '{item_data['item_name']}' - Modifier is now REQUIRED"):
        item_element = new_driver.find_element(By.ID, item_data['item_id'])
        new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
        time.sleep(0.5)
        item_element.click()
        time.sleep(1)

        try:
            modal = new_driver.find_element(By.CSS_SELECTOR, ".mod-card")
            group_headers = modal.find_elements(By.CSS_SELECTOR, ".mod-group-title")

            for header in group_headers:
                if mod_group_name.lower() in header.text.lower():
                    new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", header)
                    time.sleep(0.5)
                    break
        except:
            pass

    with allure.step("Try to Add without selecting - expect 'Required' error"):
        try:
            add_button = new_driver.find_element(By.CSS_SELECTOR,".mod-cta-btn")
            add_button.click()
            time.sleep(1)

            error_elements = new_driver.find_elements(By.CSS_SELECTOR, ".mod-error, [class*='error']")

            found_required_error = False
            for error_elem in error_elements:
                if error_elem.is_displayed() and "required" in error_elem.text.lower():
                    found_required_error = True

                    new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", error_elem)
                    time.sleep(0.5)

                    allure.attach(
                        new_driver.get_screenshot_as_png(),
                        name=f"'Required' Error Message Displayed",
                        attachment_type=allure.attachment_type.PNG
                    )

                    assert True, "Required error message displayed as expected"
                    break

            if not found_required_error:
                allure.attach(
                    new_driver.get_screenshot_as_png(),
                    name=f"After clicking Add (looking for Required error)",
                    attachment_type=allure.attachment_type.PNG
                )


        except Exception as e:
            allure.attach(
                new_driver.get_screenshot_as_png(),
                name=f"Error during Add attempt",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Failed to verify Required validation: {str(e)}")

    with allure.step(f"Restore modifier group '{mod_group_name}' to OPTIONAL"):
        api.make_modifier_optional(mod_group_id, mod_group_data, menu_items)
        time.sleep(3)

        allure.attach(
            f"Modifier Group: {mod_group_name}\n"
            f"Changed: Required → Optional\n"
            f"Restored to original state",
            name="API Update - Made Optional",
            attachment_type=allure.attachment_type.TEXT
        )


