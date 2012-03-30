import datetime
import logging

from celery.task import task
from django.core.mail.backends.smtp import EmailBackend
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from pigeonpost.models import Pigeon, Outbox, send_email

logger = logging.getLogger('pigeonpost.tasks')


@task
def queue_to_send(sender, **kwargs):
    # Check to see if the object is mailable
    try:
        scheduled_for = datetime.date.today()
        countdown = 0
        if hasattr(sender, 'email_defer'):
            countdown = sender.email_defer()
            scheduled += datetime.timedelta(seconds=countdown)
        # Save it in the model
        try:
            pigeon = Pigeon.objects.get(source_content_type=ContentType.objects.get_for_model(sender),
                source_id=sender.id)
        except Pigeon.DoesNotExist:
            pigeon = Pigeon(source=sender, scheduled_for=scheduled_for)
            pigeon.save()
            # Create a task to send
            send_messages.delay(sender, countdown=countdown)
    except AttributeError:
	if not hasattr(sender, 'email_render'):
            logger.error('%r requires a email_render method.' % sender)
        else:
            raise
            


@task
def send_messages(content, backend=EmailBackend):
    users = User.objects.all()
    for user in users:
        msg = content.render_email(user)
        if msg:
            msg.send()


@task
def send_pending_messages():
    send_email()
