
import re
import allure

class ConsoleMonitor:
    """Monitor browser console for errors and PII exposure"""


    PII_PATTERNS = {
        'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        'cvv': r'\b\d{3,4}\b(?=.*cvv|cvc|security)',
    }

    def __init__(self, driver):
        """
        Initialize console monitor.

        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.errors = []
        self.pii_violations = []

    def capture_console_logs(self):
        """
        Capture all browser console logs.

        Returns:
            list: All console log entries
        """
        try:
            logs = self.driver.get_log('browser')
            return logs
        except Exception as e:
            print(f"Warning: Could not capture console logs: {str(e)}")
            return []

    def check_for_errors(self):
        """
        Check console for JavaScript/network errors.

        Returns:
            list: Error messages found
        """
        logs = self.capture_console_logs()
        errors = []

        for log in logs:
            level = log.get('level', '').upper()
            message = log.get('message', '')

            # Check for severe errors
            if level in ['SEVERE', 'ERROR']:
                errors.append({
                    'level': level,
                    'message': message,
                    'timestamp': log.get('timestamp')
                })

        self.errors.extend(errors)
        return errors

    def check_for_pii(self):
        """
        Check console logs for exposed PII.

        Returns:
            list: PII violations found
        """
        logs = self.capture_console_logs()
        violations = []

        for log in logs:
            message = log.get('message', '')

            # Check against each PII pattern
            for pii_type, pattern in self.PII_PATTERNS.items():
                matches = re.findall(pattern, message, re.IGNORECASE)
                if matches:
                    violations.append({
                        'type': pii_type,
                        'message': self._redact_sensitive(message),
                        'matches': len(matches),
                        'timestamp': log.get('timestamp')
                    })

        self.pii_violations.extend(violations)
        return violations

    def check_all(self):
        """
        Check for both errors and PII violations.

        Returns:
            dict: Results with errors and pii_violations
        """
        errors = self.check_for_errors()
        pii = self.check_for_pii()

        return {
            'errors': errors,
            'pii_violations': pii,
            'has_issues': len(errors) > 0 or len(pii) > 0
        }

    def report_to_allure(self):
        """Attach console violations to Allure report"""

        # Report errors
        if self.errors:
            error_report = "CONSOLE ERRORS FOUND:\n\n"
            for i, error in enumerate(self.errors, 1):
                error_report += f"{i}. [{error['level']}] {error['message']}\n\n"

            allure.attach(
                error_report,
                name="❌ Console Errors",
                attachment_type=allure.attachment_type.TEXT
            )
        else:
            allure.attach(
                "✅ No console errors detected",
                name="Console Errors Check",
                attachment_type=allure.attachment_type.TEXT
            )

        # Report PII violations
        if self.pii_violations:
            pii_report = "⚠️ PII EXPOSURE DETECTED:\n\n"
            for i, violation in enumerate(self.pii_violations, 1):
                pii_report += f"{i}. Type: {violation['type'].upper()}\n"
                pii_report += f"   Message: {violation['message']}\n"
                pii_report += f"   Matches: {violation['matches']}\n\n"

            allure.attach(
                pii_report,
                name="⚠️ PII Violations",
                attachment_type=allure.attachment_type.TEXT
            )
        else:
            allure.attach(
                "✅ No PII exposure detected",
                name="PII Check",
                attachment_type=allure.attachment_type.TEXT
            )

    def assert_no_violations(self):

        issues = []

        if self.errors:
            issues.append(f"Found {len(self.errors)} console errors")

        if self.pii_violations:
            issues.append(f"Found {len(self.pii_violations)} PII violations")

        if issues:
            self.report_to_allure()
            raise AssertionError(f"Console violations detected: {', '.join(issues)}")

    def _redact_sensitive(self, message):
        """Redact sensitive information from message for safe logging"""
        redacted = message

        # Redact credit cards
        redacted = re.sub(self.PII_PATTERNS['credit_card'], '****-****-****-XXXX', redacted)

        # Redact SSN
        redacted = re.sub(self.PII_PATTERNS['ssn'], '***-**-XXXX', redacted)

        # Redact emails (partially)
        redacted = re.sub(
            r'\b([A-Za-z0-9._%+-]{1,3})[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b',
            r'\1***@\2',
            redacted
        )

        # Redact phone numbers
        redacted = re.sub(self.PII_PATTERNS['phone'], '(***) ***-XXXX', redacted)

        return redacted

    def get_summary(self):

        return {
            'total_errors': len(self.errors),
            'total_pii_violations': len(self.pii_violations),
            'has_violations': len(self.errors) > 0 or len(self.pii_violations) > 0,
            'errors': self.errors,
            'pii_violations': self.pii_violations
        }


def check_console(driver, report_to_allure=True, assert_clean=False):

    monitor = ConsoleMonitor(driver)
    results = monitor.check_all()

    if report_to_allure:
        monitor.report_to_allure()

    if assert_clean:
        monitor.assert_no_violations()

    return results