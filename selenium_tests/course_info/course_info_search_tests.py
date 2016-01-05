from django.conf import settings

from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object \
    import AccountAdminDashboardPage
from selenium_tests.course_info.page_objects.course_info_search_page_object \
    import CourseSearchPageObject


class CourseInfoSearchTest(CourseInfoBaseTestCase):

    def test_course_search(self):
        """verify the course search functionality"""
        search_page = CourseSearchPageObject(self.driver)

        course = settings.SELENIUM_CONFIG['course_info_tool']['test_course']

        self.search_for_course(
            type=course['type'], school=course['school'], term=course['term'],
            year=course['year'], search_term=course['cid'])

        self.assertTrue(search_page.is_course_displayed(cid=course['cid']))