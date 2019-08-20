# -*- coding: utf-8 -*-

from mock import patch

from django.conf import settings
from django.db.models.signals import post_save
from django.test import TestCase
from django_rq.queues import get_queues
from django_rq.workers import get_exception_handlers
from rq import (
    get_current_job,
    SimpleWorker)

from async_operations.models import Process
from publish_courses.async_operations import bulk_publish_canvas_sites

QUEUE_NAME = settings.RQWORKER_QUEUE_NAME


# modeled from https://github.com/ui/django-rq/blob/v0.9.4/django_rq/workers.py
# but needed to change Worker to SimpleWorker to avoid RQ's forking behavior
# while in Django test cases (see http://python-rq.org/docs/testing/).
def get_simple_worker(*queue_names):
    """
    Returns a RQ worker for all queues or specified ones.
    """
    queues = get_queues(*queue_names)
    return SimpleWorker(queues,
                        connection=queues[0].connection,
                        exception_handlers=get_exception_handlers() or None)


class BulkPublishCanvasSitesBaseTestCase(TestCase):
    def setUp(self):
        super(BulkPublishCanvasSitesBaseTestCase, self).setUp()
        self.account = 'colgsas'
        self.term = '2017-1'
        self.test_user_id = '12345678'
        self.process = Process.enqueue(
            bulk_publish_canvas_sites,
            QUEUE_NAME,
            account='sis_account_id:school:{}'.format(self.account),
            term='sis_term_id:{}'.format(self.term),
            audit_user=self.test_user_id,
            course_list=None)

        self._refresh_from_db()
        self.assertIsNotNone(self.process.date_created)
        self.assertIsNone(self.process.date_active)
        self.assertEqual(self.process.state, Process.QUEUED)
        self.assertEqual(self.process.status, '')

    @staticmethod
    def _flush_jobs():
        get_simple_worker(QUEUE_NAME).work(burst=True)

    def _refresh_from_db(self):
        self.process.refresh_from_db()


@patch('publish_courses.async_operations.BulkCourseSettingsOperation.execute')
class ActiveStateTestCase(BulkPublishCanvasSitesBaseTestCase):

    def _add_handler(self):
        post_save.connect(self._process_save_signal_handler, sender=Process)

    def _remove_handler(self):
        post_save.disconnect(self._process_save_signal_handler, sender=Process)

    def _process_save_signal_handler(self, sender, instance, **kwargs):
        self.assertIsNotNone(instance.date_created)
        self.assertIsNotNone(instance.date_active)
        self.assertEqual(instance.state, Process.ACTIVE)
        self.assertEqual(instance.status, '')
        self.have_asserted_active = True

    def test_activate(self, mock_execute, *args, **kwargs):
        # process status, timestamps updated when activated

        self.have_asserted_active = False
        self._add_handler()
        mock_execute.side_effect = self._remove_handler
        self._flush_jobs()
        self.assertTrue(self.have_asserted_active)


@patch('publish_courses.async_operations.BulkCourseSettingsOperation.execute')
class JobLinkedToProcessTestCase(BulkPublishCanvasSitesBaseTestCase):

    def _assert_job_contains_process_metadata(self):
        self.job = get_current_job()
        self.assertDictContainsSubset(
            {'process_id': self.process.id},
            self.job.meta)

    def test_job_linked_to_process(self, mock_execute, *args, **kwargs):
        # job updated with process id when activated
        # process updated with job id when activated
        mock_execute.side_effect = self._assert_job_contains_process_metadata
        self._flush_jobs()
        self._refresh_from_db()
        self.assertDictContainsSubset(
            {'rq_job_id': self.job.id},
            self.process.details)


@patch('publish_courses.async_operations.BulkCourseSettingsOperation.execute')
class CompletedStateTestCase(BulkPublishCanvasSitesBaseTestCase):

    def _assert_complete(self):
        self.assertIsNotNone(self.process.date_active)
        self.assertIsNotNone(self.process.date_complete)
        self.assertEqual(self.process.state, Process.COMPLETE)

    def test_completed(self, mock_execute, *args, **kwargs):
        # process status, timestamps, details updated when successfully completed
        self._flush_jobs()
        self._refresh_from_db()
        self._assert_complete()
        self.assertEqual(self.process.status, '')
        self.assertNotIn('error', list(self.process.details.keys()))

    def test_failed(self, mock_execute, *args, **kwargs):
        # process status, timestamps, details updated when failed (completed)
        mock_execute.side_effect = RuntimeError
        self._flush_jobs()
        self._refresh_from_db()
        self._assert_complete()
        self.assertEqual(self.process.status, 'failed')
        self.assertIn('error', list(self.process.details.keys()))


class PublishCoursesTestCase(BulkPublishCanvasSitesBaseTestCase):
    """
    If a list of course id's are not given at process creation,
    then the course_list and courses keys should be None.
    """
    def test_publish_all(self, *args):
        self._refresh_from_db()
        self.assertEqual(self.process.state, Process.QUEUED)
        self.assertIsNone(self.process.details['course_list'])

        self._flush_jobs()
        self._refresh_from_db()
        self.assertEqual(self.process.state, Process.COMPLETE)
        self.assertIsNone(self.process.details['course_list'])
        self.assertIsNone(self.process.details['op_config']['courses'])

    """
    If a list of course id's are given at process creation,
    then the course_list and courses keys should match the given list of id's.
    """
    def test_publish_selected(self, *args):
        self.process = Process.enqueue(
            bulk_publish_canvas_sites,
            QUEUE_NAME,
            account='sis_account_id:school:{}'.format(self.account),
            term='sis_term_id:{}'.format(self.term),
            audit_user=self.test_user_id,
            course_list=[123, 124, 125])

        self._refresh_from_db()
        self.assertIsNotNone(self.process.date_created)
        self.assertEqual(self.process.state, Process.QUEUED)
        self.assertEqual(self.process.details['course_list'], [123, 124, 125])

        self._flush_jobs()
        self._refresh_from_db()
        self.assertEqual(self.process.state, Process.COMPLETE)
        self.assertEqual(self.process.details['course_list'], [123, 124, 125])
        self.assertEqual(self.process.details['op_config']['courses'], [123, 124, 125])
