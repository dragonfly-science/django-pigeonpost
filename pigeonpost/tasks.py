import datetime
try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.core import mail
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.dispatch import receiver

from pigeonpost.models import Pigeon, Outbox
from pigeonpost.signals import pigeonpost_signal, pigeonpost_pre_send, pigeonpost_post_send


@receiver(pigeonpost_signal)
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


def send_email(force=False):
    if force:
        pigeons = Pigeon.objects.filter(to_send=True)
    else:
        pigeons = Pigeon.objects.filter(scheduled_for__lt=datetime.datetime.now(), to_send=True)
    try:
        connection = mail.get_connection()
        for pigeon in pigeons:
            try:
                render_email = getattr(pigeon.source, pigeon.render_email_method)
                for user in User.objects.filter(is_active=True):
                    message = render_email(user)
                    if message:
                        try:
                            Outbox.objects.get(pigeon=pigeon, user=user)
                        except Outbox.DoesNotExist:
                            outbox = Outbox(pigeon=pigeon, user=user, message=pickle.dumps(message, 0))
                            pigeonpost_pre_send.send(sender=outbox)
                            res = connection.send_messages([message])
                            if res == 1:
                                pigeon.successes += 1
                            else:
                                outbox.succeeded = False
                                outbox.failures = 1
                                pigeon.failures += 1
                            pigeonpost_post_send(sender=outbox)
                            outbox.save()
            finally:
                pigeon.sent_at = datetime.datetime.now()
                pigeon.to_send = False
                pigeon.save()
    finally:
        connection.close()

def kill_pigeons():
    """Mark all unsent pigeons in the queue as send=False, so that they won't
    generate any messages. This is the pigeonpost panic button"""
    for pigeon in Pigeon.objects.filter(to_send=True):
        pigeon.to_send = False
        pigeon.save()

def retry(max_retries=3):
    """
    retry attempts to resend any emails that have failed.
    
    It is designed to be run from a periodicly, e.g. daily via cron.
    """
    failures = Outbox.objects.filter(failures__lt=max_retries, succeeded=False)
    for outbox in failures:
        try:
            pickle.load(outbox.message).send()
            outbox.succeeded = True
            outbox.sent = datetime.datetime.now()
        except:
            outbox.failures +=  1
        outbox.save()
