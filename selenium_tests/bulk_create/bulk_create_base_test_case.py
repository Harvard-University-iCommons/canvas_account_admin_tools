from django.conf import settings
from os.path import abspath, dirname, join
from urlparse import urljoin

from selenium_tests.canvas_account_admin_tools_base_test_case \
    import AccountAdminBaseTestCase
from selenium_tests.bulk_create.page_objects.index_page import IndexPageObject

CANVAS_PERMISSION_ROLES = join(dirname(abspath(__file__)),
                               'test_data', 'roles_access.xlsx')


class BulkCreateBaseTestCase(AccountAdminBaseTestCase):

    def setUp(self):

        super(AccountAdminBaseTestCase, self).setUp()

        self.test_data = settings.SELENIUM_CONFIG['bulk_create']['test_data']
        self.test_data_course1 = settings.SELENIUM_CONFIG['bulk_create'][
            'test_data']['course_with_registrar_code_display']
        self.test_data_course2 = settings.SELENIUM_CONFIG['bulk_create'][
            'test_data']['course_without_registrar_code_display']
        self.main_page = IndexPageObject(self.driver)


        # initialize
        if not self.acct_admin_dashboard_page.is_loaded():
            self.acct_admin_dashboard_page.get(self.TOOL_URL)

        # navigate to the create canvas site card on dashboard
        self.acct_admin_dashboard_page.select_create_canvas_site_link()

        # check if page is loaded (which will also set the focus on the tool)
        self.assertTrue(self.main_page.is_loaded())


