import time
from selenium.webdriver import Keys
from src.pages.base_page import BasePage, wait_for_loader
from src.locators.store_locators import CheckoutPageLocators, FreedomPayLocators
from src.utils.logger import Logger
import random
import math
import allure


class CheckoutPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger("CheckoutPage")

    @allure.step("Get order number from checkout")
    def order_number(self):
        self.wait_for_loading_to_disappear(FreedomPayLocators.LOADER, name="#3 wait")
        try:
            number = self.get_text_2(CheckoutPageLocators.CHECK_NUMBER)
            result = number.replace("#", "")
            self.logger.debug(f"Order number: {result}")
            return result
        except Exception as e:
            self.logger.exception(f"Failed to get order number: {str(e)}")
            raise

    @allure.step("Customer info")
    @wait_for_loader
    def customer_info_input(self, email, phone):
        if self.is_element_present(CheckoutPageLocators.PHONE_NUMBER):
            self.send_keys(CheckoutPageLocators.PHONE_NUMBER, phone)
        if self.is_element_present(CheckoutPageLocators.EMAIL):
            self.send_keys(CheckoutPageLocators.EMAIL, email)
    @wait_for_loader
    def manage_exact_amount(self, number):
        try:
            total_due = self.find_element(CheckoutPageLocators.TOTAL_VALUE).text
            total_due = float(total_due.replace("$", "").strip())
            self.logger.debug(f"Total due: {total_due}")
            if number == 1:
                pass
            else:
                amount_to_pay = f"{total_due/number:.2f}"
                self.logger.debug(f"Amount to pay: {amount_to_pay}")
                time.sleep(2)
                exact_amount_field = self.find_element(CheckoutPageLocators.SPLIT_BY_EXACT_AMOUNT_INPUT_FIELD)
                exact_amount_field.send_keys(Keys.CONTROL + "a")
                exact_amount_field.send_keys(Keys.DELETE)
                exact_amount_field.send_keys(amount_to_pay)
                self.attach_note(f'Amount typed - {amount_to_pay}', "AMOUNT DETAIL")
        except Exception as e:
            print(e)
            pass

    @allure.step("Manage tips")
    def manage_tips(self, amount=None):
        self.logger.info("managing tips")
        try:
            if amount == 0:
                self.click(CheckoutPageLocators.TIP_CUSTOM)
                pass
            elif amount is None:
                self.click(random.choice([CheckoutPageLocators.TIP_5, CheckoutPageLocators.TIP_10, CheckoutPageLocators.TIP_15, CheckoutPageLocators.TIP_20]))
            else:
                self.click(CheckoutPageLocators.TIP_CUSTOM)
                custom_tip_input = self.find_element(CheckoutPageLocators.CUSTOM_TIP_INPUT)
                # custom_tip_input.clear()
                custom_tip_input.send_keys(str(amount))
            self.logger.debug(f"tips applied - {self.read_tip_amount()}")

        except:
            pass

    def read_tip_amount(self):
        if self.is_element_present(CheckoutPageLocators.TIP_VALUE, timeout=1):
            tip_amount = self.find_element(CheckoutPageLocators.TIP_VALUE).text
        elif self.is_element_present(CheckoutPageLocators.SPLIT_TIP_VALUE, timeout=1):
            tip_amount = self.find_element(CheckoutPageLocators.SPLIT_TIP_VALUE).text
        else:
            tip_amount = self.find_element(CheckoutPageLocators.SPLIT_EQUALLY_TIP_VALUE).text
        return float(tip_amount.replace('$',''))


    def calculate_roundup_amount(self):
        total = float(self.find_element(CheckoutPageLocators.TOTAL_VALUE).text)
        rounded_up = math.ceil(total)
        amount_needed = round(rounded_up - total, 2)
        print(f"total is - {total}")
        print(f"roundup needed is {amount_needed}")
        self.attach_note(f"The amount required to roundup the total was calculated - ${amount_needed}")
        return amount_needed

    @allure.step("Proceed to checkout")
    def proceed_to_checkout(self, charity=None):
        self.logger.info("clicking payment button")
        self.click(CheckoutPageLocators.MAKE_PAYMENT)
        self.wait_for_loading_to_disappear(FreedomPayLocators.LOADER, name= "#4 wait", initial_delay=3)

    def split_by_exact_amount(self, amount=None):
        pass

    def split_equally(self, split_num=2):
        if split_num > 2:
            clicks = split_num - 2
            for _ in range(clicks):
                self.click(CheckoutPageLocators.SPLIT_EQUALLY_PLUS_BUTTON)
                time.sleep(0.5)
        actual_value = self.find_element(CheckoutPageLocators.SPLIT_FIELD_VALUE).text
        return actual_value


    def next_split_payment(self):
        self.wait_for_loading_to_disappear(FreedomPayLocators.LOADER, name= "Proceed to next payment wait")
        self.click(CheckoutPageLocators.SPLIT_EQUALLY_NEXT_PAYMENT)

