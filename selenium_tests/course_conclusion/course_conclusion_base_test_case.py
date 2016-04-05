from django.conf import settings

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object import PinLoginPageObject


class CourseConclusionBaseTestCase(BaseSeleniumTestCase):

    @classmethod
    def setUpClass(cls):
        super(CourseConclusionBaseTestCase, cls).setUpClass()
        cls.USERNAME = settings.SELENIUM_CONFIG['selenium_username']
        cls.PASSWORD = settings.SELENIUM_CONFIG['selenium_password']
        cls.BASE_URL = '{}{}'.format(
            settings.SELENIUM_CONFIG['term_tool_base_url'],
            settings.SELENIUM_CONFIG['course_conclusion']['index_page'])

        pin_page = PinLoginPageObject(cls.driver)
        pin_page.get(cls.BASE_URL)
        pin_page.login_xid(cls.USERNAME, cls.PASSWORD)
