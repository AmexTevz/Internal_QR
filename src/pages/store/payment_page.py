import time
import allure
from selenium.common import TimeoutException
from src.pages.base_page import BasePage
from src.utils.credit_card import generate_customer
from src.locators.store_locators import PaymentPageLocators
from src.data.endpoints.get_details import get_check_details
from src.utils.logger import Logger


class PaymentPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger("PaymentPage")


    @allure.step("Place the order")
    def make_the_payment(self):
        self.switch_to_frame(PaymentPageLocators.IFRAME)
        if self.is_element_present(PaymentPageLocators.POSTAL_CODE, timeout=10):
            self.switch_to_default_content()
            try:
                card_data = generate_customer()
                time.sleep(1)
                self.send_keys(PaymentPageLocators.CARD_HOLDER_NAME,card_data['fullname'])
                self.switch_to_frame(PaymentPageLocators.IFRAME)
                self.send_keys(PaymentPageLocators.CARD_NUMBER, card_data['number'])
                self.send_keys(PaymentPageLocators.CARD_DATE, card_data['exp'])
                self.send_keys(PaymentPageLocators.SECURITY_CODE, card_data['cvv'])
                self.send_keys(PaymentPageLocators.POSTAL_CODE, card_data['zip'])
                self.attach_screenshot("After filling the card info")
                self.switch_to_default_content()
                self.click(PaymentPageLocators.MAKE_PAYMENT)
                self.attach_screenshot("After clicking the payment button")
                self.wait_for_loading_to_disappear(PaymentPageLocators.LOADER, timeout=300)
            except TimeoutException:
                pass

    @allure.step("Total Amount on the Payment Page")
    def get_total_amount(self, scroll_into_view=True):
        if scroll_into_view:
            total_element = self.wait_for_element_visible(PaymentPageLocators.TOTAL_AMOUNT)
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", total_element)
            time.sleep(0.5)
            self.attach_screenshot("Total Amount on the Payment Page")

        total_text = self.get_text_3(PaymentPageLocators.TOTAL_AMOUNT)
        amount = float(total_text.replace('$', '').strip())
        return amount
