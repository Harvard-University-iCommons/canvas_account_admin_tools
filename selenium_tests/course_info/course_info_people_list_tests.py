from django.conf import settings

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object import AccountAdminDashboardPage
from selenium_tests.course_info.page_objects.course_people_page_object import \
    CoursePeoplePageObject


class CourseInfoPeopleListTest(CourseInfoBaseTestCase):

    def test_people_list_page_loaded(self):
        """verify the people search functionality"""
        # initialize
        parent_page = AccountAdminDashboardPage(self.driver)
        # navigate to course info page
        parent_page.select_course_info_link()

        # check if page is loaded (which will also set the focus on the tool),
        # before selecting search terms
        search_page = CourseSearchPageObject(self.driver)
        search_page.is_loaded()

        course = settings.SELENIUM_CONFIG['course_info_tool']['test_course']
        # select a school, year, term and course type
        search_page.select_course_type(course['type'])
        search_page.select_school(course['school'])
        search_page.select_term(course['term'])
        search_page.select_year(course['year'])

        # submit a search term, a course instance id in this case
        search_page.submit_search(course['cid'])

        # click on course link to view list of people in course
        search_page.select_course(cid=course['cid'])

        user = settings.SELENIUM_CONFIG['course_info_tool']['test_user']
        people_page = CoursePeoplePageObject(self.driver)
        # assert that an expected enrollment is present
        self.assertTrue(people_page.is_loaded())
        self.assertTrue(people_page.is_person_on_page(user['user_id']))
