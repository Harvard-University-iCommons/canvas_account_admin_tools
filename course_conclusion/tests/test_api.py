import uuid

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from mock import patch

from course_conclusion import api


# TODO - implement test auth backend that sets request.session['USER_GROUPS']
#        the way pinauth does.  for now, just patch user_is_admin.


@override_settings(AUTHENTICATION_BACKENDS=('django.contrib.auth.backends.ModelBackend',))
@override_settings(LOGIN_URL='/accounts/login/')
class SchoolsTestCase(TestCase):
    fixtures = [
        'course_conclusion/fixtures/schools.json',
        'course_conclusion/fixtures/users.json',
    ]
    longMessage = True
    urls = 'course_conclusion.test_urls'

    def setUp(self):
        # NOTE - user credentials come from users.json fixture
        self.client.login(username='test1', password='password1')

    @patch('course_conclusion.api.user_is_admin', return_value=True)
    def test_get(self, user_is_admin):
        response = self.client.get('/api/schools')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            '[{"title_short": "Harvard Test", "school_id": "1"}]'
        )
