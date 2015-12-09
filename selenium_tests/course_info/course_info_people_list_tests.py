from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object import AccountAdminDashboardPage
COURSE_INSTANCE_ID = '347547'

class CourseInfoPeopleListTest(CourseInfoBaseTestCase):

    def test_people_list_page_loaded(self):
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

        # assert that this person is in this course
        self.assertTrue(search_page.find_test_person_on_page())
