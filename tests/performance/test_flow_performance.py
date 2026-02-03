"""
Flow Performance Tests - Measure complete user journey performance
"""
import pytest
import allure
import time
from src.pages.store.menu_page import MenuPage
from src.pages.store.cart_page import CartPage
from src.pages.store.checkout_page import CheckoutPage
from src.pages.store.payment_page import PaymentPage
from src.pages.store.confirmation_page import ConfirmationPage
from src.utils.performance_metrics import PerformanceTimer
from tests.performance.conftest import (
    PERFORMANCE_TABLE,
    get_sla_threshold
)


@pytest.mark.performance
@pytest.mark.flow_performance
@allure.feature("Performance Testing")
@allure.story("Complete Flow Performance")
class TestFlowPerformance:
    """Test complete user flow performance"""

    @allure.title("Complete Checkout Flow - Performance")
    def test_complete_checkout_flow_performance(
            self,
            browser_factory,
            endpoint_setup,
            performance_collector,
            performance_reporter
    ):
        """Measure complete checkout flow - 10 iterations on Table 51"""

        # ✅ CREATE BROWSER ONCE (outside loop)
        [chrome] = browser_factory("chrome")

        flow_metrics = performance_collector.get_or_create("Complete Checkout Flow")
        nav_metrics = performance_collector.get_or_create("Step: Navigate to Menu")
        select_metrics = performance_collector.get_or_create("Step: Select Items")
        cart_metrics = performance_collector.get_or_create("Step: View Cart")
        checkout_metrics = performance_collector.get_or_create("Step: Checkout")
        payment_metrics = performance_collector.get_or_create("Step: Payment")
        confirm_metrics = performance_collector.get_or_create("Step: Confirmation")

        threshold = get_sla_threshold('full_checkout_flow')
        iterations = 10

        with allure.step(f"Run {iterations} complete checkout flows on Table {PERFORMANCE_TABLE}"):
            for iteration in range(iterations):

                # Recreate table for iterations 2-10
                if iteration > 0:
                    with allure.step(f"Iteration {iteration + 1}: Recreate Table {PERFORMANCE_TABLE}"):
                        endpoint_setup.setup_table()
                        time.sleep(2)

                        # ✅ NAVIGATE BROWSER BACK TO TABLE URL
                        from src.utils.navigation import Navigation
                        Navigation.navigate(chrome, endpoint_setup.session_id, PERFORMANCE_TABLE)

                # ✅ CREATE PAGE OBJECTS (FRESH for each iteration)
                menu_page = MenuPage(chrome)
                cart_page = CartPage(chrome)
                checkout_page = CheckoutPage(chrome)
                payment_page = PaymentPage(chrome)
                confirmation_page = ConfirmationPage(chrome)

                overall_start = time.time()
                step_times = {}

                with allure.step("1. Navigate to Menu"):
                    step_start = time.time()
                    menu_page.navigate_to_main_menu()
                    step_duration = time.time() - step_start
                    step_times['navigate'] = step_duration
                    nav_metrics.add_timing(step_duration, {'iteration': iteration})

                with allure.step("2. Select Items"):
                    step_start = time.time()
                    menu_page.select_random_menu_items(num_items=2, quantity=1)
                    step_duration = time.time() - step_start
                    step_times['select'] = step_duration
                    select_metrics.add_timing(step_duration, {'iteration': iteration})

                with allure.step("3. View Cart"):
                    step_start = time.time()
                    menu_page.go_to_basket()
                    cart_page.place_order()
                    step_duration = time.time() - step_start
                    step_times['cart'] = step_duration
                    cart_metrics.add_timing(step_duration, {'iteration': iteration})

                with allure.step("4. Navigate to Checkout"):
                    step_start = time.time()
                    menu_page.go_to_basket()
                    cart_page.navigate_to_checkout_page()
                    checkout_page.manage_tips(0)
                    checkout_page.apply_charity()
                    step_duration = time.time() - step_start
                    step_times['checkout'] = step_duration
                    checkout_metrics.add_timing(step_duration, {'iteration': iteration})

                with allure.step("5. Process Payment"):
                    step_start = time.time()
                    checkout_page.go_to_payment_page()
                    payment_page.make_the_payment()
                    step_duration = time.time() - step_start
                    step_times['payment'] = step_duration
                    payment_metrics.add_timing(step_duration, {'iteration': iteration})

                with allure.step("6. View Confirmation"):
                    step_start = time.time()
                    status = confirmation_page.get_order_status()
                    step_duration = time.time() - step_start
                    step_times['confirm'] = step_duration
                    confirm_metrics.add_timing(step_duration, {'iteration': iteration})

                total_duration = time.time() - overall_start

                flow_metrics.add_timing(total_duration, {
                    'iteration': iteration + 1,
                    'breakdown': step_times
                })

                with allure.step(f"Iteration {iteration + 1} completed in {total_duration:.2f}s"):
                    breakdown_text = f"""
                    Iteration {iteration + 1} Breakdown:
                    ├── Navigate:  {step_times['navigate']:.2f}s
                    ├── Select:    {step_times['select']:.2f}s
                    ├── Cart:      {step_times['cart']:.2f}s
                    ├── Checkout:  {step_times['checkout']:.2f}s
                    ├── Payment:   {step_times['payment']:.2f}s
                    └── Confirm:   {step_times['confirm']:.2f}s
                    ────────────────────────────────
                    Total:         {total_duration:.2f}s
                    """
                    allure.attach(
                        breakdown_text,
                        name=f"Iteration {iteration + 1} Timing",
                        attachment_type=allure.attachment_type.TEXT
                    )

                # ✅ WAIT before next iteration (no manual close)
                time.sleep(1)

        with allure.step("Performance Analysis"):
            flow_stats = flow_metrics.get_statistics()
            flow_summary = flow_metrics.format_summary()
            performance_reporter.attach_summary_table(
                flow_summary,
                "Complete Flow Statistics"
            )

            comparison = performance_collector.format_comparison_table()
            performance_reporter.attach_summary_table(
                comparison,
                "Step Comparison"
            )

            performance_reporter.attach_collector_report(performance_collector)

        with allure.step(f"Validate Flow SLA (< {threshold}s)"):
            assert flow_stats['p95'] < threshold, \
                f"Flow p95 ({flow_stats['p95']:.2f}s) exceeds threshold ({threshold}s)"