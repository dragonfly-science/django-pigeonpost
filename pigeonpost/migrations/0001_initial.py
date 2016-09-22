# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Outbox',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.TextField()),
                ('sent_at', models.DateTimeField(null=True, blank=True)),
                ('succeeded', models.BooleanField(default=False)),
                ('failures', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['sent_at'],
                'verbose_name_plural': 'outboxes',
            },
        ),
        migrations.CreateModel(
            name='Pigeon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source_id', models.PositiveIntegerField(null=True, blank=True)),
                ('successes', models.IntegerField(default=0, help_text=b'Number of successful messages sent.')),
                ('failures', models.IntegerField(default=0, help_text=b'Number of errors encountered while sending.')),
                ('to_send', models.BooleanField(default=True, help_text=b'Whether this object should be sent (some time in the future).')),
                ('sent_at', models.DateTimeField(help_text=b'Indicates the time that this job was sent.', null=True, blank=True)),
                ('send_to_method', models.TextField(help_text=b'If specified, we call send_to_method to get the users that will be called with render_email_method.', null=True, blank=True)),
                ('render_email_method', models.TextField(default=b'render_email', help_text=b'The name of the method to be called on the sender to generates an EmailMessage for each User.')),
                ('scheduled_for', models.DateTimeField(help_text=b'The datetime when emails should be sent. Defaults to ASAP.')),
                ('send_to', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, help_text=b'If specified, we call only call render_email_method for this user.', null=True)),
                ('source_content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['scheduled_for'],
            },
        ),
        migrations.AddField(
            model_name='outbox',
            name='pigeon',
            field=models.ForeignKey(blank=True, to='pigeonpost.Pigeon', null=True),
        ),
        migrations.AddField(
            model_name='outbox',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='outbox',
            unique_together=set([('pigeon', 'user')]),
        ),
    ]
