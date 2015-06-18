import copy
import json

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from mock import patch

from course_conclusion import api



'''
The following structures match what we're expecting to get back from the
api.  Any updates made to the test fixtures should be mirrored here.

NOTE - Some fixtures are flagged as inactive, and serve as a silent test
       verifying that inactive entities won't be returned from the api.
'''

# SCHOOLS = { school_id: { SCHOOL }, ... }
SCHOOLS = {
    'bar': {'title_short': 'Harvard Bar', 'school_id': 'bar'},
    'foo': {'title_short': 'Harvard Foo', 'school_id': 'foo'},
}

# TERMS = { school_id: { term_id: { TERM }, ... }, ... }
TERMS = {
    'bar': {},
    'foo': {
        1: {
            'conclude_date': '2015-03-15',
            'display_name': 'Foo Something 2015',
            'term_id': 1, 
        },
    },
}

# COURSES = { school_id: { term_id: { course_instance_id: { COURSE }, ... }, ... }, ...}
COURSES = {
    'bar': {},
    'foo': {
        1: {
            1: {
                'conclude_date': None,
                'course_id': 1,
                'course_instance_id': 1,
                'title': 'Basket Weaving 101',
            },
        },
    },
}


@override_settings(AUTHENTICATION_BACKENDS=('django.contrib.auth.backends.ModelBackend',))
@override_settings(LOGIN_URL='/accounts/login/')
class PinAuthWorkaroundTestCase(TestCase):
    '''
    In order to test the endpoints in course_conclusion.api, we need to have
    requests associated with a logged in user.  We can't just mock the
    login_required decorator, since we'd have to do it before the module
    is read in.  Instead, we override AUTHENTICATION_BACKENDS to use the stock
    ModelBackend, set up a "test1" user via fixtures, and log in as that user
    before every test.

    We defer patching of the two authorization checks, user_is_admin() and
    user_allowed_schools(), to individual tests, since those may need to be
    changed on a test by test basis to get full coverage.
    '''
    fixtures = ('course_conclusion/fixtures/users.json',)
    longMessage = True
    urls = 'course_conclusion.test_urls'

    def setUp(self):
        # NOTE - user credentials come from users.json fixture
        self.client.login(username='test1', password='password1')


class SchoolsTestCase(PinAuthWorkaroundTestCase):
    fixtures = (PinAuthWorkaroundTestCase.fixtures
                + ('course_conclusion/fixtures/schools.json',))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get_user_is_admin(self, *args, **kwargs):
        response = self.client.get('/api/schools')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(SCHOOLS.values()), json.loads(response.content))

    @patch('course_conclusion.api.user_allowed_schools',
           return_value=['foo']) 
    @patch('course_conclusion.api.user_is_admin', return_value=False)
    def test_get_user_not_admin(self, *args, **kwargs):
        response = self.client.get('/api/schools')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([SCHOOLS['foo']], json.loads(response.content))


class TermsTestCase(PinAuthWorkaroundTestCase):
    fixtures = (PinAuthWorkaroundTestCase.fixtures
                + ('course_conclusion/fixtures/schools.json',
                   'course_conclusion/fixtures/terms.json'))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get_user_admin(self, *args, **kwargs):
        for school_id, school in SCHOOLS.iteritems():
            response = self.client.get(
                           '/api/terms?school_id={}'.format(school_id))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(sorted(TERMS[school_id].values()),
                             json.loads(response.content))

    @patch('course_conclusion.api.user_allowed_schools',
           return_value=['foo']) 
    @patch('course_conclusion.api.user_is_admin', return_value=False)
    def test_get_user_not_admin(self, *args, **kwargs):
        response = self.client.get('/api/terms?school_id=foo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(TERMS['foo'].values()),
                         json.loads(response.content))

    @patch('course_conclusion.api.user_allowed_schools',
           return_value=['foo']) 
    @patch('course_conclusion.api.user_is_admin', return_value=False)
    def test_get_user_not_allowed_school(self, *args, **kwargs):
        response = self.client.get('/api/terms?school_id=bar')
        self.assertEqual(response.status_code, 403)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get_invalid_school(self, *args, **kwargs):
        response = self.client.get('/api/terms?school_id=notaschool')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get_missing_school(self, *args, **kwargs):
        response = self.client.get('/api/terms')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))


