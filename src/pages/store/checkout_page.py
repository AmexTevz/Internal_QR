import time

from src.pages.base_page import BasePage
from src.locators.store_locators import CheckoutPageLocators
from src.utils.logger import Logger
import random
import allure



class CheckoutPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger("CheckoutPage")




    @allure.step("Manage tips")
    def manage_tips(self, amount=None, manual_roundup = False):
        self.logger.info("managing tips")
        self.attach_screenshot("Before sending the tips")
        try:
            if manual_roundup:
                self.click(CheckoutPageLocators.TIP_CUSTOM)
                tip_input = self.find_element(CheckoutPageLocators.TIP_CUSTOM_INPUT)
                tip_input.clear()
                amount_needed = self.get_text_3(CheckoutPageLocators.CHARITY_AMOUNT)
                if amount_needed != '$0.00':
                    tip_input.send_keys(amount_needed)
                else:
                    self.logger.debug("tip not added - already rounded up")
                    self.attach_screenshot("tip not added - already rounded up")
            elif amount == 0 and manual_roundup is False:
                self.click(CheckoutPageLocators.CASH_TIP)
            elif amount is None and manual_roundup is False:
                self.click(random.choice([CheckoutPageLocators.TIP_18, CheckoutPageLocators.TIP_20, CheckoutPageLocators.TIP_22]))
            else:
                self.click(CheckoutPageLocators.TIP_CUSTOM)
                tip_input = self.find_element(CheckoutPageLocators.TIP_CUSTOM_INPUT)
                tip_input.clear()
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

    @allure.step("Manage charity")
    def apply_charity(self):
        self.click(CheckoutPageLocators.CHARITY_TOGGLE)
        applied_charity = self.get_text_3(CheckoutPageLocators.CHARITY_AMOUNT)
        applied_charity = float(applied_charity.replace('$','').strip())
        self.attach_screenshot("After applying the charity")
        self.attach_note(f"Charity amount: ${applied_charity}")
        return applied_charity





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


    def get_check_table_checkout(self):
        try:
            self.wait_for_element_visible(CheckoutPageLocators.TABLE_NUMBER_CHECKOUT)
            if self.is_element_present(CheckoutPageLocators.TABLE_NUMBER_CHECKOUT):
                table_number = self.get_text(CheckoutPageLocators.TABLE_NUMBER_CHECKOUT)
                table_number = table_number.split()[-1].strip()
                table_num = int(table_number)

                self.logger.info(f"Table number retrieved from checkout: {table_num}")
                return table_num
        except Exception as e:
            self.logger.error(f"Failed to get table number from checkout: {str(e)}")
            self.logger.exception(f"Failed to get table number from checkout: {str(e)}")


    @allure.step("Navigate to payment page")
    def go_to_payment_page(self, upsell=False):

        # Click PAY button
        self.click(CheckoutPageLocators.PAY_BUTTON)
        self.logger.info(f"Clicked Pay button")

        if upsell:
            info = {}
            try:
                self.attach_screenshot("The list of upsell items")
                upsell_items = self.find_elements(CheckoutPageLocators.UPSELL_ITEMS, timeout=3)
                upsell_choice = random.choice(upsell_items)
                self.click(upsell_choice)
                upsell_item_name = self.get_text(CheckoutPageLocators.UPSELL_ITEM_NAME)
                info['name'] = upsell_item_name
                self.logger.info(f"Upsell item name: {upsell_item_name}")
                if self.is_element_displayed(CheckoutPageLocators.UPSELL_ITEM_PRICE):
                    price_text = self.get_text(CheckoutPageLocators.UPSELL_ITEM_PRICE)
                    upsell_price = float(price_text.replace('$', '').replace(',', ''))
                    self.logger.info(f"Upsell price: {upsell_price:.2f}")
                    info['price'] = upsell_price
                self.attach_screenshot(f"Selected upsell item: {info['name']} - ${info['price']:.2f}")
                self.click(CheckoutPageLocators.ADD_BUTTON)
                return True

            except:
                self.logger.info("Upsell items were not found")
                self.attach_note("Upsell items were not found")
                return False

        else:
            try:
                no_thanks = self.find_element(CheckoutPageLocators.NO_THANKS, timeout=2)
                if no_thanks:
                    self.click(no_thanks)
                    self.logger.info(f"Declined additional upsells")
                    self.attach_screenshot("Declined additional upsells")
            except:
                pass

    @allure.step("Get subtotal amount from checkout page")
    def get_tip_amount(self):
        try:
            self.is_element_displayed(CheckoutPageLocators.SUBTOTAL_VALUE, timeout=5)

            tip_value = self.get_text_3(CheckoutPageLocators.TIPS_VALUE)
            tip_value = float(tip_value.replace('$', '').strip())

            self.logger.info(f"Tip retrieved from checkout: ${tip_value:.2f}")
            self.attach_note(f"Tip: ${tip_value:.2f}")

            return tip_value
        except Exception as e:
            self.logger.error(f"Failed to get subtotal from checkout: {str(e)}")
            self.logger.exception(f"Failed to get subtotal from checkout: {str(e)}")

    @allure.step("Get tax amount from checkout page")
    def get_tax_amount(self):
        try:
            self.is_element_displayed(CheckoutPageLocators.TAXES_VALUE, timeout=5)

            tax_value = self.get_text_3(CheckoutPageLocators.TAXES_VALUE)
            tax_value = float(tax_value.replace('$', '').strip())

            self.logger.info(f"Tip retrieved from checkout: ${tax_value:.2f}")
            self.attach_note(f"Tip: ${tax_value:.2f}")

            return tax_value
        except Exception as e:
            self.logger.error(f"Failed to get tax from checkout: {str(e)}")
            self.logger.exception(f"Failed to get tax from checkout: {str(e)}")

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


    @allure.step("Get total from checkout page")
    def get_total(self):
        try:
            self.is_element_displayed(CheckoutPageLocators.TOTAL_VALUE, timeout=5)
            time.sleep(1)
            total_value = self.get_text_3(CheckoutPageLocators.TOTAL_VALUE)
            total_value = float(total_value.replace('$', '').strip())

            self.logger.info(f"Total retrieved from checkout: ${total_value:.2f}")
            self.attach_note(f"Total: ${total_value:.2f}")

            return total_value
        except Exception as e:
            self.logger.error(f"Failed to get total from checkout: {str(e)}")
            self.logger.exception(f"Failed to get total from checkout: {str(e)}")


    def choose_cash_tip(self):
        self.click(CheckoutPageLocators.CASH_TIP)

    def calculate_expected_total(self):

        subtotal = self.get_subtotal()
        tax = self.get_tax_amount()
        tip = self.get_tip_amount()
        calculated_total = round(subtotal + tax + tip, 2)

        self.logger.info(
            f"Calculated total: ${calculated_total:.2f} "
            f"(${subtotal:.2f} + ${tax:.2f} + ${tip:.2f})"
        )


        return calculated_total




