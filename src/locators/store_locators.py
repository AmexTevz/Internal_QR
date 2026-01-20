from selenium.webdriver.common.by import By

class MenuPageLocators:
    RESTAURANT_NAME = (By.CSS_SELECTOR, '#resturant-name')
    ITEMS = (By.CSS_SELECTOR, '.menu-list-row')
    MENU_ITEMS = (By.CSS_SELECTOR, '.menu-list-row')
    MENU_ITEM_TITLE = (By.CSS_SELECTOR, '.menu-list-title')
    MENU_ITEM_DESCRIPTION = (By.CSS_SELECTOR, '.menu-list-description')
    ITEM_NAME = (By.CSS_SELECTOR, '.mod-title')
    ITEM_PRICE = (By.CSS_SELECTOR, '.mod-cta-price')
    ITEM_COUNT_BADGE = ()
    SEARCH_BUTTON = (By.CSS_SELECTOR, '.lucide-search')
    SEARCH_INPUT = (By.CSS_SELECTOR, '#search-text-input')
    SEARCH_CANCEL = (By.CSS_SELECTOR, '.menu-search-cancel')
    CHECK_NUMBER = (By.CSS_SELECTOR, 'div.order-no')
    CUSTOMER_NAME = (By.CSS_SELECTOR, 'span.capitalize')
    TABLE_NUMBER_MENU_PAGE = (By.CSS_SELECTOR, ".basket-table-text")
    MODIFIER_NAME = (By.CSS_SELECTOR, '.mod-option-label')
    MODIFIER_PRICE = (By.CSS_SELECTOR, '.mod-option-price')
    ADD_BUTTON = (By.CSS_SELECTOR, ".mod-cta-btn")
    VIEW_BASKET = (By.CSS_SELECTOR, ".menu-bottom-bar-button")
    LOGO = (By.CSS_SELECTOR, '.menu-header-logo')
    QTY_PLUS_BUTTON = (By.ID, "qty-plus-button")
    QTY_MINUS_BUTTON = (By.ID, "qty-minus-button")
    CART_BADGE = (By.CSS_SELECTOR, ".menu-cart-badge")
    CART_ICON = (By.CSS_SELECTOR, "#shopping-basket-img")
    LANGUAGE_ICON = (By.CSS_SELECTOR, "#global-icon-img")
    CLOSE_BUTTON = (By.CSS_SELECTOR, '.mod-close-btn')
    ACTIVE_CATEGORY_SLIDER = (By.CSS_SELECTOR, '.menu-category-pill--active')
    MENU_SECTION_TITLE = (By.CSS_SELECTOR, '.menu-section-title')
    CATEGORY_PILLS = (By.CSS_SELECTOR, '.menu-category-pill')
    CATEGORY_LABEL = (By.CSS_SELECTOR, '.menu-category-label')
    NO_RESULTS_FOUND = (By.CSS_SELECTOR, ".menu-empty")
    LOADER = (By.CSS_SELECTOR, '.spinner-border')

    INITIAL_BUTTON = (By.CSS_SELECTOR, '#goto-main-page-button')

    def category_button_by_id(category_id):
        return By.ID, category_id

    @staticmethod
    def item_count_badge(item_id):
        return By.CSS_SELECTOR, f"#add-item-{item_id} .menu-item-add-count"

class CartPageLocators:
    TABLE_NUMBER_CART = (By.CSS_SELECTOR, "#cart-table-number")
    CHECK_NUMBER_CART = (By.CSS_SELECTOR, "#cart-check-number")
    PLACE_ORDER = (By.XPATH, "//button[text()='Place order']")
    CONTINUE_ORDERING = (By.CSS_SELECTOR, "#continue-ordering")
    ORDER_MORE_BUTTON = (By.CSS_SELECTOR, "#add-more-button")
    CHECKOUT_BUTTON = (By.XPATH, "//button[text()='Checkout']")
    LOADER = (By.CSS_SELECTOR, '.spinner-border')
    NO_CHECK_MESSAGE = (By.CSS_SELECTOR, ".error-title")
    TRY_AGAIN_BUTTON = (By.CSS_SELECTOR, "#try-again-button")
    BROWSE_MENU_BUTTON = (By.CSS_SELECTOR, "#browse-menu-button")

