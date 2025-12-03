from src.pages.base_page import BasePage
from src.locators.store_locators import ConfirmationPageLocators, FreedomPayLocators


class ConfirmationPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)

    def thank_you_massage(self):
        self.wait_for_loading_to_disappear(FreedomPayLocators.LOADER, name= "#5 wait")
        massage = self.find_element(ConfirmationPageLocators.THANK_YOU).text
        print(f'Thank you massage confirmed - {massage}')
        return massage

    def calculations(self):
        pass