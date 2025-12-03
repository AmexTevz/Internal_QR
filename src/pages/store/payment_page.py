import time
import allure
from selenium.common import TimeoutException
from src.pages.base_page import BasePage, wait_for_loader
from src.utils.credit_card import generate_customer
from src.locators.store_locators import FreedomPayLocators, MenuContents
from src.data.endpoints.get_details import get_check_details
from src.utils.logger import Logger


class PaymentPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger("PaymentPage")


    @allure.step("Place the order as '{fullname}'")
    def place_the_order(self, fullname):
        self.switch_to_frame(FreedomPayLocators.IFRAME)
        if self.is_element_present(FreedomPayLocators.POSTAL_CODE, timeout=10):
            self.switch_to_default_content()
            try:
                card_data = generate_customer()
                time.sleep(1)
                self.send_keys(FreedomPayLocators.CARD_HOLDER_NAME,fullname)
                self.switch_to_frame(FreedomPayLocators.IFRAME)
                self.send_keys(FreedomPayLocators.CARD_NUMBER, card_data['number'])
                self.send_keys(FreedomPayLocators.CARD_DATE, card_data['exp'])
                self.send_keys(FreedomPayLocators.SECURITY_CODE, card_data['cvv'])
                self.send_keys(FreedomPayLocators.POSTAL_CODE, card_data['zip'])
                self.attach_screenshot("After filling the card info")
                self.switch_to_default_content()
                self.click(FreedomPayLocators.MAKE_PAYMENT)


                # Update session data after order is placed
                success, result = get_check_details()
                if not success:
                    self.logger.error(f"Failed to update session data after placing order: {result}")


            except TimeoutException:
                pass
