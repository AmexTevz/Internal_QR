import random
import time
from datetime import datetime
import pytest
import allure
from src.data.endpoints.get_details import get_check_details
from src.pages.store.menu_page import MenuPage
from src.pages.store.checkout_page import CheckoutPage
from src.pages.store.cart_page import CartPage
from src.pages.store.payment_page import PaymentPage
from src.pages.store.confirmation_page import ConfirmationPage
from src.data.endpoints.close_table import close_table
import pytest_check as check


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
        'check_number': api_check.get('TransactionNumber', ''),
        'trans_guid': api_check.get('TransactionGuid', ''),
    }

    return field_map.get(field, None)

TABLES = [52]

@pytest.mark.parametrize("table", TABLES)
@pytest.mark.checkout
@pytest.mark.checkout_with_upsell
@pytest.mark.all
@allure.feature("Menu")
@allure.story("Checkout")
@allure.title("Checkout Flow with Upsell Items")
def test_checkout_flow_upsell(browser_factory, endpoint_setup, table):
    """
    Test checkout flow with multiple ordering rounds before payment.

    Flow:
    1. Navigate to main menu
    2. Verify logo exists and table number is correct
    3. Select items and place initial order
    4. Verify that the item and cart badges match the quantity of the selected items
    5. Verify check number and table number in cart match API
    6. Navigate to checkout page
    7. Verify total item count, table number, and check number
    8. Verify subtotal matches API data
    9. Send random tip and apply charity
    10. Verify total equals subtotal + tip + tax + donation
    11. Navigate to payment page
    12. Verify total amount matches between checkout and payment pages
    13. Complete payment
    14. Verify check number, breakdowns, and calculations on the final page are correct
    15. Generate unique test email address with test name and timestamp
    16. Send email receipt to generated address
    17. Wait for email to arrive in inbox
    18. Verify email receipt contents:
        - Check number matches expected value
        - Total amount matches payment total
        - All financial calculations are correct (subtotal + tax + service charge + tip + donation = total)
    """

    test_title = "Checkout Flow with Upsell Items"
    timestamp = datetime.now().strftime("%B %d, %Y %H:%M")
    allure.dynamic.title(f"Checkout Flow - {timestamp}")
    [chrome] = browser_factory("chrome")

    menu_page = MenuPage(chrome)
    cart_page = CartPage(chrome)
    checkout_page = CheckoutPage(chrome)
    payment_page = PaymentPage(chrome)
    confirmation_page = ConfirmationPage(chrome)

    num_items = 2
    quantity = 2
    reorder_count = 0

    try:
        with allure.step(f"Customer places the order on table {table}"):
            with allure.step("First order round"):
                menu_page.navigate_to_main_menu()
                menu_page.select_random_menu_items(num_items=num_items, quantity=quantity, verify_badges=True)

                check.is_true(menu_page.verify_logo_exists(), "Logo does not exist")
                check.is_true(menu_page.verify_cart_badge(), "Cart badge verification failed")
                check.is_true(menu_page.verify_item_badges(), "All cart badges verification failed")

                menu_page.go_to_basket()

                api_check_number = int(get_api_data('check_number'))
                cart_check_number = cart_page.get_check_number_in_basket()
                check.equal(api_check_number, cart_check_number, "Check number does not match in cart page")

                cart_table_number = cart_page.get_check_table_in_basket()
                check.equal(table, cart_table_number, "Check table does not match in cart page")

                cart_page.place_order()  # Returns to menu

            for round_num in range(1, reorder_count + 1):
                with allure.step(f"Reorder round {round_num}"):
                    menu_page.select_random_menu_items(num_items=1, quantity=1, verify_badges=True)
                    menu_page.go_to_basket()
                    cart_page.place_order()

        with allure.step(f"Customer navigates to checkout page {table}"):
            with allure.step("Navigate to checkout"):
                menu_page.go_to_basket()
                cart_page.navigate_to_checkout_page()

                api_item_count = get_api_data('count')
                total_expected_items = (num_items * quantity) + reorder_count
                check.equal(api_item_count, total_expected_items, "Number of items does not match")

                checkout_table_number = checkout_page.get_check_table_checkout()
                check.equal(checkout_table_number, table, "Check table does not match in checkout page")

                checkout_check_number = checkout_page.get_check_number_checkout()
                check.equal(checkout_check_number, api_check_number, "Check number does not match in checkout page")

                app_subtotal = checkout_page.get_subtotal()
                api_subtotal = get_api_data('subtotal')
                check.equal(app_subtotal, api_subtotal, "Subtotal is incorrect")

                checkout_page.manage_tips(random.uniform(3.99, 8.99))
                charity_applied = checkout_page.apply_charity()
                check.not_equal(charity_applied, 0, f"Charity Fail: $0 was applied")
                check.equal(checkout_page.calculate_expected_total(), True, "Checkout Page breakdown does not add up")
                checkout_page_total = checkout_page.get_total()

                upsell_items_found = checkout_page.go_to_payment_page(upsell=True)
                check.not_equal(upsell_items_found, False, "Upsell items were not found")
                if upsell_items_found:
                    with allure.step(f"Customer accepts UPSELL and navigates to payment page"):
                        cart_page.place_order()
                        menu_page.go_to_basket()
                        cart_page.navigate_to_checkout_page()
                        app_subtotal = checkout_page.get_subtotal()
                        api_subtotal = get_api_data('subtotal')
                        check.equal(app_subtotal, api_subtotal, "Subtotal is incorrect after adding the upsell item")
                        checkout_page_total = checkout_page.get_total()

                    with allure.step(f"Customer navigates to payment page {table}"):
                        checkout_page.go_to_payment_page()
                        payment_page_total = payment_page.get_total_amount()
                        check.equal(payment_page_total, checkout_page_total, "Payment Page Total is incorrect")
                        payment_page.make_the_payment()

                    with allure.step(f"Customer navigates to confirmation page {table}"):
                        check.equal(confirmation_page.get_order_status(), True, "Confirmation Page Status is incorrect")
                        check.equal(api_check_number, confirmation_page.get_order_number(),
                                    "Check number does not match in confirmation page")
                        check.equal(confirmation_page.calculate_expected_total(), True,
                                    "Confirmation Page Total is incorrect")

                        email_verification = confirmation_page.send_and_verify_email_receipt(
                            expected_check_number=api_check_number,
                            expected_total=payment_page_total,
                            test_name=test_title
                        )
                        check.equal(email_verification['passed'], True, "Email receipt verification failed")
                else:
                    with allure.step(f"Upsell items are not present - Customer navigates to payment page {table}"):
                        payment_page_total = payment_page.get_total_amount()
                        check.equal(payment_page_total, checkout_page_total, "Payment Page Total is incorrect")
                        payment_page.make_the_payment()

                    with allure.step(f"Customer navigates to confirmation page {table}"):
                        check.equal(confirmation_page.get_order_status(), True, "Confirmation Page Status is incorrect")
                        check.equal(api_check_number, confirmation_page.get_order_number(),
                                    "Check number does not match in confirmation page")
                        check.equal(confirmation_page.get_total(), payment_page_total,
                                    "Confirmation Page Total is incorrect")
                        check.equal(confirmation_page.calculate_expected_total(), True,
                                    "Confirmation Page breakdown does not add up")

                        email_verification = confirmation_page.send_and_verify_email_receipt(
                            expected_check_number=api_check_number,
                            expected_total=payment_page_total,
                            test_name=test_title,
                            table_number = table
                        )
                        check.equal(email_verification['passed'], True, "Email receipt verification failed")


    except Exception as e:
        close_table()
        print(f"Error: {str(e)}")
        raise