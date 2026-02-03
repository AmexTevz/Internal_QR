import time
import re
import requests
from datetime import datetime
from src.utils.logger import Logger


class EmailService:
    def __init__(self):
        self.logger = Logger("EmailService")

        # Mailinator configuration
        self.api_token = "3d7babc101164861b1ab7c203020a54c"  # ✅ FIXED TOKEN
        self.private_domain = "team645380.testinator.email"
        self.base_url = "https://api.mailinator.com/api/v2"  # ✅ FIXED URL

        self.current_email = None
        self.current_inbox = None

    def get_test_email(self, test_name="test", table_number=None, use_private_domain=True):
        """
        Generate email address with table number and timestamp only

        Args:
            test_name: NOT USED (kept for compatibility)
            table_number: Table number (will be primary identifier)
            use_private_domain: Use private domain vs public

        Returns:
            tuple: (email_address, domain)
        """
        # ✅ ADD DEBUG LOGGING
        self.logger.info(f"🔍 get_test_email called with table_number={table_number}, type={type(table_number)}")

        # Compact timestamp: HHMMSS
        now = datetime.now()
        timestamp = now.strftime("%H%M%S")

        # ✅ Use "is not None" to handle table 0
        if table_number is not None:
            inbox_name = f"{table_number}-{timestamp}"
            self.logger.info(f"✅ Using table number: {table_number}")
        else:
            inbox_name = f"test-{timestamp}"
            self.logger.info(f"⚠️ No table number provided, using fallback")

        domain = self.private_domain if use_private_domain else "mailinator.com"
        email_address = f"{inbox_name}@{domain}"

        self.current_email = email_address
        self.current_inbox = inbox_name

        self.logger.info(f"📧 Generated email: {email_address}")

        return email_address, domain

    def wait_for_email(self, email=None, domain=None, subject_contains=None, timeout=90):
        """Wait for email using polling"""
        if email:
            inbox_name = email.split('@')[0]
        else:
            inbox_name = self.current_inbox

        if not inbox_name:
            self.logger.error("No inbox provided")
            return None

        self.logger.info(f"Waiting for email in {inbox_name}...")
        self.logger.info(f"Timeout: {timeout}s")

        start_time = time.time()
        poll_interval = 3  # Poll every 3 seconds

        while (time.time() - start_time) < timeout:
            try:
                url = f"{self.base_url}/domains/private/inboxes/{inbox_name}"
                params = {
                    "token": self.api_token,
                    "limit": 1
                }

                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    messages = data.get('msgs', [])

                    if messages:
                        # Found a message, fetch full content
                        msg_id = messages[0]['id']

                        msg_url = f"{self.base_url}/domains/private/messages/{msg_id}"
                        msg_response = requests.get(msg_url, params={"token": self.api_token})

                        if msg_response.status_code == 200:
                            full_message = msg_response.json()
                            subject = full_message.get('subject', '')

                            self.logger.info(f"✓ Email received!")
                            self.logger.info(f"  Subject: {subject}")

                            email_data = {
                                'id': full_message.get('id', ''),
                                'subject': subject,
                                'from': full_message.get('from', ''),
                                'to': full_message.get('to', ''),
                                'body': full_message.get('parts', [{}])[0].get('body', ''),
                                'text_body': self._extract_text_part(full_message),
                                'html': self._extract_html_part(full_message),
                                'received_at': full_message.get('time', '')
                            }

                            return email_data

            except Exception as e:
                self.logger.error(f"Error checking inbox: {str(e)}")

            # Wait before next poll
            elapsed = time.time() - start_time
            remaining = timeout - elapsed
            self.logger.debug(f"Checking again in {poll_interval}s... ({remaining:.0f}s remaining)")
            time.sleep(poll_interval)

        self.logger.warning(f"No email received within {timeout}s")
        return None

    def _extract_text_part(self, message):
        """Extract plain text part from message"""
        parts = message.get('parts', [])
        for part in parts:
            if part.get('headers', {}).get('content-type', '').startswith('text/plain'):
                return part.get('body', '')
        # Fallback to first part
        return parts[0].get('body', '') if parts else ''

    def _extract_html_part(self, message):
        """Extract HTML part from message"""
        parts = message.get('parts', [])
        for part in parts:
            if part.get('headers', {}).get('content-type', '').startswith('text/html'):
                return part.get('body', '')
        return ''

    def strip_html(self, html_content):
        """Strip HTML tags and return plain text"""
        if not html_content:
            return ""
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = ' '.join(text.split())
        return text

    def get_email_text(self, email_data):
        """Extract plain text content"""
        text = email_data.get('text_body') or email_data.get('body', '')
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
        full_content = text + " " + html

        self.logger.debug("=" * 60)
        self.logger.debug("CHECKING FOR CHECK NUMBER:")
        self.logger.debug(f"Plain text sample: {text[:200]}")
        self.logger.debug("=" * 60)

        patterns = [
            r'Tab/Check/Order\s*#\s*(\d+)',
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

        patterns = {
            'subtotal': r'Subtotal:\s*\$\s*([\d,]+\.?\d*)',
            'tax': r'Tax:\s*\$\s*([\d,]+\.?\d*)',
            'service_charge': r'srvc chrg[^:]*:\s*\$\s*([\d,]+\.?\d*)',
            'tip': r'Tip:\s*\$\s*([\d,]+\.?\d*)',
            'donation': r'Donation:\s*\$\s*([\d,]+\.?\d*)',
            'total': r'\bTotal:\s*\$\s*([\d,]+\.?\d*)',
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