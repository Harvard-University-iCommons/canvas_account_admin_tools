import json
from unittest.mock import Mock, patch

from django.test import Client, RequestFactory, TestCase

from .views import create_bulk_job


@patch('lti_permissions.decorators.lti_permission_required_check', new=Mock(return_value=True))
@patch('django_auth_lti.decorators.is_allowed', new=Mock(return_value=True))
@patch('lti_permissions.decorators.is_allowed', new=Mock(return_value=True))
class CreateBulkJobTestCase(TestCase):
    def setUp(self):
        self.Client = Client()
        self.url = '/bulk_site_creator/create_bulk_job'
        self.data = {
            "canvas_user_id": 1,
            "logged_in_user_id": 2,
            "filters": {
                "term": "10571",
                "department": "dept:1864",
                "course_group": "",
                "school": "school:hds",
            },
            "course_instance_ids": [1, 2, 3],
            "create_all": False,
            "template": "2550"
        }
        self.json_data = json.dumps(self.data)

    @patch('bulk_site_creator.utils.get_term_data')
    @patch('bulk_site_creator.views.get_term_name_by_id')
    @patch('bulk_site_creator.views.get_department_name_by_id')
    def test_create_bulk_job(self, mock_department, mock_get_term_name_by_id, mock_get_term_data):
        mock_department.return_value = "OMS"
        mock_get_term_data.return_value = {'id': "10571", 'name': "Spring 2021"}
        mock_get_term_name_by_id.return_value = 'Spring 2021'

        self.request = RequestFactory().post(self.url, data=self.json_data, content_type='application/json')
        self.request.LTI = {
            "lis_person_sourcedid": "12345678",
            "lis_person_name_full": "First Last",
            "lis_person_contact_email_primary": "test@test.com",
        }
        self.request.user = Mock(is_authenticated=Mock(return_value=True))
        response = create_bulk_job(self.request)

        self.assertEqual(response.status_code, 200)
