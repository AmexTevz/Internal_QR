import time
import re
from datetime import datetime
from mailslurp_client import Configuration, ApiClient, InboxControllerApi, WaitForControllerApi
from mailslurp_client.exceptions import ApiException
from src.utils.logger import Logger


class EmailService:
    def __init__(self):
        self.logger = Logger("EmailService")

        # MailSlurp configuration
        self.api_key = "sk_hBJ9YbQmlCj0x5Fp_IBR0xwaUTvZwuXYLmYYejAYF9tEQ0W7YjlKV4XPhHrLzMa7laGvj8dbw3JQ0dju8"

        configuration = Configuration()
        configuration.api_key['x-api-key'] = self.api_key

        self.api_client = ApiClient(configuration)
        self.inbox_controller = InboxControllerApi(self.api_client)
        self.wait_controller = WaitForControllerApi(self.api_client)

        self.current_inbox = None
        self.current_email = None

    def get_test_email(self, test_name="test"):
        """
        Create a new MailSlurp inbox with test name and timestamp

        Args:
            test_name: Name of the test (e.g., "Simple Checkout Flow")

        Returns:
            tuple: (email_address, inbox_id)
        """
        try:
            # Clean test name: lowercase, replace spaces with hyphens
            clean_name = test_name.lower().replace(' ', '-').replace('_', '-')
            # Remove special characters
            clean_name = re.sub(r'[^a-z0-9-]', '', clean_name)

            # Format timestamp: MONTH_DAY_HOUR_MINUTE (01_20_09_40)
            now = datetime.now()
            timestamp = now.strftime("%m_%d_%H_%M")

            # Create email: test-name-01_20_09_40@mailslurp.biz
            email_prefix = f"{clean_name}-{timestamp}"

            # Create inbox
            inbox = self.inbox_controller.create_inbox(
                name=email_prefix  # Label the inbox
            )

            self.current_inbox = inbox.id
            self.current_email = inbox.email_address

            self.logger.info(f"Created inbox: {self.current_email}")
            self.logger.info(f"Test name: {test_name}")
            self.logger.info(f"Timestamp: {timestamp}")
            self.logger.info(f"Inbox ID: {self.current_inbox}")

            return self.current_email, self.current_inbox

        except ApiException as e:
            self.logger.error(f"Failed to create inbox: {str(e)}")
            raise

    def wait_for_email(self, email=None, inbox_id=None, subject_contains=None, timeout=60):
        """
        Wait for email to arrive in MailSlurp inbox
        """
        inbox_id = inbox_id or self.current_inbox

        if not inbox_id:
            self.logger.error("No inbox ID provided")
            return None

        self.logger.info(f"Waiting for email in inbox {inbox_id}...")
        timeout_ms = timeout * 1000

        try:
            email_obj = self.wait_controller.wait_for_latest_email(
                inbox_id=inbox_id,
                timeout=timeout_ms,
                unread_only=True
            )

            self.logger.info(f"✓ Email received!")
            self.logger.info(f"  Subject: {email_obj.subject}")
            self.logger.info(f"  From: {email_obj._from}")  # ✅ FIXED HERE

            email_data = {
                'id': email_obj.id,
                'subject': email_obj.subject or '',
                'from': email_obj._from or '',  # ✅ AND HERE
                'to': email_obj.to or [],
                'body': email_obj.body or '',
                'text_body': email_obj.body or '',
                'html': email_obj.body or '',
                'received_at': email_obj.created_at
            }

            if subject_contains:
                if subject_contains.lower() not in email_data['subject'].lower():
                    self.logger.warning(f"Subject doesn't match filter: {subject_contains}")
                    return None

            return email_data

        except ApiException as e:
            if "timeout" in str(e).lower():
                self.logger.warning(f"No email received within {timeout}s")
            else:
                self.logger.error(f"Error waiting for email: {str(e)}")
            return None

    def strip_html(self, html_content):
        """Strip HTML tags and return plain text"""
        if not html_content:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def get_email_text(self, email_data):
        """Extract plain text content"""
        text = email_data.get('text_body') or email_data.get('body', '')

        # If it's HTML, strip tags
        if '<html' in text.lower() or '<body' in text.lower():
            return self.strip_html(text)

        return text

    def get_email_html(self, email_data):
        """Extract HTML content"""
        return email_data.get('html') or email_data.get('body', '')

    def extract_check_number(self, email_data):
        """Extract check/order number from receipt email"""
        text = self.get_email_text(email_data) or ""
        html = self.get_email_html(email_data) or ""

        # Try plain text first
        full_content = text + " " + html

        self.logger.debug("=" * 60)
        self.logger.debug("CHECKING FOR CHECK NUMBER:")
        self.logger.debug(f"Plain text sample: {text[:200]}")
        self.logger.debug("=" * 60)

        # Patterns to match check number
        patterns = [
            r'Tab/Check/Order\s*#\s*(\d+)',  # With spaces/tags
            r'Order\s*#\s*(\d+)',
            r'Check\s*#\s*(\d+)',
            r'Tab\s*#\s*(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, full_content, re.IGNORECASE)
            if match:
                check_number = int(match.group(1))
                self.logger.info(f"Extracted check number: {check_number}")
                return check_number

        self.logger.warning("Could not extract check number from email")
        return None

    def extract_financial_breakdown(self, email_data):
        """Extract all financial values from receipt"""
        text = self.get_email_text(email_data) or ""
        html = self.get_email_html(email_data) or ""
        full_content = text + " " + html

        self.logger.debug("=" * 60)
        self.logger.debug("FINANCIAL EXTRACTION:")
        self.logger.debug(f"Plain text sample: {text[:500]}")
        self.logger.debug("=" * 60)

        breakdown = {}

        # IMPORTANT: Extract in specific order to avoid conflicts
        # Use word boundaries to prevent "Subtotal" matching "total"
        patterns = {
            'subtotal': r'Subtotal:\s*\$\s*([\d,]+\.?\d*)',
            'tax': r'Tax:\s*\$\s*([\d,]+\.?\d*)',
            'service_charge': r'srvc chrg[^:]*:\s*\$\s*([\d,]+\.?\d*)',
            'tip': r'Tip:\s*\$\s*([\d,]+\.?\d*)',
            'donation': r'Donation:\s*\$\s*([\d,]+\.?\d*)',
            'total': r'\bTotal:\s*\$\s*([\d,]+\.?\d*)',  # \b = word boundary
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, full_content, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '').strip()
                breakdown[key] = float(value_str)
                self.logger.info(f"Extracted {key}: ${breakdown[key]:.2f}")
            else:
                breakdown[key] = 0.0
                self.logger.warning(f"Could not extract {key}, defaulting to $0.00")

        return breakdown

    def verify_check_number(self, email_data, expected_check_number):
        """Verify check number matches expected"""
        found_check_number = self.extract_check_number(email_data)

        result = {
            'passed': found_check_number == expected_check_number,
            'expected': expected_check_number,
            'found': found_check_number
        }

        if result['passed']:
            self.logger.info(f"✓ Check number verified: {expected_check_number}")
        else:
            self.logger.error(
                f"✗ Check number mismatch! Expected: {expected_check_number}, "
                f"Found: {found_check_number}"
            )

        return result

    def verify_calculations(self, email_data, tolerance=0.02):
        """Verify receipt calculations are correct"""
        breakdown = self.extract_financial_breakdown(email_data)

        calculated_total = (
                breakdown['subtotal'] +
                breakdown['tax'] +
                breakdown['service_charge'] +
                breakdown['tip'] +
                breakdown['donation']
        )

        email_total = breakdown['total']
        difference = abs(calculated_total - email_total)

        result = {
            'passed': difference <= tolerance,
            'breakdown': breakdown,
            'calculated_total': round(calculated_total, 2),
            'email_total': email_total,
            'difference': round(difference, 2)
        }

        if result['passed']:
            self.logger.info(
                f"✓ Calculations verified: "
                f"${breakdown['subtotal']:.2f} + ${breakdown['tax']:.2f} + "
                f"${breakdown['service_charge']:.2f} + ${breakdown['tip']:.2f} + "
                f"${breakdown['donation']:.2f} = ${email_total:.2f}"
            )
        else:
            self.logger.error(
                f"✗ Calculation mismatch! "
                f"Calculated: ${calculated_total:.2f}, "
                f"Email shows: ${email_total:.2f}, "
                f"Difference: ${difference:.2f}"
            )

        return result

    def verify_receipt_complete(self, email_data, expected_check_number, expected_total):
        """Complete receipt verification"""
        self.logger.info("=" * 60)
        self.logger.info("RECEIPT VERIFICATION")
        self.logger.info("=" * 60)

        check_verification = self.verify_check_number(email_data, expected_check_number)
        calc_verification = self.verify_calculations(email_data)

        email_total = calc_verification['email_total']
        total_matches = abs(email_total - expected_total) <= 0.02

        if total_matches:
            self.logger.info(f"✓ Total verified: ${expected_total:.2f}")
        else:
            self.logger.error(
                f"✗ Total mismatch! Expected: ${expected_total:.2f}, "
                f"Email: ${email_total:.2f}"
            )

        all_passed = (
                check_verification['passed'] and
                calc_verification['passed'] and
                total_matches
        )

        result = {
            'passed': all_passed,
            'check_number': check_verification,
            'calculations': calc_verification,
            'total_matches': total_matches,
            'expected_total': expected_total
        }

        self.logger.info("=" * 60)
        if all_passed:
            self.logger.info("✓ ALL VERIFICATIONS PASSED")
        else:
            self.logger.error("✗ VERIFICATION FAILED")
        self.logger.info("=" * 60)

        return result

    def delete_inbox(self, inbox_id=None):
        """Delete inbox after test (optional cleanup)"""
        inbox_id = inbox_id or self.current_inbox

        if inbox_id:
            try:
                self.inbox_controller.delete_inbox(inbox_id)
                self.logger.info(f"Deleted inbox: {inbox_id}")
            except ApiException as e:
                self.logger.warning(f"Failed to delete inbox: {str(e)}")