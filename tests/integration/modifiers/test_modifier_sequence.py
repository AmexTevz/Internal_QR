import time
import pytest
import allure
import json
from selenium.webdriver.common.by import By
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.modifier_group_management import ModifierGroupManagementAPI

TABLES = [63]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.all
@pytest.mark.integration
@pytest.mark.modifier_integration
@pytest.mark.modifier_sequence
@allure.feature("Modifier Groups")
@allure.story("Modifier Group Sequence Order")
def test_modifier_group_sequence_change(browser_factory, endpoint_setup, table):
    """
    Test that modifier group sequence changes are reflected in UI order.

    Flow:
    1. Find item with at least 2 modifier groups
    2. Open item, note original order, screenshot
    3. Swap sequences via API (group1 <-> group2)
    4. Restart browser
    5. Open item, verify order changed via HTML elements
    6. Screenshot showing new order
    7. Restore original sequences
    8. Verify order restored
    """
    api = ModifierGroupManagementAPI()

    [driver] = browser_factory("chrome")
    menu_page = MenuPage(driver)
    menu_page.navigate_to_main_menu()

    # Step 1: Find item with multiple modifier groups
    item_data = api.get_item_with_multiple_modifiers(menu_page, min_groups=2)

    modifier_groups = item_data['modifier_groups']

    # Ensure we have at least 2 groups
    assert len(modifier_groups) >= 2, "Need at least 2 modifier groups"

    # Get first two groups to swap
    group1 = modifier_groups[0]
    group2 = modifier_groups[1]

    with allure.step(f"Found item with {len(modifier_groups)} modifier groups"):
        allure.attach(
            json.dumps({
                "Item": item_data['item_name'],
                "Item ID": item_data['item_id'],
                "Category": item_data['category_name'],
                "Modifier Groups": [
                    {
                        "Name": g['name'],
                        "ID": g['id'],
                        "Sequence": g['sequence'],
                        "Required": g['required']
                    }
                    for g in modifier_groups
                ]
            }, indent=2),
            name="Item with Multiple Modifier Groups",
            attachment_type=allure.attachment_type.JSON
        )

    # Step 2: Open item and capture original order
    with allure.step(f"Open item '{item_data['item_name']}' - Original sequence"):
        item_element = driver.find_element(By.ID, item_data['item_id'])
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
        time.sleep(0.5)
        item_element.click()
        time.sleep(1)

        try:
            modal = driver.find_element(By.CSS_SELECTOR, ".mod-card")
            group_headers = modal.find_elements(By.CSS_SELECTOR, ".mod-group-title")

            # Get original order from HTML
            original_order = [header.text.strip() for header in group_headers if header.is_displayed()]

            allure.attach(
                f"Original Order:\n" + "\n".join([f"{i + 1}. {name}" for i, name in enumerate(original_order)]),
                name="Original Modifier Order",
                attachment_type=allure.attachment_type.TEXT
            )

            # Scroll through groups for screenshot
            for header in group_headers[:2]:  # Show first two groups
                if header.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", header)
                    time.sleep(0.3)

            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Original Order: {group1['name']} → {group2['name']}",
                attachment_type=allure.attachment_type.PNG
            )

        except Exception as e:
            allure.attach(
                driver.get_screenshot_as_png(),
                name="Could not capture original order",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Failed to get original order: {str(e)}")

        # Close modal
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")  # ESC key
            time.sleep(0.5)
        except:
            pass

    # Step 3: Swap sequences via API
    with allure.step(f"Swap sequences: '{group1['name']}' ↔ '{group2['name']}'"):
        # Get menu items for both groups
        menu_items_group1 = api.get_menu_items_using_modifier(group1['id'])
        menu_items_group2 = api.get_menu_items_using_modifier(group2['id'])

        # Prepare updates - swap sequences
        updates = [
            {
                'modifier_group_id': group1['id'],
                'mod_group_data': group1['original_data'],
                'menu_items_list': menu_items_group1,
                'new_sequence': group2['sequence']  # Group1 gets Group2's sequence
            },
            {
                'modifier_group_id': group2['id'],
                'mod_group_data': group2['original_data'],
                'menu_items_list': menu_items_group2,
                'new_sequence': group1['sequence']  # Group2 gets Group1's sequence
            }
        ]

        api.update_modifier_sequences(updates)

        allure.attach(
            f"Group 1: '{group1['name']}'\n"
            f"  Sequence: {group1['sequence']} → {group2['sequence']}\n\n"
            f"Group 2: '{group2['name']}'\n"
            f"  Sequence: {group2['sequence']} → {group1['sequence']}",
            name="API Update - Swapped Sequences",
            attachment_type=allure.attachment_type.TEXT
        )

    # Step 4: Restart browser
    with allure.step("Restart browser"):
        drivers = browser_factory("chrome")
        new_driver = drivers[-1]
        new_menu_page = MenuPage(new_driver)
        new_menu_page.navigate_to_main_menu()

    # Step 5: Verify order changed
    with allure.step(f"Verify order changed - Should be reversed"):
        item_element = new_driver.find_element(By.ID, item_data['item_id'])
        new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_element)
        time.sleep(0.5)
        item_element.click()
        time.sleep(1)

        try:
            modal = new_driver.find_element(By.CSS_SELECTOR, ".mod-card")
            group_headers = modal.find_elements(By.CSS_SELECTOR, ".mod-group-title")

            # Get new order from HTML
            new_order = [header.text.strip() for header in group_headers if header.is_displayed()]

            allure.attach(
                f"New Order:\n" + "\n".join([f"{i + 1}. {name}" for i, name in enumerate(new_order)]),
                name="New Modifier Order (After Swap)",
                attachment_type=allure.attachment_type.TEXT
            )

            # Verify order changed
            # Group2 should now come before Group1
            try:
                index_group1_new = new_order.index(group1['name'])
                index_group2_new = new_order.index(group2['name'])

                # After swap, group2 should come before group1
                assert index_group2_new < index_group1_new, \
                    f"Order did not change correctly. {group2['name']} should come before {group1['name']}"

                # Scroll through groups for screenshot
                for header in group_headers[:2]:
                    if header.is_displayed():
                        new_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", header)
                        time.sleep(0.3)

                allure.attach(
                    new_driver.get_screenshot_as_png(),
                    name=f"New Order: {group2['name']} → {group1['name']} (SWAPPED)",
                    attachment_type=allure.attachment_type.PNG
                )

                allure.attach(
                    f"✅ Order Change Verified\n\n"
                    f"Before: {group1['name']} → {group2['name']}\n"
                    f"After:  {group2['name']} → {group1['name']}",
                    name="Order Verification",
                    attachment_type=allure.attachment_type.TEXT
                )

            except ValueError as e:
                allure.attach(
                    new_driver.get_screenshot_as_png(),
                    name="Could not find groups in new order",
                    attachment_type=allure.attachment_type.PNG
                )
                pytest.fail(f"Could not verify order change: {str(e)}")

        except Exception as e:
            allure.attach(
                new_driver.get_screenshot_as_png(),
                name="Error verifying new order",
                attachment_type=allure.attachment_type.PNG
            )
            pytest.fail(f"Failed to verify order change: {str(e)}")

        # Close modal
        try:
            new_driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
            time.sleep(0.5)
        except:
            pass

    # Step 6: Restore original sequences
    with allure.step("Restore original sequences"):
        # Restore to original sequences
        restore_updates = [
            {
                'modifier_group_id': group1['id'],
                'mod_group_data': group1['original_data'],
                'menu_items_list': menu_items_group1,
                'new_sequence': group1['sequence']  # Back to original
            },
            {
                'modifier_group_id': group2['id'],
                'mod_group_data': group2['original_data'],
                'menu_items_list': menu_items_group2,
                'new_sequence': group2['sequence']  # Back to original
            }
        ]

        api.update_modifier_sequences(restore_updates)

        allure.attach(
            f"Restored to original sequences:\n"
            f"  {group1['name']}: {group1['sequence']}\n"
            f"  {group2['name']}: {group2['sequence']}",
            name="API Update - Restored Sequences",
            attachment_type=allure.attachment_type.TEXT
        )

