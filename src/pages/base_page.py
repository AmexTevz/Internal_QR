# import sys
# import threading
# import time
# from datetime import datetime
# from collections import deque
# import tempfile
# import os
# import logging
# from typing import Tuple
# import cv2
# import numpy as np
# import mss
# import imageio
# import allure
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.common.keys import Keys
# from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
# from selenium.webdriver.remote.webelement import WebElement
# from typing import Union, List
# import functools
#
#
# def wait_for_loader(func):
#     @functools.wraps(func)
#     def wrapper(self, *args, **kwargs):
#         self.wait_for_loader_to_disappear()
#         return func(self, *args, **kwargs)
#
#     return wrapper
#
#
# class VideoRecorder:
#     """Simplified video recorder for loader waiting"""
#
#     def __init__(self, fps=12, quality=7):
#         self.fps = fps
#         self.quality = quality
#         self.frames = deque()
#         self.recording = False
#         self.thread = None
#         self.monitor = None
#         self.start_time = None
#         self.logger = logging.getLogger(__name__)
#         self._lock = threading.Lock()
#         self.max_frames = 600  # ~50 seconds at 12fps
#
#     def start_recording(self, monitor_area=None):
#         """Start recording"""
#         try:
#             with mss.mss() as sct:
#                 self.monitor = monitor_area or sct.monitors[1]
#
#             self.recording = True
#             self.frames = deque()
#             self.start_time = time.time()
#             self.thread = threading.Thread(target=self._record_frames, daemon=True)
#             self.thread.start()
#
#         except Exception as e:
#             self.logger.error(f"Video recording start failed: {e}")
#             self.recording = False
#
#     def stop_recording(self):
#         """Stop recording"""
#         if self.recording:
#             self.recording = False
#             if self.thread and self.thread.is_alive():
#                 self.thread.join(timeout=3)
#
#     def _record_frames(self):
#         """Record frames in background thread"""
#         frame_duration = 1.0 / float(self.fps)
#
#         try:
#             with mss.mss() as sct:
#                 while self.recording:
#                     frame_start = time.time()
#
#                     try:
#                         screenshot = sct.grab(self.monitor)
#                         frame = np.array(screenshot)
#                         frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
#
#                         with self._lock:
#                             self.frames.append({
#                                 'frame': frame,
#                                 'timestamp': time.time() - self.start_time
#                             })
#
#                             # Memory management
#                             while len(self.frames) > self.max_frames:
#                                 self.frames.popleft()
#
#                     except Exception:
#                         pass  # Continue recording on frame errors
#
#                     # Maintain frame rate
#                     elapsed = time.time() - frame_start
#                     sleep_time = max(0.0, frame_duration - elapsed)
#                     if sleep_time > 0:
#                         time.sleep(sleep_time)
#
#         except Exception:
#             pass  # Fail silently
#         finally:
#             self.recording = False
#
#     def save_video(self, filename, detection_time=None, disappear_time=None):
#         """Save video with timing"""
#         try:
#             with self._lock:
#                 if not self.frames:
#                     return None
#
#                 # Extract frames in time range if provided
#                 if detection_time is not None and disappear_time is not None:
#                     start_time = max(0.0, detection_time - 1.0)  # 1 sec before
#                     end_time = disappear_time + 1.0  # 1 sec after
#
#                     frames_to_save = [
#                         f['frame'] for f in self.frames
#                         if start_time <= f['timestamp'] <= end_time
#                     ]
#                 else:
#                     frames_to_save = [f['frame'] for f in self.frames]
#
#                 if not frames_to_save:
#                     return None
#
#             # Save video
#             if not filename.endswith('.mp4'):
#                 filename += '.mp4'
#
#             with imageio.get_writer(filename, fps=self.fps, quality=self.quality) as writer:
#                 for frame in frames_to_save:
#                     writer.append_data(frame)
#
#             return filename
#
#         except Exception:
#             return None
#
#     def cleanup(self):
#         """Cleanup resources"""
#         try:
#             self.stop_recording()
#             with self._lock:
#                 self.frames.clear()
#         except Exception:
#             pass
#
#
# class BasePage:
#     def __init__(self, driver):
#         self.driver = driver
#         self.wait = WebDriverWait(self.driver, 10)
#         self.actions = ActionChains(self.driver)
#         self.logger = logging.getLogger(__name__)
#         self.store_id = None
#
#         self.LOADER = (By.CSS_SELECTOR, ".loader")
#
#     def wait_for_loader_to_disappear(self, timeout=60):
#         """Original method - unchanged for backward compatibility"""
#         try:
#             initial_elements = self.driver.find_elements(*self.LOADER)
#             if not initial_elements:
#                 self.logger.debug("Loader not found initially - continuing")
#                 return True
#
#             visible_elements = [el for el in initial_elements if el.is_displayed()]
#             if not visible_elements:
#                 self.logger.debug("Loader present but not visible - continuing")
#                 return True
#
#             self.logger.debug("Waiting for loader to disappear...")
#
#             WebDriverWait(self.driver, timeout).until_not(
#                 EC.presence_of_element_located(self.LOADER)
#             )
#             self.logger.debug("Loader disappeared successfully")
#             return True
#
#         except TimeoutException:
#             self.logger.warning(f"Loader didn't disappear within {timeout}s, proceeding anyway")
#             return False
#         except Exception as e:
#             self.logger.debug(f"Loader wait exception: {str(e)}")
#             return True
#
#     def wait_for_loading_to_disappear(self, loading_locator: Tuple[str, str],
#                                       timeout: int = 50, initial_delay=None,
#                                       name: str = None, record_video: bool = False) -> bool:
#         """
#         Enhanced loader waiting with optional video recording.
#         BACKWARD COMPATIBLE - existing calls work unchanged.
#         NEW FEATURE - pass record_video=True to enable video recording.
#         """
#
#         if initial_delay is not None:
#             time.sleep(initial_delay)
#
#         element_name = name if name else str(loading_locator)
#         video_recorder = None
#         detection_time = None
#         disappear_time = None
#
#         def log_and_print(message, level="info"):
#             if level == "info":
#                 logging.info(message)
#             elif level == "warning":
#                 logging.warning(message)
#             elif level == "error":
#                 logging.error(message)
#             print(f"[{time.strftime('%H:%M:%S')}] {message}")
#             sys.stdout.flush()
#
#         def is_loader_visible():
#             try:
#                 elements = self.driver.find_elements(*loading_locator)
#                 if not elements:
#                     return False
#                 for el in elements:
#                     try:
#                         if el.is_displayed():
#                             return True
#                     except StaleElementReferenceException:
#                         continue
#                 return False
#             except:
#                 return False
#
#         # Initialize video recording if requested
#         if record_video:
#             try:
#                 video_recorder = VideoRecorder(fps=12, quality=7)
#                 browser_rect = self.driver.get_window_rect()
#                 monitor_area = {
#                     'top': browser_rect['y'],
#                     'left': browser_rect['x'],
#                     'width': browser_rect['width'],
#                     'height': browser_rect['height']
#                 }
#                 video_recorder.start_recording(monitor_area)
#                 log_and_print("Video recording started")
#             except Exception as e:
#                 log_and_print(f"Video recording failed to start: {e}", "warning")
#                 record_video = False
#
#         try:
#             log_and_print(f"Waiting for loading element: {element_name}")
#
#             # Check if loader is initially visible
#             if not is_loader_visible():
#                 log_and_print(f"Loading element not visible initially: {element_name}")
#                 return True
#
#             # Mark detection time for video
#             if record_video and video_recorder:
#                 detection_time = time.time() - video_recorder.start_time
#
#             log_and_print(f"Loading element detected and monitoring: {element_name}")
#
#             start_time = time.time()
#             last_log_time = start_time
#             loader_was_visible = True
#
#             while time.time() - start_time < timeout:
#                 current_time = time.time()
#                 loader_visible = is_loader_visible()
#
#                 # Log progress every second
#                 if current_time - last_log_time >= 1.0:
#                     if loader_visible:
#                         elapsed = int(current_time - start_time)
#                         log_and_print(f"Loading element still visible after {elapsed}s")
#                     last_log_time = current_time
#
#                 # Check if loader disappeared
#                 if loader_was_visible and not loader_visible:
#                     elapsed = int(current_time - start_time)
#                     log_and_print(f"Loading element disappeared after {elapsed}s")
#
#                     # Mark disappearance time for video
#                     if record_video and video_recorder:
#                         disappear_time = current_time - video_recorder.start_time
#
#                     # Confirm it's really gone
#                     time.sleep(0.5)
#                     if not is_loader_visible():
#                         log_and_print("Loading element confirmed gone")
#
#                         # Wait extra second for video post-buffer
#                         if record_video:
#                             time.sleep(1.0)
#
#                         return True
#                     else:
#                         log_and_print("Loading element reappeared")
#
#                 loader_was_visible = loader_visible
#                 time.sleep(0.2)
#
#             log_and_print(f"Timeout after {timeout}s", "warning")
#             return False
#
#         except StaleElementReferenceException:
#             log_and_print("Page changed - assuming loading complete", "info")
#             return True
#         except Exception as e:
#             log_and_print(f"Error: {str(e)}", "error")
#             return False
#         finally:
#             # Handle video recording cleanup
#             if record_video and video_recorder:
#                 try:
#                     log_and_print("Processing video recording...")
#                     video_recorder.stop_recording()
#
#                     # Create temp file for video
#                     temp_dir = tempfile.mkdtemp()
#                     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                     video_filename = os.path.join(temp_dir, f"loader_wait_{timestamp}.mp4")
#
#                     # Save video
#                     saved_file = video_recorder.save_video(video_filename, detection_time, disappear_time)
#
#                     if saved_file and os.path.exists(saved_file):
#                         # Attach to Allure
#                         try:
#                             with open(saved_file, 'rb') as video_file:
#                                 allure.attach(
#                                     video_file.read(),
#                                     name=f"Loader Wait Video - {element_name}",
#                                     attachment_type=allure.attachment_type.MP4
#                                 )
#                             log_and_print("Video attached to Allure report")
#                         except Exception:
#                             pass  # Fail silently if Allure attachment fails
#
#                         # Cleanup temp file
#                         try:
#                             os.remove(saved_file)
#                             os.rmdir(temp_dir)
#                         except Exception:
#                             pass  # Fail silently on cleanup
#
#                     # Cleanup recorder
#                     video_recorder.cleanup()
#
#                 except Exception:
#                     pass  # Fail silently on video processing errors
#
#     # All your existing methods remain exactly the same...
#
#     def send_keys(self, locator, text, clear=True, name=None):
#         logging.info(f"Attempting to send keys to element: {name if name else locator}")
#         try:
#             self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
#
#             element = self.wait.until(EC.presence_of_element_located(locator))
#             try:
#                 if clear:
#                     element.clear()
#                 element.send_keys(text)
#                 logging.info(f"Successfully sent keys using regular method: {name if name else locator}")
#                 return element
#             except Exception as e:
#                 logging.info(f"Regular send_keys failed: {str(e)}")
#
#             try:
#                 if clear:
#                     self.driver.execute_script("arguments[0].value = '';", element)
#                 self.driver.execute_script(f"arguments[0].value = arguments[1];", element, text)
#                 logging.info(f"Successfully sent keys using JavaScript: {name if name else locator}")
#                 return element
#             except Exception as e:
#                 logging.info(f"JavaScript send_keys failed: {str(e)}")
#
#             try:
#                 actions = ActionChains(self.driver)
#                 if clear:
#                     actions.click(element).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(
#                         Keys.BACK_SPACE)
#                 actions.send_keys(text).perform()
#                 logging.info(f"Successfully sent keys using ActionChains: {name if name else locator}")
#                 return element
#             except Exception as e:
#                 logging.error(f"All send_keys attempts failed: {str(e)}")
#                 raise
#
#         except Exception as e:
#             logging.error(f"Failed to interact with element {name if name else locator}: {str(e)}")
#             raise
#
#     def get_text(self, locator, name=None, element=None, timeout=30):
#         logging.info(f"Attempting to get text from element: {name if name else locator}")
#         try:
#             if element is None:
#                 element = WebDriverWait(self.driver, timeout).until(
#                     EC.presence_of_element_located(locator)
#                 )
#
#             try:
#                 text = element.text.strip()
#                 if text:
#                     logging.info(f"Successfully got text using .text: '{text}'")
#                     return text
#             except Exception as e:
#                 logging.debug(f"Regular .text failed: {str(e)}")
#
#             try:
#                 text = element.get_attribute('textContent').strip()
#                 if text:
#                     logging.info(f"Successfully got text using textContent: '{text}'")
#                     return text
#             except Exception as e:
#                 logging.debug(f"textContent failed: {str(e)}")
#
#             try:
#                 text = self.driver.execute_script("return arguments[0].innerText;", element)
#                 if text:
#                     text = text.strip()
#                     logging.info(f"Successfully got text using JavaScript: '{text}'")
#                     return text
#             except Exception as e:
#                 logging.debug(f"JavaScript innerText failed: {str(e)}")
#
#             logging.warning(f"Element found but no text could be extracted from {name if name else locator}")
#             return ""
#
#         except Exception as e:
#             logging.error(f"Failed to locate or get text from element {name if name else locator}: {str(e)}")
#             raise
#
#     def click(self, target: Union[WebElement, Tuple[str, str]], name=None, timeout=30):
#         try:
#             self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
#
#             if isinstance(target, tuple):
#                 element = WebDriverWait(self.driver, timeout).until(
#                     EC.element_to_be_clickable(target)
#                 )
#                 logging.info(f"Element found and is clickable: {name if name else target}")
#             else:
#                 element = target
#
#             try:
#                 element.click()
#                 logging.info(f"Successfully clicked element using regular click: {name if name else target}")
#                 return element
#             except Exception as e:
#                 logging.info(f"Regular click failed, trying alternative methods: {str(e)}")
#
#             try:
#                 self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
#                 self.driver.execute_script("arguments[0].click();", element)
#                 logging.info(f"Successfully clicked element using JavaScript: {name if name else target}")
#                 return element
#             except Exception as e:
#                 logging.info(f"JavaScript click failed, trying ActionChains: {str(e)}")
#
#             try:
#                 actions = ActionChains(self.driver)
#                 actions.move_to_element(element).click().perform()
#                 logging.info(f"Successfully clicked element using ActionChains: {name if name else target}")
#                 return element
#             except Exception as e:
#                 logging.error(f"All click attempts failed for {name if name else target}: {str(e)}")
#                 raise
#
#         except TimeoutException:
#             logging.error(f"Element not found within 30 seconds: {name if name else target}")
#             raise TimeoutException(f"Element {name if name else target} did not appear within 30 seconds")
#         except Exception as e:
#             logging.error(f"Failed to interact with element {name if name else target}: {str(e)}")
#             raise
#
#     def attach_screenshot(self, name="screenshot"):
#         try:
#             WebDriverWait(self.driver, 5).until(
#                 lambda d: d.execute_script('return document.readyState') == 'complete'
#             )
#             time.sleep(0.3)
#             png = self.driver.get_screenshot_as_png()
#             allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
#             logging.info(f"Attached screenshot: {name}")
#         except Exception as e:
#             logging.error(f"Could not attach screenshot '{name}': {e}")
#
#     def attach_note(self, note_text, name="Note"):
#         allure.attach(
#             note_text,
#             name=name,
#             attachment_type=allure.attachment_type.TEXT
#         )
#
#
#
#     def get_text_short(self, locator, name=None, element=None, timeout=2):
#         logging.info(f"Attempting to get text from element: {name if name else locator}")
#         try:
#             if element is None:
#                 element = WebDriverWait(self.driver, timeout).until(
#                     EC.presence_of_element_located(locator)
#                 )
#
#             try:
#                 text = element.text.strip()  # Added strip()
#                 if text:
#                     logging.info(f"Successfully got text using .text: '{text}'")
#                     return text
#             except Exception as e:
#                 logging.debug(f"Regular .text failed: {str(e)}")
#
#             # Try textContent
#             try:
#                 text = element.get_attribute('textContent').strip()
#                 if text:
#                     logging.info(f"Successfully got text using textContent: '{text}'")
#                     return text
#             except Exception as e:
#                 logging.debug(f"textContent failed: {str(e)}")
#
#             # Try JavaScript innerText
#             try:
#                 text = self.driver.execute_script("return arguments[0].innerText;", element)
#                 if text:
#                     text = text.strip()
#                     logging.info(f"Successfully got text using JavaScript: '{text}'")
#                     return text
#             except Exception as e:
#                 logging.debug(f"JavaScript innerText failed: {str(e)}")
#
#             # If we get here, no method worked but element exists
#             logging.warning(f"Element found but no text could be extracted from {name if name else locator}")
#             return ""
#
#         except Exception as e:
#             logging.error(f"Failed to locate or get text from element {name if name else locator}: {str(e)}")
#             raise
#
#     def get_text_2(self, locator, name=None, max_attempts=50):
#         """Ultra-patient text getter that keeps trying until it finds text"""
#         logging.info(f"Patiently waiting for text from element: {name if name else locator}")
#
#         attempt = 0
#
#         while attempt < max_attempts:
#             try:
#                 attempt += 1
#                 logging.info(f"Attempt {attempt}/{max_attempts}")
#
#                 # Wait for element with longer timeout each attempt
#                 timeout = min(10 + (attempt * 2), 60)  # Gradually increase timeout
#                 element = WebDriverWait(self.driver, timeout).until(
#                     EC.visibility_of_element_located(locator)
#                 )
#
#                 # Try all text extraction methods
#                 methods = [
#                     lambda e: e.text.strip(),
#                     lambda e: e.get_attribute('textContent').strip(),
#                     lambda e: self.driver.execute_script("return arguments[0].innerText;", e).strip(),
#                     lambda e: self.driver.execute_script("return arguments[0].textContent;", e).strip()
#                 ]
#
#                 for method in methods:
#                     try:
#                         text = method(element)
#                         if text:
#                             logging.info(f"Success on attempt {attempt}: '{text}'")
#                             return text
#                     except:
#                         continue
#
#                 logging.info(f"No text found on attempt {attempt}, waiting 3 seconds...")
#                 time.sleep(1)  # Wait before next attempt
#
#             except Exception as e:
#                 logging.debug(f"Attempt {attempt} failed: {str(e)}")
#                 time.sleep(1)  # Wait before retrying after exception
#
#         logging.error(f"Failed to get text after {max_attempts} attempts")
#         raise TimeoutException(f"Could not get text from {name if name else locator} after {max_attempts} attempts")
#
#     def is_element_displayed(self, locator, timeout=2):
#         try:
#             elements = self.driver.find_elements(*locator)
#             if elements and elements[0].is_displayed():
#                 return True
#
#             WebDriverWait(self.driver, timeout).until(
#                 EC.visibility_of_element_located(locator)
#             )
#             return True
#         except:
#             return False
#
#     def wait_for_url_contains(self, partial_url, timeout=10):
#         try:
#             WebDriverWait(self.driver, timeout).until(
#                 EC.url_contains(partial_url)
#             )
#             logging.info(f"URL contains '{partial_url}'")
#             return True
#         except TimeoutException:
#             logging.error(f"URL does not contain '{partial_url}' within {timeout} seconds")
#             return False
#
#     def get_elements(self, *locators):
#         for locator in locators:
#             elements = self.driver.find_elements(*locator)
#             if elements:
#                 return elements
#         return []
#
#     def wait_for_elements(self, locator, timeout=20):
#         wait = WebDriverWait(self.driver, timeout)
#         return wait.until(EC.presence_of_all_elements_located(locator))
#
#
#
#     def wait_for_element_visible(self, locator: Tuple[str, str], timeout: int = 30,
#                                  poll_frequency: float = 0.5) -> WebElement:
#
#         try:
#             wait = WebDriverWait(self.driver, timeout, poll_frequency=poll_frequency)
#             element = wait.until(EC.visibility_of_element_located(locator))
#             logging.info(f"Element became visible: {locator}")
#             return element
#         except TimeoutException:
#             logging.error(f"Element not visible after {timeout}s: {locator}")
#             raise  # Re-raise for calling code to handle
#
#     def is_element_present(self, locator: Tuple[str, str], timeout: int = 2) -> bool:
#         """
#         Check if element is present and visible within timeout period
#
#         Args:
#             locator: Element locator tuple
#             timeout: Maximum time to wait (default 10 seconds)
#
#         Returns:
#             True if element becomes visible within timeout, False otherwise
#         """
#         try:
#             wait = WebDriverWait(self.driver, timeout, poll_frequency=0.5)
#             wait.until(EC.visibility_of_element_located(locator))
#             return True
#         except TimeoutException:
#             return False
#         except Exception:
#             return False
#
#     def get_elements_alt(self, *locators: Tuple[str, str]) -> List[WebElement]:
#         for locator in locators:
#             elements = self.driver.find_elements(*locator)
#             if elements:
#                 return elements
#         return []
#
#     def wait_for_element_to_disappear(self, locator, timeout=10):
#         try:
#             WebDriverWait(self.driver, timeout).until_not(
#                 EC.presence_of_element_located(locator)
#             )
#             return True
#         except TimeoutException:
#             return False
#
#     def switch_to_frame(self, locator):
#         frame = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(locator))
#         self.driver.switch_to.frame(frame)
#
#     def switch_to_default_content(self):
#         self.driver.switch_to.default_content()
#
#     def find_element(self, locator: Tuple[str, str], timeout: int = 10, name: str = None) -> WebElement:
#         """Simple but effective element finder"""
#         element_name = name if name else str(locator)
#
#         try:
#             # Try visibility first (most reliable)
#             element = WebDriverWait(self.driver, timeout).until(
#                 EC.visibility_of_element_located(locator)
#             )
#             return element
#         except TimeoutException:
#             try:
#                 # Fallback to presence
#                 element = WebDriverWait(self.driver, timeout // 2).until(
#                     EC.presence_of_element_located(locator)
#                 )
#                 return element
#             except TimeoutException:
#                 raise Exception(f"Element not found: {element_name}")
#
#     def find_elements(self, locator: Tuple[str, str], timeout: int = 60, name: str = None) -> list:
#         """Simple but effective elements finder"""
#         element_name = name if name else str(locator)
#         logging.info(f"Looking for elements: {element_name}")
#
#         try:
#             # Try visibility first (elements are visible and interactable)
#             elements = WebDriverWait(self.driver, timeout).until(
#                 EC.visibility_of_all_elements_located(locator)
#             )
#             logging.info(f"Found {len(elements)} visible elements: {element_name}")
#             return elements
#         except TimeoutException:
#             try:
#                 # Fallback to presence (elements exist but might not be visible)
#                 WebDriverWait(self.driver, timeout // 2).until(
#                     EC.presence_of_element_located(locator)
#                 )
#                 elements = self.driver.find_elements(*locator)
#                 logging.info(f"Found {len(elements)} elements (some may not be visible): {element_name}")
#                 return elements
#             except TimeoutException:
#                 # Final attempt - direct find without wait
#                 elements = self.driver.find_elements(*locator)
#                 if elements:
#                     logging.info(f"Found {len(elements)} elements (no wait): {element_name}")
#                 else:
#                     logging.warning(f"No elements found: {element_name}")
#                 return elements
#         except Exception as e:
#             logging.error(f"Error finding elements {element_name}: {str(e)}")
#             return []
#
#
#
#
#
#     def wait_for_element_state(self, locator: Tuple[str, str], state: str = "disappear",
#                                timeout: int = 30, name: str = None) -> bool:
#
#         element_name = name if name else str(locator)
#         logging.info(f"Waiting for element to be {state}: {element_name}")
#
#         try:
#             if state == "disappear":
#                 return self.wait_for_loading_to_disappear(locator, timeout, name)
#
#             elif state == "appear":
#                 WebDriverWait(self.driver, timeout).until(
#                     EC.visibility_of_element_located(locator)
#                 )
#                 logging.info(f"Element appeared: {element_name}")
#                 return True
#
#             elif state == "clickable":
#                 WebDriverWait(self.driver, timeout).until(
#                     EC.element_to_be_clickable(locator)
#                 )
#                 logging.info(f"Element is clickable: {element_name}")
#                 return True
#
#             elif state == "invisible":
#                 WebDriverWait(self.driver, timeout).until(
#                     EC.invisibility_of_element_located(locator)
#                 )
#                 logging.info(f"Element became invisible: {element_name}")
#                 return True
#
#             else:
#                 logging.error(f"Unknown state: {state}")
#                 return False
#
#         except TimeoutException:
#             logging.error(f"Timeout waiting for element to be {state}: {element_name}")
#             return False
#         except Exception as e:
#             logging.error(f"Error waiting for element state {state}: {str(e)}")
#             return False
#
#
#
#



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

    def wait_for_element_visible(self, locator: Tuple[str, str], timeout: int = 30,
                                 poll_frequency: float = 0.5) -> WebElement:

        try:
            wait = WebDriverWait(self.driver, timeout, poll_frequency=poll_frequency)
            element = wait.until(EC.visibility_of_element_located(locator))
            logging.info(f"Element became visible: {locator}")
            return element
        except TimeoutException:
            logging.error(f"Element not visible after {timeout}s: {locator}")
            raise  # Re-raise for calling code to handle

    def is_element_present(self, locator: Tuple[str, str], timeout: int = 2) -> bool:
        """
        Check if element is present and visible within timeout period

        Args:
            locator: Element locator tuple
            timeout: Maximum time to wait (default 10 seconds)

        Returns:
            True if element becomes visible within timeout, False otherwise
        """
        try:
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
    # def wait_for_loading_to_disappear(self, loading_locator: Tuple[str, str], timeout: int = 30,
    #                                   name: str = None, stable_time: float = 1.0) -> bool:
    #     element_name = name if name else str(loading_locator)
    #     logging.info(f"Waiting for loading element to disappear: {element_name}")
    #
    #     try:
    #         # Quick initial check
    #         elements = self.driver.find_elements(*loading_locator)
    #         if not elements or not any(el.is_displayed() for el in elements):
    #             logging.info(f"Loading element not visible initially: {element_name}")
    #             return True
    #
    #         logging.info(f"Loading element is visible, waiting for stable disappearance: {element_name}")
    #
    #         # Wait for element to become invisible with faster polling
    #         WebDriverWait(self.driver, timeout, poll_frequency=0.2).until(
    #             EC.invisibility_of_element_located(loading_locator)
    #         )
    #
    #         # Wait for stable disappearance (element stays gone)
    #         stable_start = time.time()
    #         while time.time() - stable_start < stable_time:
    #             elements = self.driver.find_elements(*loading_locator)
    #             if elements and any(el.is_displayed() for el in elements):
    #                 logging.info(f"Loading element reappeared, resetting stability timer: {element_name}")
    #                 # Element reappeared, wait for it to disappear again
    #                 WebDriverWait(self.driver, timeout, poll_frequency=0.2).until(
    #                     EC.invisibility_of_element_located(loading_locator)
    #                 )
    #                 stable_start = time.time()  # Reset timer
    #             time.sleep(0.1)  # Small sleep between stability checks
    #
    #         logging.info(f"Loading element confirmed stable disappearance: {element_name}")
    #         return True
    #
    #     except TimeoutException:
    #         logging.warning(f"Loading element still visible after {timeout}s: {element_name}")
    #         return False
    #     except StaleElementReferenceException:
    #         logging.info(f"Loading element became stale: {element_name}")
    #         return True
    #     except Exception as e:
    #         logging.error(f"Error waiting for loading to disappear: {str(e)}")
    #         return False

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

    # def attach_screenshot(self, name="screenshot", full_page=False):
    #     """
    #     Waits for the page to be in a reasonably stable state and then attaches a screenshot to the Allure report.
    #     """
    #     try:
    #         WebDriverWait(self.driver, 5).until(
    #             lambda d: d.execute_script('return document.readyState') == 'complete'
    #         )
    #         time.sleep(0.3)
    #
    #         if full_page:
    #             # Store original window size
    #             original_size = self.driver.get_window_size()
    #
    #             # Wait for the total/summary content to be present (adjust selector as needed)
    #             try:
    #                 WebDriverWait(self.driver, 3).until(
    #                     EC.presence_of_element_located(
    #                         (By.XPATH, "//*[contains(text(), 'Service Charge') or contains(text(), 'Total')]"))
    #                 )
    #             except:
    #                 pass  # Continue if element not found
    #
    #             # Multiple attempts to get accurate height
    #             heights = []
    #             for _ in range(3):
    #                 height = self.driver.execute_script("""
    #                     var body = document.body;
    #                     var html = document.documentElement;
    #                     return Math.max(
    #                         body.scrollHeight,
    #                         body.offsetHeight,
    #                         html.clientHeight,
    #                         html.scrollHeight,
    #                         html.offsetHeight,
    #                         window.innerHeight + window.scrollY
    #                     );
    #                 """)
    #                 heights.append(height)
    #                 time.sleep(0.2)
    #
    #             # Use the maximum height found
    #             total_height = max(heights) + 300  # Extra padding
    #
    #             # Scroll to absolute bottom to ensure everything loads
    #             self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #             time.sleep(0.5)
    #             self.driver.execute_script("window.scrollTo(0, 0);")
    #             time.sleep(0.3)
    #
    #             # Set window size
    #             self.driver.set_window_size(original_size['width'], total_height)
    #             time.sleep(1.2)  # Even longer wait
    #
    #             png = self.driver.get_screenshot_as_png()
    #
    #             # Restore original window size
    #             self.driver.set_window_size(original_size['width'], original_size['height'])
    #         else:
    #             png = self.driver.get_screenshot_as_png()
    #
    #         allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
    #         logging.info(f"Attached screenshot: {name}")
    #
    #     except Exception as e:
    #         logging.error(f"Could not attach screenshot '{name}': {e}")

    def attach_note(self, note_text, name="Note"):
        allure.attach(
            note_text,
            name=name,
            attachment_type=allure.attachment_type.TEXT
        )
