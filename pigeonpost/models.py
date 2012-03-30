from smtplib import SMTPException
try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.dispatch import Signal, receiver

class Pigeon(models.Model):
    source_content_type = models.ForeignKey(ContentType)
    source_id = models.PositiveIntegerField()  # Assume the models have an integer primary key
    source = generic.GenericForeignKey('source_content_type', 'source_id')
    successes = models.IntegerField(default=0, help_text="Number of successful messages sent.")
    failures = models.IntegerField(default=0, help_text="Number of errors encountered while sending.")
    to_send = models.BooleanField(default=True, help_text="Whether this object should be sent (some time in the future) .")
    sent_at = models.DateTimeField(null=True, blank=True, help_text="Indicates the time that this job was sent.")
    render_email_method = models.TextField(default="render_email", help_text="The name of the method to be called on the sender to generates an EmailMessage for each User.")
    scheduled_for = models.DateTimeField(auto_now_add=True, help_text="The datetime when emails should be sent. Defaults to ASAP.")

    class Meta:
        unique_together = ('source_content_type', 'source_id')
        ordering = ['scheduled_for']


class Outbox(models.Model):
    pigeon = models.ForeignKey(Pigeon)
    user = models.ForeignKey(User)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    succeeded = models.BooleanField(default=True)
    failures = models.IntegerField(default=0)

    class Meta:
        unique_together = ('pigeon', 'user')
        ordering = ['sent_at']

pigeonpost_signal = Signal(providing_args=['render_email_method', 'scheduled_for'])


@receiver(pigeonpost_signal)
def add_to_queue(sender, render_email_method='render_email', scheduled_for=None, **kwargs):
    if not scheduled_for:
        scheduled_for = datetime.datetime.now()
    try:
        Pigeon.objects.get(source=sender)
    except Pigeon.DoesNotExist:
        p = Pigeon(source=sender, render_email_method=render_email_method, scheduled_for=scheduled_for)
        p.save()


def send_email(as_of=None):
    if as_of is None:
        as_of = datetime.datetime.now()
    sendables = Pigeon.objects.filter(schedule_time__lt=as_of, to_send=True)
    try:
        connection = mail.get_connection()
        for pigeon in sendables:
            for user in User.objects.filter(active=True):
	        render_email = getattr(pigeon.source, pigeon.render_email_method)
                message = render_email(user)
                if message:
                    try:
                        Outbox.objects.get(pigeon=pigeon, user=user)
                    except Outbox.DoesNotExist:
		        outbox = Outbox(content=pigeon,user=user, message=pickle.dumps(message, 2))
                        res = connection.send_messages([message])
                        if res == 1:
                            pigeon.successes += 1
                        else:
                            outbox.succeeded = False
                            outbox.failures = 1
                            pigeon.failures += 1
                        outbox.save()
            # Now make a record
            pigeon.sent_at=datetime.datetime.now()
            pigeon.to_send=False
            seandable.save()
    finally:
        connection.close()

def kill_pigeons():
    """Mark all unsent pigeons in the queue as send=False, so that they won't
    generate any messages. This is the pigeonpost panic button"""
    for pigeon in Pigeon.objects.filter(send=True):
        pigeon.send = False
        pigeon.save()

def retry(max_retries=3):
    """
    retry attempts to resend any emails that have failed.
    
    It is designed to be run from a periodicly, e.g. daily via cron.
    """
    failures = Outbox.objects.filter(failures__lt=max_retries, succeeded=False)
    for outbox in failures:
        try:
            message.to = outbox.user.email
            message.send()
            outbox.succeeded = True
            outbox.sent = datetime.datetime.now()
        except:
            outbox.failures = msg.failures + 1
        outbox.save()
