import time
import allure
from selenium.common import TimeoutException
from src.pages.base_page import BasePage
from src.utils.credit_card import generate_customer
from src.locators.store_locators import FreedomPayLocators
from src.data.endpoints.get_details import get_check_details
from src.utils.logger import Logger


class PaymentPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger("PaymentPage")


    @allure.step("Place the order")
    def make_the_payment(self):
        self.switch_to_frame(FreedomPayLocators.IFRAME)
        if self.is_element_present(FreedomPayLocators.POSTAL_CODE, timeout=10):
            self.switch_to_default_content()
            try:
                card_data = generate_customer()
                time.sleep(1)
                self.send_keys(FreedomPayLocators.CARD_HOLDER_NAME,card_data['fullname'])
                self.switch_to_frame(FreedomPayLocators.IFRAME)
                self.send_keys(FreedomPayLocators.CARD_NUMBER, card_data['number'])
                self.send_keys(FreedomPayLocators.CARD_DATE, card_data['exp'])
                self.send_keys(FreedomPayLocators.SECURITY_CODE, card_data['cvv'])
                self.send_keys(FreedomPayLocators.POSTAL_CODE, card_data['zip'])
                self.attach_screenshot("After filling the card info")
                self.switch_to_default_content()
                self.click(FreedomPayLocators.MAKE_PAYMENT)
                self.attach_screenshot("After clicking the payment button")



            except TimeoutException:
                pass
