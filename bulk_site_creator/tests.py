import json

from django.test import Client, TestCase
from django.urls import reverse


class BulkCreateJobTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("create_bulk_job")
        self.data = {
            "canvas_user_id": 1,
            "logged_in_user_id": 2,
            "filters": {
                "term": "2018-summer",
                "school": "colgsas",
                "department": "anthropology",
                "course_group": 1,
            },
            "course_instance_ids": [1, 2, 3],
        }

    def test_bulk_create_job_post(self):
        # Make a POST request to the view with the data
        response = self.client.post(
            self.url, data=json.dumps(self.data), content_type="application/json"
        )

        # Assert that the response has a 200 OK status code
        self.assertEqual(response.status_code, 200)

        # Assert that the response content is what you expect
        expected_response = {"status": "success"}
        self.assertEqual(json.loads(response.content), expected_response)
