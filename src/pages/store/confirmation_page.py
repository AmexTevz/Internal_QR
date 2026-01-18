import allure
from src.pages.base_page import BasePage
from src.locators.store_locators import ConfirmationPageLocators
from src.utils.logger import Logger


class ConfirmationPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger("PaymentPage")



    def get_subtotal(self):
        try:
            text = self.get_text(ConfirmationPageLocators.SUBTOTAL)
            value = float(text.replace('$', '').strip())
            self.logger.debug(f"Subtotal: ${value:.2f}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to get subtotal: {str(e)}")
            return 0.0

    def get_tax(self):

        try:
            text = self.get_text(ConfirmationPageLocators.TAX)
            value = float(text.replace('$', '').strip())
            self.logger.debug(f"Tax: ${value:.2f}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to get tax: {str(e)}")
            return 0.0

    def get_tip(self):
        if self.is_element_present(ConfirmationPageLocators.TIP, timeout=1):
            try:
                text = self.get_text(ConfirmationPageLocators.TIP)
                value = float(text.replace('$', '').strip())
                self.logger.debug(f"Tip: ${value:.2f}")
                return value
            except Exception as e:
                self.logger.error(f"Failed to get tip: {str(e)}")
        return 0.0

    def get_donation(self):
        if self.is_element_present(ConfirmationPageLocators.DONATION, timeout=1):
            try:
                text = self.get_text(ConfirmationPageLocators.DONATION)
                value = float(text.replace('$', '').strip())
                self.logger.debug(f"Donation: ${value:.2f}")
                return value
            except Exception as e:
                self.logger.error(f"Failed to get donation: {str(e)}")
        return 0.0

    def get_service_charge(self):
        if self.is_element_present(ConfirmationPageLocators.SERVICE_CHARGE, timeout=1):
            try:
                text = self.get_text(ConfirmationPageLocators.SERVICE_CHARGE)
                value = float(text.replace('$', '').strip())
                self.logger.debug(f"SERVICE_CHARGE: ${value:.2f}")
                return value
            except Exception as e:
                self.logger.error(f"Failed to get SERVICE_CHARGE: {str(e)}")
        return 0.0

    def get_total(self):
        try:
            text = self.get_text(ConfirmationPageLocators.TOTAL)
            value = float(text.replace('$', '').strip())
            self.logger.debug(f"Total: ${value:.2f}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to get total: {str(e)}")
            return 0.0

    @allure.step("Confirmation page")
    def calculate_expected_total(self):
        self.attach_screenshot("Confirmation Page")
        subtotal = self.get_subtotal()
        tax = self.get_tax()
        tip = self.get_tip()
        donation = self.get_donation()
        service_charge = self.get_service_charge()
        total = self.get_total()

        calculated_total = round(subtotal + tax + tip + donation + service_charge, 2)

        self.logger.info(
            f"Calculated total: ${calculated_total:.2f} "
            f"(${subtotal:.2f} + ${tax:.2f} + ${tip:.2f} + ${donation:.2f} + ${service_charge:.2f})"
        )

        if calculated_total == total:
            return True
        return False


    def get_order_number(self):
        try:
            text = self.get_text(ConfirmationPageLocators.ORDER_NUMBER)
            value = int(text.strip())
            self.logger.debug(f"Order number: {value}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to get order number: {str(e)}")

    def get_order_status(self):
        if self.find_element(ConfirmationPageLocators.CONFIRMATION_MESSAGE).is_displayed():
            text = self.get_text(ConfirmationPageLocators.CONFIRMATION_MESSAGE)
            if "Successful" in text:
                return True
        return False




