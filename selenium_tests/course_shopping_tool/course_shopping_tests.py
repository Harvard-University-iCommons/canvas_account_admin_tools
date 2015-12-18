from urlparse import urljoin
from django.conf import settings

from selenium_tests.course_shopping_tool.course_shopping_base_test_case \
    import CourseShoppingBaseTestCase
from selenium_tests.course_shopping_tool.page_objects\
    .shopping_base_page_object import CourseShoppingPageObject


class CourseShoppingTests(CourseShoppingBaseTestCase):

    def test_is_loaded(self):
        shopping_page = CourseShoppingPageObject(self.driver)
        shopping_url = urljoin(
            settings.SELENIUM_CONFIG.get('canvas_base_dev_url'),
            settings.SELENIUM_CONFIG.get('canvas_shopping_relative_url'))
        shopping_page.get(shopping_url)
        self.assertTrue(shopping_page.is_loaded())
