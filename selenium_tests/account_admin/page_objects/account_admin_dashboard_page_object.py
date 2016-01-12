from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from selenium_tests.account_admin.page_objects.account_admin_base_page_object \
    import AccountAdminBasePage


class AccountAdminDashboardPageLocators(object):
    PAGE_TITLE = (By.XPATH, "//h3[contains(.,'Admin Console')]")
    COURSE_INFO_LINK = (By.XPATH, "//a[contains(.,'Find Course Info')]")


class AccountAdminDashboardPage(AccountAdminBasePage):

    def is_loaded(self):
        """
        Verifies that the page is loaded correctly by validating the title
        """
        # Note: this just checks that the  title is displayed;
        # it doesn't guaranteed that everything we expect is rendered on the
        # page, because angular fetches the data asynchronously

        try:
            self.find_element(*AccountAdminDashboardPageLocators.PAGE_TITLE)
        except NoSuchElementException:
            return False
        return True

    def select_course_info_link(self):
        """
        select the course info link element and click it
        """
        self.focus_on_tool_frame()
        self.find_element(
            *AccountAdminDashboardPageLocators.COURSE_INFO_LINK).click()
