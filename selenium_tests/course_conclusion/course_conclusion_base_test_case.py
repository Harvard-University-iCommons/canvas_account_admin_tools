from os.path import abspath, dirname, join

from selenium_tests.canvas_account_admin_tools_base_test_case \
    import AccountAdminBaseTestCase
from selenium_tests.course_conclusion.page_objects\
    .course_conclusion_main_page import CourseConclusionMainPage

PERMISSIONS_ROLES = join(dirname(abspath(__file__)), 'test_data',
                         'permissions_roles_access.xlsx')


class CourseConclusionBaseTestCase(AccountAdminBaseTestCase):

    def setUp(self):
        super(CourseConclusionBaseTestCase, self).setUp()

        # instantiate
        self.main_page = CourseConclusionMainPage(self.driver)

        # initialize
        if not self.acct_admin_dashboard_page.is_loaded():
            self.acct_admin_dashboard_page.get(self.TOOL_URL)

        # navigate to cross-list tool
        self.acct_admin_dashboard_page.select_conclude_courses_link()

        # check if page is loaded (which will also set the focus on the tool)
        self.assertTrue(self.main_page.is_loaded())
