import unittest

from selenium_tests.term_tool.term_tool_base_test_case import TermToolBaseTestCase
from selenium_tests.term_tool.page_objects.term_tool_shopping_exclude_page_object \
    import TermToolShoppingExcludePageObject


class TermToolExcludeShoppingTests (TermToolBaseTestCase):
    # Note:  There is no direct UI path to the Exclude Button in term tool (see TLT-1903), so tests will go
    # directly to exclude_from_shopping page to validate page that a course instance ID is checked
    # to be excluded from shopping in termtool.

    def test_exclude_from_shopping_checked(self):
        exclude_page = TermToolShoppingExcludePageObject(self.driver)  # instantiate
        # This checks if a course is excluded from shopping.  If not, it ticks on the checkbox.
        exclude_page.select_disable_auth_user_access()
        # This asserts the course is excluded from shopping
        self.assertTrue(exclude_page.check_course_is_selected(), "course is not excluded from shopping")


if __name__ == "__main__":
    unittest.main()
