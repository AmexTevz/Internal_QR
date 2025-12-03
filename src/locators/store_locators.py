from selenium.webdriver.common.by import By

class CommonLocators:
    GET_STARTED = (By.CSS_SELECTOR, 'button.get-started')
    CUSTOMER_NAME_INPUT = (By.XPATH, "//input[@placeholder='Type Name Here']")
    SAVE_AND_CONTINUE = (By.CSS_SELECTOR, 'button.haptic_vibrate')
    CLOSE_AD_BUTTON = (By.CSS_SELECTOR, 'i.icons-close-ad')
    CLOSE_POPUP_BUTTON = (By.CSS_SELECTOR, 'button#CookiePrefencesModalButton')
    DISMISS_BUTTON = (By.CSS_SELECTOR, '.cc-dismiss')

class MenuContents:
    CHECK_NUMBER = (By.CSS_SELECTOR, 'div.order-no')
    CUSTOMER_NAME = (By.CSS_SELECTOR, 'span.capitalize')
    TABLE_NUMBER = (By.CSS_SELECTOR, "svg#table_no")
    ITEMS = (By.CSS_SELECTOR, '.menu-list-title')
    ITEM_NAME = (By.CSS_SELECTOR, '.mod-title')
    ITEM_PRICE = (By.CSS_SELECTOR, '.mod-cta-price')
    MODIFIER_NAME = (By.CSS_SELECTOR, '.mod-option-label')
    MODIFIER_PRICE = (By.CSS_SELECTOR, '.mod-option-price')
    ADD_BUTTON = (By.CSS_SELECTOR, ".mod-cta-btn")
    VIEW_ORDER = (By.XPATH, "//button[contains(@class, 'button--moema') and contains(., 'View Order')]")
    SUBMIT_ORDER = (By.XPATH, "//button[contains(@class, 'button--moema') and contains(., 'Submit Order')]")
    CONFIRM_SUBMIT_ORDER = (By.XPATH, "//button[contains(@class, 'mt-2') and contains(., 'Yes, Submit Order')]")
    ORDER_LOADING = (By.CSS_SELECTOR, "div.loader-box")
    GO_TO_CHECKOUT = (By.XPATH, "//button[contains(@class, 'btn') and contains(., 'Checkout')]")
    SINGLE_PAYMENT = (By.XPATH, "//button[contains(@class, 'btn') and contains(., 'Single Payment')]")
    SPLIT_BY_EXACT_AMOUNT_PAYMENT = (By.XPATH, "//button[contains(@class, 'btn') and contains(., 'Split By Exact Amount')]")
    SPLIT_EQUALLY = (By.XPATH, "//button[contains(@class, 'btn') and contains(., 'Split Equally')]")
    PAY_FOR_ENTIRE_CHECK = (By.XPATH, "//button[contains(@class, 'btn') and contains(., 'Pay for Entire Check')]")
    PAY_FOR_MYSELF = (By.XPATH, "//button[contains(@class, 'btn') and contains(., 'Pay for Myself')]")
    PAY_FOR_OTHERS_AT_TABLE = (By.XPATH, "//button[contains(@class, 'btn') and contains(., 'Pay for others at table')]")
    SERVER_POPUP = (By.CSS_SELECTOR, ".close")
    ERROR_MESSAGE = (By.CSS_SELECTOR, "#toast-container")
    SEARCH_BUTTON = (By.CSS_SELECTOR, ".btn.search-icon.active")
    INPUT_FIELD = (By.CSS_SELECTOR, ".SearchInputBox")
    BACK_TO_MENU_BUTTON = (By.CSS_SELECTOR, ".check-out-back-menu")
    REORDER_BUTTON = (By.XPATH, "//button[contains(text(), 'Reorder')]")
    UHNO_ERROR = (By.CSS_SELECTOR, ".error-icon")

