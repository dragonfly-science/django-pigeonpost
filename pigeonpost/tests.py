import logging

from django.conf import settings
from django.test import TestCase
from mock import MagicMock
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

class DummyCompliantSender:
    email_render = lambda self: sys.stdout.write('email_render called')
    email_defer = lambda self: 10
    

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
    def test_error_on_bad_input(self, capture):
        logger_name = 'pigeonpost.tasks'
        msg = ' requires an email_render method.'
        tasks.queue_to_send(DummySenderA())
        tasks.queue_to_send(DummySenderB())
        capture.check(
            (logger_name, 'ERROR', 'A' + msg),
            (logger_name, 'ERROR', 'B' + msg),
        )                    
    
    def test_that_a_defer_email_method_is_respected(self):
        sender = DummyCompliantSender()
        sender.defer_email = MagicMock(name='defer_email')
        tasks.queue_to_send(sender)
        self.assertTrue(sender.defer_email.called)
