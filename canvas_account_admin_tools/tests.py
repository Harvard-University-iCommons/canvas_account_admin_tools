import json
from urlparse import urlparse

from django.test import RequestFactory, TestCase
from mock import patch, Mock

from views import icommons_rest_api_proxy


@patch('django_auth_lti.decorators.is_allowed', new=Mock(return_value=True))
@patch('lti_permissions.decorators.is_allowed', new=Mock(return_value=True))
class CanvasAccountAdminToolsAPIProxyTests(TestCase):
    longMessage = True

    def setUp(self):
        super(CanvasAccountAdminToolsAPIProxyTests, self).setUp()
        self.user_id = '12345678'

    def _setup_request(self, method='GET', path='fake-path/', data=None, request_lti_dict=None):
        self.request = RequestFactory().generic(method=method, path=path, data=data)
        self.request.user = Mock(is_authenticated=Mock(return_value=True))
        if request_lti_dict is None:
            self.request.LTI = {
                'lis_person_sourcedid': self.user_id,
            }

    @patch('canvas_account_admin_tools.views.proxy_view')
    def test_proxy_xlist_maps_auditing(self, mock_proxy_view, *args, **kwargs):
        """
        Proxy should add the last_modified_by to the xlistmap POST data
        """

        # test_path represents the path fragment handed to
        # views.icommons_rest_api_proxy from the router (see the <path> arg
        # in urls.py).
        test_path = 'api-path/xlist_maps/'
        # test_request_path is the actual path required for the fake request
        # object to be set up properly
        test_request_path = '/{}'.format(test_path)

        test_post_data = {"any": "thing"}
        self._setup_request(method='POST', path=test_request_path,
                            data=json.dumps(test_post_data))

        # we expect views.icommons_rest_api_proxy to add in the last_modified_by
        # POST param if it's an xlistmap POST request
        xlist_map_auditing_arg = {'last_modified_by': self.user_id}
        expected_request_args = test_post_data.copy()
        expected_request_args.update(xlist_map_auditing_arg)

        # call the view
        response = icommons_rest_api_proxy(self.request, test_path)

        # get the call args from the first call to proxy.views.proxy_view
        actual_call = mock_proxy_view.call_args_list[0][0]

        # first call arg is the fake request object, ignore that for our test

        # parse just the path fragment from the second call arg
        # (which is the full request url)
        actual_call_path = urlparse(actual_call[1]).path

        # get the 'data' subdict from the third call arg, which is a dict of
        # request arguments. Note that 'data' should _only_ be present if the
        # request was an xlistmap POST request.
        actual_call_data = actual_call[2]['data']

        self.assertEqual(actual_call_path, self.request.path)
        self.assertEqual(actual_call_data, json.dumps(expected_request_args))

    @patch('canvas_account_admin_tools.views.proxy_view')
    def test_proxy_no_xlist_maps_auditing(self, mock_proxy_view, *args, **kwargs):
        """
        Proxy should not add last_modified_by to non-xlistmap POST data
        """

        # test_path represents the path fragment handed to
        # views.icommons_rest_api_proxy from the router (see the <path> arg
        # in urls.py). If it doesn't contain xlist_map, the proxy layer
        # should not add user auditing info
        test_path = 'api-path/something_else/'
        # test_request_path is the actual path required for the fake request
        # object to be set up properly
        test_request_path = '/{}'.format(test_path)

        test_post_data = {"any": "thing"}
        self._setup_request(method='POST', data=json.dumps(test_post_data))

        # call the view
        response = icommons_rest_api_proxy(self.request, test_path)

        # get the call args from the first call to proxy.views.proxy_view
        actual_call = mock_proxy_view.call_args_list[0][0]  # just the call args

        # first call arg is the fake request object, ignore that for our test
        # second call arg is the full request url, ignore that for our test
        # third call arg is the dict of request arguments
        actual_call_request_args = actual_call[2]

        # 'data' subdict should _only_ be present if the request was an
        # xlistmap POST request. It isn't in this case, so we're expecting it to
        # be absent from the request args.
        self.assertNotIn('data', actual_call_request_args)
