from selenium.webdriver.common.by import By

from selenium_tests.term_tool.page_objects.term_tool_base_page_object import TermToolBasePageObject


class TermToolShoppingExcludePageLocators (TermToolBasePageObject):
    COURSE_INSTANCE_ID = '331527'
    TERM_TOOL_EXCLUDE_SHOPPING_SEARCH_INPUT = (By.CSS_SELECTOR, "input[type=\"search\"]")
    TERM_TOOL_SELECT_CI_ID = (By.ID, "input-course-instance-331527")


class TermToolShoppingExcludePageObject(TermToolBasePageObject):

    def select_disable_auth_user_access(self):
        search_element = self.find_element(*TermToolShoppingExcludePageLocators.TERM_TOOL_EXCLUDE_SHOPPING_SEARCH_INPUT)
        search_element.clear()
        # This searches for a particular course instance id, defined in the PageLocators above.
        search_element.send_keys(TermToolShoppingExcludePageLocators.COURSE_INSTANCE_ID)
        # This selects the course instance on the exclude_shopping page
        ci_selection = self.find_element(*TermToolShoppingExcludePageLocators.TERM_TOOL_SELECT_CI_ID)
        # If the course instance is already selected
        if ci_selection.is_selected():
            print "This course is already selected."
        else:
            #  If course has not been exclude from shopping, click the button to exclude.
            ci_selection.click()

    def check_course_is_selected(self):
            course_selected = self.find_element(*TermToolShoppingExcludePageLocators.TERM_TOOL_SELECT_CI_ID)
            if course_selected.is_selected():
                print "This course is excluded from shopping"
                return True
            else:
                return False