class CheckoutPageLocators:
    CHECK_NUMBER = (By.CSS_SELECTOR, 'div.order-no')
    PHONE_NUMBER = (By.CSS_SELECTOR, 'input[name="phone"]')
    EMAIL = (By.CSS_SELECTOR, 'input[name="email"]')
    TIP_5 = (By.XPATH, '//button[contains(text(), "5%")]')
    TIP_10 = (By.XPATH, '//button[contains(text(), "10%")]')
    TIP_15 = (By.XPATH, '//button[contains(text(), "15%")]')
    TIP_20 = (By.XPATH, '//button[contains(text(), "20%")]')
    TIP_CUSTOM = (By.XPATH, '//button[contains(text(), "Custom")]')
    CUSTOM_TIP_INPUT = (By.CSS_SELECTOR, 'input[name="checkout-tip-tip-amount"]')
    TIP_AMOUNT = (By.XPATH, "//input[@name='checkout-tip-tip-amount']")
    TIP_VALUE = (By.XPATH, "//div[contains(@class, 'sum-bar d-fx-sb') and contains(., 'Tip')]//span[@id='JS_Tip_Show']")
    SUBTOTAL_VALUE = (By.XPATH, "//div[contains(@class, 'sum-bar') and contains(., 'Subtotal')]")
    TAX_VALUE = (By.CSS_SELECTOR, "#JS_Tax_Show")
    TOTAL_VALUE = (By.CSS_SELECTOR, "#JS_Total_Show")
    MAKE_PAYMENT = (By.XPATH, "//button[contains(@class, 'button--moema') and contains(., 'Payment')]")
    CHARITY_AGREE = (By.CSS_SELECTOR, ".btn.mt-2")
    CHARITY_DECLINE = (By.CSS_SELECTOR, ".btn.mt-4")
    SPLIT_EQUALLY_PLUS_BUTTON = (By.CSS_SELECTOR, ".plus-btn")
    SPLIT_EQUALLY_AMOUNT = (By.CSS_SELECTOR, ".JS_SplitEqually_CheckoutDetail_Amount")
    SPLIT_EQUALLY_TOTAL_PEOPLE = (By.CSS_SELECTOR, "JS_SplitEqually_CheckoutDetail_TotalPeople")
    SPLIT_EQUALLY_NEXT_PAYMENT = (By.XPATH, "//button[contains(@class, 'btn') and contains(., 'Process Next Payment')]")
    SPLIT_INPUT = (By.CSS_SELECTOR, "#JS_SplitByAmount_Input_CheckOutDetail")
    SPLIT_BY_EXACT_AMOUNT_INPUT_FIELD = (By.CSS_SELECTOR, "#JS_SplitByAmount_Input_CheckOutDetail")
    KITCHEN_MESSAGE = (By.XPATH, "//h2[contains(text(), 'Please wait while we send')]")
    SPLIT_FIELD_VALUE = (By.CSS_SELECTOR, ".qty-count")
    SPLIT_TIP_VALUE = (By.XPATH, "(//p[@class='JS_SplitByAmount_ValueShow_CheckoutDetail'])[2]")
    SPLIT_EQUALLY_TIP_VALUE = (By.XPATH, "//*[text()=' Tip ']/following-sibling::p[1]")


class FreedomPayLocators:
    ANCHOR_ELEMENT = (By.XPATH, '//h4[contains(text(), "Select Payment Type")]')
    CARD_HOLDER_NAME = (By.XPATH, "//input[@name='cardholderName']")
    IFRAME = (By.ID, "hpc--card-frame")
    CARD_NUMBER = (By.XPATH, "//input[@name='CardNumber']")
    CARD_DATE = (By.CSS_SELECTOR, "#ExpirationDate")
    SECURITY_CODE = (By.CSS_SELECTOR, "#SecurityCode")
    POSTAL_CODE = (By.CSS_SELECTOR, "#PostalCode")
    MAKE_PAYMENT = (By.CSS_SELECTOR, ".fw-hms-btn")
    PAYMENT_IN_PROGRESS = (By.CSS_SELECTOR, "div.loader-box")
    LOADER = (By.CSS_SELECTOR, "div.loader")
    KITCHEN_MESSAGE = (By.XPATH, "//h2[contains(text(), 'Please wait while we send')]")

class ConfirmationPageLocators:
    THANK_YOU = (By.CSS_SELECTOR, ".titel")








