import datetime
import logging
import smtplib
import pickle
import inspect

from django.core import mail
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.timezone import now
from django.db import models

from pigeonpost.models import Pigeon, Outbox
from pigeonpost.signals import pigeonpost_queue
from pigeonpost.signals import pigeonpost_pre_send, pigeonpost_post_send

send_logger = logging.getLogger('pigeonpost.send')
dryrun_logger = logging.getLogger('pigeonpost.dryrun')

def add_to_outbox(message, user):
    """
    Allows for a generic email message to be sent via pigeon post outbox.

    Note that it is not connected to a Pigeon object, so once it is placed in
    the queue it's up to the caller to manage the message if something changes
    before the message is sent.
    """
    msg = Outbox(message=pickle.dumps(message), user=user)
    msg.save()
    return msg

def unique(the_list):
    """ Used to remove duplicate users, but preserving send order """
    seen = set()
    for x in the_list:
        if x in seen: continue
        seen.add(x)
        yield x

def _get_source(pigeon):
    if pigeon.source_content_type and not pigeon.source_id:
        return pigeon.source_content_type.model_class()
    else:
        return pigeon.source


def process_queue(force=False, dry_run=False):
    """
    Takes pigeons from queue, adds messages to the outbox 
    """
    if force:
        pigeons = Pigeon.objects.filter(to_send=True)
    else:
        pigeons = Pigeon.objects.filter(scheduled_for__lte=now(), to_send=True)
    for pigeon in pigeons:
        the_source = _get_source(pigeon)
        if the_source is None:
            # Ensure the source object that the pigeon is related to still exists.
            # If it doesn't, then we just mark the pigeon as processed and move on.
            pigeon.to_send = False
            pigeon.failures += 1
            pigeon.save()
            dryrun_logger.debug("Skipping Pigeon %d with missing %s source object" %
                    (pigeon.id, str(pigeon.source_content_type)) )
            continue
        # Get method for rendering email for each user
        render_email = getattr(the_source, pigeon.render_email_method)
        # Get a list of users to potentially generated emails for
        if pigeon.send_to:
            users = [pigeon.send_to]
        elif pigeon.send_to_method:
            get_user_method = getattr(the_source, pigeon.send_to_method)
            users = get_user_method()
        else:
            users = User.objects.filter(is_active=True)
        # prevent users getting duplicate emails if the get_user_method is naughty
        # and adds a user twice
        users = list(unique(users))
        # Iterate through the users and try adding messages to the Outbox model
        if hasattr(settings, 'PIGEONPOST_SINK_EMAIL'):
            send_logger.debug("Using sink email and a message for %d users, only sending first 5!" %
                    len(users))
            users = users[:getattr(settings, 'PIGEONPOST_SINK_LIMIT', 5)]
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
                    pickled = pickle.dumps(email, 2)
                    Outbox(pigeon=pigeon, user=user, message=pickled.encode('base64')).save()
                pigeon.successes+=1
        pigeon.to_send = False
        pigeon.sent_at = now()
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
            send_logger.debug("Sending pigeons via %s:%s " % (
                settings.EMAIL_HOST, settings.EMAIL_PORT))
        for msg in Outbox.objects.filter(**query_params):
            email = pickle.loads(msg.message.decode('base64'))
            pigeonpost_pre_send.send(email)
            if hasattr(settings, 'PIGEONPOST_SINK_EMAIL'):
                send_logger.debug("A message for %s, rerouting to %s!" %
                        (email.to, settings.PIGEONPOST_SINK_EMAIL))
                email.to = [settings.PIGEONPOST_SINK_EMAIL]
                email.cc = []
                email.bcc = []
            else:
                send_logger.debug("A message for %s to deliver!" % email.to)
            try:
                connection.send_messages([email])
                send_logger.debug("Message sent!")
                msg.succeeded = True
                msg.sent_at = now()
            except (smtplib.SMTPException, smtplib.socket.error) as err:
                send_logger.debug("Message failed!")
                send_logger.exception(err.args[0])
                msg.failures += 1
            msg.save()
            pigeonpost_post_send.send(email, successful=msg.succeeded)
    except (smtplib.SMTPException, smtplib.socket.error) as err:
        send_logger.exception(err.args[0])

@receiver(pigeonpost_queue)
def add_to_queue(sender, render_email_method='render_email', send_to=None, send_to_method=None, scheduled_for=None, defer_for=None, **kwargs):
    # Check that we don't define both scheduled_for and defer_for at the same time. That is silly.
    assert not (scheduled_for and defer_for)
    # Work out the scheduled delivery time if necessary
    if defer_for is not None:
        scheduled_for = now() + datetime.timedelta(seconds=defer_for)
    elif scheduled_for is None:
        scheduled_for = now()
    # Check that either a model instance, or a model, is responsible for this pigeon
    if isinstance(sender, models.Model):
        sender_id = sender.id
        ct = ContentType.objects.get_for_model(sender, for_concrete_model=False)
    elif inspect.isclass(sender) and issubclass(sender, models.Model):
        # sender_model
        sender_id = None
        ct = ContentType.objects.get_for_model(sender, for_concrete_model=False)
    else:
        raise Exception("Unknown sender type. Must be models.Model subclass or instance")
    try:
        if sender_id:
            p = Pigeon.objects.get(source_content_type=ct,
                    source_id=sender_id,
                    render_email_method=render_email_method,
                    send_to=send_to,
                    send_to_method=send_to_method)
            if p.to_send:
                # If the pigeon has not been sent yet, or to_send has been set to True,
                # update the pigeon with whatever the new scheduled time is
                p.scheduled_for = scheduled_for
                p.save()
        else:
            p = Pigeon.objects.get(source_content_type=ct,
                    source_id=None,
                    render_email_method=render_email_method,
                    send_to=send_to,
                    send_to_method=send_to_method, to_send=True)
            # If the pigeon has not been sent yet, or to_send has been set to True,
            # update the pigeon with whatever the new scheduled time is
            p.scheduled_for = scheduled_for
            p.save()
    except Pigeon.DoesNotExist:
        # Create a new pigeon
        p = Pigeon(source_id=sender_id, source_content_type=ct,
                render_email_method=render_email_method,
                scheduled_for=scheduled_for,
                send_to=send_to,
                send_to_method=send_to_method)
        p.save()

from pigeonpost.utils import single_instance

@single_instance('pigeonpost')
def deploy_pigeons(force=False, dry_run=False):
    process_queue(force=force, dry_run=dry_run)
    if not dry_run:
        process_outbox()
send_email = deploy_pigeons # Alias

@single_instance('pigeonpost')
def kill_pigeons():
    """
    Mark all unsent pigeons in the queue as send=False, so that they won't
    generate any messages. This is the pigeonpost panic button.
    """
    for pigeon in Pigeon.objects.filter(to_send=True):
        pigeon.to_send = False
        pigeon.save()