class CoursesTestCase(PinAuthWorkaroundTestCase):
    fixtures = (PinAuthWorkaroundTestCase.fixtures
                + ('course_conclusion/fixtures/schools.json',
                   'course_conclusion/fixtures/terms.json',
                   'course_conclusion/fixtures/courses.json'))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get_user_admin(self, *args, **kwargs):
        for school_id in COURSES:
            for term_id in COURSES[school_id]:
                url = '/api/courses?school_id={}&term_id={}'.format(
                          school_id, term_id)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    sorted(COURSES[school_id][term_id].values()),
                    json.loads(response.content))

    @patch('course_conclusion.api.user_allowed_schools',
           return_value=['foo']) 
    @patch('course_conclusion.api.user_is_admin', return_value=False)
    def test_get_user_not_admin(self, *args, **kwargs):
        response = self.client.get('/api/courses?school_id=foo&term_id=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(COURSES['foo'][1].values()),
                         json.loads(response.content))

    @patch('course_conclusion.api.user_allowed_schools',
           return_value=['foo']) 
    @patch('course_conclusion.api.user_is_admin', return_value=False)
    def test_get_user_not_allowed_school(self, *args, **kwargs):
        response = self.client.get('/api/courses?school_id=bar&term_id=1')
        self.assertEqual(response.status_code, 403)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get_invalid_school(self, *args, **kwargs):
        response = self.client.get('/api/courses?school_id=notaschool&term_id=1')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get_invalid_term(self, *args, **kwargs):
        response = self.client.get('/api/courses?school_id=foo&term_id=123456')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get_missing_school(self, *args, **kwargs):
        response = self.client.get('/api/courses?term_id=1')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get_missing_term(self, *args, **kwargs):
        response = self.client.get('/api/courses?school_id=foo')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get_term_doesnt_belong_to_school(self, *args, **kwargs):
        response = self.client.get('/api/courses?school_id=bar&term_id=1')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))


class CourseTestCase(PinAuthWorkaroundTestCase):
    fixtures = (PinAuthWorkaroundTestCase.fixtures
                + ('course_conclusion/fixtures/schools.json',
                   'course_conclusion/fixtures/terms.json',
                   'course_conclusion/fixtures/courses.json'))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_patch_user_is_admin(self, *args, **kwargs):
        data = {'course_instance_id': 1, 'conclude_date': '2020-01-01'}
        response = self.client.patch('/api/courses/1', data=json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)

        expected = copy.deepcopy(COURSES['foo'][1][1])
        expected.update(data)
        self.assertEqual(expected, json.loads(response.content))

    @patch('course_conclusion.api.user_allowed_schools',
           return_value=['foo']) 
    @patch('course_conclusion.api.user_is_admin', return_value=False)
    def test_patch_user_not_admin(self, *args, **kwargs):
        data = {'course_instance_id': 1, 'conclude_date': '2020-01-01'}
        response = self.client.patch('/api/courses/1', data=json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)

        expected = copy.deepcopy(COURSES['foo'][1][1])
        expected.update(data)
        self.assertEqual(expected, json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_patch_no_body(self, *args, **kwargs):
        response = self.client.patch('/api/courses/1')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_patch_body_not_json(self, *args, **kwargs):
        response = self.client.patch('/api/courses/1', data='deadbeef')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_patch_body_fields_missing(self, *args, **kwargs):
        data = {'course_instance_id': 1}
        response = self.client.patch('/api/courses/1', data=json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))

        data = {'conclude_date': '2001-01-01'}
        response = self.client.patch('/api/courses/1', data=json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_patch_course_instance_id_mismatch(self, *args, **kwargs):
        data = {'course_instance_id': 2, 'conclude_date': '2001-01-01'}
        response = self.client.patch('/api/courses/1', data=json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_allowed_schools',
           return_value=['bar']) 
    @patch('course_conclusion.api.user_is_admin', return_value=False)
    def test_patch_course_not_allowed(self, *args, **kwargs):
        data = {'course_instance_id': 1, 'conclude_date': '2020-01-01'}
        response = self.client.patch('/api/courses/1', data=json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertIn('error', json.loads(response.content))

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_patch_malformed_date(self, *args, **kwargs):
        data = {'course_instance_id': 1, 'conclude_date': 'deadbeef'}
        response = self.client.patch('/api/courses/1', data=json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.content))
