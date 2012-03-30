import logging

import django.core.mail
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import loading
from django.test import TestCase
from mock import MagicMock
from testfixtures import identity, log_capture

import tasks
import models
import pigeonpost_example.models
from pigeonpost_example.models import MessageToEveryone

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


class TestQueuingMessages(TestCase):
    def setUp(self):
        self.old_email_backend = settings.EMAIL_BACKEND
        settings.EMAIL_BACKEND = EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

        if 'pigeonpost_example' not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS += ('pigeonpost_example',)
            loading.cache.loaded = False
            call_command('syncdb', verbosity=0)
        try:
            self.article = MessageToEveryone.objects.get(subject="something interesting")
        except MessageToEveryone.DoesNotExist:
    	    a = MessageToEveryone(subject="something interesting", body="green peas are green")
            a.save()
            self.article = a

        try: 
            users = User.objects.get(last_name='Test')
        except User.DoesNotExist:
            a = User(username='a', first_name="Andrew", last_name="Test", email="a@example.com")
            b = User(username='b', first_name="Boris", last_name="Test", email="b@example.com")
            c = User(username='c', first_name="Chelsea", last_name="Test", email="c@example.com")
            [user.save() for user in [a,b,c]]
            users = User.objects.all()
        self.users = users

    def tearDown(self):
        if hasattr(django.core.mail, 'outbox'):
            django.core.mail.outbox = []
        settings.EMAIL_BACKEND = self.old_email_backend

    def test_inactive_users_are_ignored(self):
        try:
            inactive = User.objects.get(username="inactive")
        except User.DoesNotExist:
            inactive = User(username='inactive', first_name="Non-actor", is_active=False, email="ina@example.com")
            inactive.save()
        
        # email, check that ina@example.com wasn't included as a recipient

