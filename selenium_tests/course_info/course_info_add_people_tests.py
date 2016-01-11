import unittest
from django.conf import settings

from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_search_page_object \
    import CourseSearchPageObject
from selenium_tests.course_info.page_objects.course_people_page_object \
    import CoursePeoplePageObject


class CourseInfoAddTest(CourseInfoBaseTestCase):

    def _load_test_course(self):
        self.driver.save_screenshot('_load_test_course-0.png')
        search_page = CourseSearchPageObject(self.driver)
        test_settings = settings.SELENIUM_CONFIG['course_info_tool']
        course = test_settings['test_course']

        self.assertTrue(search_page.is_loaded())
        self.search_for_course(
            type=course['type'], school=course['school'], term=course['term'],
            year=course['year'], search_term=course['cid'])

        # click on course link to view list of people in course
        search_page.select_course(cid=course['cid'])

    def test_search_and_add_person(self):
        """ verify the person search and add functionality """

        self.driver.save_screenshot('test_search_and_add_person-0.png')

        people_page = CoursePeoplePageObject(self.driver)
        test_settings = settings.SELENIUM_CONFIG['course_info_tool']
        new_user = test_settings['test_users']['new']

        self._load_test_course()

        # search for a user and add user to course
        self.assertTrue(people_page.is_loaded())
        people_page.search_and_add_user(new_user['user_id'], new_user['role'])

        self.driver.save_screenshot('test_search_and_add_person-1.png')

        # assert that user is found on page.
        # Note: If the course has a lot of people enrolled, results are
        # paginated and it's possible that user may not be on the initial
        # page. So this  may change based on data changing

        self.assertTrue(people_page.is_person_on_page(new_user['user_id']))

        # Assert that the success text is displayed
        self.assertTrue(people_page.add_was_successful())

    def test_remove_person(self):
        """ Removes a user from course using the Admin Console """

        self.driver.save_screenshot('test_remove_person-0.png')

        people_page = CoursePeoplePageObject(self.driver)
        test_settings = settings.SELENIUM_CONFIG['course_info_tool']
        new_user = test_settings['test_users']['new']

        self._load_test_course()

        self.driver.save_screenshot('test_remove_person-1.png')

        # asserts that test is on people page and to-be-removed user is on page
        self.assertTrue(people_page.is_loaded())
        self.assertTrue(people_page.is_person_on_page(new_user['user_id']))

        # deletes user and confirms that delete is successful
        people_page.delete_user(new_user['user_id'])
        self.assertTrue(people_page.delete_was_successful())
        self.assertFalse(people_page.is_person_on_page(new_user['user_id']))


if __name__ == "__main__":
    unittest.main()
