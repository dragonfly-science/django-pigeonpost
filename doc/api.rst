Detailed usage
==============

Creating mail
-------------

Add a method ``render_email`` to the model that will contain the information to
be sent in the email.

``render_email`` is an instance method that takes
a :class:`django.contrib.auth.models.User` and generates either
a :class:`django.core.mail.EmailMessage` or returns ``None``. If ``None`` is
returned, no email is sent to that ``User``.

When you save an instance of a model that you want to generate an email, just send a signal
to ``pigeonpost_queue``::

    from pigeonpost.signals import pigeonpost_queue

    def save(self):
        ...
        pigeonpost_queue.send(sender=self,...)

This signal tells pigeonpost to queue a pigeon for sending. The model instance
is added to the queue, and when the queue is processed the ``render_email``
method being will be called for each user immediately before the email is sent.

A cron job can be used to send any queued messages, which will use the standard
django email mechanism::

    python manage.py deploy_pigeons

Directed Pigeons 
----------------

Pigeonpost originally would call the ``render_email`` method for **every** user.
This is still the default behaviour but you can now target your pigeons to avoid
this behaviour which is inefficient when your User base becomes large.

To target the pigeon you pass either ``send_to`` or
``send_to_method`` to the ``pigeonpost_queue`` signal along with the normal options.

``send_to`` is good for sending to a single specific user::

    u = User.objects.get(username='bob')
    pigeonpost_queue.send(sender=self, send_to=u)

it will completely avoid the loop and only call ``render_email`` with the ``send_to``
user. It will still only send the email if ``render_email`` returns an
``EmailMessage`` and not ``None``.

``send_to_method`` is good if you have some logic about which users you want to
send an email to, and it can be expressed faster (or in a conceptually simpler
way) than working it out on a per-user basis. The method should return an iterable of
``Users``::

    def get_subscribers(self):
        # assuming a ManyToManyField called subscribers.
        return subscriptions.all()
    u = User.objects.get(username='bob')
    pigeonpost_queue.send(sender=self, send_to=u)

Do not define both ``send_to`` and ``send_to_method``. The resulting behaviour is
not guaranteed and your Pigeons may get confused.

Multiple emails
---------------

You can change the ``render_email`` method by passing ``render_email_method`` as
an argument to the pigeonpost_queue. This allows you to use different logic and
delays before sending email.

E.g. you could send specific updates to an admin as well as use a general
``render_email`` method::

    u = User.objects.get(username='bob')
    admin = User.objects.get(username='admin')
    p = u.profile # Has a render_email method and a sysop_email method
    ten_minutes = 10*60
    pigeonpost_queue.send(sender=p, defer_for=ten_minutes)
    pigeonpost_queue.send(sender=p, send_to=admin, render_email_method='sysop_email', defer_for=ten_minutes)

Moderation
----------

Emails are not sent immediately when pigeonpost_queue.send is called. First the
deploy_pigeons management task needs to be run, and second, the ``defer_for``
parameter delays when the pigeon is transmuted into an Outbox object.

This gives window for amendments to be made and for the messages to be blocked by
admins if required. Once that time period passes, messages are sent.

In addition, it allows for multiple changes to a model to be buffered before
sending. If you submit the same model instance, with the same parameters (apart
from when to send the email), it will update the scheduled time for sending the
existing pigeon.

For example, the below code queues the same pigeon twice, but will only send
one message::

    u = User.objects.get(username='bob')
    p = u.profile # Has a render_email method
    ten_minutes = 10*60
    pigeonpost_queue.send(sender=p, defer_for=ten_minutes) # send in 10 minutes
    from time import sleep
    sleep(ten_minutes/5)
    pigeonpost_queue.send(sender=p, defer_for=10*60) # send in 10 minutes

Due to the sleep function, and the pigeon being resubmitted, the actual email
won't be scheduled until 15 minutes after this code begins execution.

.. warning:: Don't actually call ``sleep`` while processing a request. It
    could potentially block your server from processing other requests!

Sending Pigeons without a model instance
----------------------------------------

In some situations you may want to send a Pigeon, but without tying it to
a specific model instance.

From `0.3.1` Pigeonpost will accept a django model class as the signal sender,
and call ``render_email`` (and similar methods) if they are marked with the
``@classmethod`` decorator::

    class AggregateNews(models.Model):
        """ News that is aggregated as a single message """
        news_bit = models.TextField()
        read = models.BooleanField(default=False)

        @classmethod
        def render_email(cls, user):
            news = cls.objects.filter(read=False)
            msg_body = []
            for n in news:
                msg_body.append(n.news_bit)
            return EmailMessage("The latest news!", "\n".join(msg_body),
                    from_email='anon@example.com', to=[user.email]) 

    ...
    pigeonpost_queue.send(sender=AggregateNews)


Helper function for multiple message formats
--------------------------------------------

A common pattern is to send an HTML and text version of an email.

While django provides this functionality, we provide a wrapper function that
takes a user, subject, context and two templates to be rendered. One template for
the text version, and another for html::

    from pigeonpost.utils import generate_email

    u = User.objects.get(username='bob')
    email_message = generate_email(u, "hello bob", dict(msg="you are a funny guy"), 'funny.txt', 'funny.html')

This returns a :class:`django.core.mail.EmailMultiAlternatives` object, which
can passed as the return value from a render_email method because it inherits
from :class:`django.core.mail.EmailMessage`.

Development/Testing environments
--------------------------------

To avoid actually sending emails to other users, but to still actually send
them via your main SMTP host, you can put ``PIGEONPOST_SINK_EMAIL`` in
settings.py.  It should be a single email address as a string, and it will
receive all generated emails.

Alternatively, you could also run a console logging smtp server, using the
standard Python smtpd library::

    python -m smtpd -n -c DebuggingServer localhost:1025

Setting up cron
---------------

To check for any new pigeons, generate and send messages every 10 minutes, add
the following line to your cron::

    */10 * * * * python /path/to/project/manage.py deploy_pigeons

Available signals
-----------------

Pigeonpost provides several signals to support advanced functionality:

* ``pigeonpost_immediate`` - A message has been created to be sent immediately.
* ``pigeonpost_queue`` - A message has been created, to be added to the queue.
* ``pigeonpost_pre_send``
* ``pigeonpost_post_send``

Caveats and alternatives
------------------------

Pigeonpost was made and has been used in a number of websites, but these are
mostly small scale (e.g. < 1000 users). Some of the mechanisms of pigeonpost
are not optimised for larger deployments, although it wouldn't be hard to
improve it in this way.

Other mailing systems that we know of are:

- `django-mailer`_ by James Tauber.
  
.. _django-mailer: https://github.com/jtauber/django-mailer/

