from django.conf import settings

from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_search_page_object \
    import CourseSearchPageObject
from selenium_tests.course_info.page_objects.course_people_page_object \
    import CoursePeoplePageObject


class CourseInfoPeopleListTest(CourseInfoBaseTestCase):

    def test_people_list_page_loaded(self):
        """verify the people search functionality"""
        search_page = CourseSearchPageObject(self.driver)

        test_settings = settings.SELENIUM_CONFIG['course_info_tool']
        course = test_settings['test_course']
        user = test_settings['test_users']['existing']

        self.search_for_course(
            type=course['type'], school=course['school'], term=course['term'],
            year=course['year'], search_term=course['cid'])

        # click on course link to view list of people in course
        search_page.select_course(cid=course['cid'])

        people_page = CoursePeoplePageObject(self.driver)
        # assert that an expected enrollment is present
        self.assertTrue(people_page.is_loaded())
        self.assertTrue(people_page.is_person_on_page(user['user_id']))
