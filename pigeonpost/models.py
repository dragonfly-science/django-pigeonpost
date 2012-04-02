from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

class Pigeon(models.Model):
    source_content_type = models.ForeignKey(ContentType)
    source_id = models.PositiveIntegerField()  # Assume the models have an integer primary key
    source = generic.GenericForeignKey('source_content_type', 'source_id')
    successes = models.IntegerField(default=0, help_text="Number of successful messages sent.")
    failures = models.IntegerField(default=0, help_text="Number of errors encountered while sending.")
    to_send = models.BooleanField(default=True, help_text="Whether this object should be sent (some time in the future) .")
    sent_at = models.DateTimeField(null=True, blank=True, help_text="Indicates the time that this job was sent.")
    render_email_method = models.TextField(default="render_email", help_text="The name of the method to be called on the sender to generates an EmailMessage for each User.")
    scheduled_for = models.DateTimeField(help_text="The datetime when emails should be sent. Defaults to ASAP.")

    class Meta:
        unique_together = ('source_content_type', 'source_id')
        ordering = ['scheduled_for']


class Outbox(models.Model):
    pigeon = models.ForeignKey(Pigeon, null=True, blank=True)
    user = models.ForeignKey(User)
    message = models.TextField()
    sent_at = models.DateTimeField(null=True, blank=True)
    succeeded = models.BooleanField(default=False)
    failures = models.IntegerField(default=0)

    class Meta:
        unique_together = ('pigeon', 'user')
        ordering = ['sent_at']

