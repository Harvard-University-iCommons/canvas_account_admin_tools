from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object import PinLoginPageObject
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object import AccountAdminDashboardPage

from urlparse import urljoin
from django.conf import settings
from selenium_tests.course_info.page_objects.course_info_search_page_object import \
    CourseSearchPageObject


class CourseInfoBaseTestCase(BaseSeleniumTestCase):

    _search_page = None

    @classmethod
    def setUpClass(cls):
        super(CourseInfoBaseTestCase, cls).setUpClass()

        cls.USERNAME = settings.SELENIUM_CONFIG.get('selenium_username')
        cls.PASSWORD = settings.SELENIUM_CONFIG.get('selenium_password')

        cls.CANVAS_BASE_URL = settings.SELENIUM_CONFIG.get('canvas_base_url')
        cls.TOOL_RELATIVE_URL = settings.SELENIUM_CONFIG['course_info_tool']['relative_url']
        cls.TOOL_URL = urljoin(cls.CANVAS_BASE_URL, cls.TOOL_RELATIVE_URL)

        cls.course_info_parent_page = AccountAdminDashboardPage(cls.driver)
        cls.course_info_parent_page.get(cls.TOOL_URL)
        login_page = PinLoginPageObject(cls.driver)
        if login_page.is_loaded():
            login_page.login_huid(cls.USERNAME, cls.PASSWORD)
        else:
            print '(User {} already logged in to PIN)'.format(cls.USERNAME)

    def setUp(self):
        super(CourseInfoBaseTestCase, self).setUp()

        # initialize
        parent_page = AccountAdminDashboardPage(self.driver)
        # navigate to course info page
        parent_page.select_course_info_link()

        # check if page is loaded (which will also set the focus on the tool)
        self._search_page = CourseSearchPageObject(self.driver)
        self.assertTrue(self._search_page.is_loaded())

    def search_for_course(self, type=None, school=None, term=None, year=None,
                          search_term=''):
        if type:
            self._search_page.select_course_type(type)
        if school:
            self._search_page.select_school(school)
        if term:
            self._search_page.select_term(term)
        if year:
            self._search_page.select_year(year)
        self._search_page.submit_search(search_term)

