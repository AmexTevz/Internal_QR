
import os
import random
import time
import pytest
import allure
from src.data.endpoints.get_details import get_check_details
from src.pages.store.menu_page import MenuPage
from src.pages.store.checkout_page import CheckoutPage
from src.pages.store.payment_page import PaymentPage
from src.pages.store.confirmation_page import ConfirmationPage
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
    return random.randint(2, 5)


TABLES = [7, 8]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.test_run
@allure.feature("Checkout Flow")
@allure.title("Single Payment Checkout Test - Parallel Execution")
def test_checkout_parallel(browser_factory, endpoint_setup, table):

    [chrome] = browser_factory("chrome")
    menu_page = MenuPage(chrome)

    try:
        with allure.step(f"PHASE 1: Customer places the order on table {table}"):
            with allure.step("Navigate to main menu"):
                menu_page.navigate_to_main_menu()
                menu_page.select_random_menu_items(1)
                close_table()

    except Exception as e:
        with allure.step("ERROR"):
            close_table()
            print(f"Error: {str(e)}")