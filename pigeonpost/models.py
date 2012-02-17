
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

class ContentQueue(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField() #Assume the models have an integer primary key
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    scheduled = models.DateTimeField()

    class Meta:
        unique_together = ('content_type', 'object_id',)
        ordering = ['scheduled',]

class Outbox(models.Model):
    content = models.ForeignKey(ContentQueue)
    user = models.ForeignKey(User)
    message = models.TextField()
    sent = models.DateTimeField()
    retries = models.IntegerField()

    class Meta:
        unique_together = ('content', 'user',)
        ordering = ['sent']



                

