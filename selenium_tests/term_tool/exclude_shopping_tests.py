import unittest

from django.conf import settings

from urlparse import urljoin

from selenium_tests.term_tool.term_tool_base_test_case \
    import TermToolBaseTestCase
from selenium_tests.term_tool.page_objects.shopping_exclude_page_object \
    import ShoppingExcludePageObject


class ExcludeShoppingTests(TermToolBaseTestCase):
    # Note:  There is no direct UI path to the Exclude Button in term tool
    # (see TLT-1903), so tests will go directly to exclude_from_shopping page
    # to validate page loads.

    def test_tool_is_loaded(self):
        exclude_page = ShoppingExcludePageObject(self.driver)
        term_tool_url = urljoin(settings.SELENIUM_CONFIG.get(
            'term_tool_base_url'), settings.SELENIUM_CONFIG.get(
            'term_tool_relative_url'))
        exclude_page.get(term_tool_url)
        self.assertTrue(exclude_page.is_loaded())


if __name__ == "__main__":
    unittest.main()
