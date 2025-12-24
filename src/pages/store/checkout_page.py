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




    @allure.step("Manage tips")
    def manage_tips(self, amount=None, manual_roundup = False):
        self.logger.info("managing tips")
        try:
            if amount == 0 and manual_roundup is False:
                self.click(CheckoutPageLocators.CASH_TIP)
                pass
            elif amount is None and manual_roundup is False:
                self.click(random.choice([CheckoutPageLocators.TIP_18, CheckoutPageLocators.TIP_20, CheckoutPageLocators.TIP_22]))
            elif manual_roundup:
                self.click(CheckoutPageLocators.TIP_CUSTOM)
                self.click(CheckoutPageLocators.TIP_CUSTOM)
                tip_input = self.find_element(CheckoutPageLocators.TIP_CUSTOM_INPUT)
                tip_input.clear()
                if manual_roundup:
                    amount_needed = self.get_text_3(CheckoutPageLocators.CHARITY_AMOUNT)
                    if amount_needed != '$0.00':
                        tip_input.send_keys(amount_needed)
                    else:
                        self.logger.debug("tip not added - already rounded up")
                        self.attach_screenshot("tip not added - already rounded up")
                else:
                    tip_input.send_keys(amount)

            applied_tip = self.get_text_3(CheckoutPageLocators.TIPS_VALUE).strip()

            if applied_tip != '$0.00':
                self.logger.debug(f"tips applied - {applied_tip}")
                self.attach_note(f"Tips applied: {applied_tip}")
                self.attach_screenshot("After applying the tips")
            else:
                self.logger.debug("Tip was not added")
                self.attach_note(f"Tip was not added")
                self.attach_screenshot("Tip was not added")

        except:
            pass

    def apply_charity(self):
        self.click(CheckoutPageLocators.CHARITY_TOGGLE)
        applied_charity = self.get_text_3(CheckoutPageLocators.CHARITY_AMOUNT)
        applied_charity = float(applied_charity.strip())
        return applied_charity


    @allure.step("Get subtotal from checkout page")
    def get_subtotal(self):
        try:
            self.is_element_displayed(CheckoutPageLocators.SUBTOTAL_VALUE, timeout=5)
            self.logger.info("Subtotal element is displayed")

            app_subtotal = self.wait_for_value_to_update(
                CheckoutPageLocators.SUBTOTAL_VALUE,
                initial_value="$0.00",
                timeout=10,
                name="Subtotal"
            )
            app_subtotal_value = float(app_subtotal.replace('$', '').strip())

            self.logger.info(f"Subtotal retrieved from checkout: ${app_subtotal_value:.2f}")
            self.attach_note(f"Subtotal: ${app_subtotal_value:.2f}")
            self.attach_screenshot("Subtotal on checkout page")
            return app_subtotal_value
        except Exception as e:
            self.logger.error(f"Failed to get subtotal from checkout: {str(e)}")
            self.logger.exception(f"Failed to get subtotal from checkout: {str(e)}")
            raise

    @allure.step("Get check and table numbers from checkout page")
    def get_check_number_checkout(self):
        try:
            self.wait_for_element_visible(CheckoutPageLocators.CHECK_NUMBER_CHECKOUT)
            if self.is_element_present(CheckoutPageLocators.CHECK_NUMBER_CHECKOUT):
                check_number = self.get_text(CheckoutPageLocators.CHECK_NUMBER_CHECKOUT)
                check_number = check_number.split()[-1].strip()
                check_num = int(check_number)

                self.logger.info(f"Check number retrieved from checkout: {check_num}")
                self.attach_note(f"Check number: {check_num}")
                self.attach_screenshot("Check number on checkout")
                return check_num
        except Exception as e:
            self.logger.error(f"Failed to get check number from checkout: {str(e)}")
            self.logger.exception(f"Failed to get check number from checkout: {str(e)}")
            raise

    def get_check_table_checkout(self):
        try:
            self.wait_for_element_visible(CheckoutPageLocators.TABLE_NUMBER_CHECKOUT)
            if self.is_element_present(CheckoutPageLocators.TABLE_NUMBER_CHECKOUT):
                table_number = self.get_text(CheckoutPageLocators.TABLE_NUMBER_CHECKOUT)
                table_number = table_number.split()[-1].strip()
                table_num = int(table_number)

                self.logger.info(f"Table number retrieved from checkout: {table_num}")
                self.attach_note(f"Table number: {table_num}")
                return table_num
        except Exception as e:
            self.logger.error(f"Failed to get table number from checkout: {str(e)}")
            self.logger.exception(f"Failed to get table number from checkout: {str(e)}")
            raise

    @allure.step("Navigate to payment page")
    def go_to_payment_page(self, upsell = False):
        self.click(CheckoutPageLocators.PAY_BUTTON)
        self.logger.info(f"Clicked Pay button")
        self.attach_note(f"Clicked Pay button")
        self.attach_screenshot("Clicked Pay button")

        if not upsell:
            self.click(CheckoutPageLocators.NO_THANKS)
            self.logger.info(f"Declined upsell items")
            self.attach_note(f"Declined upsell items")
            self.attach_screenshot("Declined upsell items")



