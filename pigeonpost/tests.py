import datetime

from django.conf import settings
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
settings.AUTH_PROFILE_MODULE = 'pigeonpost_example.Profile'

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.test import TestCase

from pigeonpost.models import Pigeon, Outbox
from pigeonpost_example.models import ModeratedNews, News, Profile
from pigeonpost.tasks import send_email, kill_pigeons, process_queue, process_outbox
from pigeonpost.signals import pigeonpost_queue

def create_fixtures():
    # Set up test users
    andrew  = User(username='a', first_name="Andrew", last_name="Test", email="a@example.com")
    boris   = User(username='b', first_name="Boris", last_name="Test", email="b@example.com")
    chelsea = User(username='c', first_name="Chelsea", last_name="Test", email="c@foo.org")
    users = [andrew, boris, chelsea]
    for user in users:
        user.save()
    p1 = Profile(user=andrew, subscribed_to_news=True)
    p2 = Profile(user=boris, subscribed_to_news=True)
    p3 = Profile(user=chelsea, subscribed_to_news=False)
    for p in [p1, p2, p3]:
        p.save()

    # Setup test pigeon/message
    message = News(subject='Test', body='A test message')
    message.save()
    pigeon = Pigeon.objects.get(
        source_content_type=ContentType.objects.get_for_model(message),
        source_id=message.id)
    return users, message, pigeon


class TestExampleMessage(TestCase):
    """
    Test that the example message gets added to the queue when it is saved.
    """

    def setUp(self):
        self.users, self.message, self.pigeon = create_fixtures()
        
    def test_to_send(self):
        """ When a message is added, the field 'to_send' should be True """
        self.assertEqual(self.pigeon.to_send, True)

    def test_sent_at(self):
        """ When a message is added, the field 'sent_at' should be None """
        assert(self.pigeon.sent_at is None)

    def test_scheduled_for(self):
        """ The example Message has a deferred sending time of 6 hours """
        assert((self.pigeon.scheduled_for - datetime.datetime.now()).seconds > 5*60*60) 
        assert((self.pigeon.scheduled_for - datetime.datetime.now()).seconds < 7*60*60) 
    
    def test_save_many_times(self):
        """ When a message is saved more than once, only one copy should go on the queue """
        self.message.save()
        self.message.save()
        self.message.save()
        pigeons = Pigeon.objects.filter(source_content_type=ContentType.objects.get_for_model(self.message),
            source_id=self.message.id)
        self.assertEqual(len(pigeons), 1)

    def test_no_message_sent_now(self):
        """ As the message is deferred, it won't be sent when send_email is run """
        send_email()
        messages = Outbox.objects.all()
        self.assertEqual(len(messages), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_message_sent_with_force(self):
        """ Force sending of all unsent pigeons """
        send_email(force=True)
        messages = Outbox.objects.all()
        self.assertEqual(len(messages), 2)
        self.assertEqual(len(mail.outbox), 2)
    
    def test_kill_pigeons(self):
        """ Kill pigeons stops any unsent pigeons from delivering messages """
        kill_pigeons()
        send_email(force=True)
        messages = Outbox.objects.all()
        self.assertEqual(len(messages), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_message_not_sent_more_than_once(self):
        """ Force sending of all unsent pigeons """
        send_email(force=True)
        send_email(force=True)
        messages = Outbox.objects.all()
        self.assertEqual(len(messages), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_updated_scheduled_for(self):
        """ Sending the same pigeon details just updates scheduled_for """

        # First try using defer_for
        pigeonpost_queue.send(sender=self.message, defer_for=10) # 10 seconds
        pigeon = Pigeon.objects.get(
            source_content_type=ContentType.objects.get_for_model(self.message),
            source_id=self.message.id)
        delta = pigeon.scheduled_for - datetime.datetime.now()
        self.assertTrue(delta.seconds<=10)

        # now try with scheduled_for
        now = datetime.datetime.now()
        pigeonpost_queue.send(sender=self.message, scheduled_for=now)
        pigeon = Pigeon.objects.get(
            source_content_type=ContentType.objects.get_for_model(self.message),
            source_id=self.message.id)
        self.assertEqual(pigeon.scheduled_for, now)


class FakeSMTPConnection:
    def send_messages(*msgs, **meh):
        return 0

    def close(*aa, **kwaa):
        return True

class TestFaultyConnection(TestCase):
    def setUp(self):
        self.users, self.message, self.pigeon = create_fixtures()
        self._get_conn = mail.get_connection
        mail.get_connection = lambda *aa, **kw: FakeSMTPConnection()
    
    def tearDown(self):
        mail.get_connection = self._get_conn

    def test_faulty_connection(self):
        """ Check that we are noting failures. """
        send_email()
        outboxes = Outbox.objects.all()
        for ob in outboxes:
            self.assertEqual(ob.succeeded, False)
            self.assertEqual(ob.failures, 1)
            assert(ob.pigeon.failures > 0)
        
    def test_message_not_sent_more_than_once(self):
        pass

    def test_message_sent_with_force(self):
        pass
        

class TestImmediateMessage(TestCase):
    def setUp(self):
        andrew  = User(username='a', first_name="Andrew", last_name="Test", email="a@example.com")
        boris   = User(username='b', first_name="Boris", last_name="Test", email="b@example.com")
        chelsea = User(username='c', first_name="Chelsea", last_name="Test", email="c@foo.org")
        z = User(username='z', first_name="Zach", last_name="Test", email="z@example.com", is_staff=True)
        x = User(username='x', first_name="Xray", last_name="Test", email="x@example.com", is_staff=True)
        self.users = [andrew, boris, chelsea, z, x]
        self.staff = [z, x]
        for user in self.users:
            user.save()
            Profile(user=user, subscribed_to_news=True).save()
        self.users = set(self.users)
        self.staff = set(self.staff)
        ModeratedNews(subject='...', body='...', published=True).save()

        process_queue()
 
    def test_outboxes_for_staff(self):
        messages = Outbox.objects.all()
        self.assertEqual(len(messages),2)
        for m in messages:
            assert m.user in self.staff

    def test_no_outboxes_for_nonstaff(self):
        messages = Outbox.objects.all()
        nonstaff = self.users - self.staff
        self.assertEqual(len(messages),2)
        for m in messages:
            assert m.user not in nonstaff

