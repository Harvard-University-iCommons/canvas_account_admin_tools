from selenium.common.exceptions import NoSuchElementException


class BasePageObject(object):
    """
    This is the base class that all page models can inherit from
    """

    def __init__(self, driver):
        self._driver = driver

    # These methods locate a specific element or elements.
    def find_element(self, *loc):
        """
        find the web element specified by *loc
        :param loc:
        :return:
        """
        return self._driver.find_element(*loc)

    def find_elements(self, *loc):
        """
        find the web elements specified by *loc
        :param loc:
        :return:
        """
        return self._driver.find_elements(*loc)

    def find_element_by_xpath(self, *loc):
        """
        find the web element specified by *loc using an xpath expression
        :param loc:
        :return:
        """
        return self._driver.find_element_by_xpath(*loc)

    def get_title(self):
        """
        get the page title
        :return:
        """
        return self._driver.title

    def get_url(self):
        """
        get the page url
        :return:
        """
        return self._driver.current_url

    def get(self, url):
        """
        open the provided url
        :param url:
        :return:
        """
        self._driver.get(url)

    def focus_on_tool_frame(self):
        """
        The pages we are testing are in an iframe, make sure we have the correct focus
        :return:
        """
        try:
            self._driver.switch_to.frame(self._driver.find_element_by_id("tool_content"))
        except NoSuchElementException:
            pass

