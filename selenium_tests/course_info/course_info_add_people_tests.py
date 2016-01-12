import json
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
        search_page = CourseSearchPageObject(self.driver)
        test_settings = settings.SELENIUM_CONFIG['course_info_tool']
        course = test_settings['test_course']

        self.assertTrue(search_page.is_loaded())
        self.search_for_course(
            type=course['type'], school=course['school'], term=course['term'],
            year=course['year'], search_term=course['cid'])

        # click on course link to view list of people in course
        search_page.select_course(cid=course['cid'])

    def _add_user_via_api(self, cid, user_id, role_id):
        # todo: refactor
        body = {'user_id': user_id, 'role_id': role_id}
        path = 'course_instances/{}/people/'.format(cid)
        r = self._api_post(path=path, body=body)
        if r.status_code not in [409, 201]:
            msg = 'DELETE {} (data: {}) expected a 409 (conflict) or 201 ' \
                  '(created), instead got: status {}, data:\n{}'
            body_json = json.dumps(body, sort_keys=True, indent=2)
            resp_json = json.dumps(r._content, sort_keys=True, indent=2)
            self.fail(msg.format(path, body_json, r.status_code, resp_json))

    def _remove_user_via_api(self, cid, user_id, role_id):
        body = {'user_id': user_id, 'role_id': role_id}
        path = 'course_instances/{}/people/{}/'.format(cid, user_id)
        r = self._api_delete(path=path, body=body)
        if r.status_code not in [404, 204]:
            msg = 'DELETE {} (data: {}) expected a 404 (not found) or 204 ' \
                  '(no content), instead got: status {}, data:\n{}'
            body_json = json.dumps(body, sort_keys=True, indent=2)
            resp_json = json.dumps(r._content, sort_keys=True, indent=2)
            self.fail(msg.format(path, body_json, r.status_code, resp_json))

    def test_add_person(self):
        """ verify the person search and add functionality """

        people_page = CoursePeoplePageObject(self.driver)
        test_settings = settings.SELENIUM_CONFIG['course_info_tool']
        new_user = test_settings['test_users']['new']

        # ensure person isn't in course before attempting to add
        self._remove_user_via_api(test_settings['test_course']['cid'],
                                  new_user['user_id'], new_user['role_id'])

        self._load_test_course()

        # search for a user and add user to course
        self.assertTrue(people_page.is_loaded())

        # assert that the success message is not already loaded on the page
        self.assertFalse(people_page.add_was_successful())

        # add user to role
        people_page.search_and_add_user(new_user['user_id'], new_user['role'])

        # assert that user is found on page.
        # Note: If the course has a lot of people enrolled, results are
        # paginated and it's possible that user may not be on the initial
        # page. So this  may change based on data changing
        self.assertTrue(people_page.is_person_on_page(new_user['user_id']))

        # Assert that the success text is displayed
        self.assertTrue(people_page.add_was_successful())

    def test_remove_person(self):
        """ Removes a user from course using the Admin Console """

        people_page = CoursePeoplePageObject(self.driver)
        test_settings = settings.SELENIUM_CONFIG['course_info_tool']
        test_user = test_settings['test_users']['existing']

        # ensure person is in course before attempting to remove
        self._add_user_via_api(test_settings['test_course']['cid'],
                               test_user['user_id'], test_user['role_id'])

        self._load_test_course()

        # asserts test user is on people page and to-be-removed user is on page
        self.assertTrue(people_page.is_loaded())
        self.assertTrue(people_page.is_person_on_page(test_user['user_id']))

        # asserts that the delete confirmation text is not already on the page
        self.assertFalse(people_page.delete_was_successful())

        # deletes user and confirms that delete is successful
        people_page.delete_user(test_user['user_id'])

        self.assertTrue(people_page.delete_was_successful())
        self.assertTrue(people_page.is_person_removed_from_list(test_user['user_id']))

        # ensure person is put back into course as cleanup
        self._add_user_via_api(test_settings['test_course']['cid'],
                               test_user['user_id'], test_user['role_id'])


if __name__ == "__main__":
    unittest.main()
