from selenium_tests.course_shopping_tool.course_shopping_base_test_case import CourseShoppingBaseTestCase
from selenium_tests.course_shopping_tool.page_objects.shopping_page_object import CourseShoppingPageObject

class CourseShoppingTests(CourseShoppingBaseTestCase):

    def shopping_page_is_loaded_test(self):
        shopping_page = CourseShoppingPageObject(self.driver)
        self.assertTrue(shopping_page.is_loaded(), 'Shopping page is not loaded, shopping is not ON')

    def shopping_is_on_test(self):
        shopping_page = CourseShoppingPageObject(self.driver)
        self.assertTrue(shopping_page.is_shopping_available(), 'Shopping option is not available, shopping is not ON')

