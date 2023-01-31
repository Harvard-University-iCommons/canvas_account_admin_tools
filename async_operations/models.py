# -*- coding: utf-8 -*-

import inspect
import logging

from django.core import serializers
from django.db import models

from django.utils import timezone
from django.db.models import JSONField
import django_rq

from async_operations import introspection


logger = logging.getLogger(__name__)


class Process(models.Model):
    """
    Data model for generic asynchronous processes which allows the tracking of state/status.
    This is designed to be a thin wrapper around RQ jobs so that their state can be queried.
    """
    QUEUED = 'queued'
    ACTIVE = 'active'
    COMPLETE = 'complete'
    PROCESS_STATES = (
        (QUEUED, 'Queued'),
        (ACTIVE, 'Active'),
        (COMPLETE, 'Complete')
    )
    process_states_dict = dict(PROCESS_STATES)

    name = models.CharField(max_length=128)
    source = models.CharField(max_length=128)
    state = models.CharField(max_length=16, choices=PROCESS_STATES, default=QUEUED)
    status = models.CharField(max_length=16, blank=True, default='')
    # Details can be populated with process domain specific data to provide
    # additional details related to the process
    details = JSONField(null=True, blank=True)
    date_created = models.DateTimeField(blank=True, default=timezone.now)
    date_active = models.DateTimeField(null=True, blank=True)
    date_complete = models.DateTimeField(null=True, blank=True)
    created_by_user_id = models.CharField(max_length=20, blank=True)

    @property
    def is_complete(self):
        return self.state == Process.COMPLETE

    @property
    def status_display(self):
        if self.is_complete:
            return self.status.title()
        else:
            return self.state_display

    @property
    def state_display(self):
        return self.process_states_dict.get(self.state, '')

    @classmethod
    def enqueue(cls, func, queue='default', audit_user='', *args, **kwargs):
        """
        Creates the Process model for tracking the passed RQ job function
        and puts the job on the Redis queue.

        :param func: The RQ job function
        :param queue: RQ queue to put the job on
        :param audit_user:
        :param args:
        :param kwargs:
        :return: The Process model which tracks the RQ job
        """
        # Create the Process model with the fully qualified function name of the
        # RQ job Include the passed args and kwargs in the details jsonb field
        process = cls(
            name="%s.%s" % (inspect.getmodule(func).__name__, func.__name__),
            source=introspection.caller_name(),
            created_by_user_id=audit_user,
            details={
                'queue': queue,
                'args': args,
            }
        )
        process.details.update(kwargs)
        process.save()

        # Enqueue the job for later execution by an RQ worker
        job = django_rq.get_queue(queue).enqueue(func, process.id, *args, **kwargs)

        # From this point forward, the job can be picked up by an RQ worker, and
        # the job may write back into the job redis key or the Process record at
        # any time, so we want to avoid further updates to either the RQ job or
        # the Process record (although we could attempt the latter with
        # select_for_update() if needed, but only if the worker function also
        # used select_for_update() for all of its writes back to the Process
        # record as well)

        logger.debug('Enqueued async_operations.models.Process: {}'.format(process))
        logger.debug('RQ job for process {}: {}'.format(process.id, job))

        return process

    def __unicode__(self):
        return str(self.as_dict())

    def as_json(self):
        return serializers.serialize('json', [self])

    def as_dict(self):
        fv_list = [(f.name, getattr(self, f.name)) for f in self._meta.fields]
        return dict(fv_list)

    # todo: do we need really need the error handling here?
    def update_field(self, field_name, value, raise_exception=False):
        """
        Updates single field on job record. Return True if update succeeded.
        If raise_exception param is not True, or not provided, it will return
        False if update fails. If raise_exception is True, it will re-raise
        failures/exceptions.
        """
        setattr(self, field_name, value)
        try:
            self.save(update_fields=[field_name])
        except Exception as e:
            if raise_exception:
                raise e
            else:
                return False
        return True

    def save(self, update_fields=None, *args, **kwargs):
        super(Process, self).save(*args, update_fields=update_fields, **kwargs)

    def update_state(self, state, raise_exception=False):
        self.update_field('state', state, raise_exception=raise_exception)

    def update_status(self, status, raise_exception=False):
        self.update_field('status', status, raise_exception=raise_exception)
