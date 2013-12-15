Getting Started
===============

Pigeonpost has two core models:

* **Pigeons** - these represent an intention to send out a message. They need to be
  associated with another model inside your project. When the
  ``deploy_pigeons`` action occurs, the associated model has the ability to
  decide which users to send the message to (if any), and control per-user
  rendering of the email.

* **Outbox** - these are messages that have been rendered and track whether they've
  successfully been sent. The rendering of a Pigeon may depend on the state of
  the model the pigeon is associated with, so storing the rendered messages
  is useful as an audit of what has, or will be, sent.

Installation
------------

Get the code
''''''''''''

The easiest way is to use ``pip``::

    pip install git+ssh://git@github.com:dragonfly-science/django-pigeonpost.git


Setup
'''''

1. Add `pigeonpost` to ``INSTALLED_APPS`` in the settings file of your Django application
2. Make sure that `django is set up for sending email`_.
   This typically requires the ``EMAIL_HOST``, ``EMAIL_HOST_USER``, and
   ``EMAIL_HOST_PASSWORD`` to be set. Other settings include the ``EMAIL_PORT`` and
   ``EMAIL_USE_TLS`` and are explained in the `Django documentation`_.
3. Run ``./manage.py syncdb`` to create the pigeonpost models (there are also
   sql migrations for `cuckoo`_, which is a custom migration tool Dragonfly
   uses. (One day we might transition to South, or just use the inbuilt
   migrations of Django 1.7).

.. _django is set up for sending email: https://docs.djangoproject.com/en/dev/topics/email/
.. _Django documentation: https://docs.djangoproject.com/en/1.4/ref/settings/#email-backend
.. _cuckoo: https://github.com/dragonfly-science/cuckoo-migrations

Usage
-----

To send mail:

1. Choose the model that makes most sense to associate a pigeon with. This
   might be a Message model, or a blog Post model. Whatever would contain the
   information that is intended to be sent to Users.
2. Give the chosen model a ``render_email`` method. The method should return
   a :class:`django.core.mail.EmailMessage` or None. If no message is returned, no
   email will be sent for that user::

    def render_email(self, user):
        subject = "Hello World!"
        body = "Have a nice day"
        return EmailMessage(subject, body, to=[user.email])

3. Add an entry to cron to call::

    python manage.py deploy_pigeons

4. To test your setup, using your normal SMTP server, but rerouting all email
   to your own email address (i.e. to avoid spamming your users with test email)
   you can change the Pigeonpost Django setting ``PIGEONPOST_SINK_EMAIL``  to
   a string containing your email address. This will also only render the first
   5 emails per pigeon, to avoid spamming your own email address.
   
You should be good to go!

Compatibility
-------------

We have successfully used Pigeonpost on Django 1.4 and 1.5. Please file an
`issue`_ if you notice problems with other versions (newer versions are more
likely to be supported than older ones though).

.. _issue: https://github.com/dragonfly-science/django-pigeonpost/issues
  

