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


def get_session_data(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as f:
        return json.load(f)

def get_session_value(file_path: str, key: str, default=None):
    return get_session_data(file_path).get(key, default)

def attach_session_data_json(session_data_path, name="session_data.json after update"):
    with open(session_data_path, "r") as f:
        allure.attach(
            f.read(),
            name=name,
            attachment_type=allure.attachment_type.JSON
        )
def attach_note(note_text, name="Note"):
    allure.attach(
        note_text,
        name=name,
        attachment_type=allure.attachment_type.TEXT
    )

def menu_item_number():
    return random.randint(2, 5)


# ============================================================================
# SINGLE TABLE - Just change table=NUMBER
# ============================================================================
@pytest.mark.test_run
@allure.feature("Checkout Flow")
def test_checkout(browser_factory, endpoint_setup, table=8):

    SESSION_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'data', 'endpoints',
                                     'session_data.json')

    [chrome] = browser_factory("chrome")
    menu_page = MenuPage(chrome)

    try:
        with allure.step(f"PHASE 1: Customer places the order on table {table}"):
            with allure.step("Navigate to main menu"):
                menu_page.navigate_to_main_menu()
                menu_page.select_random_menu_items(5)
                time.sleep(5)

    except Exception as e:
        with allure.step("ERROR"):
            close_table()
            print(f"Error: {str(e)}")