class CheckoutPageLocators:
    CHECK_NUMBER_CHECKOUT = (By.CSS_SELECTOR, "#dinein-check-number")
    TABLE_NUMBER_CHECKOUT = (By.CSS_SELECTOR, "#dinein-table-number")
    SUBTOTAL_VALUE = (By.CSS_SELECTOR, "#Subtotal-value")
    TOTAL_VALUE = (By.CSS_SELECTOR, "#Total-value")
    TAXES_VALUE = (By.CSS_SELECTOR, "#Taxes-value")
    TIPS_VALUE = (By.CSS_SELECTOR, "#Tip-value")
    SERVICE_CHARGE_VALUE = (By.XPATH, "//span[contains(@id, 'Object]-value')]")
    DONATION_VALUE = (By.CSS_SELECTOR, "#Donation-value")
    CHARITY_TOGGLE = (By.CSS_SELECTOR, "#charity-input")
    CHARITY_AMOUNT = (By.CSS_SELECTOR, "#roundup-amount")
    TIP_22 = (By.CSS_SELECTOR, "#tip-22")
    TIP_20 = (By.CSS_SELECTOR, "#tip-20")
    TIP_18 = (By.CSS_SELECTOR, "#tip-18")
    TIP_CUSTOM = (By.CSS_SELECTOR, "#tip-custom")
    TIP_CUSTOM_INPUT = (By.CSS_SELECTOR, "#custom-tip-input")
    CASH_TIP = (By.CSS_SELECTOR, "#tip-cash")
    PAY_BUTTON = (By.CSS_SELECTOR, "#dinein-pay-button")
    NO_THANKS = (By.CSS_SELECTOR, ".rounded-pill")
    UPSELL_ITEMS = (By.CSS_SELECTOR, "#add-button")
    UPSELL_ITEM_PRICE = (By.CSS_SELECTOR, '.mod-cta-price')
    UPSELL_ITEM_NAME = (By.CSS_SELECTOR, '.mod-title')
    ADD_BUTTON = (By.CSS_SELECTOR, "#add-for-button")
    LOADER = (By.CSS_SELECTOR, '.spinner-border')


class PaymentPageLocators:
    ANCHOR_ELEMENT = (By.XPATH, 'input[placeholder="Name"]')
    CARD_HOLDER_NAME = (By.CSS_SELECTOR, 'input[placeholder="Name"]')
    IFRAME = (By.ID, "hpc--card-frame")
    CARD_NUMBER = (By.XPATH, "//input[@name='CardNumber']")
    CARD_DATE = (By.CSS_SELECTOR, "#ExpirationDate")
    SECURITY_CODE = (By.CSS_SELECTOR, "#SecurityCode")
    POSTAL_CODE = (By.CSS_SELECTOR, "#PostalCode")
    MAKE_PAYMENT = (By.XPATH, "//button[text()='Pay now']")
    TOTAL_AMOUNT = (By.XPATH, "//p[starts-with(text(), '$')]")
    LOADER = (By.CSS_SELECTOR, '.loader')

class ConfirmationPageLocators:
    CONFIRMATION_MESSAGE = (By.CSS_SELECTOR, "#receipt-success-title")
    ORDER_NUMBER = (By.CSS_SELECTOR, "#receipt-order-number")
    SUBTOTAL = (By.CSS_SELECTOR, "#receipt-subtotal")
    TAX = (By.CSS_SELECTOR, "#receipt-tax")
    TIP = (By.CSS_SELECTOR, "#receipt-tip")
    DONATION = (By.CSS_SELECTOR, "#receipt-donation")
    CHARITY = (By.CSS_SELECTOR, "#receipt-service-charge")
    SERVICE_CHARGE = (By.CSS_SELECTOR, "#receipt-service-charge")
    TOTAL = (By.CSS_SELECTOR, "#receipt-total")
    EMAIL_BUTTON = (By.CSS_SELECTOR, ".receipt-email-btn")
    EMAIL_FIELD = (By.CSS_SELECTOR, ".toast-input")
    EMAIL_SEND_BUTTON = (By.CSS_SELECTOR, ".toast-btn-primary")
    CANCEL_BUTTON = (By.CSS_SELECTOR, "toast-btn-secondary")
    EMAIL_CONFIRMATION = (By.CSS_SELECTOR, ".toast-message")











