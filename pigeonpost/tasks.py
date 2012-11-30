import datetime
import logging
import smtplib
try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.core import mail
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import EmailMessage

from pigeonpost.models import Pigeon, Outbox
from pigeonpost.signals import pigeonpost_queue
from pigeonpost.signals import pigeonpost_pre_send, pigeonpost_post_send

send_logger = logging.getLogger('pigeonpost.send')
dryrun_logger = logging.getLogger('pigeonpost.dryrun')

def process_queue(force=False, dry_run=False):
    """
    Takes pigeons from queue, adds messages to the outbox 
    """
    if force:
        pigeons = Pigeon.objects.filter(to_send=True)
    else:
        pigeons = Pigeon.objects.filter(scheduled_for__lte=datetime.datetime.now(), to_send=True)
    for pigeon in pigeons:
        # Get method for rendering email for each user
        render_email = getattr(pigeon.source, pigeon.render_email_method)
        # Get a list of users to potentially generated emails for
        if pigeon.send_to:
            users = [pigeon.send_to]
        elif pigeon.send_to_method:
            get_user_method = getattr(pigeon.source, pigeon.send_to_method)
            users = get_user_method()
        else:
            users = User.objects.filter(is_active=True)
        # Iterate through the users and try adding messages to the Outbox model
        for user in users:
            email = render_email(user)
            if dry_run:
                try:
                    message = '{0} CREATED [{0}])'.format(user.email, email.message().as_string().replace('\n', '\t'))
                except AttributeError:
                    message = '{0} PASS'.format(user.email)
                dryrun_logger.debug(message)
                continue
            if email and isinstance(email, EmailMessage):
                try:
                    Outbox.objects.get(pigeon=pigeon, user=user)
                except Outbox.DoesNotExist:
                    Outbox(pigeon=pigeon, user=user, message=pickle.dumps(email, 0)).save()
            pigeon.to_send = False
            pigeon.sent_at = datetime.datetime.now()
            pigeon.save()

def process_outbox(max_retries=3, pigeon=None):
    """
    Sends mail from Outbox.
    """
    query_params = dict(succeeded=False, failures__lt=max_retries)
    if pigeon:
        query_params['pigeon'] = pigeon
    try:
        connection = mail.get_connection()
        if settings.EMAIL_HOST:
            send_logger.debug("Connection made to %s:%s ".format(
                settings.EMAIL_HOST, settings.EMAIL_PORT))
        for msg in Outbox.objects.filter(**query_params):
            send_logger.debug("A message to deliver!")
            email = pickle.loads(msg.message.encode('utf-8'))
            pigeonpost_pre_send.send(email)
            successful = connection.send_messages([email])
            successful = bool(successful)
            pigeonpost_post_send.send(email, successful=successful)
            if not successful:
                msg.failures += 1
            else:
                send_logger.debug("Message sent!")
            msg.succeeded = successful
            msg.sent_at = datetime.datetime.now()
            msg.save()
    except (smtplib.SMTPException, smtplib.socket.error) as err:
        send_logger.exception(err.args[0])
    finally:
        connection.close()
        if settings.EMAIL_HOST:
            send_logger.debug("Connection closed to %s:%s ".format(
                settings.EMAIL_HOST, settings.EMAIL_PORT))

def add_to_outbox(message, user):
    Outbox(message=pickle.dumps(message), user=user).save()

@receiver(pigeonpost_queue)
def add_to_queue(sender, render_email_method='render_email', send_to=None, send_to_method=None, scheduled_for=None, defer_for=None, **kwargs):
    # Check that we don't define both scheduled_for and defer_for at the same time. That is silly.
    assert not (scheduled_for and defer_for)
    # Work out the scheduled delivery time if necessary
    if defer_for is not None:
        scheduled_for = datetime.datetime.now() + datetime.timedelta(seconds=defer_for)
    elif scheduled_for is None:
        scheduled_for = datetime.datetime.now()
    try:
        p = Pigeon.objects.get(source_content_type=ContentType.objects.get_for_model(sender),
                source_id=sender.id,
                render_email_method=render_email_method,
                send_to=send_to,
                send_to_method=send_to_method)
        if p.to_send:
            # If the pigeon has not been sent yet, or to_send has been set to True,
            # update the pigeon with whatever the new scheduled time is
            p.scheduled_for = scheduled_for
            p.save()
    except Pigeon.DoesNotExist:
        # Create a new pigeon
        p = Pigeon(source=sender, render_email_method=render_email_method,
                scheduled_for=scheduled_for,
                send_to=send_to,
                send_to_method=send_to_method)
        p.save()

def deploy_pigeons(force=False, dry_run=False):
    process_queue(force=force, dry_run=dry_run)
    if not dry_run:
        process_outbox()
send_email = deploy_pigeons # Alias


def kill_pigeons():
    """
    Mark all unsent pigeons in the queue as send=False, so that they won't
    generate any messages. This is the pigeonpost panic button.
    """
    for pigeon in Pigeon.objects.filter(to_send=True):
        pigeon.to_send = False
        pigeon.save()

