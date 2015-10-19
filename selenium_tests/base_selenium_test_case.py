import unittest
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pyvirtualdisplay import Display
from django.conf import settings


# Enabling stdout logging only for high `-v`
class BaseSeleniumTestCase(unittest.TestCase):
    driver = None  # make selenium driver available to any part of the test case
    display = None  # a reference to the virtual display (for running tests locally)

    @classmethod
    def setUpClass(cls):
        """
        Sets up the test case, including the selenium browser driver to use
        """

        local = True

        # todo: tlt-1263 remote URL should be configurable from outside the code
        selenium_grid_url = settings.SELENIUM_CONFIG.get('selenium_grid_url', None)

        if local:
            # Run selenium tests from a headless browser within the VM
            print "\nSetting up selenium testing locally..."
            # set up virtual display
            cls.display = Display(visible=0, size=(1480, 1024)).start()
            # create a new local browser session
            cls.driver = webdriver.Firefox()
        else:
            # Run selenium tests from the Selenium Grid server
            # print "\nSetting up selenium testing on selenium grid at %s..." % selenium_grid_url
            # todo: tlt-1263 the server address and desired_capabilities should be configurable
            cls.driver = webdriver.Remote(
                command_executor=selenium_grid_url,
                desired_capabilities=DesiredCapabilities.FIREFOX
            )

        # shared defaults
        cls.driver.implicitly_wait(10)
        cls.driver.maximize_window()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        if cls.display:
            cls.display.stop()
