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

class TestExampleMessage(TestCase):
    """
    Test that the example message gets added to the queue when it is saved.
    """

    def setUp(self):
        self.message = News(subject='Test', body='A test message')
        self.message.save()
        self.pigeon = Pigeon.objects.get(
            source_content_type=ContentType.objects.get_for_model(self.message),
            source_id=self.message.id)
        self.pigeon.save()
        andrew  = User(username='a', first_name="Andrew", last_name="Test", email="a@example.com")
        boris   = User(username='b', first_name="Boris", last_name="Test", email="b@example.com")
        chelsea = User(username='c', first_name="Chelsea", last_name="Test", email="c@foo.org")
        self.users = [andrew, boris, chelsea]
        [user.save() for user in self.users]
        p1 = Profile(user=andrew, subscribed_to_news=True)
        p2 = Profile(user=boris, subscribed_to_news=True)
        p3 = Profile(user=chelsea, subscribed_to_news=False)
        [p.save() for p in [p1, p2, p3]]
        
    def test_to_send(self):
        """
        When a message is added, the field 'to_send' should be True
        """
        self.assertEqual(self.pigeon.to_send, True)

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
        self.assertEqual(len(pigeons), 1)

    def test_no_message_sent_now(self):
        """
        As the message is deferred, it won't be sent when send_email is run
        """
        send_email()
        messages = Outbox.objects.all()
        self.assertEqual(len(messages), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_message_sent_with_force(self):
        """
        Force sending of all unsent pigeons
        """
        send_email(force=True)
        messages = Outbox.objects.all()
        self.assertEqual(len(messages), 2)
        self.assertEqual(len(mail.outbox), 2)
    
    def test_kill_pigeons(self):
        """
        Kill pigeons stops any unsent pigeons from delivering messages
        """
        kill_pigeons()
        send_email(force=True)
        messages = Outbox.objects.all()
        self.assertEqual(len(messages), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_message_not_sent_more_than_once(self):
        """
        Force sending of all unsent pigeons
        """
        send_email(force=True)
        send_email(force=True)
        messages = Outbox.objects.all()
        self.assertEqual(len(messages), 2)
        self.assertEqual(len(mail.outbox), 2)

class FakeSMTPConnection:
    def send_messages(*msgs, **meh):
        return 0

    def close(*aa, **kwaa):
        return True

class TestFaultyConnection(TestExampleMessage):
    def setUp(self):
        super(TestFaultyConnection, self).setUp()
        self._get_conn = mail.get_connection
        mail.get_connection = lambda *aa, **kw: FakeSMTPConnection()
    
    def tearDown(self):
        mail.get_connection = self._get_conn

    def test_faulty_connection(self):
        """
        Check that we are noting failures.
        """
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
        ModeratedNews(subject='...', body='...', published=True).save()
        andrew  = User(username='a', first_name="Andrew", last_name="Test", email="a@example.com")
        boris   = User(username='b', first_name="Boris", last_name="Test", email="b@example.com")
        chelsea = User(username='c', first_name="Chelsea", last_name="Test", email="c@foo.org")
        z = User(first_name="Zach", last_name="Test", email="z@example.com", is_staff=True)
        x = User(first_name="Xray", last_name="Test", email="x@example.com", is_staff=True)
        self.users = set([andrew, boris, chelsea, z, x])
        self.staff = set([z, x])
        [user.save() for user in self.users]
        [Profile(user=user, subscribed_to_news=True).save() for user in self.users]
 
    def test_outboxes_for_staff(self):
        messages = Outbox.objects.all()
        for m in messages:
            assert m.user in self.staff

    def test_no_outboxes_for_nonstaff(self):
        messages = Outbox.objects.all()
        nonstaff = self.users - self.staff
        for m in messages:
            assert m.user not in nonstaff
