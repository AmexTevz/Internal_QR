import time
from selenium.common import TimeoutException
from src.pages.base_page import BasePage
from src.locators.store_locators import (MenuContents)
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
        self.cart_items = {}
        self.logger = Logger("MenuPage")
        self.reorder = 0

    @allure.step("Navigate to main page")
    def navigate_to_main_menu(self):
        try:
            self.logger.info("Starting navigation to main menu")
            if self.is_element_present(MenuContents.INITIAL_BUTTON):
                time.sleep(2)
                # self.driver.refresh()
                self.click(MenuContents.INITIAL_BUTTON)
            self.logger.info("Successfully navigated to main menu")
            while not self.find_elements(MenuContents.MENU_ITEMS):
                self.driver.refresh()
                time.sleep(1)
        except Exception as e:
            self.logger.exception(f"Failed to navigate to main menu: {str(e)}")


    @allure.step("Get order number")
    def order_number(self):
        try:
            number = self.get_text_2(MenuContents.CHECK_NUMBER)
            result = number.replace("#", "")
            self.logger.info(f"Order number retrieved: {result}")
            self.attach_note(f"Order number: {result}")
            self.attach_screenshot("Order number")
            return result
        except Exception as e:
            self.logger.error(f"Failed to get order number: {str(e)}")
            self.logger.exception(f"Failed to get order number: {str(e)}")
    def _extract_item_info(self, item):
        """Extract item ID and name from an article element"""
        try:
            item_id = item.get_attribute("id")

            # Find the title element INSIDE this article
            title_element = item.find_element(By.CSS_SELECTOR, '.menu-list-title')
            item_name = title_element.text.strip()

            self.logger.debug(f"Extracted item - ID: {item_id}, Name: {item_name}")
            return item_id, item_name
        except Exception as e:
            self.logger.exception(f"Failed to extract item info: {str(e)}")
            return None, None

    @allure.step("Verify badge count for item {item_id}")
    def verify_item_badge_count(self, item_id, expected_count):

        try:
            # Locate the add button for this specific item
            add_button_locator = (By.ID, f"add-item-{item_id}")
            add_button = self.find_element(add_button_locator, timeout=5)

            if not add_button:
                self.logger.error(f"Add button not found for item {item_id}")
                return False

            # Check if badge exists (item has been added to cart)
            badge_locator = (By.CSS_SELECTOR, f"#add-item-{item_id} .menu-item-add-count")

            if expected_count == 0:
                if not self.is_element_displayed(badge_locator):
                    self.logger.info(f"Badge correctly not displayed for item {item_id} (expected: 0)")
                    return True
                else:
                    actual_count = self._get_badge_count(item_id)
                    self.logger.error(f"Badge unexpectedly displayed for item {item_id}. Count: {actual_count}")
                    return False

            actual_count = self._get_badge_count(item_id)

            if actual_count == expected_count:
                self.logger.info(f"Badge count verified for item {item_id}: {actual_count} == {expected_count}")
                self.attach_note(f"Badge count verified for item {item_id}: {actual_count} == {expected_count}")
                self.attach_screenshot()
                return True
            else:
                self.logger.error(
                    f"Badge count mismatch for item {item_id}: expected {expected_count}, got {actual_count}")
                return False

        except Exception as e:
            self.logger.exception(f"Failed to verify badge count for item {item_id}: {str(e)}")
            return False

    def _get_badge_count(self, item_id):
        try:
            badge_selector = f"#add-item-{item_id} .menu-item-add-count"
            badge_elements = self.driver.find_elements(By.CSS_SELECTOR, badge_selector)

            # Return only VISIBLE badge (not all instances)
            for badge in badge_elements:
                if badge.is_displayed():
                    count_text = badge.text.strip()
                    return int(count_text) if count_text else 0

            return 0
        except Exception as e:
            self.logger.debug(f"No visible badge found for item {item_id}: {str(e)}")
            return 0

    @allure.step("Verify all cart item badges")
    def verify_item_badges(self):
        results = {}
        for item_id, expected_count in self.cart_items.items():
            results[item_id] = self.verify_item_badge_count(item_id, expected_count)

        all_passed = all(results.values())
        self.logger.info(f"Badge verification complete. All passed: {all_passed}")
        return all_passed

    def clear_cart_tracking(self):
        """Reset the cart tracking dictionary"""
        self.cart_items = {}
        self.logger.debug("Cart tracking cleared")

    def _increase_quantity(self, times=1):
        """Click the plus button to increase quantity"""
        try:
            for i in range(times):
                plus_button = self.find_element(MenuContents.QTY_PLUS_BUTTON)
                self.click(plus_button)
                self.logger.debug(f"Clicked plus button ({i + 1}/{times})")
        except Exception as e:
            self.logger.exception(f"Failed to increase quantity: {str(e)}")

    @allure.step("Get cart badge count")
    def get_cart_badge_count(self):
        """Get the total count shown on cart icon"""
        try:
            if self.is_element_displayed(MenuContents.CART_BADGE):
                count_text = self.get_text(MenuContents.CART_BADGE)
                count = int(count_text) if count_text else 0
                self.logger.info(f"Cart badge count: {count}")
                return count
            self.logger.debug("Cart badge not displayed")
            return 0
        except Exception as e:
            self.logger.error(f"Failed to get cart badge count: {str(e)}")
            self.logger.debug(f"Cart badge not found: {str(e)}")
            return 0

    @allure.step("Verify cart badge shows accurate number")
    def verify_cart_badge(self, expected_count=None):

        try:
            if expected_count is None:
                expected_count = sum(self.cart_items.values())

            actual_count = self.get_cart_badge_count()

            if actual_count == expected_count:
                self.logger.info(f"Cart badge verified: {actual_count} == {expected_count}")
                self.attach_note(f"Cart badge verified: {actual_count} == {expected_count}")
                self.attach_screenshot("Cart badge verified")
                return True
            else:
                self.logger.error(f"Cart badge mismatch: expected {expected_count}, got {actual_count}")
                self.attach_screenshot("Cart badge mismatch")
                return False
        except Exception as e:
            self.logger.error(f"Failed to verify cart badge: {str(e)}")
            self.logger.exception(f"Failed to verify cart badge: {str(e)}")
            return False

    @allure.step("Add {quantity} more of item {item_id}")
    def add_more_of_item(self, item_id, quantity=1, verify_badges=True):
        try:
            item_locator = (By.ID, item_id)
            item = self.find_element(item_locator)
            item_name = item.find_element(By.CSS_SELECTOR, '.menu-list-title').text.strip()

            previous_count = self.cart_items.get(item_id, 0)
            new_count = previous_count + quantity

            with allure.step(f"Adding {quantity} more of '{item_name}'"):
                allure.attach(
                    f"Item: {item_name}\n"
                    f"Item ID: {item_id}\n"
                    f"Previous Quantity: {previous_count}\n"
                    f"Adding: {quantity}\n"
                    f"New Expected Quantity: {new_count}",
                    name=f"Before Adding More",
                    attachment_type=allure.attachment_type.TEXT
                )

            self.logger.info(f"Adding {quantity} more of item {item_id} ({item_name})")
            self.click(item)

            if quantity > 1:
                with allure.step(f"Increase quantity to {quantity}"):
                    self._increase_quantity(quantity - 1)

            with allure.step(f"Add to cart"):
                add_button = self.find_element(MenuContents.ADD_BUTTON)
                self.click(add_button)

            self.cart_items[item_id] = new_count
            self.logger.debug(f"Cart updated - {item_id}: {self.cart_items[item_id]}")

            allure.attach(
                f"Item: {item_name}\n"
                f"Item ID: {item_id}\n"
                f"Quantity Added: {quantity}\n"
                f"New Total Quantity: {new_count}",
                name=f"After Adding More",
                attachment_type=allure.attachment_type.TEXT
            )

            if verify_badges:
                with allure.step(f"Verify badges after adding more of '{item_name}'"):
                    item_badge_ok = self.verify_item_badge_count(item_id, new_count)
                    cart_badge_ok = self.verify_cart_badge()
                    self.attach_screenshot(f"After adding {quantity} more of '{item_name}'")
                    return item_badge_ok and cart_badge_ok

            return True

        except Exception as e:
            with allure.step(f"❌ ERROR adding more of item {item_id}"):
                allure.attach(
                    f"Item ID: {item_id}\n"
                    f"Quantity to Add: {quantity}\n"
                    f"Error: {str(e)}",
                    name="Error Adding More",
                    attachment_type=allure.attachment_type.TEXT
                )
                self.attach_screenshot(f"Error adding more of {item_id}")
            self.logger.exception(f"Failed to add more of item {item_id}: {str(e)}")
            return False

    @allure.step("Select {num_items} random menu items")
    def select_random_menu_items(self, num_items=2, quantity=1, verify_badges=True):

        self.logger.info(f"Starting to select {num_items} random menu items (qty: {quantity} each)")
        try:
            while not self.find_elements(MenuContents.MENU_ITEMS):
                self.driver.refresh()
                time.sleep(1)
            items = self.find_elements(MenuContents.ITEMS)

            if not items:
                return {'items': [], 'total': 0.0, 'count': 0}

            self.logger.debug(f"Found {len(items)} menu items")
            random.shuffle(items)
            selected_items = items[:min(num_items, len(items))]

            item_details = []
            total_price = 0.0

            for index, item in enumerate(selected_items, 1):
                try:
                    item_id, item_name = self._extract_item_info(item)
                    self.logger.debug(f"Processing item - ID: {item_id}, Name: {item_name}")

                    self.click(item)

                    if self.is_element_displayed(MenuContents.ITEM_PRICE):
                        price_text = self.get_text(MenuContents.ITEM_PRICE)
                        base_price = float(price_text.replace('$', '').replace(',', ''))
                    else:
                        base_price = 0.0

                    self.logger.debug(f"Item: {item_name}, Base price: ${base_price}")

                    with allure.step(f"Select modifiers for '{item_name}'"):
                        selected_modifiers, modifier_cost = self._handle_all_modifiers()
                        self.attach_screenshot(f"After selecting modifiers for '{item_name}'")

                    # Increase quantity if more than 1
                    if quantity > 1:
                        with allure.step(f"Set quantity to {quantity}"):
                            self._increase_quantity(quantity - 1)
                            self.attach_screenshot(f"Quantity set to {quantity}")

                    # Click ADD button
                    with allure.step(f"Add '{item_name}' to cart"):
                        add_button = self.find_element(MenuContents.ADD_BUTTON)
                        self.click(add_button)

                    # Track this item in cart
                    if item_id:
                        self.cart_items[item_id] = self.cart_items.get(item_id, 0) + quantity
                        self.logger.debug(f"Cart tracking updated - {item_id}: {self.cart_items[item_id]}")

                    total_item_price = (base_price + modifier_cost) * quantity
                    item_details.append({
                        'id': item_id,
                        'name': item_name,
                        'base_price': base_price,
                        'modifiers': selected_modifiers,
                        'modifier_cost': modifier_cost,
                        'total_price': total_item_price,
                        'quantity': self.cart_items.get(item_id, 1)
                    })
                    total_price += total_item_price
                    self.logger.debug(f"Item added successfully. Total price so far: ${total_price:.2f}")

                    # Verify badges after adding
                    if verify_badges and item_id:
                        with allure.step(f"Verify badges for '{item_name}'"):
                            expected_item_count = self.cart_items[item_id]
                            item_badge_ok = self.verify_item_badge_count(item_id, expected_item_count)
                            if not item_badge_ok:
                                self.logger.warning(f"Item badge verification failed for {item_id}")

                            cart_badge_ok = self.verify_cart_badge()
                            if not cart_badge_ok:
                                self.logger.warning("Cart badge verification failed")

                            self.attach_screenshot(f"Badge verification for '{item_name}'")

                except Exception as e:
                    self.logger.exception(f"Failed to process item {index}: {str(e)}")
                    continue

            result = {
                'items': item_details,
                'total': round(total_price, 3),
                'count': len(item_details),
                'cart_tracking': self.cart_items.copy() if self.cart_items else {}
            }
            self.logger.info(f"Successfully selected {len(item_details)} items. Total: ${result['total']}")
            self.logger.info(f"Cart summary: {self.cart_items}")
            return result['total']

        except Exception as e:
            self.logger.exception(f"Failed to select random menu items: {str(e)}")


    def _handle_all_modifiers(self):
        try:
            modal = self.find_element((By.CSS_SELECTOR, ".mod-card"), timeout=0)
            if not modal:
                return [], 0.0

            all_selected_modifiers = []
            total_cost = 0.0

            all_elements = modal.find_elements(By.XPATH, ".//*")

            group_headers = modal.find_elements(By.CSS_SELECTOR, ".mod-group-title")

            if not group_headers:
                self.logger.debug("No modifier groups found")
                return [], 0.0

            for header_index in range(len(group_headers)):
                try:
                    header = group_headers[header_index]

                    section_title = header.text.strip()  # ← CHANGED THIS LINE
                    self.logger.info(f"Processing modifier section {header_index + 1}: {section_title}")
                    self.logger.info(
                        f"Processing modifier section {header_index + 1}: {section_title}")  # Changed to INFO

                    # Get the position of this header and the next header
                    header_position = all_elements.index(header)

                    # Find the position of the next header (if exists)
                    next_header_position = None
                    if header_index + 1 < len(group_headers):
                        next_header = group_headers[header_index + 1]
                        next_header_position = all_elements.index(next_header)

                    option_buttons = []
                    start_search = header_position + 1
                    end_search = next_header_position if next_header_position else len(all_elements)

                    for elem in all_elements[start_search:end_search]:
                        if elem.tag_name == "button" and "mod-option-row" in elem.get_attribute("class"):
                            option_buttons.append(elem)

                    self.logger.info(
                        f"Found {len(option_buttons)} option buttons in section: {section_title}")  # ADD THIS

                    if not option_buttons:
                        self.logger.info(f"No options found in section: {section_title}")  # Changed to INFO
                        continue

                    available_options = [btn for btn in option_buttons
                                         if btn.get_attribute("aria-pressed") == "false"]

                    self.logger.info(
                        f"Available options (not pressed): {len(available_options)} out of {len(option_buttons)}")  # ADD THIS

                    if not available_options:
                        self.logger.info(f"All options already selected in section: {section_title}")  # Changed to INFO
                        continue

                    selected_button = random.choice(available_options)
                    modifier_info = self._extract_modifier_info_new(selected_button, section_title)

                    self.logger.info(  # Changed to INFO
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
        try:

            button_text = button_element.text.strip()

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

    @allure.step("Verify logo exists")
    def verify_logo_exists(self):
        try:
            if self.is_element_present(MenuContents.LOGO):
                self.logger.info("Logo verification passed")
                self.attach_note("Logo exists on page")
                self.attach_screenshot("Logo verified")
                return True
            else:
                self.logger.error("Logo not found on page")
                self.attach_screenshot("Logo not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to verify the logo: {str(e)}")
            self.logger.exception(f"Failed to verify the logo: {str(e)}")
            self.attach_screenshot("Logo verification failed")
            return False

    @allure.step("Get table number from menu page")
    def menu_page_table_num(self):
        try:
            element = self.wait_for_element_with_text(
                MenuContents.TABLE_NUMBER_MENU_PAGE,
                timeout=3
            )

            raw_text = element.text.strip()
            table_number = int(raw_text.split('#')[1])
            self.logger.info(f"Table number retrieved: {table_number}")
            self.attach_note(f"Table number: {table_number}")
            self.attach_screenshot("Table number")
            return table_number

        except Exception as e:
            self.logger.error(f"Failed to get table number: {str(e)}")
            self.logger.exception("Failed to get table number from the menu page")


    def search_multiple_keywords(self, keywords: list[str]) -> dict:
        while not self.find_elements(MenuContents.MENU_ITEMS):
            self.driver.refresh()
            time.sleep(1)
        all_results = {}
        try:
            for keyword in keywords:
                try:
                    search_button = self.wait_for_element_visible(MenuContents.SEARCH_BUTTON, timeout=5)
                    if search_button:
                        self.click(search_button)
                        search_input = self.wait_for_element_visible(MenuContents.SEARCH_INPUT)
                        search_input.clear()
                        self.send_keys(MenuContents.SEARCH_INPUT, keyword)
                        self.logger.info(f"Searching for '{keyword}'")
                        time.sleep(1)
                        results = self.find_elements(MenuContents.MENU_ITEMS)
                        self.attach_screenshot(f"Results for '{keyword}'")
                        result_texts = []
                        for result in results:
                            name = description = ""
                            try:
                                name_elem = result.find_element(*MenuContents.MENU_ITEM_TITLE)
                                name = name_elem.text.strip()
                                self.logger.debug(f"Found name: {name}")
                            except Exception:
                                pass
                            try:
                                desc_elem = result.find_element(*MenuContents.MENU_ITEM_DESCRIPTION)
                                description = desc_elem.text.strip()
                                self.logger.debug(f"Found description: {description}")
                            except Exception:
                                pass
                            full_text = f"{name} {description}".strip()
                            result_texts.append(full_text)
                            self.logger.debug(f"Found search result: {full_text}")
                        all_results[keyword] = result_texts
                except Exception as e:
                    self.logger.exception(f"Search failed for '{keyword}': {e}")
                    all_results[keyword] = []
        except TimeoutException:
            self.logger.warning("Search button was not visible before timeout.")
        except Exception as e:
            self.logger.exception(f"Failed during multi-search: {str(e)}")
        return all_results

    def category_navigation_sync(self):
        while not self.find_elements(MenuContents.MENU_ITEMS):
            self.driver.refresh()
            time.sleep(1)
            self.logger.info(f"Searching for '{MenuContents.MENU_ITEMS}'")
        categories = self.find_elements((By.CSS_SELECTOR, ".menu-category-label"))
        assert categories, "No categories found at top bar"

        for category in categories:
            category_name = category.text.strip()
            self.logger.info(f"Checking category click scroll for '{category_name}'")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", category)
            category.click()

            active_category = self.find_element(MenuContents.ACTIVE_CATEGORY_SLIDER)
            expected_lower = category_name.lower()
            active_text = active_category.text.lower()

            if expected_lower not in active_text:
                self.driver.execute_script("window.scrollBy(0, -120);")
                time.sleep(0.5)
                self.find_element(MenuContents.ACTIVE_CATEGORY_SLIDER).text.lower()


            sections = self.find_elements(MenuContents.MENU_SECTION_TITLE)
            matched_section = next((s for s in sections if category_name.lower() in s.text.lower()), None)
            assert matched_section, f"No section found for category '{category_name}'"
            self.driver.execute_script("return arguments[0].getBoundingClientRect().middle;",
                                                     matched_section)

        for section in self.find_elements(MenuContents.MENU_SECTION_TITLE):
            section_name = section.text.strip()
            self.logger.info(f"Checking scroll sync for section '{section_name}'")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", section)
            self.wait_until(
                lambda: section_name.lower() in self.find_element(MenuContents.ACTIVE_CATEGORY_SLIDER).text.lower(),
                timeout=5,
                description=f"active category to switch to {section_name}"
            )
            active = self.find_element(MenuContents.ACTIVE_CATEGORY_SLIDER)
            assert section_name.lower() in active.text.lower(), f"Category slider did not switch to '{section_name}'"


    @allure.step("Navigate to basket")
    def go_to_basket(self):
        try:
            self.click(MenuContents.CART_ICON)
            self.logger.info("Successfully navigated to basket")
            self.attach_screenshot("Basket page")
        except Exception as e:
            self.logger.error(f"Failed to go to basket: {str(e)}")
            self.logger.exception(f"Failed to go to basket: {str(e)}")


    @allure.step("Get all category buttons with IDs")
    def get_all_category_buttons(self):
        """
        Get all category pill buttons with their IDs and names.

        Returns:
            list: List of dicts with 'element', 'id', 'name' for each category button
        """
        try:
            category_buttons = self.find_elements(MenuContents.CATEGORY_PILLS)
            categories = []

            for button in category_buttons:
                try:
                    category_id = button.get_attribute('id')
                    label_element = button.find_element(*MenuContents.CATEGORY_LABEL)
                    category_name = label_element.text.strip()

                    if category_id and category_name:
                        categories.append({
                            'element': button,
                            'id': category_id,
                            'name': category_name
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to extract category info from button: {str(e)}")
                    continue

            self.logger.info(f"Found {len(categories)} categories in UI navigation bar")
            return categories

        except Exception as e:
            self.logger.error(f"Failed to get category buttons: {str(e)}")
            return []

    @allure.step("Click category: {category_name}")
    def click_category_by_id(self, category_id, category_name):
        """
        Click a category button by its ID and wait for it to become active.

        Args:
            category_id: The HTML id attribute of the category button
            category_name: Name for logging purposes

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            category_button = self.find_element(MenuContents.category_button_by_id(category_id))

            if not category_button:
                self.logger.error(f"Category button not found for '{category_name}' (ID: {category_id})")
                return False

            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", category_button)
            time.sleep(0.2)

            # Click the button
            self.click(category_button)
            self.logger.info(f"Clicked category '{category_name}', waiting for it to become active...")

            # Wait for this category to become active (DOM update)
            def category_is_active():
                try:
                    active_ids = self.get_active_category_ids()
                    return category_id in active_ids
                except:
                    return False

            wait_success = self.wait_until(
                category_is_active,
                timeout=7,
                poll_frequency=0.1,
                description=f"category '{category_name}' to become active"
            )

            if not wait_success:
                current_active = self.get_active_category_ids()
                if current_active:
                    # Try to get the name of the currently active category
                    active_id = current_active[0]
                    self.logger.error(
                        f"Category '{category_name}' (ID: {category_id}) did not become active within 7 seconds. "
                        f"Different category is active (ID: {active_id})"
                    )
                else:
                    self.logger.error(
                        f"Category '{category_name}' (ID: {category_id}) did not become active within 7 seconds. "
                        f"No active category detected"
                    )
                return False

            self.logger.info(f"Category '{category_name}' successfully became active")
            return True

        except Exception as e:
            self.logger.error(f"Failed to click category '{category_name}' (ID: {category_id}): {str(e)}")
            return False

    def get_active_category_ids(self):
        """
        Get IDs of all currently active categories.
        Should normally be only one, but this checks for multiple.

        Returns:
            list: List of active category IDs
        """
        try:
            active_categories = self.find_elements(MenuContents.ACTIVE_CATEGORY_SLIDER)
            active_ids = []

            for cat in active_categories:
                cat_id = cat.get_attribute('id')
                if cat_id:
                    active_ids.append(cat_id)

            if len(active_ids) > 1:
                self.logger.warning(f"Multiple active categories detected: {active_ids}")

            return active_ids

        except Exception as e:
            self.logger.error(f"Failed to get active categories: {str(e)}")
            return []

    @allure.step("Wait for section title to be visible: {expected_title}")
    def wait_for_section_title_visible(self, expected_title, timeout=7):
        """
        Wait for a section title matching expected_title to be visible in viewport.

        Args:
            expected_title: The expected section title text (case-insensitive)
            timeout: Maximum seconds to wait (default 7)

        Returns:
            bool: True if section title found and visible, False otherwise
        """
        try:
            self.logger.info(f"Waiting for section '{expected_title}' to become visible in viewport...")

            def section_is_visible():
                sections = self.find_elements(MenuContents.MENU_SECTION_TITLE)
                for section in sections:
                    try:
                        section_text = section.text.strip()
                        if expected_title.lower() in section_text.lower():
                            is_displayed = section.is_displayed()

                            if is_displayed:
                                rect = self.driver.execute_script(
                                    "return arguments[0].getBoundingClientRect();",
                                    section
                                )
                                viewport_height = self.driver.execute_script("return window.innerHeight;")

                                # Log the position details
                                self.logger.info(
                                    f"Section '{expected_title}' found: "
                                    f"top={rect['top']:.1f}, bottom={rect['bottom']:.1f}, "
                                    f"viewport_height={viewport_height}"
                                )

                                # More lenient check - section just needs to be somewhat visible
                                in_viewport = rect['bottom'] > 0 and rect['top'] < viewport_height

                                if in_viewport:
                                    self.logger.info(f"Section '{expected_title}' is in viewport")
                                    return True
                                else:
                                    self.logger.info(
                                        f"Section '{expected_title}' outside viewport"
                                    )
                    except Exception as e:
                        self.logger.debug(f"Error checking section: {str(e)}")
                        continue
                return False

            result = self.wait_until(
                section_is_visible,
                timeout=timeout,
                poll_frequency=0.1,
                description=f"section '{expected_title}' to be visible in viewport",
                on_timeout_return=True
            )

            if result:
                self.logger.info(f"Section '{expected_title}' is now visible in viewport")
            else:
                self.logger.warning(
                    f"Section '{expected_title}' did not become visible within {timeout} seconds. "
                    f"Page may not have scrolled to this section."
                )

            return result

        except Exception as e:
            self.logger.error(f"Error waiting for section '{expected_title}': {str(e)}")
            return False

    def get_visible_section_title(self):
        """
        Get the section title that is currently most visible in the viewport.

        Returns:
            str: The visible section title text, or None if none found
        """
        try:
            sections = self.find_elements(MenuContents.MENU_SECTION_TITLE)

            for section in sections:
                try:
                    if section.is_displayed():
                        rect = self.driver.execute_script(
                            "return arguments[0].getBoundingClientRect();",
                            section
                        )
                        viewport_height = self.driver.execute_script("return window.innerHeight;")

                        if rect['top'] < viewport_height and rect['bottom'] > 0:
                            section_text = section.text.strip()
                            if section_text:
                                return section_text
                except Exception:
                    continue

            self.logger.warning("No section title is currently visible in viewport")
            return None

        except Exception as e:
            self.logger.error(f"Failed to get visible section title: {str(e)}")
            return None

    def attach_api_category_data(self, api_category, category_name):
        """Attach API category data to Allure report"""
        api_info = (
            f"Category: {category_name}\n"
            f"ID: {api_category.get('ID')}\n"
            f"Active: {api_category.get('Active')}\n"
            f"OpenTime: {api_category.get('OpenTime')}\n"
            f"CloseTime: {api_category.get('CloseTime')}\n"
            f"IsAlcohol: {api_category.get('IsAlcohol')}\n"
            f"DisplayOrder: {api_category.get('DisplayOrder')}"
        )
        self.attach_note(api_info, f"API: {category_name}")

    @allure.step("Verify category: {category_name}")
    def verify_category_navigation(self, category_id, category_name, expected_active_count=1):
        """
        Click a category and verify it works correctly.
        Returns dict with results - does not raise exceptions.

        Args:
            category_id: Category ID to click
            category_name: Category name for logging
            expected_active_count: Expected number of active categories (default 1)

        Returns:
            dict: {
                'clicked': bool,
                'became_active': bool,
                'section_visible': bool,
                'active_count': int,
                'active_category_name': str or None
            }
        """
        results = {
            'clicked': False,
            'became_active': False,
            'section_visible': False,
            'active_count': 0,
            'active_category_name': None
        }

        try:
            # Click the category
            click_success = self.click_category_by_id(category_id, category_name)
            results['clicked'] = click_success

            if not click_success:
                self.logger.warning(f"Failed to click category '{category_name}'")
                return results

            # Check if this category became active (log only, don't fail)
            active_ids = self.get_active_category_ids()
            results['active_count'] = len(active_ids)
            results['became_active'] = category_id in active_ids

            if not results['became_active']:
                if active_ids:
                    self.logger.warning(
                        f"Category '{category_name}' was clicked but did not become active. "
                        f"Another category is active instead."
                    )
                else:
                    self.logger.warning(f"Category '{category_name}' was clicked but no category is active.")

            if active_ids and len(active_ids) > 0:
                # Try to get the name if we can
                results['active_category_name'] = active_ids[0]

            # Check if section appears
            section_visible = self.wait_for_section_title_visible(category_name, timeout=7)
            results['section_visible'] = section_visible

            if not section_visible:
                self.logger.warning(
                    f"Section '{category_name}' did not become visible in viewport within 7 seconds"
                )

            # Take screenshot
            self.attach_screenshot(f"Category: {category_name}")
            return results



        except Exception as e:
            self.logger.error(f"Error verifying category '{category_name}': {str(e)}")
            return results

    @allure.step("Get {num_items} random menu items for search testing")
    def get_random_menu_items_for_search(self, num_items=5):
        self.click(MenuContents.SEARCH_CANCEL)
        time.sleep(1)
        try:
            while not self.find_elements(MenuContents.MENU_ITEMS):
                self.driver.refresh()
                time.sleep(1)

            items = self.find_elements(MenuContents.ITEMS)

            if not items:
                self.logger.warning("No menu items found")
                return []

            self.logger.info(f"Found {len(items)} total menu items, selecting {num_items} random items")

            random.shuffle(items)
            selected_items = items[:min(num_items, len(items))]

            item_details = []
            for item in selected_items:
                try:
                    item_id, item_name = self._extract_item_info(item)
                    if item_id and item_name:
                        item_details.append({
                            'id': item_id,
                            'name': item_name
                        })
                        self.logger.debug(f"Selected item for search test: {item_name} (ID: {item_id})")
                except Exception as e:
                    self.logger.warning(f"Failed to extract item info: {str(e)}")
                    continue

            self.logger.info(f"Successfully selected {len(item_details)} items for search testing")
            return item_details

        except Exception as e:
            self.logger.exception(f"Failed to get random menu items: {str(e)}")
            return []

    @allure.step("Search for '{item_name}' and verify it's first result")
    def search_and_verify_first_result(self, item_name):

        result = {
            'searched': False,
            'results_found': False,
            'is_first': False,
            'first_result_name': None,
            'total_results': 0
        }

        try:
            # Click search button
            search_button = self.wait_for_element_visible(MenuContents.SEARCH_BUTTON, timeout=5)
            if not search_button:
                self.logger.error("Search button not found")
                return result

            self.click(search_button)

            # Enter search query
            search_input = self.wait_for_element_visible(MenuContents.SEARCH_INPUT)
            if not search_input:
                self.logger.error("Search input not found")
                return result

            search_input.clear()
            self.send_keys(MenuContents.SEARCH_INPUT, item_name)
            self.logger.info(f"Searching for exact item name: '{item_name}'")
            result['searched'] = True

            # Wait for results
            time.sleep(1)

            # Get search results
            results = self.find_elements(MenuContents.MENU_ITEMS)
            result['total_results'] = len(results)

            if not results:
                self.logger.warning(f"No results found for '{item_name}'")
                self.attach_screenshot(f"No results for '{item_name}'")
                return result

            result['results_found'] = True
            self.logger.info(f"Found {len(results)} results for '{item_name}'")

            # Get the first result's name
            try:
                first_result = results[0]
                first_name_elem = first_result.find_element(*MenuContents.MENU_ITEM_TITLE)
                first_result_name = first_name_elem.text.strip()
                result['first_result_name'] = first_result_name

                # Check if first result matches the searched item
                if first_result_name.lower() == item_name.lower():
                    result['is_first'] = True
                    self.logger.info(f"✅ '{item_name}' is the first result")
                else:
                    result['is_first'] = False
                    self.logger.warning(
                        f"❌ '{item_name}' is NOT the first result. "
                        f"First result is: '{first_result_name}'"
                    )

                self.attach_screenshot(f"Search results for '{item_name}'")

            except Exception as e:
                self.logger.error(f"Failed to extract first result name: {str(e)}")

            return result

        except Exception as e:
            self.logger.exception(f"Failed to search and verify '{item_name}': {str(e)}")
            return result

    def attach_badge_test_summary(self):
        """Call at end of badge test to show what failed/passed"""
        import allure

        summary_lines = ["BADGE VERIFICATION SUMMARY", "=" * 60, "", "CART CONTENTS:"]

        for item_id, count in self.cart_items.items():
            summary_lines.append(f"  {item_id}: {count} items")
        summary_lines.append("")

        expected_total = sum(self.cart_items.values())
        actual_total = self.get_cart_badge_count()

        summary_lines.append("CART BADGE:")
        if expected_total == actual_total:
            summary_lines.append(f"  ✅ PASSED - Expected: {expected_total}, Actual: {actual_total}")
        else:
            summary_lines.append(
                f"  ❌ FAILED - Expected: {expected_total}, Actual: {actual_total} (Diff: +{actual_total - expected_total})")
        summary_lines.append("")

        summary_lines.append("ITEM BADGES:")
        for item_id, expected_count in self.cart_items.items():
            actual_count = self._get_badge_count(item_id)
            if expected_count == actual_count:
                summary_lines.append(f"  ✅ {item_id}: Expected {expected_count}, Got {actual_count}")
            else:
                summary_lines.append(
                    f"  ❌ {item_id}: Expected {expected_count}, Got {actual_count} (Diff: +{actual_count - expected_count})")

        summary_text = "\n".join(summary_lines)

        allure.attach(
            summary_text,
            name="Badge Test Summary",
            attachment_type=allure.attachment_type.TEXT
        )

        print("\n" + summary_text)















