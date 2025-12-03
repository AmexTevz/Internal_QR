

from src.pages.base_page import BasePage
from src.locators.store_locators import (
    CommonLocators, MenuContents, FreedomPayLocators
)
import random
from selenium.webdriver.common.by import By
from src.utils.logger import Logger
from src.data.endpoints.get_details import get_check_details
import allure



# name = TEST_CARD
get_check_details()
class MenuPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger("MenuPage")


    def navigate_to_main_menu(self):
        try:
            self.logger.info("Starting navigation to main menu")
            self.logger.info("Successfully navigated to main menu")
        except Exception as e:
            self.logger.exception(f"Failed to navigate to main menu: {str(e)}")
            raise

    @allure.step("Order number")
    def order_number(self):
        try:
            number = self.get_text_2(MenuContents.CHECK_NUMBER)
            result = number.replace("#", "")
            self.logger.debug(f"Order number: {result}")
            return result
        except Exception as e:
            self.logger.exception(f"Failed to get order number: {str(e)}")
            raise

    @allure.step("Customer name")
    def customer_name(self):
        try:
            customer_name = self.get_text_2(MenuContents.CUSTOMER_NAME)
            return customer_name
        except Exception as e:
            self.logger.exception(f"Failed to get customer name: {str(e)}")
            raise

    # @allure.step("Table number")
    # def table_num(self):
    #     try:
    #         self.wait_for_element_visible(MenuContents.TABLE_NUMBER)
    #         number = int(self.get_text_2(MenuContents.TABLE_NUMBER).text)
    #         return number
    #     except Exception as e:
    #         self.logger.exception(f"Failed to get table number: {str(e)}")

    @allure.step("Select {num_items} random menu items")
    def select_random_menu_items(self, num_items=2):
        self.logger.info(f"Starting to select {num_items} random menu items")
        try:
            items = self.find_elements(MenuContents.ITEMS)
            if not items:
                return {'items': [], 'total': 0.0, 'count': 0}

            self.logger.debug(f"Found {len(items)} menu items")
            selected_items = random.sample(items, min(num_items, len(items)))

            item_details = []
            total_price = 0.0

            for index, item in enumerate(selected_items, 1):
                try:

                    # First click the item
                    self.click(item)

                    # Then get the item details
                    item_name = self.get_text(MenuContents.ITEM_NAME)
                    if self.is_element_displayed(MenuContents.ITEM_PRICE):
                        price_text = self.get_text(MenuContents.ITEM_PRICE)
                        base_price = float(price_text.replace('$', '').replace(',', ''))
                    else:
                        base_price = 0.0

                    self.logger.debug(f"Item: {item_name}, Base price: ${base_price}")

                    with allure.step(f"Select modifiers for '{item_name}'"):
                        selected_modifiers, modifier_cost = self._handle_all_modifiers()
                        self.attach_screenshot(f"After selecting modifiers for '{item_name}'")

                    # Click ADD button and continue immediately
                    with allure.step(f"Add '{item_name}' to cart"):
                        add_button = self.find_element(MenuContents.ADD_BUTTON)

                        self.click(add_button)


                    total_item_price = base_price + modifier_cost
                    item_details.append({
                        'name': item_name,
                        'base_price': base_price,
                        'modifiers': selected_modifiers,
                        'modifier_cost': modifier_cost,
                        'total_price': total_item_price
                    })
                    total_price += total_item_price
                    self.logger.debug(f"Item added successfully. Total price so far: ${total_price}")

                except Exception as e:
                    self.logger.exception(f"Failed to process item {index}: {str(e)}")
                    continue

            result = {
                'items': item_details,
                'total': round(total_price, 3),
                'count': len(item_details)
            }
            self.logger.info(f"Successfully selected {len(item_details)} items. Total: ${result['total']}")
            return result

        except Exception as e:
            self.logger.exception(f"Failed to select random menu items: {str(e)}")
            raise

    # @allure.step("Has upsell")
    # def has_upsell(self):
    #     try:
    #         has_upsell = bool(self.find_element(MenuContents.NO_THANKS_UPSELL, timeout=0))
    #         return has_upsell
    #     except Exception as e:
    #         return False

    # def has_age_check(self):
    #     try:
    #         has_age_check = bool(self.find_element(MenuContents.ABOVE_21, timeout=1))
    #         return has_age_check
    #     except Exception as e:
    #         return False
    #
    # def has_chevron(self):
    #     try:
    #         has_age_check = bool(self.find_element(MenuContents.HAS_CHEVRON, timeout=0))
    #         return has_age_check
    #     except Exception as e:
    #         return False

    def _handle_all_modifiers(self):
        try:
            # Find the modal/container that holds all modifiers
            modal = self.find_element((By.CSS_SELECTOR, ".mod-card"), timeout=0)
            if not modal:
                return [], 0.0

            all_selected_modifiers = []
            total_cost = 0.0

            # Get all elements inside the modal to work with the flat structure
            all_elements = modal.find_elements(By.XPATH, ".//*")

            # Find all modifier group headers
            group_headers = modal.find_elements(By.CSS_SELECTOR, ".mod-group-header")

            if not group_headers:
                self.logger.debug("No modifier groups found")
                return [], 0.0

            for header_index in range(len(group_headers)):
                try:
                    header = group_headers[header_index]

                    # Get the section title
                    section_title = header.find_element(By.CSS_SELECTOR, ".mod-group-title").text.strip()
                    self.logger.debug(f"Processing modifier section {header_index + 1}: {section_title}")

                    # Get the position of this header and the next header
                    header_position = all_elements.index(header)

                    # Find the position of the next header (if exists)
                    next_header_position = None
                    if header_index + 1 < len(group_headers):
                        next_header = group_headers[header_index + 1]
                        next_header_position = all_elements.index(next_header)

                    # Get all buttons between this header and the next header (or end)
                    option_buttons = []
                    start_search = header_position + 1
                    end_search = next_header_position if next_header_position else len(all_elements)

                    for elem in all_elements[start_search:end_search]:
                        if elem.tag_name == "button" and "mod-option-row" in elem.get_attribute("class"):
                            option_buttons.append(elem)

                    if not option_buttons:
                        self.logger.debug(f"No options found in section: {section_title}")
                        continue

                    # Filter for non-pressed buttons (aria-pressed="false")
                    available_options = [btn for btn in option_buttons
                                         if btn.get_attribute("aria-pressed") == "false"]

                    if not available_options:
                        self.logger.debug(f"All options already selected in section: {section_title}")
                        continue

                    # Randomly select one option
                    selected_button = random.choice(available_options)
                    modifier_info = self._extract_modifier_info_new(selected_button, section_title)

                    self.logger.debug(
                        f"Selected modifier in section '{section_title}': {modifier_info['name']}, Price: ${modifier_info['price']}")

                    # Click the button
                    self.click(selected_button)

                    all_selected_modifiers.append(modifier_info)
                    total_cost += modifier_info['price']

                except Exception as e:
                    self.logger.exception(f"Failed to select modifier in section {header_index + 1}: {str(e)}")
                    continue

            self.logger.debug(
                f"Modifier selection complete. Selected {len(all_selected_modifiers)} modifiers, total cost: ${total_cost}")
            return all_selected_modifiers, total_cost

        except Exception as e:
            self.logger.exception(f"Failed to handle all modifiers: {str(e)}")
            return [], 0.0

    def _extract_modifier_info_new(self, button_element, section_name):
        """Extract modifier information from the new app structure"""
        try:
            # Get the full button text
            button_text = button_element.text.strip()

            # Try to extract name and price
            # Usually format is "Modifier Name" or "Modifier Name +$X.XX"
            modifier_name = button_text
            modifier_price = 0.0

            # Check if there's a price in the text
            if '+$' in button_text or '$' in button_text:
                parts = button_text.split('$')
                if len(parts) > 1:
                    modifier_name = parts[0].replace('+', '').strip()
                    try:
                        modifier_price = float(parts[1].strip())
                    except:
                        modifier_price = 0.0

            return {
                'section': section_name,
                'name': modifier_name,
                'price': modifier_price
            }
        except Exception as e:
            self.logger.exception(f"Failed to extract modifier info: {str(e)}")
            return {'section': section_name, 'name': 'Unknown', 'price': 0.0}


    @allure.step("View order")
    def view_order(self):
        self.click(MenuContents.VIEW_ORDER)


    @allure.step("Submit order")
    def submit_order(self):
        self.logger.info("Submitting the order")
        self.click(MenuContents.SUBMIT_ORDER)

        self.wait_for_loading_to_disappear(FreedomPayLocators.LOADER, name="#0 wait", initial_delay=1)
        self.click(MenuContents.CONFIRM_SUBMIT_ORDER)

        self.wait_for_loading_to_disappear(FreedomPayLocators.LOADER, name="#1 wait", initial_delay=1)
        if not self.is_element_present(MenuContents.ERROR_MESSAGE):
            self.logger.info("order submitted")
            self.logger.info("updating the check json")
            get_check_details()
            self.logger.info("json updated")
            self.attach_screenshot("After submitting order")
            return True
        else:
            self.attach_screenshot(f"ERROR while submitting the order")
            return False

    @allure.step("Go to checkout page")
    def checkout(self, payment_step_1 = None, payment_step_2 = None):
        payment_types = {
            'single_payment': MenuContents.SINGLE_PAYMENT,
            'split_by_exact_amount': MenuContents.SPLIT_BY_EXACT_AMOUNT_PAYMENT,
            'split_equally': MenuContents.SPLIT_EQUALLY,
            'pay_for_entire_check': MenuContents.PAY_FOR_ENTIRE_CHECK,
            'pay_for_myself': MenuContents.PAY_FOR_MYSELF,
            'pay_for_others': MenuContents.PAY_FOR_OTHERS_AT_TABLE
        }
        self.logger.info("clicking checkout button")

        if self.is_element_present(MenuContents.GO_TO_CHECKOUT):
            self.click(MenuContents.GO_TO_CHECKOUT)
        else:
            self.click(MenuContents.VIEW_ORDER)
            self.click(MenuContents.GO_TO_CHECKOUT)
        self.logger.info("checkout button clicked")
        self.wait_for_loading_to_disappear(FreedomPayLocators.LOADER, name="#2 wait", initial_delay=1)
        self.logger.info("checking server popup")
        if self.is_element_present(MenuContents.SERVER_POPUP, timeout=3):
            self.attach_screenshot("Popup")
            self.click(MenuContents.SERVER_POPUP)
            self.click(MenuContents.GO_TO_CHECKOUT)
        self.logger.info("server popup checked")

        if payment_step_1 is not None and payment_step_1 in payment_types:
            self.logger.info("clicking payment step 1")
            self.click(payment_types[payment_step_1])
            self.logger.info("clicked payment step 1")
        # self.wait_for_loading_to_disappear(FreedomPayLocators.LOADER, name="#3 wait")


        if payment_step_2 is not None and payment_step_2 in payment_types:
            if not self.is_element_present(payment_types[payment_step_2]):
                self.click(MenuContents.GO_TO_CHECKOUT)
            self.logger.info("clicking payment step 2")
            self.click(payment_types[payment_step_2])
            self.logger.info("clicked payment step 2")

    @allure.step("Another service round")
    def another_service_rounds(self, item_count, current_sub_total):
        if self.is_element_present(MenuContents.BACK_TO_MENU_BUTTON):
            self.click(MenuContents.BACK_TO_MENU_BUTTON)
            new_round = self.select_random_menu_items(item_count)
            self.view_order()
            self.submit_order()
        else:
            new_round = self.select_random_menu_items(item_count)
            self.view_order()
            self.submit_order()
        new_subtotal = round(new_round['total'], 2) + current_sub_total
        return new_subtotal


    @allure.step("Click random reorder buttons")
    def reorder(self, num_clicks=None):
        self.logger.info("Looking for reorder buttons")
        reorder_buttons = self.find_elements(MenuContents.REORDER_BUTTON)

        if num_clicks is None:
            num_clicks = random.randint(1, len(reorder_buttons))
        else:
            num_clicks = min(num_clicks, len(reorder_buttons))
        selected_buttons = random.sample(reorder_buttons, num_clicks)
        self.logger.info(f"Clicking {num_clicks} out of {len(reorder_buttons)} reorder buttons")

        clicked_count = 0
        for button in selected_buttons:
            self.click(button)
            clicked_count += 1

        self.logger.info(f"Successfully clicked {clicked_count} reorder buttons")
        self.submit_order()

    def page_crash(self):
        try:
            locator = self.find_element(MenuContents.UHNO_ERROR, timeout=1)
            if locator:
                return True
            return False
        except Exception as e:
            return False












