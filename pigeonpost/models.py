from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.dispatch import Signal, receiver

class ContentQueue(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()  # Assume the models have an integer primary key
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    successes = models.IntegerField(null=True, blank=True, help_text="Number of successful messages sent.")
    failures = models.IntegerField(null=True, blank=True, help_text="Number of errors encountered while sending.")
    send = models.BooleanField(default=True, help_text="Whether this object should be sent (some time in the future) .")
    sent = models.DateTimeField(null=True, blank=True, help_text="Indicates whether the object has been sent.")
    render_email = models.TextField(help_text="The name of the method to be called on the sender to generates an EmailMessage for each User.")
    schedule_time = models.DateTimeField(help_text="The datetime when emails should be sent.")

    class Meta:
        unique_together = ('content_type', 'object_id',)
        ordering = ['schedule_time',]


class Outbox(models.Model):
    content = models.ForeignKey(ContentQueue)
    user = models.ForeignKey(User)
    message = models.TextField()
    sent = models.DateTimeField()
    succeeded = models.BooleanField()
    failures = models.IntegerField()

    class Meta:
        unique_together = ('content', 'user',)
        ordering = ['sent']

pigeonpost_signal = Signal(providing_args=['render_email', 'schedule_time'])


@receiver(pigeonpost_signal)
def add_to_queue(sender, render_email='render_email', schedule_time=None, **kwargs):
    if not schedule_time:
        schedule_time = datetime.datetime.now()
    try:
        ContentQueue.objects.get(content_object=sender)
    except ContentQueue.DoesNotExist:
        contentqueue = ContentQueue(content_object=sender,
            render_email=render_email,
            schedule_time=schedule_time
            )


def send_email(scheduled_time=None):
    if scheduled_time is None:
        scheduled_time = datetime.datetime.now()
    sendables = ContentQueue.objects.filter(schedule_time__lt=scheduled_time, send=None)
    for sendable in sendables:
        failures = 0
        successes = 0
        for user in User.objects.filter(active=True):
            try:
                outmessage = Outbox.objects.get(content=sendable, user=user)
            except Outbox.DoesNotExist:
	        render_email = getattr(sendable.content_object, sendable.render_email)
                message = render_email(user)
                if message:
		    outbox = Outbox(content=sendable, user=user, message=message, succeeded=False, failures=1, sent=datetime.datetime.now())
                    try:
                        message.to = [user.email]
                        message.send()
                        outbox.succeeded = True
                        outbox.failures = 0
                        successes += 1
                    except KeyboardInterrupt:
                        raise
                    except:
                        failures += 1
                    outbox.save()
        # Now make a record
        sendable.successes = successes
        sendable.failures = failures
        sendable.sent=datetime.datetime.now()
        sendable.send=False
        seandable.save()

def kill_pigeons():
    """Mark all unsent pigeons in the queue as send=False, so that they won't
    generate any messages. This is the pigeonpost panic button"""
    for pigeon in ContentQueue.objects.filter(send=True):
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
