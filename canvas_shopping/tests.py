"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from mock import Mock
from django.test import RequestFactory
from .views import user_has_harvard_student_status

class ShoppingTest(TestCase):

    def setUp(self):
        self.request = RequestFactory().get('/fake-path')
        self.request.user = Mock(name='user_mock')
        self.request.user.is_authenticated.return_value = True
        self.request.session = {
            'USER_GROUPS': {
                'LdapGroup:UIS.student' : 'true',
            }
        }

    def test_user_has_harvard_student_status_regex(self):
        """
        test to make sure the regex expression is matching correctly
        :return:
        """
        request = self.request
        result = user_has_harvard_student_status(request)
        self.assertTrue(result)


