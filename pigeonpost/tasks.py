import datetime
import logging

from celery.task import task
from django.core.mail.backends.smtp import EmailBackend
from django.contrib.auth.models import User

from pigeonpost.models import ContentQueue, Outbox, send_email

logger = logging.getLogger('pigeonpost.tasks')


@task
def queue_to_send(sender, **kwargs):
    # Check to see if the object is mailable
    try:
        now = datetime.date.today()
        countdown = 0
        if hasattr(sender, 'email_defer'):
            countdown = sender.email_defer()
            scheduled = now + datetime.timedelta(seconds=countdown)
        # Save it in the model
        try:
            post = ContentQueue.get(content_object=sender)
        except ContentQueue.DoesNotExist:
            post = ContentQueue(content_object=sender, scheduled=scheduled)
            post.save()
            # Create a task to send
            send_messages.delay(sender, countdown=countdown)
    except AttributeError:
	if not hasattr(sender, 'email_render') or not hasattr(sender, 'email_user'):
            logger.error('%r requires both email_render and email_user methods.' % sender)
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
