import random
import pytest
import allure
from src.data.endpoints.get_details import get_check_details
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.close_table import close_table



def attach_note(note_text, name="Note"):
    allure.attach(
        note_text,
        name=name,
        attachment_type=allure.attachment_type.TEXT
    )

def menu_item_number():
    return random.randint(1, 3)

def get_api_data(field):
    api_check = get_check_details()

    if not api_check:
        defaults = {
            'subtotal': 0.0, 'total': 0.0, 'tax': 0.0,
            'due': 0.0, 'paid': 0.0, 'count': 0,
            'items': [], 'trans_num': '', 'trans_guid': ''
        }
        return defaults.get(field, None)

    field_map = {
        'subtotal': api_check.get('Subtotal', 0.0),
        'total': api_check.get('TotalPrice', 0.0),
        'tax': api_check.get('TotalTax', 0.0),
        'due': api_check.get('AmountDueTotal', 0.0),
        'paid': api_check.get('PaymentTotal', 0.0),
        'count': len(api_check.get('Items', [])),
        'items': api_check.get('Items', []),
        'check_num': api_check.get('TransactionNumber', ''),
        'trans_guid': api_check.get('TransactionGuid', ''),
    }

    return field_map.get(field, None)

TABLES = [2]

@pytest.mark.parametrize("table", TABLES)
@pytest.mark.badge
@pytest.mark.functional
@allure.feature("Menu")
@allure.story("Cart Badges")  # Optional - sub-category
@allure.title("Verify Item and Cart Badges Update Correctly")
def test_badges(browser_factory, endpoint_setup, table):

    [chrome] = browser_factory("chrome")
    menu_page = MenuPage(chrome)


    try:
        with allure.step(f"Verify item and cart badges - {table}"):
            with allure.step("Navigate to main menu"):
                menu_page.navigate_to_main_menu()

                menu_page.select_random_menu_items(num_items=2, quantity=3, verify_badges=True)
                item_id = list(menu_page.cart_items.keys())[0]
                menu_page.add_more_of_item(item_id, quantity=2)
                assert menu_page.verify_cart_badge()
                assert menu_page.verify_item_badges()


    except Exception as e:
        with allure.step("ERROR"):
            close_table()
            print(f"Error: {str(e)}")
            raise