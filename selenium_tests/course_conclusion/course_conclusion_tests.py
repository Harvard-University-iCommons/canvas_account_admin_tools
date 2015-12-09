from django.conf import settings

from selenium_tests.course_conclusion.course_conclusion_base_test_case import CourseConclusionBaseTestCase
from selenium_tests.course_conclusion.page_objects.index_page import IndexPage


class CourseConclusionTests(CourseConclusionBaseTestCase):
    def test_tool_loads(self):
        index_page = IndexPage(self.driver)
        index_page.get(self.BASE_URL)
        self.assertTrue(index_page.is_loaded())

    def test_term_column_showing(self):
        """
        TLT-2015: Data shown in table on course conclusion index page should
        include term information
        """
        index_page = IndexPage(self.driver)
        test_data = settings.SELENIUM_CONFIG['course_conclusion']
        index_page.select_school(test_data['school'])
        expected_course_data = test_data['course_data']
        course_data = index_page.get_data_for_course(test_data['cid'])
        self.assertEqual(course_data, expected_course_data)
