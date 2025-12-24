import os
import random
import time
import pytest
import allure
from src.data.endpoints.get_details import get_check_details
from src.pages.store.menu_page import MenuPage
from src.pages.store.checkout_page import CheckoutPage
from src.pages.store.cart_page import CartPage
from src.pages.store.payment_page import PaymentPage
import json
from typing import Dict, Any
from src.data.endpoints.close_table import close_table
from src.utils.credit_card import generate_customer
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
        'check_num': api_check.get('TransactionNumber', ''),
        'trans_guid': api_check.get('TransactionGuid', ''),
    }

    return field_map.get(field, None)

TABLES = [3]

@pytest.mark.parametrize("table", TABLES)

@pytest.mark.functional
@allure.feature("Menu")
@allure.story("Checkout")
@allure.title("Simple Checkout Flow")
def test_checkout_flow(browser_factory, endpoint_setup, table):

    [chrome] = browser_factory("chrome")
    menu_page = MenuPage(chrome)
    cart_page = CartPage(chrome)
    checkout_page = CheckoutPage(chrome)
    # get_check = get_check_details()

    try:
        with allure.step(f"PHASE 1: Customer places the order on table {table}"):
            with allure.step("Navigate to main menu"):
                menu_page.navigate_to_main_menu()

                menu_page.select_random_menu_items(num_items=2, quantity=3, verify_badges=True)
                assert menu_page.verify_cart_badge()
                assert menu_page.verify_item_badges()
                # menu_page.go_to_basket()
                #
                # cart_page.place_order()
                # cart_page.upsell_popup()
                # api_item_count = get_api_data('count')
                # api_subtotal = get_api_data('subtotal')
                # print("api subtotal:", api_subtotal)
                api_check_number = int(get_api_data('check_num'))

                # cart_page.navigate_to_checkout_page()
                #
                # check.equal(subtotal, api_subtotal, "The API and app subtotals are not equal")
                #
                # app_subtotal = checkout_page.get_subtotal()
                # checkout_page_check_number, checkout_page_table_number = checkout_page.get_table_details()
                #
                # check.equal(checkout_page_check_number, api_check_number)
                # check.equal(checkout_page_table_number, int(table))
                # check.equal(api_item_count, number_of_items, "Item count is incorrect")
                # check.equal(app_subtotal, subtotal, "The script calculated and app subtotals are not equal")


    except Exception as e:
        with allure.step("ERROR"):
            close_table()
            print(f"Error: {str(e)}")