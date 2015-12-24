from selenium_tests.course_shopping_tool.course_shopping_base_test_case \
    import CourseShoppingBaseTestCase
from selenium_tests.course_shopping_tool.page_objects.shopping_page_object \
    import CourseShoppingPageObject

class CourseShoppingTests(CourseShoppingBaseTestCase):

    def test_shopping_banner_on(self):
        '''
        Test that the shopping banner appears by checking for shopping options
        '''
        shopping_page = CourseShoppingPageObject(self.driver)
        self.assertTrue(shopping_page.is_shopping_available(),
                        'Shopping option is not available')

