import json

from os import path

from django.test import TestCase

from mock import patch, Mock

from canvas_course_site_wizard.models import CanvasSchoolTemplate

from common.utils import (
    get_school_data_for_user,
    get_department_data_for_school,
    get_course_group_data_for_school,
    get_canvas_site_templates_for_school,
    get_canvas_site_template
)


class UtilsTest(TestCase):
    def setUp(self):
        fixtures_path = path.join(path.dirname(__file__), '../fixtures')
        with open(path.join(fixtures_path, 'canvas_accounts_school.json')) as fixture:
            self.school_accounts = json.load(fixture)
        with open(path.join(fixtures_path, 'canvas_accounts_department.json')) as fixture:
            self.department_accounts = json.load(fixture)
        with open(path.join(fixtures_path, 'canvas_accounts_course_group.json')) as fixture:
            self.course_group_accounts = json.load(fixture)
        self.school_sis_account_ids = [a['sis_account_id'] for a in self.school_accounts]
        self.department_sis_account_ids = [a['sis_account_id'] for a in self.department_accounts]
        self.course_group_sis_account_ids = [a['sis_account_id'] for a in self.course_group_accounts]
        self.canvas_user_id = 104779
        self.school_sis_account_id = 'school:colgsas'
        for account in self.school_accounts:
            if account['sis_account_id'] == self.school_sis_account_id:
                self.school_account = account
        self.department_sis_account_id = 'dept:57'
        self.course_group_sis_account_id = 'coursegroup:904'
        self.colgsas_template_mock = Mock(spec=CanvasSchoolTemplate)
        self.colgsas_template_mock.id = 1
        self.colgsas_template_mock.school_id = 'colgsas'
        self.colgsas_template_mock.template_id = 6066
        self.colgsas_template_mock.is_default = True
        self.colgsas_template_course = {
            "name": "FAS Course Template QA Fall 2014"
        }
        self.colgsas_template_context_data = [{
            "is_default": True,
            "canvas_course_id": 6066,
            "canvas_course_name": "FAS Course Template QA Fall 2014",
            "canvas_course_url": "https://canvas.dev.tlt.harvard.edu/courses/6066"
        }]

    @patch('icommons_common.canvas_api.helpers.accounts.get_school_accounts')
    def test_get_school_data_for_user(self, mock_get_accounts):
        mock_get_accounts.return_value = self.school_accounts
        result = get_school_data_for_user(self.canvas_user_id)

        for account in result:
            self.assertIn(account['id'], self.school_sis_account_ids)

    @patch('icommons_common.canvas_api.helpers.accounts.get_school_accounts')
    def test_get_school_data_for_user_single(self, mock_get_accounts):
        mock_get_accounts.return_value = self.school_accounts
        result = get_school_data_for_user(self.canvas_user_id, self.school_sis_account_id)

        self.assertEqual(result['id'], self.school_sis_account_id)

    @patch('canvas_site_creator.utils.canvas_api_accounts_helper.get_all_sub_accounts_of_account')
    def test_get_department_data_for_school(self, mock_get_account_by_sis_account_id):
        """ test that dept account exists in dept list returned when no sis dept is given """
        mock_get_account_by_sis_account_id.return_value = self.department_accounts
        result = get_department_data_for_school(self.school_sis_account_id)
        for account in result:
            self.assertIn(account['id'], self.department_sis_account_ids)

    @patch('canvas_site_creator.utils.canvas_api_accounts_helper.get_all_sub_accounts_of_account')
    def test_get_department_data_for_school_single(self, mock_get_account_by_sis_account_id):
        """ test that the correct dept is returned when the dept id is provided """
        mock_get_account_by_sis_account_id.return_value = self.department_accounts
        result = get_department_data_for_school(
            self.school_sis_account_id,
            self.department_sis_account_id
        )
        self.assertEqual(result['id'], self.department_sis_account_id)

    @patch('canvas_site_creator.utils.canvas_api_accounts_helper.get_all_sub_accounts_of_account')
    def test_get_course_group_data_for_school(self, mock_get_account_by_sis_account_id):
        """ test that course group exists in list returned when no course group provided """
        mock_get_account_by_sis_account_id.return_value = self.course_group_accounts
        result = get_course_group_data_for_school(self.school_sis_account_id)
        for account in result:
            self.assertIn(account['id'], self.course_group_sis_account_ids)

    @patch('canvas_site_creator.utils.canvas_api_accounts_helper.get_all_sub_accounts_of_account')
    def test_get_course_group_data_for_school_single(self, mock_get_account_by_sis_account_id):
        mock_get_account_by_sis_account_id.return_value = self.course_group_accounts
        result = get_course_group_data_for_school(
            self.school_sis_account_id,
            self.course_group_sis_account_id
        )

        self.assertEqual(result['id'], self.course_group_sis_account_id)

    @patch('canvas_site_creator.utils.get_all_list_data')
    @patch('canvas_site_creator.utils.CanvasSchoolTemplate.objects.filter')
    def test_get_canvas_site_templates_for_school(self, mock_filter_canvas_school_template, mock_get_course):
        mock_filter_canvas_school_template.return_value = [self.colgsas_template_mock]
        mock_get_course.return_value = self.colgsas_template_course
        result = get_canvas_site_templates_for_school('colgsas')

        self.assertEqual(result, self.colgsas_template_context_data)

    @patch('canvas_site_creator.utils.get_all_list_data')
    @patch('canvas_site_creator.utils.CanvasSchoolTemplate.objects.filter')
    @patch('canvas_site_creator.utils.settings.CANVAS_URL', 'https://canvas.dev.tlt.harvard.edu')
    def test_get_canvas_site_template(self, mock_filter_canvas_school_template, mock_get_course):
        mock_filter_canvas_school_template.return_value = [self.colgsas_template_mock]
        mock_get_course.return_value = self.colgsas_template_course
        result = get_canvas_site_template('colgsas', self.colgsas_template_mock.template_id)

        self.assertEqual(result, self.colgsas_template_context_data[0])
