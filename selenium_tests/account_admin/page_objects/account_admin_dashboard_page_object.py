from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from selenium_tests.account_admin.page_objects.account_admin_base_page_object \
    import AccountAdminBasePage


class AccountAdminDashboardPageLocators(object):
    # if PAGE_TITLE uses contains() it will match for sub-pages as well, so
    # use text() for exact match (should only match on dashboard page)
    PAGE_TITLE = (By.XPATH, '//h3[text()="Admin Console"]')
    CREATE_CANVAS_SITE_LINK = (By.XPATH, "//a[contains(.,'Create Canvas "
                                        "Sites')]")
    COURSE_INFO_LINK = (By.XPATH, "//a[contains(.,'Search Courses')]")
    CROSS_LISTING_LINK = (By.XPATH, "//a[contains(., 'Cross-list Courses')]")
    PUBLISH_COURSES_LINK = (By.XPATH, "//a[contains(., 'Publish Courses')]")


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

    def cross_listing_button_is_displayed(self):
        """
        Verifies that the cross listing div is displayed or not
        """
        try:
            self.find_element(*AccountAdminDashboardPageLocators.CROSS_LISTING_LINK)
        except NoSuchElementException:
            return False
        return True

    def select_course_info_link(self):
        """
        select the course info list link element and click it
        """
        self.focus_on_tool_frame()
        self.find_element(
            *AccountAdminDashboardPageLocators.COURSE_INFO_LINK).click()

    def select_create_canvas_site_link(self):
        """
        select the bulk create card and and click it
        """
        self.focus_on_tool_frame()
        self.find_element(
            *AccountAdminDashboardPageLocators.CREATE_CANVAS_SITE_LINK).click()

    def select_cross_listing_link(self):
        """
        select the cross list link element and click it
        """
        self.focus_on_tool_frame()
        self.find_element(
            *AccountAdminDashboardPageLocators.CROSS_LISTING_LINK).click()

    def select_publish_courses_link(self):
        """
        select the cross list link element and click it
        """
        self.focus_on_tool_frame()
        self.find_element(
            *AccountAdminDashboardPageLocators.PUBLISH_COURSES_LINK).click()

