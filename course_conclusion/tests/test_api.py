import json

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from mock import patch

from course_conclusion import api


# TODO - implement test auth backend that sets request.session['USER_GROUPS']
#        the way pinauth does.  for now, just patch user_is_admin.

# NOTE - some fixtures are flagged as inactive, and should not show up in any
#        api results.
# TODO - autogen some of this, so we're not putting it in the fixures and here?
SCHOOLS = {
    'bar': {'title_short': 'Harvard Bar', 'school_id': 'bar'},
    'foo': {'title_short': 'Harvard Foo', 'school_id': 'foo'},
}
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
