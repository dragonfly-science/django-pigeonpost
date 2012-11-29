from django import forms
from django.db import models
from django.contrib import admin

from django.contrib.admin import ModelAdmin
from pigeonpost.models import Pigeon, Outbox

class PigeonAdmin(ModelAdmin):
    list_display = ('id', 'source', 'scheduled_for', 'render_email_method', 'successes', 'failures')
    list_filter = ('to_send',)

admin.site.register(Pigeon, PigeonAdmin)


class OutboxAdmin(ModelAdmin):
    list_display = ('pigeon', 'user', 'sent_at', 'succeeded', 'failures')
    list_filter = ('user',)
admin.site.register(Outbox, OutboxAdmin)

