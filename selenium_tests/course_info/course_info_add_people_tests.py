import unittest

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object import AccountAdminDashboardPage
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject
from selenium_tests.course_info.page_objects.course_people_page_object import \
    CoursePeoplePageObject

COURSE_INSTANCE_ID = '347547'
COURSE_USER_ID = "30833767"
USER_ROLE = "Teacher"


class CourseInfoAddTest(CourseInfoBaseTestCase):

    def test_people_search(self):
        """verify the people search functionality"""
        # initialize
        parent_page = AccountAdminDashboardPage(self.driver)
        # navigate to course info page
        parent_page.select_course_info_link()

        # check if page is loaded(which will also set the focus on the tool), before selecting search terms
        search_page = CourseSearchPageObject(self.driver)
        search_page.is_loaded()

        # submit a search term, a course instance id in this case
        search_page.submit_search(COURSE_INSTANCE_ID)

        # click on course link to view list of people in course
        search_page.select_course(cid=COURSE_INSTANCE_ID)

        # search for a user
        people_page = CoursePeoplePageObject(self.driver)
        people_page.search_for_a_user(COURSE_USER_ID)

        # assert that user is found
        # TODO - look for tag uib-alert type=success or look up by univ_id

    @unittest.skip("repetitive adding of the same user is not allowed and delete function is not in place yet")
    def test_add_user_found_on_page(self):
        """verify the people search functionality"""
        # initialize
        parent_page = AccountAdminDashboardPage(self.driver)
        # navigate to course info page
        parent_page.select_course_info_link()

        # check if page is loaded(which will also set the focus on the tool), before selecting search terms
        search_page = CourseSearchPageObject(self.driver)
        search_page.is_loaded()

        # submit a search term, a course instance id in this case
        search_page.submit_search(COURSE_INSTANCE_ID)

        # click on course link to view list of people in course
        search_page.select_course_id()

        # add user to the course
        search_page.add_user_to_course(COURSE_USER_ID, USER_ROLE)

        # verify that user was added successfully

        # TODO:  Verify success text

        # assert that this person is in this course
        self.assertTrue(search_page.find_user_added_on_page(COURSE_USER_ID))
