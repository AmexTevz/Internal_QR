# """
# Application Performance Tests - Measure user experience speed
# Tests real browser operations (Selenium) to measure what users experience
# """
# import pytest
# import allure
# import time
# from src.pages.store.menu_page import MenuPage
# from src.pages.store.cart_page import CartPage
# from src.pages.store.checkout_page import CheckoutPage
# from src.pages.store.payment_page import PaymentPage
# from src.data.endpoints.close_table import close_table
# from src.utils.performance_metrics import PerformanceTimer
# from tests.performance.conftest import (
#     PERFORMANCE_TABLE,
#     get_sla_threshold
# )
#
#
# @pytest.mark.performance
# @pytest.mark.app_performance
# @allure.feature("Performance Testing")
# @allure.story("Application Performance - User Actions")
# class TestPagePerformance:
#     """Test individual user action performance in the browser"""
#
#     @pytest.mark.parametrize("table", PERFORMANCE_TABLES)
#     @allure.title("Navigate to Main Menu - User Experience Time")
#     def test_navigate_to_menu_performance(
#         self,
#         browser_factory,
#         endpoint_setup,
#         table,
#         performance_collector,
#         performance_reporter
#     ):
#         """
#         Measure: How long does it take for a user to see the menu?
#
#         Includes:
#         - Page load
#         - API calls to fetch menu items
#         - Images loading
#         - JavaScript execution
#         - Page rendering
#
#         This is what the USER experiences.
#         """
#
#         [chrome] = browser_factory("chrome")
#         menu_page = MenuPage(chrome)
#
#         metrics = performance_collector.get_or_create("User Action: Navigate to Menu")
#         threshold = get_sla_threshold('navigate_to_menu')
#
#         # Run 10 times (fewer because browser operations are slow)
#         iterations = 10
#
#         with allure.step(f"Run {iterations} menu navigation operations"):
#             for iteration in range(iterations):
#
#                 metadata = {
#                     'table': table,
#                     'iteration': iteration,
#                     'action': 'navigate_to_menu',
#                     'includes': 'page_load + API + rendering'
#                 }
#
#                 # Measure full page load from user perspective
#                 with PerformanceTimer(metrics, metadata):
#                     menu_page.navigate_to_main_menu()
#
#                 # Small delay between iterations
#                 time.sleep(1)
#
#         stats = metrics.get_statistics()
#
#         with allure.step("Performance Summary"):
#             summary = metrics.format_summary()
#             performance_reporter.attach_summary_table(summary)
#
#             slowest = metrics.get_slowest_requests(5)
#             performance_reporter.attach_slowest_requests(slowest)
#
#             # Add context about what's included
#             allure.attach(
#                 f"What this measures:\n"
#                 f"✓ HTML page download\n"
#                 f"✓ API call to get menu items\n"
#                 f"✓ Images loading\n"
#                 f"✓ JavaScript execution\n"
#                 f"✓ Browser rendering\n"
#                 f"✓ Page becomes interactive\n\n"
#                 f"This is the TOTAL time a user waits to see the menu.",
#                 name="What Is Measured",
#                 attachment_type=allure.attachment_type.TEXT
#             )
#
#         with allure.step(f"Validate User Experience (p95 < {threshold}s)"):
#             p95_seconds = stats['p95']
#
#             if p95_seconds >= threshold:
#                 allure.attach(
#                     f"⚠️ Menu load time ({p95_seconds:.1f}s) is slow.\n"
#                     f"Target: < {threshold}s\n"
#                     f"Users may feel the app is sluggish.",
#                     name="Performance Warning",
#                     attachment_type=allure.attachment_type.TEXT
#                 )
#             else:
#                 allure.attach(
#                     f"✅ Menu loads fast ({p95_seconds:.1f}s)\n"
#                     f"Users will feel responsive experience.",
#                     name="Performance Good",
#                     attachment_type=allure.attachment_type.TEXT
#                 )
#
#     @pytest.mark.parametrize("table", PERFORMANCE_TABLES)
#     @allure.title("Select and Add Item - User Experience Time")
#     def test_add_item_to_cart_performance(
#         self,
#         browser_factory,
#         endpoint_setup,
#         table,
#         performance_collector,
#         performance_reporter
#     ):
#         """
#         Measure: How long does it take for a user to add an item to cart?
#
#         User flow:
#         1. Click on item (e.g., "Burger")
#         2. Modal opens with options
#         3. Click "Add to Cart"
#         4. Cart badge updates
#
#         This is the complete user interaction time.
#         """
#
#         [chrome] = browser_factory("chrome")
#         menu_page = MenuPage(chrome)
#
#         metrics = performance_collector.get_or_create("User Action: Add Item to Cart")
#         threshold = get_sla_threshold('add_item')
#
#         iterations = 10
#
#         # Navigate to menu once
#         menu_page.navigate_to_main_menu()
#
#         with allure.step(f"Run {iterations} add-to-cart operations"):
#             for iteration in range(iterations):
#
#                 metadata = {
#                     'table': table,
#                     'iteration': iteration,
#                     'action': 'add_item_to_cart',
#                     'includes': 'click + modal + API + cart_update'
#                 }
#
#                 # Measure the complete add-to-cart experience
#                 with PerformanceTimer(metrics, metadata):
#                     menu_page.select_random_menu_items(num_items=1, quantity=1)
#
#                 # Reset for next iteration
#                 close_table()
#                 menu_page.navigate_to_main_menu()
#
#         stats = metrics.get_statistics()
#
#         with allure.step("Performance Summary"):
#             summary = metrics.format_summary()
#             performance_reporter.attach_summary_table(summary)
#
#             slowest = metrics.get_slowest_requests(5)
#             performance_reporter.attach_slowest_requests(slowest)
#
#             allure.attach(
#                 f"What this measures:\n"
#                 f"✓ User clicks item\n"
#                 f"✓ Modal/popup opens\n"
#                 f"✓ User clicks 'Add to Cart'\n"
#                 f"✓ API call to add item\n"
#                 f"✓ Cart badge updates\n"
#                 f"✓ User sees confirmation\n\n"
#                 f"This is how long the user waits from click to cart update.",
#                 name="What Is Measured",
#                 attachment_type=allure.attachment_type.TEXT
#             )
#
#         with allure.step(f"Validate User Experience"):
#             p95_seconds = stats['p95']
#
#             # For add-to-cart, anything over 3 seconds feels slow
#             if p95_seconds > 3.0:
#                 allure.attach(
#                     f"⚠️ Add to cart is SLOW ({p95_seconds:.1f}s)\n"
#                     f"Users expect instant feedback (< 2s)\n"
#                     f"Current experience feels laggy.",
#                     name="Performance Warning",
#                     attachment_type=allure.attachment_type.TEXT
#                 )
#
#     @pytest.mark.parametrize("table", PERFORMANCE_TABLES)
#     @allure.title("View Cart - User Experience Time")
#     def test_view_cart_performance(
#         self,
#         browser_factory,
#         endpoint_setup,
#         table,
#         performance_collector,
#         performance_reporter
#     ):
#         """
#         Measure: How long to navigate from menu to cart page?
#
#         User clicks cart icon → Cart page loads
#         """
#
#         [chrome] = browser_factory("chrome")
#         menu_page = MenuPage(chrome)
#
#         metrics = performance_collector.get_or_create("User Action: View Cart")
#         threshold = get_sla_threshold('navigate_to_cart')
#
#         iterations = 10
#
#         # Setup: Add item first
#         menu_page.navigate_to_main_menu()
#         menu_page.select_random_menu_items(num_items=1, quantity=1)
#
#         with allure.step(f"Run {iterations} cart navigation operations"):
#             for iteration in range(iterations):
#
#                 metadata = {
#                     'table': table,
#                     'iteration': iteration,
#                     'action': 'navigate_to_cart'
#                 }
#
#                 # Measure cart page load time
#                 with PerformanceTimer(metrics, metadata):
#                     menu_page.go_to_basket()
#
#                 # Go back to menu
#                 menu_page.navigate_to_main_menu()
#                 time.sleep(0.5)
#
#         stats = metrics.get_statistics()
#
#         with allure.step("Performance Summary"):
#             summary = metrics.format_summary()
#             performance_reporter.attach_summary_table(summary)
#
#     @pytest.mark.parametrize("table", PERFORMANCE_TABLES)
#     @allure.title("Complete Checkout - User Experience Time")
#     def test_checkout_page_performance(
#         self,
#         browser_factory,
#         endpoint_setup,
#         table,
#         performance_collector,
#         performance_reporter
#     ):
#         """
#         Measure: How long from cart to checkout page?
#
#         User clicks "Checkout" → Checkout page loads
#         """
#
#         [chrome] = browser_factory("chrome")
#         menu_page = MenuPage(chrome)
#         cart_page = CartPage(chrome)
#         checkout_page = CheckoutPage(chrome)
#
#         metrics = performance_collector.get_or_create("User Action: Navigate to Checkout")
#
#         iterations = 10
#
#         with allure.step(f"Run {iterations} checkout navigation operations"):
#             for iteration in range(iterations):
#
#                 # Setup: Add item and place order
#                 menu_page.navigate_to_main_menu()
#                 menu_page.select_random_menu_items(num_items=1, quantity=1)
#                 menu_page.go_to_basket()
#                 cart_page.place_order()
#
#                 metadata = {
#                     'table': table,
#                     'iteration': iteration,
#                     'action': 'navigate_to_checkout'
#                 }
#
#                 # Measure checkout page load
#                 menu_page.go_to_basket()
#                 with PerformanceTimer(metrics, metadata):
#                     cart_page.navigate_to_checkout_page()
#
#                 # Reset
#                 close_table()
#
#         stats = metrics.get_statistics()
#
#         with allure.step("Performance Summary"):
#             summary = metrics.format_summary()
#             performance_reporter.attach_summary_table(summary)
#
#     @pytest.mark.parametrize("table", PERFORMANCE_TABLES)
#     @allure.title("Process Payment - User Experience Time")
#     def test_payment_processing_performance(
#         self,
#         browser_factory,
#         endpoint_setup,
#         table,
#         performance_collector,
#         performance_reporter
#     ):
#         """
#         Measure: How long does payment take?
#
#         User clicks "Pay Now" → Payment processes → Confirmation page
#
#         This is critical - users are waiting for their payment to complete.
#         """
#
#         [chrome] = browser_factory("chrome")
#         menu_page = MenuPage(chrome)
#         cart_page = CartPage(chrome)
#         checkout_page = CheckoutPage(chrome)
#         payment_page = PaymentPage(chrome)
#
#         metrics = performance_collector.get_or_create("User Action: Process Payment")
#         threshold = get_sla_threshold('payment_processing')
#
#         iterations = 5  # Fewer iterations because full checkout is slow
#
#         with allure.step(f"Run {iterations} payment operations"):
#             for iteration in range(iterations):
#
#                 # Complete flow up to payment
#                 menu_page.navigate_to_main_menu()
#                 menu_page.select_random_menu_items(num_items=1, quantity=1)
#                 menu_page.go_to_basket()
#                 cart_page.place_order()
#                 menu_page.go_to_basket()
#                 cart_page.navigate_to_checkout_page()
#                 checkout_page.manage_tips(0)
#                 checkout_page.apply_charity()
#                 checkout_page.go_to_payment_page()
#
#                 metadata = {
#                     'table': table,
#                     'iteration': iteration,
#                     'action': 'process_payment',
#                     'critical': True  # Flag critical user action
#                 }
#
#                 # Measure payment processing time
#                 with PerformanceTimer(metrics, metadata):
#                     payment_page.make_the_payment()
#
#                 # Reset
#                 close_table()
#
#         stats = metrics.get_statistics()
#
#         with allure.step("Payment Performance Summary"):
#             summary = metrics.format_summary()
#             performance_reporter.attach_summary_table(summary)
#
#             slowest = metrics.get_slowest_requests(5)
#             performance_reporter.attach_slowest_requests(slowest)
#
#             allure.attach(
#                 f"⚠️ CRITICAL USER EXPERIENCE\n\n"
#                 f"What this measures:\n"
#                 f"✓ Payment API call\n"
#                 f"✓ Payment gateway processing\n"
#                 f"✓ Database updates\n"
#                 f"✓ Navigation to confirmation\n\n"
#                 f"Users are WAITING for payment to complete.\n"
#                 f"Long wait times cause anxiety and cart abandonment.",
#                 name="Why This Matters",
#                 attachment_type=allure.attachment_type.TEXT
#             )
#
#         with allure.step("Validate Payment Speed"):
#             p95_seconds = stats['p95']
#
#             if p95_seconds > 5.0:
#                 allure.attach(
#                     f"❌ CRITICAL: Payment takes {p95_seconds:.1f}s\n"
#                     f"This is TOO SLOW!\n"
#                     f"Users will abandon carts.\n"
#                     f"Target: < 3 seconds",
#                     name="CRITICAL ISSUE",
#                     attachment_type=allure.attachment_type.TEXT
#                 )
#             elif p95_seconds > 3.0:
#                 allure.attach(
#                     f"⚠️ Payment takes {p95_seconds:.1f}s\n"
#                     f"This is acceptable but could be faster.\n"
#                     f"Target: < 3 seconds",
#                     name="Performance Warning",
#                     attachment_type=allure.attachment_type.TEXT
#                 )
#             else:
#                 allure.attach(
#                     f"✅ Payment is fast ({p95_seconds:.1f}s)\n"
#                     f"Good user experience.",
#                     name="Performance Good",
#                     attachment_type=allure.attachment_type.TEXT
#                 )