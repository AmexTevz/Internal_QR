import pytest
import allure
import pytest_check as check
from datetime import datetime, time as dt_time
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.get_menu import get_menu_categories, get_active_categories, get_full_menu
from src.data.endpoints.close_table import close_table
from datetime import datetime

def attach_note(note_text, name="Note"):
    allure.attach(
        note_text,
        name=name,
        attachment_type=allure.attachment_type.TEXT
    )


def parse_time_string(time_str):
    try:
        hours, minutes, seconds = map(int, time_str.split(':'))
        return dt_time(hours, minutes, seconds)
    except Exception:
        return None


def is_time_in_range(open_time_str, close_time_str):
    current_time = datetime.now().time()
    open_time = parse_time_string(open_time_str)
    close_time = parse_time_string(close_time_str)

    if not open_time or not close_time:
        return False, current_time.strftime("%H:%M:%S")

    is_in_range = open_time <= current_time <= close_time
    return is_in_range, current_time.strftime("%H:%M:%S")


def category_has_available_items(category_id, menu_data):

    if not menu_data or 'Items' not in menu_data:
        return False

    for item in menu_data['Items']:
        # Check if this item belongs to the category
        item_categories = item.get('Categories', [])
        for cat in item_categories:
            if cat.get('ID') == category_id:
                # Check if item is available
                is_active = item.get('Active', False)
                is_in_stock = not item.get('IsOutOfStock', False)

                if is_active and is_in_stock:
                    return True

    return False


TABLES = [53]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.categories
@pytest.mark.functional
@pytest.mark.all
@allure.feature("Categories")
@allure.title("Category Navigation and API Verification")
def test_category_navigation_and_api_verification(browser_factory, endpoint_setup, table):
    """
    Test that UI categories match API data and respect time windows.

    Flow:
    1. Navigate to main menu
    2. Get all category buttons from UI
    3. Get all categories and active categories from API
    4. For each UI category, verify navigation works
    5. Verify category is within its time window (OpenTime/CloseTime)
    6. Verify category has Active=true in API
    7. Check for missing categories (active in API, in time window, has items, but not in UI)
    8. Check for inactive categories incorrectly showing in UI
    9. Attach summary of missing and inactive categories
    """

    timestamp = datetime.now().strftime("%B %d, %Y %H:%M")
    allure.dynamic.title(f"Category Navigation and API Verification - {timestamp}")
    [chrome] = browser_factory("chrome")
    menu_page = MenuPage(chrome)

    try:
        menu_page.navigate_to_main_menu()

        # Get data
        ui_categories = menu_page.get_all_category_buttons()
        check.is_true(len(ui_categories) > 0, "No categories found in UI")

        all_api_categories = get_menu_categories()
        check.is_not_none(all_api_categories, "Failed to get API categories")

        active_api_categories = get_active_categories()

        # Get full menu data for checking available items
        full_menu_data = get_full_menu()
        check.is_not_none(full_menu_data, "Failed to get full menu data")

        # Create API lookup
        api_by_id = {cat['ID']: cat for cat in all_api_categories}
        active_api_ids = {cat['ID'] for cat in active_api_categories}

        attach_note(
            f"UI Categories: {len(ui_categories)}\n"
            f"API Categories: {len(all_api_categories)}\n"
            f"Active API Categories: {len(active_api_ids)}",
            "Category Counts"
        )

        # Test each UI category
        for ui_cat in ui_categories:
            category_id = ui_cat['id']
            category_name = ui_cat['name']

            with allure.step(f"Testing category: {category_name}"):
                # Verify category navigation (all UI checks done in menu_page)
                nav_results = menu_page.verify_category_navigation(category_id, category_name)

                # Main test 1: Section should appear in viewport
                # check.is_true(
                #     nav_results['section_visible'],
                #     f"Section '{category_name}' did not appear in viewport after clicking"
                # )

                # Verify API data
                api_cat = api_by_id.get(category_id)
                check.is_not_none(api_cat, f"Category '{category_name}' not found in API")

                if api_cat:
                    # Main test 2: Category timing check
                    open_time = api_cat.get('OpenTime', '00:00:00')
                    close_time = api_cat.get('CloseTime', '23:59:59')
                    in_range, current_time = is_time_in_range(open_time, close_time)

                    check.is_true(
                        in_range,
                        f"Category '{category_name}' is outside its time window. "
                        f"Current time: {current_time}, Window: {open_time}-{close_time}"
                    )

                    # Check API active status
                    is_active = api_cat.get('Active', False)
                    check.is_true(is_active, f"Category '{category_name}' should have Active=true in API")

                    menu_page.attach_api_category_data(api_cat, category_name)

        # Check for missing categories
        ui_category_ids = {cat['id'] for cat in ui_categories}
        missing_categories = []
        empty_categories = []

        excluded_categories = ['To-Go Upsell']

        for api_cat in active_api_categories:
            api_cat_id = api_cat['ID']
            api_cat_name = api_cat['Name']

            # Skip excluded categories
            if api_cat_name in excluded_categories:
                continue

            # Check if in time window
            open_time = api_cat.get('OpenTime', '00:00:00')
            close_time = api_cat.get('CloseTime', '23:59:59')
            in_range, current_time = is_time_in_range(open_time, close_time)

            # Only check categories that are in time window and not in UI
            if in_range and api_cat_id not in ui_category_ids:
                has_items = category_has_available_items(api_cat_id, full_menu_data)

                if has_items:
                    missing_categories.append(api_cat_name)
                    check.fail(
                        f"Category '{api_cat_name}' (ID: {api_cat_id}) is active in API, "
                        f"in time window ({open_time}-{close_time}), has available items, "
                        f"but is missing from UI"
                    )
                else:
                    empty_categories.append(api_cat_name)

        if missing_categories:
            attach_note(
                "\n".join([f"- {name}" for name in missing_categories]),
                "⚠️ Missing Categories (Have Available Items)"
            )

        if empty_categories:
            attach_note(
                "\n".join([f"- {name} (correctly hidden - no active, in-stock items)" for name in empty_categories]),
                "Empty Categories (Correctly Hidden)"
            )

        # Check for inactive categories in UI
        inactive_in_ui = []

        for ui_cat in ui_categories:
            ui_cat_id = ui_cat['id']
            ui_cat_name = ui_cat['name']

            api_cat = api_by_id.get(ui_cat_id)
            if api_cat and not api_cat.get('Active', False):
                inactive_in_ui.append(ui_cat_name)
                check.fail(
                    f"Category '{ui_cat_name}' (ID: {ui_cat_id}) is INACTIVE in API "
                    f"but appears in UI navigation"
                )

        if inactive_in_ui:
            attach_note(
                "\n".join([f"- {name}" for name in inactive_in_ui]),
                "⚠️ Inactive Categories in UI"
            )

    except Exception as e:
        close_table()
        print(f"Error: {str(e)}")
        raise