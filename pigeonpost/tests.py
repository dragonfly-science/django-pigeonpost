import datetime

from django.conf import settings
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from pigeonpost.models import Pigeon, Outbox
from pigeonpost_example.models import Message
from pigeonpost.tasks import send_email, kill_pigeons

class ExampleMessage(TestCase):
    """
    Test that the example message gets added to the queue when it is saved
    """
    def setUp(self):
        self.message = Message(subject='Test', body='A test message')
        self.message.save()
        self.pigeon = Pigeon.objects.get(source_content_type=ContentType.objects.get_for_model(self.message),
            source_id=self.message.id)
        User(username='a', first_name="Andrew", last_name="Test", email="a@example.com").save()
        User(username='b', first_name="Boris", last_name="Test", email="b@example.com").save()
        User(username='c', first_name="Chelsea", last_name="Test", email="c@foo.org").save()

    def test_to_send(self):
        """
        When a message is added, the field 'to_send' should be True
        """
        assert(self.pigeon.to_send == True)

    def test_sent_at(self):
        """
        When a message is added, the field 'sent_at' should be None
        """
        assert(self.pigeon.sent_at is None)

    def test_scheduled_for(self):
        """
        The example Message has a deferred sending time of 6 hours
        """
        assert((self.pigeon.scheduled_for - datetime.datetime.now()).seconds > 5*60*60) 
        assert((self.pigeon.scheduled_for - datetime.datetime.now()).seconds < 7*60*60) 
    
    def test_save_many_times(self):
        """
        When a message is saved more than once, only one copy should go on the queue
        """
        self.message.save()
        self.message.save()
        self.message.save()
        pigeons = Pigeon.objects.filter(source_content_type=ContentType.objects.get_for_model(self.message),
            source_id=self.message.id)
        assert(len(pigeons) == 1)

    def test_no_message_sent_now(self):
        """
        As the message is deferred, it won't be sent when send_email is run
        """
        send_email()
        messages = Outbox.objects.all()
        assert(len(messages) == 0)

    def test_message_sent_with_force(self):
        """
        Force sending of all unsent pigeons
        """
        send_email(force=True)
        messages = Outbox.objects.all()
        assert(len(messages) == 2)
    
    def test_kill_pigeons(self):
        """
        Kill pigeons stops any unsent pigeons from delivering messages
        """
        kill_pigeons()
        send_email(force=True)
        messages = Outbox.objects.all()
        assert(len(messages) == 0)

    def test_message_not_sent_more_than_once(self):
        """
        Force sending of all unsent pigeons
        """
        send_email(force=True)
        send_email(force=True)
        messages = Outbox.objects.all()
        assert(len(messages) == 2)
