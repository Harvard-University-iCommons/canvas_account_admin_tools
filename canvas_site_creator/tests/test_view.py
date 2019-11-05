
from canvas_site_creator.views import index
import json
from mock import ANY, DEFAULT, call, Mock, patch
from os import path


from django.test import Client, RequestFactory, TestCase

@patch('django_auth_lti.decorators.is_allowed', new=Mock(return_value=True))
@patch('lti_permissions.decorators.is_allowed', new=Mock(return_value=True))
class BulkSiteViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(BulkSiteViewTest, cls).setUpClass()
        cls.client = Client()

    def setUp(self):
        super(BulkSiteViewTest, self).setUp()
        self.url = '/lti_tools/canvas_site_creator/index'

    def _prep_request_for_view(self):

        self.request = RequestFactory().get(self.url)
        self.request.LTI = {
            'custom_canvas_user_id': '1',
            'custom_canvas_account_sis_id' : 'xyz',
        }
        self.request.user = Mock(is_authenticated=Mock(return_value=True))
        return index(self.request)

    @patch('canvas_site_creator.views.render')
    @patch('icommons_common.canvas_api.helpers.accounts.parse_canvas_account_id')
    def test_restricted_message_for_dept_subacct(self,
                                                 mock_parse_canvas_account_id,
                                                 render_view):
        """
        Tests that the restricted message is rendered for 'dept'(department)
        account type
        """
        mock_parse_canvas_account_id.return_value = ['dept', 'abc']
        self._prep_request_for_view()
        self.assertEqual(render_view.call_args, call(
                self.request, 'canvas_site_creator/restricted_access.html',
                status=403))


    @patch('canvas_site_creator.views.render')
    @patch('icommons_common.canvas_api.helpers.accounts.parse_canvas_account_id')
    def test_restricted_message_for_coursegroup_subacct(self,
                                                 mock_parse_canvas_account_id,
                                                 render_view):
        """
        Tests that the restricted message is rendered for 'coursegroup'
        account type
        """
        mock_parse_canvas_account_id.return_value = ['coursegroup', 'abc']
        self._prep_request_for_view()
        self.assertEqual(render_view.call_args, call(
                self.request, 'canvas_site_creator/restricted_access.html',
                status=403))

    @patch('canvas_site_creator.views.render')
    @patch('icommons_common.canvas_api.helpers.accounts.parse_canvas_account_id')
    @patch('canvas_site_creator.utils.get_term_data_for_school')
    @patch('canvas_site_creator.views.get_school_sub_account_from_account_id')
    @patch('canvas_site_creator.views.get_department_data_for_school')
    @patch('canvas_site_creator.views.get_course_group_data_for_school')

    def test_for_school_acct(self, mock_get_course_group_data,mock_get_dept_data,
                             mock_get_school_sub_acct,mock_get_term,
                             mock_parse_canvas_account_id,render_view):
        """
        Tests that the index page is rendered  for 'school'
        account types
        """
        mock_parse_canvas_account_id.return_value = ['school', 'abc']
        mock_get_school_sub_acct.return_value = { 'sis_account_id': 'school:abc',
                                              'name': 'ABC School'}
        mock_get_term.return_value = ([{'id': '111', 'name': 'Summer2 '},
                                       {'id': '222', 'name': 'Spring 2014'}])
        mock_get_dept_data.return_value = DEFAULT
        mock_get_course_group_data.retrun_value = DEFAULT
        self._prep_request_for_view()
        self.assertEqual(render_view.call_args, call(
        self.request, 'canvas_site_creator/index.html',
                 {  'terms': [],
                    'in_school_account': True,
                    'departments': ANY,
                    'filters': ANY,
                    'schools': ANY,
                    'course_groups': ANY}))

