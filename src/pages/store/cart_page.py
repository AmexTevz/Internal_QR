from src.pages.base_page import BasePage
from src.locators.store_locators import CartPageLocators, CheckoutPageLocators
import allure
from src.utils.logger import Logger


class CartPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger("CartPage")
        self.store_id = None


    @allure.step("Get check and table numbers from basket")
    def get_check_number_in_basket(self):
        try:
            self.wait_for_loading_to_disappear(CartPageLocators.LOADER, timeout=300)
            self.wait_for_element_visible(CartPageLocators.CHECK_NUMBER_CART)
            if self.is_element_present(CartPageLocators.CHECK_NUMBER_CART):
                check_number = self.get_text(CartPageLocators.CHECK_NUMBER_CART)
                check_number = check_number.split()[-1].strip()
                check_num = int(check_number)
                self.logger.info(f"Check number retrieved from basket: {check_num}")
                self.attach_note(f"Check number: {check_num}")
                self.attach_screenshot("Check number in basket")
                return check_num
        except Exception as e:
            self.logger.error(f"Failed to get check number from basket: {str(e)}")
            self.logger.exception(f"Failed to get check number from basket: {str(e)}")
            raise

    def get_check_table_in_basket(self):
        try:
            if self.is_element_present(CartPageLocators.TABLE_NUMBER_CART):
                table_number = self.get_text(CartPageLocators.TABLE_NUMBER_CART)
                table_number = table_number.split()[-1].strip()
                table_num = int(table_number)
                self.logger.info(f"Table number retrieved from basket: {table_num}")
                return table_num
        except Exception as e:
            self.logger.error(f"Failed to get table number from basket: {str(e)}")
            self.logger.exception(f"Failed to get table number from basket: {str(e)}")
            raise

    @allure.step("Continue ordering")
    def continue_ordering(self):
        try:
            self.click(CartPageLocators.CONTINUE_ORDERING)
            self.logger.info("Clicked continue ordering button")
            self.attach_note("Continue ordering clicked")
            self.attach_screenshot("Continue ordering")
        except Exception as e:
            self.logger.error(f"Failed to continue ordering: {str(e)}")
            self.logger.exception(f"Failed to continue ordering: {str(e)}")
            raise

    @allure.step("Place order")
    def place_order(self):
        try:
            if self.is_element_displayed(CartPageLocators.CHECK_NUMBER_CART, timeout=5):
                self.logger.info("Check number in basket is present")
            else:
                self.logger.warning("Check number in basket is not present")

            self.wait_for_element_visible(CartPageLocators.PLACE_ORDER, 5)
            self.logger.info("Place order button is present")
            self.attach_screenshot("Before placing order")

            self.click(CartPageLocators.PLACE_ORDER)
            self.logger.info("Place order button was clicked")
            self.attach_screenshot("After placing order")
            self.wait_for_element_visible(CartPageLocators.CONTINUE_ORDERING)
            if self.is_element_present(CartPageLocators.CONTINUE_ORDERING, timeout=3):
                self.click(CartPageLocators.CONTINUE_ORDERING)
                self.logger.info("Successfully navigated back to menu page")
                self.attach_screenshot("Successfully navigated back to menu page")
        except Exception as e:
            self.logger.error(f"Failed to place order: {str(e)}")
            self.logger.exception(f"Failed to place order: {str(e)}")
            raise


    def navigate_to_checkout_page(self, reorder = 0):
        try:
            self.wait_for_element_visible(CartPageLocators.CHECKOUT_BUTTON)
            if self.is_element_present(CartPageLocators.CHECKOUT_BUTTON, timeout=3):
                self.click(CartPageLocators.CHECKOUT_BUTTON)
                self.wait_for_loading_to_disappear(CartPageLocators.LOADER)
                self.logger.info("Successfully navigated to checkout page")
                self.attach_screenshot("Checkout page")
                self.wait_for_value_to_update(CheckoutPageLocators.TOTAL_VALUE)
            else:
                self.logger.error("Cannot navigate to checkout page - button not present")
                self.attach_screenshot("Checkout button not found")
                raise Exception("Close check and pay button not found")
        except Exception as e:
            self.logger.error(f"Failed to navigate to checkout page: {str(e)}")
            self.logger.exception(f"Failed to navigate to checkout page: {str(e)}")
            raise