import unittest

from django.conf import settings

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject
from selenium_tests.course_info.page_objects.course_people_page_object import \
    CoursePeoplePageObject

COURSE_INSTANCE_ID = '339331'
COURSE_USER_ID = "30833767"
USER_ROLE = "Teacher"


class CourseInfoAddTest(CourseInfoBaseTestCase):

    def test_search_and_add_person(self):
        """verify the person  search and add functionality"""

        search_page = CourseSearchPageObject(self.driver)

        course = settings.SELENIUM_CONFIG['course_info_tool']['test_course']

        self.search_for_course(
            type=course['type'], school=course['school'], term=course['term'],
            year=course['year'], search_term=course['cid'])
        self.driver.save_screenshot('image0.jpeg')

        # click on course link to view list of people in course
        search_page.select_course(cid=COURSE_INSTANCE_ID)
        # search_page.select_course_id_link()

        people_page = CoursePeoplePageObject(self.driver)

        # search for a user and add user to course
        people_page.search_and_add_user(COURSE_USER_ID, USER_ROLE)
        self.driver.save_screenshot('image2.jpeg')

        # assert that user is found
        self.assertTrue(people_page.find_test_person_exists_on_page())
        # Verify success text
        self.assertTrue(people_page.find_success_message())




if __name__ == "__main__":
    unittest.main()

