from django.conf import settings

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject
from selenium_tests.course_info.page_objects.course_people_page_object import \
    CoursePeoplePageObject


class CourseInfoAddTest(CourseInfoBaseTestCase):

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
        self.driver.save_screenshot('image0.jpeg')

        # click on course link to view list of people in course
        search_page.select_course(cid=course['cid'])
        self.driver.save_screenshot('image1.jpeg')

        # search for a user and add user to course
        people_page.search_and_add_user(new_user['user_id'], new_user['role'])
        self.driver.save_screenshot('image2.jpeg')

        # assert that user is found
        self.assertTrue(people_page.is_person_on_page(new_user['user_id']))
        self.driver.save_screenshot('image3.jpeg')
        # Verify success text
        self.assertTrue(people_page.add_was_successful())
        self.driver.save_screenshot('image4.jpeg')
