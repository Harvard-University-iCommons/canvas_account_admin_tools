import abc

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from selenium_tests.pin.page_objects.pin_base_page_object import PinBasePageObject


class PinPageLocators(object):
    # List of WebElements found on PIN Login Page
    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "password")
    SUBMIT_BUTTON = (By.ID,"submitLogin")
    LoginType = (By.XPATH, "//div[@id='XID']")


class PinLoginPageObject(PinBasePageObject):
    """
    Page Object of the Pin Login Page

    """
    __metaclass__ = abc.ABCMeta

    def is_loaded(self):
        """ determine if the page loaded by looking for a specific element on the page """
        try:
            self.find_element(*PinPageLocators.USERNAME)
        except NoSuchElementException:
            return False
        return True

    def set_login_type_xid(self):
        """ set the login type to XID """
        comp_auth_source_type_element = self.find_element(*PinPageLocators.LoginType)
        comp_auth_source_type_element.click()

    def set_username(self, username):
        """ set the username """
        username_element = self.find_element(*PinPageLocators.USERNAME)
        username_element.clear()
        username_element.send_keys(username)

    def set_password(self, password):
        """ set the password """
        password_element = self.find_element(*PinPageLocators.PASSWORD)
        password_element.clear()
        password_element.send_keys(password)

    def click_submit(self):
        """ click the submit button """
        submit_button = self.find_element(*PinPageLocators.SUBMIT_BUTTON)
        submit_button.click()

    def login(self, username, password):
        """
        the abstract method can be overridden for individual projects to allow
        the login to return the appropriate page object for the test. If you do override
        you will need to call super to invoke the login
        """
        self.set_login_type_xid()
        self.set_username(username)
        self.set_password(password)
        self.click_submit()
        print 'Logging in user: %s' % username
