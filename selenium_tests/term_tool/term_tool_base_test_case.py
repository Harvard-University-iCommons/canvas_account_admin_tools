from urlparse import urljoin
from django.conf import settings

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object \
    import PinLoginPageObject
from selenium_tests.term_tool.page_objects.index_page_page_object \
    import IndexPageObject


class TermToolBaseTestCase(BaseSeleniumTestCase):
    """Term Tool base test case, all other tests will subclass this class"""

    @classmethod
    def setUpClass(cls):
        """
        setup values for the tests
        """
        super(TermToolBaseTestCase, cls).setUpClass()
        cls.USERNAME = settings.SELENIUM_CONFIG.get('selenium_username')
        cls.PASSWORD = settings.SELENIUM_CONFIG.get('selenium_password')
        cls.TERM_TOOL_URL = '{}{}'.format(
            settings.SELENIUM_CONFIG['project_base_url'],
            settings.SELENIUM_CONFIG['exclude_courses_relative_url']
        )

        #  Login to Term Tool Index Page
        cls.term_tool_index_page = IndexPageObject(cls.driver)
        cls.term_tool_index_page.get(cls.TERM_TOOL_URL)
        login_page = PinLoginPageObject(cls.driver)
        # TODO: check that the term_tool_index_page.is_loaded()
        if login_page.is_loaded():
            login_page.login_xid(cls.USERNAME, cls.PASSWORD)
        else:
            print '(User {} already logged in to PIN)'.format(cls.USERNAME)
