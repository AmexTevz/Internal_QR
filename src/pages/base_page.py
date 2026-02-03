
import sys
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import logging
import time
from selenium.webdriver.remote.webelement import WebElement
from typing import Union, List, Tuple
import allure
import functools

def wait_for_loader(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        self.wait_for_loader_to_disappear()
        return func(self, *args, **kwargs)
    return wrapper

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = ActionChains(self.driver)
        self.logger = logging.getLogger(__name__)
        self.store_id = None

        self.LOADER = (By.CSS_SELECTOR, ".loader")

    def wait_for_loader_to_disappear(self, timeout=30):

        try:
            # Check if loader is present first
            initial_elements = self.driver.find_elements(*self.LOADER)
            if not initial_elements:
                self.logger.debug("Loader not found initially - continuing")
                return True

            # Check if any of the elements are actually visible
            visible_elements = [el for el in initial_elements if el.is_displayed()]
            if not visible_elements:
                self.logger.debug("Loader present but not visible - continuing")
                return True

            self.logger.debug("Waiting for loader to disappear...")

            # Wait for loader to disappear
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(self.LOADER)
            )
            self.logger.debug("Loader disappeared successfully")
            return True

        except TimeoutException:
            self.logger.warning(f"Loader didn't disappear within {timeout}s, proceeding anyway")
            return False
        except Exception as e:
            # If loader was never present or other error, that's usually fine
            self.logger.debug(f"Loader wait exception: {str(e)}")
            return True



    def send_keys(self, locator, text, clear=True, name=None):
        logging.info(f"Attempting to send keys to element: {name if name else locator}")
        try:
            # Ensure page is fully loaded before attempting to interact
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            element = self.wait.until(EC.presence_of_element_located(locator))
            try:
                if clear:
                    element.clear()
                element.send_keys(text)
                logging.info(f"Successfully sent keys using regular method: {name if name else locator}")
                return element
            except Exception as e:
                logging.info(f"Regular send_keys failed: {str(e)}")

            try:
                if clear:
                    self.driver.execute_script("arguments[0].value = '';", element)
                self.driver.execute_script(f"arguments[0].value = arguments[1];", element, text)
                logging.info(f"Successfully sent keys using JavaScript: {name if name else locator}")
                return element
            except Exception as e:
                logging.info(f"JavaScript send_keys failed: {str(e)}")

            try:
                actions = ActionChains(self.driver)
                if clear:
                    actions.click(element).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(
                        Keys.BACK_SPACE)
                actions.send_keys(text).perform()
                logging.info(f"Successfully sent keys using ActionChains: {name if name else locator}")
                return element
            except Exception as e:
                logging.error(f"All send_keys attempts failed: {str(e)}")
                raise

        except Exception as e:
            logging.error(f"Failed to interact with element {name if name else locator}: {str(e)}")
            raise

    def get_text(self, locator, name=None, element=None, timeout=30):
        logging.info(f"Attempting to get text from element: {name if name else locator}")
        try:
            if element is None:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(locator)
                )


            try:
                text = element.text.strip()  # Added strip()
                if text:
                    logging.info(f"Successfully got text using .text: '{text}'")
                    return text
            except Exception as e:
                logging.debug(f"Regular .text failed: {str(e)}")

            # Try textContent
            try:
                text = element.get_attribute('textContent').strip()
                if text:
                    logging.info(f"Successfully got text using textContent: '{text}'")
                    return text
            except Exception as e:
                logging.debug(f"textContent failed: {str(e)}")

            # Try JavaScript innerText
            try:
                text = self.driver.execute_script("return arguments[0].innerText;", element)
                if text:
                    text = text.strip()
                    logging.info(f"Successfully got text using JavaScript: '{text}'")
                    return text
            except Exception as e:
                logging.debug(f"JavaScript innerText failed: {str(e)}")

            # If we get here, no method worked but element exists
            logging.warning(f"Element found but no text could be extracted from {name if name else locator}")
            return ""

        except Exception as e:
            logging.error(f"Failed to locate or get text from element {name if name else locator}: {str(e)}")
            raise
    def get_text_short(self, locator, name=None, element=None, timeout=2):
        logging.info(f"Attempting to get text from element: {name if name else locator}")
        try:
            if element is None:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(locator)
                )


            try:
                text = element.text
                if text:
                    logging.info(f"Successfully got text using .text: '{text}'")
                    return text
            except Exception as e:
                logging.debug(f"Regular .text failed: {str(e)}")

            # Try textContent
            try:
                text = element.get_attribute('textContent').strip()
                if text:
                    logging.info(f"Successfully got text using textContent: '{text}'")
                    return text
            except Exception as e:
                logging.debug(f"textContent failed: {str(e)}")

            # Try JavaScript innerText
            try:
                text = self.driver.execute_script("return arguments[0].innerText;", element)
                if text:
                    text = text.strip()
                    logging.info(f"Successfully got text using JavaScript: '{text}'")
                    return text
            except Exception as e:
                logging.debug(f"JavaScript innerText failed: {str(e)}")

            # If we get here, no method worked but element exists
            logging.warning(f"Element found but no text could be extracted from {name if name else locator}")
            return ""

        except Exception as e:
            logging.error(f"Failed to locate or get text from element {name if name else locator}: {str(e)}")
            raise

    def get_text_2(self, locator, name=None, max_attempts=50):
        """Ultra-patient text getter that keeps trying until it finds text"""
        logging.info(f"Patiently waiting for text from element: {name if name else locator}")


        attempt = 0

        while attempt < max_attempts:
            try:
                attempt += 1
                logging.info(f"Attempt {attempt}/{max_attempts}")

                # Wait for element with longer timeout each attempt
                timeout = min(10 + (attempt * 2), 60)  # Gradually increase timeout
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located(locator)
                )

                # Try all text extraction methods
                methods = [
                    lambda e: e.text.strip(),
                    lambda e: e.get_attribute('textContent').strip(),
                    lambda e: self.driver.execute_script("return arguments[0].innerText;", e).strip(),
                    lambda e: self.driver.execute_script("return arguments[0].textContent;", e).strip()
                ]

                for method in methods:
                    try:
                        text = method(element)
                        if text:
                            logging.info(f"Success on attempt {attempt}: '{text}'")
                            return text
                    except:
                        continue

                logging.info(f"No text found on attempt {attempt}, waiting 3 seconds...")
                time.sleep(1)  # Wait before next attempt

            except Exception as e:
                logging.debug(f"Attempt {attempt} failed: {str(e)}")
                time.sleep(1)  # Wait before retrying after exception

        logging.error(f"Failed to get text after {max_attempts} attempts")
        raise TimeoutException(f"Could not get text from {name if name else locator} after {max_attempts} attempts")

    def get_text_3(self, locator, name=None, element=None, timeout=30):
        logging.info(f"Attempting to get text from element: {name if name else locator}")

        try:
            if element is None:
                element = WebDriverWait(self.driver, timeout).until(
                    lambda d: d.find_element(*locator)
                )

            # Wait until text is actually populated
            WebDriverWait(self.driver, timeout).until(
                lambda d: element.text and element.text.strip()
            )

            text = element.text.strip()
            logging.info(f"Successfully got text: '{text}'")
            return text

        except Exception as e:
            logging.error(
                f"Failed to get non-empty text from element {name if name else locator}: {str(e)}"
            )
            raise

    def is_element_displayed(self, locator, timeout=2):
        try:
            elements = self.driver.find_elements(*locator)
            if elements and elements[0].is_displayed():
                return True

            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except:
            return False

    def wait_for_url_contains(self, partial_url, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.url_contains(partial_url)
            )
            logging.info(f"URL contains '{partial_url}'")
            return True
        except TimeoutException:
            logging.error(f"URL does not contain '{partial_url}' within {timeout} seconds")
            return False

    def get_elements(self, *locators):
        for locator in locators:
            elements = self.driver.find_elements(*locator)
            if elements:
                return elements
        return []

    def wait_for_elements(self, locator, timeout=20):
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_all_elements_located(locator))

    def click(self, target: Union[WebElement, Tuple[str, str]], name=None, timeout=30):
        try:
            # Ensure page is fully loaded before attempting to interact
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            if isinstance(target, tuple):
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable(target)
                )
                logging.info(f"Element found and is clickable: {name if name else target}")
            else:
                # If target is already a WebElement, use it directly
                element = target

            try:
                element.click()
                logging.info(f"Successfully clicked element using regular click: {name if name else target}")
                return element
            except Exception as e:
                logging.info(f"Regular click failed, trying alternative methods: {str(e)}")

            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                self.driver.execute_script("arguments[0].click();", element)
                logging.info(f"Successfully clicked element using JavaScript: {name if name else target}")
                return element
            except Exception as e:
                logging.info(f"JavaScript click failed, trying ActionChains: {str(e)}")

            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(element).click().perform()
                logging.info(f"Successfully clicked element using ActionChains: {name if name else target}")
                return element
            except Exception as e:
                logging.error(f"All click attempts failed for {name if name else target}: {str(e)}")
                raise

        except TimeoutException:
            logging.error(f"Element not found within 30 seconds: {name if name else target}")
            raise TimeoutException(f"Element {name if name else target} did not appear within 30 seconds")
        except Exception as e:
            logging.error(f"Failed to interact with element {name if name else target}: {str(e)}")
            raise

    def wait_for_element_visible(self, locator: Tuple[str, str], timeout: int = 60,
                                 poll_frequency: float = 0.5) -> WebElement:

        try:
            wait = WebDriverWait(self.driver, timeout, poll_frequency=poll_frequency)
            element = wait.until(EC.visibility_of_element_located(locator))
            logging.info(f"Element became visible: {locator}")
            return element
        except TimeoutException:
            logging.error(f"Element not visible after {timeout}s: {locator}")
            raise  # Re-raise for calling code to handle

    def is_element_present(self, locator: Tuple[str, str], timeout: int = 2, initial_delay: float = 0) -> bool:
        """
        Check if element is present and visible within timeout period

        Args:
            locator: Element locator tuple
            timeout: Maximum time to wait (default 2 seconds)
            initial_delay: Delay before starting to check (default 0 seconds)

        Returns:
            True if element becomes visible within timeout, False otherwise
        """
        try:
            # ✅ Wait before starting to look
            if initial_delay > 0:
                time.sleep(initial_delay)

            wait = WebDriverWait(self.driver, timeout, poll_frequency=0.5)
            wait.until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False
        except Exception:
            return False

    def get_elements_alt(self, *locators: Tuple[str, str]) -> List[WebElement]:
        for locator in locators:
            elements = self.driver.find_elements(*locator)
            if elements:
                return elements
        return []

    def wait_for_element_to_disappear(self, locator, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def switch_to_frame(self, locator):
        frame = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(locator))
        self.driver.switch_to.frame(frame)

    def switch_to_default_content(self):
        self.driver.switch_to.default_content()

    def find_element(self, locator: Tuple[str, str], timeout: int = 10, name: str = None) -> WebElement:
        """Simple but effective element finder"""
        element_name = name if name else str(locator)

        try:
            # Try visibility first (most reliable)
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return element
        except TimeoutException:
            try:
                # Fallback to presence
                element = WebDriverWait(self.driver, timeout // 2).until(
                    EC.presence_of_element_located(locator)
                )
                return element
            except TimeoutException:
                raise Exception(f"Element not found: {element_name}")

    def find_elements(self, locator: Tuple[str, str], timeout: int = 60, name: str = None) -> list:
        """Simple but effective elements finder"""
        element_name = name if name else str(locator)
        logging.info(f"Looking for elements: {element_name}")

        try:
            # Try visibility first (elements are visible and interactable)
            elements = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_all_elements_located(locator)
            )
            logging.info(f"Found {len(elements)} visible elements: {element_name}")
            return elements
        except TimeoutException:
            try:
                # Fallback to presence (elements exist but might not be visible)
                WebDriverWait(self.driver, timeout // 2).until(
                    EC.presence_of_element_located(locator)
                )
                elements = self.driver.find_elements(*locator)
                logging.info(f"Found {len(elements)} elements (some may not be visible): {element_name}")
                return elements
            except TimeoutException:
                # Final attempt - direct find without wait
                elements = self.driver.find_elements(*locator)
                if elements:
                    logging.info(f"Found {len(elements)} elements (no wait): {element_name}")
                else:
                    logging.warning(f"No elements found: {element_name}")
                return elements
        except Exception as e:
            logging.error(f"Error finding elements {element_name}: {str(e)}")
            return []

    def wait_for_loading_to_disappear(self, loading_locator: Tuple[str, str], timeout: int = 120, initial_delay = None,
                                      name: str = None) -> bool:

        if initial_delay is not None:
            time.sleep(initial_delay)
        element_name = name if name else str(loading_locator)

        def log_and_print(message, level="info"):
            """Log and print for real-time output"""
            if level == "info":
                logging.info(message)
            elif level == "warning":
                logging.warning(message)
            elif level == "error":
                logging.error(message)

            print(f"[{time.strftime('%H:%M:%S')}] {message}")
            sys.stdout.flush()  # Force immediate output

        def is_loader_visible():
            """Check if loader is visible, handling stale elements"""
            try:
                elements = self.driver.find_elements(*loading_locator)
                if not elements:
                    return False

                # Check each element safely
                for el in elements:
                    try:
                        if el.is_displayed():
                            return True
                    except StaleElementReferenceException:
                        # This element is stale, continue to next
                        continue
                return False

            except StaleElementReferenceException:
                # All elements stale, treat as gone
                return False
            except Exception:
                # Any other error, treat as gone
                return False

        try:
            log_and_print(f"Starting to wait for loading element: {element_name}")

            # Initial check
            if not is_loader_visible():
                log_and_print(f"Loading element not visible initially: {element_name}")
                return True

            log_and_print(f"Loading element is VISIBLE - monitoring: {element_name}")

            start_time = time.time()
            last_log_time = start_time
            loader_was_visible = True

            while time.time() - start_time < timeout:
                current_time = time.time()
                loader_visible = is_loader_visible()  # Now safe from stale elements

                # Log every 1 second
                if current_time - last_log_time >= 1.0:
                    if loader_visible:
                        elapsed = int(current_time - start_time)
                        log_and_print(f"⏳ Loading element still VISIBLE after {elapsed}s")
                    last_log_time = current_time

                # Check if loader disappeared
                if loader_was_visible and not loader_visible:
                    elapsed = int(current_time - start_time)
                    log_and_print(f"✅ Loading element DISAPPEARED after {elapsed}s")

                    time.sleep(0.5)
                    if not is_loader_visible():
                        log_and_print(f"✅ Loading element confirmed GONE")
                        return True
                    else:
                        log_and_print(f"⚠️ Loading element REAPPEARED")

                loader_was_visible = loader_visible
                time.sleep(0.2)

            log_and_print(f"⏰ TIMEOUT after {timeout}s", "warning")
            return False

        except StaleElementReferenceException:
            log_and_print(f"🔄 Page changed - assuming loading complete", "info")
            return True
        except Exception as e:
            log_and_print(f"❌ Error: {str(e)}", "error")
            return False


    def wait_for_element_state(self, locator: Tuple[str, str], state: str = "disappear",
                               timeout: int = 30, name: str = None) -> bool:

        element_name = name if name else str(locator)
        logging.info(f"Waiting for element to be {state}: {element_name}")

        try:
            if state == "disappear":
                return self.wait_for_loading_to_disappear(locator, timeout, name)

            elif state == "appear":
                WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located(locator)
                )
                logging.info(f"Element appeared: {element_name}")
                return True

            elif state == "clickable":
                WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable(locator)
                )
                logging.info(f"Element is clickable: {element_name}")
                return True

            elif state == "invisible":
                WebDriverWait(self.driver, timeout).until(
                    EC.invisibility_of_element_located(locator)
                )
                logging.info(f"Element became invisible: {element_name}")
                return True

            else:
                logging.error(f"Unknown state: {state}")
                return False

        except TimeoutException:
            logging.error(f"Timeout waiting for element to be {state}: {element_name}")
            return False
        except Exception as e:
            logging.error(f"Error waiting for element state {state}: {str(e)}")
            return False

    def attach_screenshot(self, name="screenshot"):
        """
        Waits for the page to be in a reasonably stable state and then attaches a screenshot to the Allure report.
        """
        try:
            # Wait for the main document to be loaded.
            WebDriverWait(self.driver, 5).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )

            time.sleep(0.3)

            # Now, take and attach the screenshot.
            png = self.driver.get_screenshot_as_png()
            allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
            logging.info(f"Attached screenshot: {name}")

        except Exception as e:
            # Log an error if screenshot fails, but don't stop the test.
            logging.error(f"Could not attach screenshot '{name}': {e}")



    def attach_note(self, note_text, name="Note"):
        allure.attach(
            note_text,
            name=name,
            attachment_type=allure.attachment_type.TEXT
        )

    def wait_for_value_to_update(self, locator, initial_value="$0.00", timeout=60, name=None):
        """Wait for element text to change from initial value to actual calculated value"""
        element_name = name if name else str(locator)
        logging.info(f"Waiting for {element_name} to update from '{initial_value}'")

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                element = self.find_element(locator, timeout=2)
                current_text = self.get_text(locator, element=element, name=element_name)
                self.logger.info(f"Current text: {current_text}")

                # Check if value has changed from initial value
                if current_text and current_text != initial_value:
                    logging.info(f"{element_name} updated to: '{current_text}'")
                    return current_text

                time.sleep(0.3)

            except Exception as e:
                logging.debug(f"Error checking value: {str(e)}")
                time.sleep(0.3)

        logging.warning(f"{element_name} did not update within {timeout}s")
        raise TimeoutException(f"{element_name} stuck at '{initial_value}' after {timeout}s")

    def wait_until(self, condition_func, timeout: int = 10, poll_frequency: float = 0.3,
                   description: str = "condition", on_timeout_return: bool = False):
        """
        Generic reusable wait.
        Executes `condition_func()` repeatedly until it returns True or timeout expires.

        Args:
            condition_func: A lambda or function returning True when the desired state is reached
            timeout (int): Maximum seconds to wait
            poll_frequency (float): Sleep interval between retries
            description (str): Text for logging/timeouts
            on_timeout_return (bool): If True, return False on timeout instead of raising TimeoutException

        Returns:
            True if condition satisfied; False (or raises TimeoutException) otherwise
        """
        start_time = time.time()
        last_log = start_time
        try:
            while time.time() - start_time < timeout:
                try:
                    if condition_func():
                        return True
                except Exception:
                    pass

                now = time.time()
                if now - last_log >= 1.0:
                    logging.debug(f"⏳ Waiting for {description}... {int(now - start_time)}s elapsed")
                    last_log = now
                time.sleep(poll_frequency)

            msg = f"❌ Timeout after {timeout}s waiting for {description}"
            logging.warning(msg)
            if on_timeout_return:
                return False
            raise TimeoutException(msg)
        except Exception as e:
            logging.error(f"Error while waiting for {description}: {e}")
            if on_timeout_return:
                return False
            raise