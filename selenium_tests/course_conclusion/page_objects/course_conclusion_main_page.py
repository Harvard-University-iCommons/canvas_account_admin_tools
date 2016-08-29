from selenium.webdriver.common.by import By

from selenium_tests.account_admin.page_objects.account_admin_base_page_object \
    import AccountAdminBasePage


class Locators(object):
    MAIN_PAGE_LOCATOR = (By.XPATH, "//a[contains(.,'Course Conclusion')]")


class CourseConclusionMainPage(AccountAdminBasePage):
    page_loaded_locator = Locators.MAIN_PAGE_LOCATOR
