from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.dispatch import Signal, receiver


class ContentQueue(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()  # Assume the models have an integer primary key
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    successes = models.IntegerField(null=True, blank=True)
    failures = models.IntegerField(null=True, blank=True)
    send = models.BooleanField(default=True)
    sent = models.DateTimeField(null=True, blank=True)
    render_email = models.TextField()
    email_user = models.TextField()
    schedule_time = models.DateTimeField()

    class Meta:
        unique_together = ('content_type', 'object_id',)
        ordering = ['schedule_time',]


class Outbox(models.Model):
    content = models.ForeignKey(ContentQueue)
    user = models.ForeignKey(User)
    message = models.TextField()
    sent = models.DateTimeField()

    class Meta:
        unique_together = ('content', 'user',)
        ordering = ['sent']

pigeonpost_signal = Signal(providing_args=['render_email', 'email_user', 'schedule_time'])


@receiver(pigeonpost_signal)
def add_to_queue(sender, render_email='render_email', email_user='email_user', schedule_time=None, **kwargs):
    if not schedule_time:
        schedule_time = datetime.datetime.now()
    try:
        ContentQueue.objects.get(content_object=sender)
    except ContentQueue.DoesNotExist:
        contentqueue = ContentQueue(content_object=sender,
            render_email=render_email,
            email_user=email_user,
            schedule_time=schedule_time
            )


def send_email():
    sendables = ContentQueue.objects.filter(schedule_time__lt=datetime.datetime.now(), send=True)
    for sendable in sendables:
        failures = 0
        successes = 0
        for user in User.objects.filter(active=True):
            try:
                outmessage = Outbox.objects.get(content=sendable, user=user)
            except Outbox.DoesNotExist:
                if getattr(sendable.content_object, sendable.email_user)():
                    message = getattr(sendable.content_object, sendable.render_email)(user)
                    try:
                        send_mail(subject, message, message.from_email, recipient_list=[user.email])
                        out = Outbox(content=sendable, user=user, message=message, sent=datetime.datetime.now())
                        out.save()
                        successes += 1
                    except SMTPException:
                        failures += 1
                    except:
                        pass
        # Now make a record
        sendable.successes = successes
        sendable.failures = failures
        sendable.sent=datetime.datetime.now()
        seandable.save()

