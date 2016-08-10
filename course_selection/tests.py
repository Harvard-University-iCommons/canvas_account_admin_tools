from __future__ import unicode_literals

from django.test import RequestFactory, TestCase
from mock import Mock, patch

from course_selection.views import locate_course

COURSE_SEARCH_URL = 'https://portal.my.harvard.edu/psp/hrvihprd/EMPLOYEE/EMPL/h/?jsconfig=%7B%22OpenLightbox%22%3Atrue%7D&tab=HU_CLASS_SEARCH&SearchReqJSON=%7B%22SearchText%22%3A%22%28CLASS_NBR%3A{}%29+%28STRM%3A{}%29%22%7D'
GENERIC_SEARCH_URL = 'https://portal.my.harvard.edu/psp/hrvihprd/EMPLOYEE/EMPL/h/?tab=HU_CLASS_SEARCH'


class TermStub:

    cs_strm = None

    def __init__(self, cs_strm):
        self.cs_strm = cs_strm


class CiStub:

    cs_class_number = None
    term = None

    def __init__(self, cs_class_number, term):
        self.cs_class_number = cs_class_number
        self.term = term


class CourseSelectionViewTest(TestCase):

    def setUp(self):
        super(CourseSelectionViewTest, self).setUp()
        self.request = RequestFactory().get('/fake-path')
        self.request.GET = {
            'course_instance_id': 1,
        }
        self.request.user = Mock(is_authenticated=Mock(return_value=True))

    @patch('course_selection.views.CourseInstance.objects.get')
    def test_locate_course_called_with_valid_course_id(self, mock_ci_get):
        """
        test that the view redirects to the correct url when a valid course is
        found
        """
        ci = CiStub(12345, TermStub(4935))
        mock_ci_get.return_value = ci
        response = locate_course(self.request)
        mock_ci_get.assert_called_with(course_instance_id=1)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, COURSE_SEARCH_URL.format(12345, 4935))


    def test_locate_course_called_with_invalid_course_id(self):
        """
        test that the view returns the generic url when a course was not found
        for the given id
        """
        request = self.request
        del request.GET['course_instance_id']
        response = locate_course(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, GENERIC_SEARCH_URL)


    @patch('course_selection.views.CourseInstance.objects.get')
    def test_locate_course_called_with_unknown_course_instance(self, mock_ci_get):
        """
        test that the view returns the generic url if no course object is found
        """
        mock_ci_get.return_value = None
        response = locate_course(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, GENERIC_SEARCH_URL)

    @patch('course_selection.views.CourseInstance.objects.get')
    def test_locate_course_called_with_course_instance_missing_cs_data(self, mock_ci_get):
        """
        test that the view returns the generic url if no course object is found
        """
        mock_ci_get.return_value = CiStub(None, TermStub(None))
        response = locate_course(self.request)
        mock_ci_get.assert_called_with(course_instance_id=1)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, GENERIC_SEARCH_URL)
