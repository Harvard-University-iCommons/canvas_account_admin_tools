from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium_tests.course_info.page_objects.course_info_base_page_object import CourseInfoBasePageObject
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject



class CourseInfoParentPageLocators(object):
    PAGE_TITLE = (By.CSS_SELECTOR, "h1")
    COURSE_INFO_LINK = (By.PARTIAL_LINK_TEXT, "Course Information")


class CourseInfoParentPage(CourseInfoBasePageObject):

    def is_loaded(self):
        # Note: this just checks that the breadcrumb title is displayed;
        # it doesn't guaranteed that everything we expect is rendered on the
        # page, because angular fetches the data asynchronously

        # frame context stickiness is a bit flaky for some reason, so make sure
        # we're in the tool_content frame context before checking for elements
        # self.focus_on_tool_frame()
        title = None
        try:
            title = self.find_element(*CourseInfoParentPageLocators.PAGE_TITLE)
        except NoSuchElementException:
            return False

        if title and 'Administration Tasks' in title.get_attribute('textContent'):
            return True
        else:
            raise RuntimeError(
                'Could not determine if Course Info  base page loaded as expected;'
                'title element was found but did not contain expected text'
            )

    def get_page_title(self):
        element = self.find_element(*CourseInfoParentPageLocators.PAGE_TITLE)
        return element

    def get_course_info_link(self):
        element = self.find_element(*CourseInfoParentPageLocators.COURSE_INFO_LINK)
        return element

    def select_course_info_link(self):
        """ select the course info link element and click it
        :returns CourseSearchPageObject
        """
        self.focus_on_tool_frame()
        self.find_element(*CourseInfoParentPageLocators.COURSE_INFO_LINK).click()
        return CourseSearchPageObject(self._driver)

