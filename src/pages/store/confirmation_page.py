import json
import allure
from src.pages.base_page import BasePage
from src.locators.store_locators import ConfirmationPageLocators
from src.utils.logger import Logger
from src.utils.email_service import EmailService
import pytest_check as check


class ConfirmationPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger("ConfirmationPage")  # Changed from PaymentPage
        self.email_service = EmailService()
        self.test_email = None



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

    def calculate_expected_total(self):
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
        try:
            element = self.find_element(ConfirmationPageLocators.CONFIRMATION_MESSAGE)
            if element.is_displayed():
                text = self.get_text(ConfirmationPageLocators.CONFIRMATION_MESSAGE)
                if "Successful" in text:
                    return True
        except Exception:
            pass

        self.attach_screenshot("Confirmation Page Issue")
        return False

    def send_and_verify_email_receipt(self, expected_check_number, expected_total, test_name="Checkout Test",
                                      table_number=None):  # ✅ Added table_number parameter

        self.logger.info("=" * 60)
        self.logger.info("EMAIL RECEIPT VERIFICATION")
        self.logger.info("=" * 60)

        with allure.step("Generate test email address"):
            self.test_email, inbox_id = self.email_service.get_test_email(
                test_name=test_name,
                table_number=table_number  # ✅ Pass table_number
            )
            allure.attach(
                self.test_email,
                name="📧 Test Email Address",
                attachment_type=allure.attachment_type.TEXT
            )
            self.logger.info(f"Using email: {self.test_email}")

        with allure.step("Enter email and send receipt"):
            self.click(ConfirmationPageLocators.EMAIL_BUTTON)

            email_field = self.find_element(ConfirmationPageLocators.EMAIL_FIELD)
            email_field.clear()
            email_field.send_keys(self.test_email)

            self.click(ConfirmationPageLocators.EMAIL_SEND_BUTTON)
            self.attach_screenshot("Email Receipt Request")

            try:
                confirmation = self.wait_for_element_visible(
                    ConfirmationPageLocators.EMAIL_CONFIRMATION,
                    timeout=10
                )
                confirmation_text = confirmation.text
                expected_msg = f"Receipt sent to {self.test_email}"

                check.equal(confirmation_text, expected_msg, "Email confirmation message incorrect")
                self.logger.info(f"✓ Email confirmation: {confirmation_text}")

            except Exception as e:
                self.logger.error(f"Failed to get email confirmation: {str(e)}")

        with allure.step("Wait for email to arrive"):
            email_data = self.email_service.wait_for_email(
                subject_contains=None,
                timeout=90
            )

            if not email_data:
                self.logger.error("Email did not arrive within timeout")
                return {
                    'passed': False,
                    'error': 'Email not received within 90 seconds'
                }

            self.logger.info(f"✓ Email received! Subject: {email_data.get('subject', 'N/A')}")

        with allure.step("Verify email receipt contents"):
            verification_result = self.email_service.verify_receipt_complete(
                email_data=email_data,
                expected_check_number=expected_check_number,
                expected_total=expected_total
            )

            # Create beautified summary for Allure
            summary = {
                "✅ PASSED" if verification_result['passed'] else "❌ FAILED": verification_result['passed'],
                "Check Number": {
                    "Expected": verification_result['check_number']['expected'],
                    "Found": verification_result['check_number']['found'],
                    "Match": "✓" if verification_result['check_number']['passed'] else "✗"
                },
                "Total Amount": {
                    "Expected": f"${verification_result['expected_total']:.2f}",
                    "Email Total": f"${verification_result['calculations']['email_total']:.2f}",
                    "Match": "✓" if verification_result['total_matches'] else "✗"
                },
                "Receipt Breakdown": {
                    "Subtotal": f"${verification_result['calculations']['breakdown']['subtotal']:.2f}",
                    "Tax": f"${verification_result['calculations']['breakdown']['tax']:.2f}",
                    "Service Charge": f"${verification_result['calculations']['breakdown']['service_charge']:.2f}",
                    "Tip": f"${verification_result['calculations']['breakdown']['tip']:.2f}",
                    "Donation": f"${verification_result['calculations']['breakdown']['donation']:.2f}"
                },
                "Calculation Check": {
                    "Calculated Total": f"${verification_result['calculations']['calculated_total']:.2f}",
                    "Email Total": f"${verification_result['calculations']['email_total']:.2f}",
                    "Difference": f"${verification_result['calculations']['difference']:.2f}",
                    "Valid": "✓" if verification_result['calculations']['passed'] else "✗"
                }
            }

            allure.attach(
                json.dumps(summary, indent=2, ensure_ascii=False),
                name="📊 Email Verification Summary",
                attachment_type=allure.attachment_type.JSON
            )

        self.logger.info("=" * 60)
        if verification_result['passed']:
            self.logger.info("✓ EMAIL VERIFICATION PASSED")
        else:
            self.logger.error("✗ EMAIL VERIFICATION FAILED")
        self.logger.info("=" * 60)

        return verification_result




