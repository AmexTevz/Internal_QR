# import random
# import logging
# import time
# import os
# from datetime import datetime
# from src.pages.base_page import BasePage
# from src.locators.store_locators import ModifierLocators, CalculationLocators
# import math
# from selenium.webdriver.common.by import By
#
#
# class CartPage(BasePage):
#     def __init__(self, driver):
#         super().__init__(driver)
#         self.logger = logging.getLogger(__name__)
#         self.store_id = None
#
#     def capture_failure(self, error_type: str):
#         """Helper method to capture screenshot on failure"""
#         if not self.store_id:
#             self.logger.warning("Store ID not set when taking screenshot")
#             self.store_id = "unknown_store"
#
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#         screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'screenshots')
#         os.makedirs(screenshots_dir, exist_ok=True)
#
#         filename = f"calc_fail_{self.store_id}_{error_type}_{timestamp}.png"
#         filepath = os.path.join(screenshots_dir, filename)
#         self.driver.save_screenshot(filepath)
#         self.logger.info(f"Screenshot saved: {filepath}")
#
#     def add_to_cart(self):
#         required_groups = self.get_elements(ModifierLocators.REQUIRED_MODIFIER_GROUP)
#         for group in required_groups:
#             radio_options = group.find_elements(*ModifierLocators.RADIO_OPTIONS)
#             if radio_options:
#                 selected_option = random.choice(radio_options)
#                 self.click(selected_option)
#         optional_groups = self.get_elements(ModifierLocators.OPTIONAL_MODIFIER_GROUP)
#
#         for group in optional_groups:
#             group_title = group.text.lower()
#             if 'additional instructions' in group_title or 'remove' in group_title:
#                 continue
#             checkbox_options = group.find_elements(*ModifierLocators.CHECKBOX_OPTIONS)
#             if checkbox_options and random.choice([True, False]):
#                 num_to_select = random.randint(1, min(2, len(checkbox_options)))
#                 selected_options = random.sample(checkbox_options, num_to_select)
#                 for option in selected_options:
#                     self.click(option)
#         self.click(ModifierLocators.ADD_TO_CART)
#         time.sleep(1)
#
#     def add_to_cart_with_all_modifiers(self):
#         """Add item to cart with all possible modifiers"""
#         print("\nAdding item with all modifiers:")
#
#         # Handle required modifiers
#         required_groups = self.get_elements(ModifierLocators.REQUIRED_MODIFIER_GROUP)
#         if required_groups:
#             print(f"Found {len(required_groups)} required modifier groups")
#             for group in required_groups:
#                 radio_options = group.find_elements(*ModifierLocators.RADIO_OPTIONS)
#                 if radio_options:
#                     # Select last option as it often has the highest price
#                     selected = radio_options[-1]
#                     print(f"  - Selecting required option: {selected.text}")
#                     self.click(selected)
#
#         # Handle optional modifiers
#         optional_groups = self.get_elements(ModifierLocators.OPTIONAL_MODIFIER_GROUP)
#         if optional_groups:
#             print(f"Found {len(optional_groups)} optional modifier groups")
#             for group in optional_groups:
#                 group_title = group.text.lower()
#                 if 'additional instructions' in group_title or 'remove' in group_title:
#                     continue
#
#                 checkbox_options = group.find_elements(*ModifierLocators.CHECKBOX_OPTIONS)
#                 if checkbox_options:
#                     print(f"  - Adding all options from group: {group_title}")
#                     # Select all available options
#                     for option in checkbox_options:
#                         try:
#                             print(f"    * Adding option: {option.text}")
#                             self.click(option)
#                         except:
#                             self.logger.warning(f"Could not select modifier: {option.text}")
#
#         print("Adding to cart...")
#         self.click(ModifierLocators.ADD_TO_CART)
#         time.sleep(1)
#         print("Item added to cart\n")
#
#     def get_subtotal(self):
#         """Get subtotal from cart with detailed item breakdown"""
#         print("\nCart Contents:")
#         print("-" * 40)
#
#         script_subtotal = 0
#         cart_items = []
#
#         # Get all items in cart
#         main_items = self.get_elements(CalculationLocators.MAIN_ITEMS)
#         for item in main_items:
#             if "modifier" in item.get_attribute("class") and not "has-modifiers" in item.get_attribute("class"):
#                 continue
#
#             try:
#                 item_name = item.find_element(By.CSS_SELECTOR, "h3.cart-title").text
#             except:
#                 try:
#                     item_name = item.find_element(By.CSS_SELECTOR, "h3.typography-text-p3.cart-title").text
#                 except:
#                     item_name = "Unknown Item"
#
#             try:
#                 price_element = item.find_element(By.CSS_SELECTOR, "div.table-col-cart-4 p")
#                 price = price_element.text
#             except:
#                 try:
#                     price_element = item.find_element(By.CSS_SELECTOR, "div.table-col-cart-4.item-price")
#                     price = price_element.text
#                 except:
#                     price = "$0.00"
#
#             item_data = {
#                 "name": item_name,
#                 "price": price,
#                 "modifiers": []
#             }
#
#             # Get modifiers if any
#             if "has-modifiers" in item.get_attribute("class"):
#                 next_element = item.find_element(By.XPATH, "following-sibling::li[1]")
#                 while next_element and "modifier" in next_element.get_attribute(
#                         "class") and not "has-modifiers" in next_element.get_attribute("class"):
#                     try:
#                         modifier_name = next_element.find_element(By.CSS_SELECTOR, "div.table-col-cart-10").text
#                     except:
#                         modifier_name = "Unknown Modifier"
#
#                     try:
#                         modifier_price = next_element.find_element(By.CSS_SELECTOR, "p.price.modifier-price").text
#                     except:
#                         try:
#                             modifier_price = next_element.find_element(By.CSS_SELECTOR, "div.table-col-cart-4").text
#                         except:
#                             modifier_price = "$0.00"
#
#                     item_data["modifiers"].append({
#                         "name": modifier_name,
#                         "price": modifier_price
#                     })
#
#                     try:
#                         next_element = next_element.find_element(By.XPATH, "following-sibling::li[1]")
#                     except:
#                         break
#
#             cart_items.append(item_data)
#
#         # Print items and calculate total
#         for item in cart_items:
#             total_item_price = 0
#             print(f"Item: {item['name']}")
#             print(f"Price: {item['price']}")
#
#             try:
#                 item_price_float = float(item['price'].replace('$', ''))
#                 total_item_price += item_price_float
#             except:
#                 print("Error converting item price")
#
#             if item['modifiers']:
#                 print("Modifiers:")
#                 for modifier in item['modifiers']:
#                     mod_price = modifier['price']
#                     print(f"  - {modifier['name']}: {mod_price}")
#                     if '$' in mod_price:
#                         try:
#                             modifier_price_float = float(mod_price.replace('$', ''))
#                             total_item_price += modifier_price_float
#                         except:
#                             print("Error converting modifier price")
#             else:
#                 print("No modifiers")
#
#             print(f"Total Price for the item - ${total_item_price:.2f}")
#             print("-" * 40)
#             script_subtotal += total_item_price
#
#         # Get app's subtotal
#         app_subtotal = float(self.find_element(CalculationLocators.SUBTOTAL).text.replace('$', ''))
#
#         print(f"Script calculated SUBTOTAL: ${script_subtotal:.2f}")
#         print(f"App provided SUBTOTAL: ${app_subtotal:.2f}\n")
#
#         return app_subtotal
#
#     def go_to_cart(self):
#         time.sleep(0.5)
#         self.click(ModifierLocators.CART_BUTTON)
#         self.click(ModifierLocators.EXPAND_BUTTON)
#
#     def add_charity(self):
#         self.click(ModifierLocators.CHARITY_BUTTON)
#
#     def manage_tips(self, amount=None):
#         try:
#             if amount == 0:
#                 self.click(ModifierLocators.NO_TIP)
#             elif amount is None:
#                 self.click(random.choice([ModifierLocators.TIP_22, ModifierLocators.TIP_20, ModifierLocators.TIP_18]))
#             else:
#                 self.click(ModifierLocators.CUSTOM_TIP)
#                 custom_tip_input = self.find_element(ModifierLocators.CUSTOM_TIP_INPUT)
#                 custom_tip_input.clear()
#                 custom_tip_input.send_keys(str(amount))
#         except:
#             pass
#
#     def click_pay_now_button(self):
#         self.click(ModifierLocators.PAY_NOW_BUTTON)
#
#     def cart_calculations(self):
#         cart_items = []
#
#         main_items = self.driver.find_elements(*CalculationLocators.MAIN_ITEMS)
#         for item in main_items:
#             if "modifier" in item.get_attribute("class") and not "has-modifiers" in item.get_attribute("class"):
#                 continue
#
#             try:
#                 item_name = item.find_element(By.CSS_SELECTOR, "h3.cart-title").text
#             except:
#                 try:
#                     item_name = item.find_element(By.CSS_SELECTOR, "h3.typography-text-p3.cart-title").text
#                 except:
#                     item_name = "Unknown Item"
#
#             try:
#                 price_element = item.find_element(By.CSS_SELECTOR, "div.table-col-cart-4 p")
#                 price = price_element.text
#             except:
#                 try:
#                     price_element = item.find_element(By.CSS_SELECTOR, "div.table-col-cart-4.item-price")
#                     price = price_element.text
#                 except:
#                     price = "Price not found"
#
#             item_data = {
#                 "name": item_name,
#                 "price": price,
#                 "modifiers": []
#             }
#
#             if "has-modifiers" in item.get_attribute("class"):
#                 next_element = item.find_element(By.XPATH, "following-sibling::li[1]")
#                 while next_element and "modifier" in next_element.get_attribute(
#                         "class") and not "has-modifiers" in next_element.get_attribute("class"):
#                     try:
#                         modifier_name = next_element.find_element(By.CSS_SELECTOR, "div.table-col-cart-10").text
#                     except:
#                         modifier_name = "Unknown Modifier"
#
#                     try:
#                         modifier_price = next_element.find_element(By.CSS_SELECTOR, "p.price.modifier-price").text
#                     except:
#                         try:
#                             modifier_price = next_element.find_element(By.CSS_SELECTOR, "div.table-col-cart-4").text
#                         except:
#                             modifier_price = "Price not found"
#
#                     item_data["modifiers"].append({
#                         "name": modifier_name,
#                         "price": modifier_price
#                     })
#
#                     try:
#                         next_element = next_element.find_element(By.XPATH, "following-sibling::li[1]")
#                     except:
#                         break
#
#             cart_items.append(item_data)
#
#         script_subtotal = 0
#         for item in cart_items:
#             total_item_price = 0
#             print(f"\nItem: {item['name']}")
#             print(f"Price: {item['price']}")
#             item_price_float = float(item['price'].split('$')[1])
#             total_item_price += item_price_float
#
#             if item['modifiers']:
#                 print("Modifiers:")
#                 for modifier in item['modifiers']:
#                     mod_price = modifier['price'] if modifier['price'] else 'No additional cost'
#                     print(f"  - {modifier['name']}: {mod_price}")
#                     if '$' in mod_price:
#                         modifier_price_float = float(modifier['price'].split('$')[1])
#                         total_item_price += modifier_price_float
#                         print(f"Total Price for the item - ${total_item_price}")
#             else:
#                 print("No modifiers")
#                 print(f"Total Price for the item - ${total_item_price}")
#             print("-" * 40)
#             script_subtotal += total_item_price
#             script_subtotal = math.ceil(script_subtotal * 100) / 100
#         print(f"Script calculated SUBTOTAL: ${script_subtotal}")
#
#         # Helper function for safely getting elements
#         def safe_get_element(locator, default="0"):
#             try:
#                 return self.driver.find_element(*locator).text.replace('$', '')
#             except:
#                 print(f"Element not found: {locator}")
#                 return default
#
#         # Get all possible price components
#         app_subtotal = safe_get_element(CalculationLocators.SUBTOTAL)
#         tax = safe_get_element(CalculationLocators.TAX)
#         tip = safe_get_element(CalculationLocators.TIP)
#         service_charge = safe_get_element(CalculationLocators.AUTO_SERVICE_CHARGE)
#         app_total = safe_get_element(CalculationLocators.TOTAL)
#
#         # Calculate script total with all possible components
#         script_total = script_subtotal + float(tax) + float(tip) + float(service_charge)
#         script_total = math.ceil(script_total * 100) / 100
#
#         # Print all components for debugging
#         print(f"App provided SUBTOTAL: ${app_subtotal}")
#         print(f"TAX: ${tax}")
#         print(f"TIP: ${tip}")
#         print(f"Service charge: ${service_charge}")
#         print(f"App calculated TOTAL: ${app_total}")
#         print(f"Script calculated TOTAL: ${script_total}")
#
#         return (
#             script_subtotal,
#             float(app_subtotal),
#             float(tax),
#             float(tip),
#             float(app_total),
#             float(script_total)
#         )
#
#     def clear_cart(self):
#
#         print("\nClearing cart...")
#         max_retries = 3
#         for attempt in range(max_retries):
#             try:
#                 items_deleted = 0
#                 while True:
#                     # Get fresh elements each time
#                     delete_buttons = self.get_elements(CalculationLocators.DELETE_FROM_CART)
#                     if not delete_buttons:
#                         print(f"Cart cleared - {items_deleted} items removed")
#                         return  # No more items to delete
#
#                     # Try to delete first item
#                     try:
#                         self.click(delete_buttons[0])
#                         items_deleted += 1
#                         time.sleep(0.5)  # Wait for animation/update
#                     except Exception as e:
#                         self.logger.warning(f"Failed to click delete button: {str(e)}")
#                         # If click failed, break inner loop to retry with fresh elements
#                         break
#
#             except Exception as e:
#                 if attempt == max_retries - 1:  # Last attempt
#                     self.logger.error(f"Failed to clear cart after {max_retries} attempts: {str(e)}")
#                     raise
#                 else:
#                     print(f"Attempt {attempt + 1} failed, retrying...")
#                     time.sleep(1)  # Wait before retry
#                     # Refresh cart view
#                     self.go_to_cart()
#
#     def return_to_menu(self):
#         """Return to menu using Add More Items button"""
#         self.click(CalculationLocators.ADD_MORE_ITEMS)
#         time.sleep(1)  # Wait for navigation
#
#     def expand(self):
#         self.click(ModifierLocators.EXPAND_BUTTON)
#
#     def calculate_price(self):
#         def safe_get_element(locator, default="0"):
#             try:
#                 return self.driver.find_element(*locator).text.replace('$', '')
#             except:
#                 print(f"Element not found: {locator}")
#                 return default
#         # Get all possible price components
#         app_subtotal = safe_get_element(CalculationLocators.SUBTOTAL)
#         tax = safe_get_element(CalculationLocators.TAX)
#         tip = safe_get_element(CalculationLocators.TIP)
#         donation = safe_get_element(CalculationLocators.DONATION)
#         app_total = safe_get_element(CalculationLocators.TOTAL)
#
#         return float(app_subtotal), float(tax), float(donation), float(tip), float(app_total)