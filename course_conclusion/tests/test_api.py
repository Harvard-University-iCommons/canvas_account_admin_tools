import json

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from mock import patch

from course_conclusion import api


# TODO - implement test auth backend that sets request.session['USER_GROUPS']
#        the way pinauth does.  for now, just patch user_is_admin.

# TODO: autogen some of this, so we're not putting it in the fixures and here?
# NOTE: fixtures contain an inactive school 'inactive', which should never show
#       up in api results
SCHOOLS = {
    'bar': {'title_short': 'Harvard Bar', 'school_id': 'bar'},
    'foo': {'title_short': 'Harvard Foo', 'school_id': 'foo'},
}
TERMS = {
    'bar': {},
    'foo': {
        1: {'term_id': 1, 
            'conclude_date': None,
            'display_name': 'Foo Something 2015'},
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
    def test_get_user_admin_valid_school(self, *args, **kwargs):
        for school_id, school in SCHOOLS.iteritems():
            response = self.client.get(
                           '/api/terms?school_id={}'.format(school_id))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(sorted(TERMS[school_id].values()),
                             json.loads(response.content))
