from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from selenium_common.base_page_object import BasePageObject


class Locators:
    TITLE = (By.CSS_SELECTOR, 'a.navbar-brand')
    SCHOOL_SELECT = (By.CSS_SELECTOR, 'select[name="school"]')
    TABLE = (By.CSS_SELECTOR, 'table')
    # matches tr that contains the information for course instance 'cid'
    CID_ROW_XPATH = './/tr[td[text()="{cid}"]]'


class IndexPage(BasePageObject):

    def is_loaded(self):
        title = self.find_element(*Locators.TITLE)
        return title.text == 'Course Conclusion'

    def select_school(self, school_display_text):
        school_select = Select(self.find_element(*Locators.SCHOOL_SELECT))
        school_select.select_by_visible_text(school_display_text)
        return school_select

    def get_data_for_course(self, course_instance_id):
        """
        returns an ordered list of values representing course information as
        shown in the row of the course conclusion information table that
        matches the course_instance_id argument passed in
        """
        table = self.find_element(*Locators.TABLE)
        cid_xpath = Locators.CID_ROW_XPATH.format(cid=course_instance_id)
        cid_row = table.find_element(By.XPATH, cid_xpath)
        cells = cid_row.find_elements_by_tag_name('td')
        return [c.text for c in cells]
