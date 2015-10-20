from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from selenium_tests.account_admin.page_objects.account_admin_base_page_object import AccountAdminBasePage
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject


class AccountAdminDashboardPageLocators(object):
    PAGE_TITLE = (By.CSS_SELECTOR, "h1")
    COURSE_INFO_LINK = (By.PARTIAL_LINK_TEXT, "Course Information")


class AccountAdminDashboardPage(AccountAdminBasePage):

    def is_loaded(self):
        """
        Verifies that the page is loaded correctly by validating the title
        :returns True if title matches else a RuntimeError is raised
        """
        # Note: this just checks that the  title is displayed;
        # it doesn't guaranteed that everything we expect is rendered on the
        # page, because angular fetches the data asynchronously

        title = None
        try:
            title = self.get_page_title()
        except NoSuchElementException:
            return False

        if title and 'Administration Tasks' in title.get_attribute('textContent'):
            return True
        else:
            raise RuntimeError(
                'Could not determine if dashboard page loaded as expected;'
                'title element was found but did not contain expected text'
            )

    def get_page_title(self):
        element = self.find_element(*AccountAdminDashboardPageLocators.PAGE_TITLE)
        return element

    def get_course_info_link(self):
        element = self.find_element(*AccountAdminDashboardPageLocators.COURSE_INFO_LINK)
        return element

    def select_course_info_link(self):
        """
        select the course info link element and click it
        :returns CourseSearchPageObject
        """
        self.focus_on_tool_frame()
        self.find_element(*AccountAdminDashboardPageLocators.COURSE_INFO_LINK).click()
        return CourseSearchPageObject(self._driver)

    def is_course_info_block_present(self):
        """
        check if course info block element is present
        :return:boolean
        """
        course_info_link = self.get_course_info_link()
        link_text = 'Course Information'

        if link_text in course_info_link.text:
            return True
        else:
            raise RuntimeError(
                'Could not find the  Course Info link on the page as expected'
            )
