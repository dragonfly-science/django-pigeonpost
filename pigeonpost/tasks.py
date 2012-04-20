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

from pigeonpost.models import Pigeon, Outbox
from pigeonpost.signals import pigeonpost_queue, pigeonpost_immediate
from pigeonpost.signals import pigeonpost_pre_send, pigeonpost_post_send

send_logger = logging.getLogger('pigeonpost.send')
dryrun_logger = logging.getLogger('pigeonpost.dryrun')

def process_queue(force=False, dry_run=False):
    """
    Takes messages from queue, adds them to Outbox.
    """
    if force:
        pigeons = Pigeon.objects.filter(to_send=True)
    else:
        pigeons = Pigeon.objects.filter(scheduled_for__lt=datetime.datetime.now(), to_send=True)
    for pigeon in pigeons:
        render_email = getattr(pigeon.source, pigeon.render_email_method)
        users = User.objects.filter(is_active=True)
        for user in users:
            mail = render_email(user)
            if dry_run:
                try:
                    message = '{0} CREATED [{0}])'.format(user.email, mail.message().as_string().replace('\n', '\t'))
                except AttributeError:
                    message = '{0} PASS'.format(user.email)
                dryrun_logger.debug(message)
                continue
            if mail:
                try:
                    Outbox.objects.get(pigeon=pigeon, user=user)
                except Outbox.DoesNotExist:
                    Outbox(pigeon=pigeon, user=user, message=pickle.dumps(mail, 0)).save()

def process_outbox(max_retries=3, pigeon=None):
    """
    Sends mail from Outbox.
    """
    query_params = dict(succeeded=False, failures__lt=max_retries)
    if pigeon:
        query_params['pigeon'] = pigeon
    try:
        connection = mail.get_connection()
        send_logger.debug("Connection made to %s:%s ".format(settings.EMAIL_HOST, settings.EMAIL_PORT))
        for msg in Outbox.objects.filter(**query_params):
            email = pickle.loads(msg.message.encode('utf-8'))
            pigeonpost_pre_send.send(email)
            successful = connection.send_messages([email])
            successful = bool(successful)
            pigeonpost_post_send.send(email, successful=successful)
            if not successful:
                msg.failures += 1
            msg.succeeded = successful
            msg.sent_at = datetime.datetime.now()
            msg.save()
    except (smtplib.SMTPException, smtplib.socket.error) as err:
        send_logger.error()
    finally:
        connection.close()
        send_logger.debug("Connection closed to %s:%s ".format(settings.EMAIL_HOST, settings.EMAIL_PORT))

@receiver(pigeonpost_immediate)
def add_immediate_message_to_outbox(sender, message, user, **kwargs):
    Outbox(message=pickle.dumps(message), user=user).save()

@receiver(pigeonpost_queue)
def add_to_queue(sender, render_email_method='render_email', scheduled_for=None, defer_for=0, **kwargs):
    if not scheduled_for:
        scheduled_for = datetime.datetime.now()
    if defer_for:
         scheduled_for += datetime.timedelta(seconds=defer_for) 
    try:
        Pigeon.objects.get(source_content_type=ContentType.objects.get_for_model(sender),
            source_id=sender.id)
    except Pigeon.DoesNotExist:
        p = Pigeon(source=sender, render_email_method=render_email_method, scheduled_for=scheduled_for)
        p.save()


def deploy_pigeons(force=False, dry_run=False):
    process_queue(force=force, dry_run=dry_run)
    if not dry_run:
        process_outbox()

#TODO get refactor sorted
send_email = deploy_pigeons

def kill_pigeons():
    """Mark all unsent pigeons in the queue as send=False, so that they won't
    generate any messages. This is the pigeonpost panic button"""
    for pigeon in Pigeon.objects.filter(to_send=True):
        pigeon.to_send = False
        pigeon.save()

