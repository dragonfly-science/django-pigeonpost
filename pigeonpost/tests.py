import logging

from django.conf import settings
from django.test import TestCase
from testfixtures import identity, log_capture

import tasks
import models

class DummySenderA:
    def __repr__(self):
        return u'A'

class DummySenderB:
    email_render = lambda self: sys.stdout.write('email_render called')

    def __repr__(self):
        return u'B'

class DummySenderC:
    email_user = lambda self: sys.stdout.write('email_user called')

    def __repr__(self):
        return u'C'

class TestTaskQueueToSend(TestCase):
    def setUp(self):
        self.old_settings = settings.LOGGING
        settings.LOGGING['handlers']['stdout'] = {
            'class': 'logging.StreamHandler',
            'level':'DEBUG', 
            'formatter': 'simple'
        }

        settings.LOGGING['loggers']['pigeonpost.tasks'] = {
            'handlers': ['stdout'],
            'level': 'DEBUG'
        }

    def tearDown(self):
        settings.LOGGING = self.old_settings

    @log_capture('pigeonpost.tasks')
    def test_logs_warning_on_bad_input(self, capture):
        logger_name = 'pigeonpost.tasks'
        msg = ' requires both email_render and email_user methods.'
        tasks.queue_to_send(DummySenderA())
        tasks.queue_to_send(DummySenderB())
        tasks.queue_to_send(DummySenderC())
        capture.check(
            (logger_name, 'ERROR', 'A' + msg),
            (logger_name, 'ERROR', 'B' + msg),
            (logger_name, 'ERROR', 'C' + msg)
        )                    

