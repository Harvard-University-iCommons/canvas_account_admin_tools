from django.conf import settings
from os.path import abspath, dirname, join
from urlparse import urljoin

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object \
    import PinLoginPageObject
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object \
    import AccountAdminDashboardPage
from selenium_tests.course_info.page_objects.course_info_search_page_object \
    import CourseSearchPageObject
from selenium_tests.course_info.page_objects.course_people_page_object \
    import CoursePeoplePageObject


# Common files used for all Manage People test cases
TEST_USERS_WITH_ROLES = join(dirname(abspath(__file__)),
    'test_data', 'admin_console_roles.xlsx')

class CourseInfoBaseTestCase(BaseSeleniumTestCase):

    people_page = None
    search_page = None
    test_settings = None

    @classmethod
    def setUpClass(cls):
        super(CourseInfoBaseTestCase, cls).setUpClass()

        cls.USERNAME = settings.SELENIUM_CONFIG.get('selenium_username')
        cls.PASSWORD = settings.SELENIUM_CONFIG.get('selenium_password')

        cls.CANVAS_BASE_URL = settings.SELENIUM_CONFIG.get('canvas_base_url')
        cls.test_settings = settings.SELENIUM_CONFIG['course_info_tool']
        cls.TOOL_RELATIVE_URL = cls.test_settings['relative_url']
        cls.TOOL_URL = urljoin(cls.CANVAS_BASE_URL, cls.TOOL_RELATIVE_URL)

        cls.course_info_parent_page = AccountAdminDashboardPage(cls.driver)
        cls.course_info_parent_page.get(cls.TOOL_URL)
        login_page = PinLoginPageObject(cls.driver)
        if login_page.is_loaded():
            login_page.login_xid(cls.USERNAME, cls.PASSWORD)
        else:
            print '(User {} already logged in to PIN)'.format(cls.USERNAME)
            
        cls.search_page = CourseSearchPageObject(cls.driver)
        cls.people_page = CoursePeoplePageObject(cls.driver)

    def setUp(self):
        super(CourseInfoBaseTestCase, self).setUp()

        # initialize
        if not self.course_info_parent_page.is_loaded():
            self.course_info_parent_page.get(self.TOOL_URL)

        # navigate to course info page
        self.course_info_parent_page.select_course_info_link()

        # check if page is loaded (which will also set the focus on the tool)
        self.assertTrue(self.search_page.is_loaded())

    @classmethod
    def search_for_course(cls, type=None, school=None, term=None, year=None,
                          search_term=''):
        if type:
            cls.search_page.select_course_type(type)
        if school:
            cls.search_page.select_school(school)
        if term:
            cls.search_page.select_term(term)
        if year:
            cls.search_page.select_year(year)
        cls.search_page.submit_search(search_term)

    @classmethod
    def _load_test_course(cls):
        course = cls.test_settings['test_course']

        cls.search_for_course(
            type=course['type'], school=course['school'], term=course['term'],
            year=course['year'], search_term=course['cid'])

        # click on course link to view list of people in course
        cls.search_page.select_course(cid=course['cid'])
