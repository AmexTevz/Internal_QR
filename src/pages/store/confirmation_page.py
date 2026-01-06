import allure
from src.pages.base_page import BasePage
from src.locators.store_locators import ConfirmationPageLocators
from src.utils.logger import Logger


class PaymentPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger("PaymentPage")


    @allure.step("Place the order")
    def get_subtotal(self):
        """Get subtotal amount from breakdown"""
        try:
            text = self.get_text(ConfirmationPageLocators.SUBTOTAL)
            value = float(text.replace('$', '').strip())
            self.logger.debug(f"Subtotal: ${value:.2f}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to get subtotal: {str(e)}")
            return 0.0

    def get_tax(self):
        """Get tax amount from breakdown"""
        try:
            text = self.get_text(ConfirmationPageLocators.TAX)
            value = float(text.replace('$', '').strip())
            self.logger.debug(f"Tax: ${value:.2f}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to get tax: {str(e)}")
            return 0.0

    def get_tip(self):
        """Get tip amount from breakdown"""
        try:
            text = self.get_text(ConfirmationPageLocators.TIP)
            value = float(text.replace('$', '').strip())
            self.logger.debug(f"Tip: ${value:.2f}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to get tip: {str(e)}")
            return 0.0

    def get_total(self):
        """Get displayed total amount from breakdown"""
        try:
            text = self.get_text(ConfirmationPageLocators.TOTAL)
            value = float(text.replace('$', '').strip())
            self.logger.debug(f"Total: ${value:.2f}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to get total: {str(e)}")
            return 0.0

    def calculate_expected_total(self):

        subtotal = self.get_subtotal()
        tax = self.get_tax()
        tip = self.get_tip()

        calculated_total = round(subtotal + tax + tip, 2)

        self.logger.info(
            f"Calculated total: ${calculated_total:.2f} "
            f"(${subtotal:.2f} + ${tax:.2f} + ${tip:.2f})"
        )

        return calculated_total