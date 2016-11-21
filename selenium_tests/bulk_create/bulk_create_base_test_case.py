from django.conf import settings
from os.path import abspath, dirname, join
from urlparse import urljoin

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object \
    import PinLoginPageObject

CANVAS_PERMISSION_ROLES = join(dirname(abspath(__file__)),
                               'test_data', 'roles_access.xlsx')


class BulkCreateBaseTestCase(BaseSeleniumTestCase):

    @classmethod
    def setUpClass(cls):
        super(BulkCreateBaseTestCase, cls).setUpClass()
        cls.username = settings.SELENIUM_CONFIG.get('selenium_username')
        cls.password = settings.SELENIUM_CONFIG.get('selenium_password')
        cls.canvas_base_url = settings.SELENIUM_CONFIG.get('canvas_base_url')
        cls.tool_relative_url = settings.SELENIUM_CONFIG['bulk_create']['url']
        cls.base_url = urljoin(cls.canvas_base_url, cls.tool_relative_url)
        cls.test_data = settings.SELENIUM_CONFIG['bulk_create']['test_data']
        cls.test_data_course1 = settings.SELENIUM_CONFIG[
            'bulk_create']['test_data']['course_with_registrar_code_display']
        cls.test_data_course2 = settings.SELENIUM_CONFIG[
            'bulk_create']['test_data']['course_without_registrar_code_display']
        # Login to PIN
        cls.driver.get(cls.base_url)

        login_page = PinLoginPageObject(cls.driver)
        if login_page.is_loaded():
            print "Logging in XID user {}".format(cls.username)
            login_page.login_xid(cls.username, cls.password)
        else:
            print '(XID user {} already logged in)'.format(cls.username)
