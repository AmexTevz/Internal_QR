import time
import pytest
import allure
import json
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.category_management import CategoryManagementAPI
from datetime import datetime

from tests.checkout_flows.test_checkout_rounds import attach_note

TABLES = [56]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.all
@pytest.mark.integration
@pytest.mark.category_integration
@pytest.mark.category_availability
@allure.feature("Category Management")
@allure.story("Category Availability by Time")
@allure.title("Category Availability by Time")
def test_category_unavailable_outside_hours(browser_factory, endpoint_setup, table):
    """
    Test that categories hide when their time window is set outside current time.

    Flow:
    1. Navigate to main menu
    2. Select random visible category and capture original state
    3. Make category unavailable by setting time window outside current time
    4. Restart browser
    5. Verify category is hidden from navigation
    6. Scroll to neighboring category to show where hidden category should be
    7. Restore original time window via API
    8. Restart browser and verify category is visible again
    """

    api = CategoryManagementAPI()
    timestamp = datetime.now().strftime("%B %d, %Y %H:%M")
    allure.dynamic.title(f"Category Availability by Time - {timestamp}")
    [driver] = browser_factory("chrome")
    menu_page = MenuPage(driver)
    attach_note("This test verifies the behaviour when category hours are set outside the current time window", "Test Description")
    menu_page.navigate_to_main_menu()

    category = api.get_random_visible_category(menu_page)

    with allure.step(f"Selected category: {category['name']}"):
        api_details = api.get_category_api_details(category['id'], category['details'])
        allure.attach(
            json.dumps(api_details, indent=2),
            name="Category API Details - Original State",
            attachment_type=allure.attachment_type.JSON
        )

        category_section = driver.find_element("css selector", f"section[data-categoryid='{category['id']}']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", category_section)
        time.sleep(2)

        allure.attach(
            driver.get_screenshot_as_png(),
            name=f"Category '{category['name']}' - Visible and Active",
            attachment_type=allure.attachment_type.PNG
        )

    with allure.step(f"Make category '{category['name']}' unavailable"):
        api.make_category_unavailable(category['id'], category['details'])


    with allure.step("Restart browser"):
        drivers = browser_factory("chrome")
        new_driver = drivers[-1]
        new_menu_page = MenuPage(new_driver)
        new_menu_page.navigate_to_main_menu()

    with allure.step(f"Verify category '{category['name']}' is hidden"):
        visible = new_menu_page.get_all_category_buttons()
        visible_names = [cat['name'] for cat in visible]
        assert category['name'] not in visible_names

        if category['neighbor_id']:
            neighbor_section = new_driver.find_element("css selector",
                                                       f"section[data-categoryid='{category['neighbor_id']}']")
            new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", neighbor_section)
            time.sleep(3)

        allure.attach(
            new_driver.get_screenshot_as_png(),
            name=f"Category '{category['name']}' - Hidden (showing neighbor '{category['neighbor_name']}')",
            attachment_type=allure.attachment_type.PNG
        )

    with allure.step(f"Restore category '{category['name']}'"):
        api.restore_category_times(
            category['id'],
            category['details'],
            category['original_open_time'],
            category['original_close_time']
        )

        drivers = browser_factory("chrome")
        verify_driver = drivers[-1]
        verify_menu_page = MenuPage(verify_driver)
        verify_menu_page.navigate_to_main_menu()

        restored_category_section = verify_driver.find_element("css selector",
                                                               f"section[data-categoryid='{category['id']}']")
        verify_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", restored_category_section)
        time.sleep(2)

        allure.attach(
            verify_driver.get_screenshot_as_png(),
            name=f"Category '{category['name']}' - Restored and Visible",
            attachment_type=allure.attachment_type.PNG
        )