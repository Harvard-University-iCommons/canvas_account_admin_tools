import unittest
from django.conf import settings

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject
from selenium_tests.course_info.page_objects.course_people_page_object import \
    CoursePeoplePageObject


class CourseInfoAddTest(CourseInfoBaseTestCase):

    @unittest.skip("repetitive adding of the same user is not allowed and delete function is not in place yet")
    def test_search_and_add_person(self):
        """verify the person  search and add functionality"""

        search_page = CourseSearchPageObject(self.driver)
        people_page = CoursePeoplePageObject(self.driver)

        test_settings = settings.SELENIUM_CONFIG['course_info_tool']
        course = test_settings['test_course']
        new_user = test_settings['test_users']['new']

        self.search_for_course(
            type=course['type'], school=course['school'], term=course['term'],
            year=course['year'], search_term=course['cid'])

        # click on course link to view list of people in course
        search_page.select_course(cid=course['cid'])

        # search for a user and add user to course
        people_page.search_and_add_user(new_user['user_id'], new_user['role'])

        # assert that user is found
        self.assertTrue(people_page.is_person_on_page(new_user['user_id']))

        # Verify success text
        self.assertTrue(people_page.add_was_successful())
