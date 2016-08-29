from os.path import abspath, dirname, join

from selenium_tests.canvas_account_admin_tools_base_test_case \
    import AccountAdminBaseTestCase
from selenium_tests.search_people.page_objects.search_people_base_page_object\
    import SearchPeoplePageObject


PERMISSIONS_ROLES = join(dirname(abspath(__file__)), 'test_data',
                         'permissions_roles_access.xlsx')


class SearchPeopleBaseTestCase(AccountAdminBaseTestCase):

    def setUp(self):
        super(SearchPeopleBaseTestCase, self).setUp()

        # instantiate
        self.main_page = SearchPeoplePageObject(self.driver)

        # initialize
        if not self.acct_admin_dashboard_page.is_loaded():
            self.acct_admin_dashboard_page.get(self.TOOL_URL)

        # navigate to Search People tool
        self.acct_admin_dashboard_page.select_search_people_link()

        # check if page is loaded (which will also set the focus on the tool)
        self.assertTrue(self.main_page.is_loaded())
