from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from selenium_tests.course_info.page_objects.course_info_base_page_object \
    import CourseInfoBasePageObject


class Locators(object):
    COURSE_PEOPLE_LINK = (By.ID, "people-link")


class CourseInfoDetailPageObject(CourseInfoBasePageObject):

    def get_people_link(self):
        """
        This locates the People link and clicks it
        """
        try:
            element = WebDriverWait(
                self._driver, 30).until(
                EC.element_to_be_clickable(Locators.COURSE_PEOPLE_LINK))
            self._driver.save_screenshot("people.jpeg")
        except TimeoutException:
            return None

        return element.click()

