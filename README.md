## Pigeonpost is a django application for sending emails

## About

Pigeonpost is a tool to make it simple to queue and send emails as a model is saved.

## Overview

To send mail, implementers should

1. Create a model with a `render_email` method
2. Have that method return a `django.core.mail.EmailMessage` or None, according to the
   implementer's preferred business logic per active user.
3. Establish a periodic crontab (or equivalent) which calls 
   `python manage.py deploy_pigeons`

Moderation is explained within Usage, below.

## Limitations

* No effort is made to rate limit messages to your SMTP server.

## Installation

### Get the code

The easiest way is to us the `pip` installer

    pip install git+ssh://git@github.com:dragonfly-science/django-pigeonpost.git

### Setup

1. Add `pigeonpost` to `INSTALLED_APPS` in the settings file of your Django application
2. Make sure that [django is set up for sending email](https://docs.djangoproject.com/en/dev/topics/email/).
   This typically requires the `EMAIL_HOST`, `EMAIL_HOST_USER`, and
   `EMAIL_HOST_PASSWORD` to be set. Other settings include the `EMAIL_PORT` and
   `EMAIL_USE_TLS` and are explained in the
   [Django documentation](https://docs.djangoproject.com/en/1.4/ref/settings/#email-backend).


## Usage

### Creating mail

In your application, add a method on your models called `render_email`.
`render_email` takes a `User` and generates either an EmailMessage or returns
`None`. If `None` is returned, no email is sent to that `User`.

When you save an instance of a model that you want to be emailed, just send a signal
to pigeonpost_queue:

```python
    def save(self):
        ...
        pigeonpost_queue.send(sender=self,...)
```

This signal tells pigeonpost when to send the message. The instance is added to
the queue, with the `render_email` method being called for each user
immediately before the message is sent.

A cron job can be used to send any queued messages, which will use the standard
django email machinery:

    python manage.py deploy_pigeons

When the message is ready to be put on the queue, send a `pigeonpost_message` to
let pigeonpost know what to do. This signal takes a `scheduled_time` argument
that allows the message to be deferred.

### Directed Pigeons 

Pigeonpost originally would call the `render_email` method for **every** user.
This is still the default behaviour but you can now target your pigeons to avoid
this inefficient behaviour.

To target the pigeon you pass either `send_to` or
`send_to_method` to the pigeonpost_queue signal along with the normal options.

`send_to` is good for sending to a single specific user:

```python
    u = User.objects.get(username='bob')
    pigeonpost_queue.send(sender=self, send_to=u)
```

it will complete avoid the loop and only call `render_email` with the `send_to`
user. It will still only send the email if `render_email` returns an
`EmailMessage` and not `None`.

`send_to_method` is good if you have some logic about which users you want to
send an email to which is faster (or conceptually simpler) than working out on
a per-user basis. It should return an iterable of Users.

```python
    def get_subscribers(self):
        # assuming a ManyToManyField called subscribers.
        return subscriptions.all()
    u = User.objects.get(username='bob')
    pigeonpost_queue.send(sender=self, send_to=u)
```

Do not define both `send_to` and `send_to_method`. The resulting behaviour is
not guaranteed and your pigeons may get confused.

### Multiple emails

You can change the `render_email` method by passing `render_email_method` as
an argument to the pigeonpost_queue. This allows you to use different logic and
delays before sending email.

E.g. you could send specific updates to an admin as well as use a general
render_email method:

```python
    u = User.objects.get(username='bob')
    admin = User.objects.get(username='admin')
    p = u.profile # Has a render_email method and a sysop_email method
    ten_minutes = 10*60
    pigeonpost_queue.send(sender=p, defer_for=10*60) # send in 10 minutes
    pigeonpost_queue.send(sender=p, send_to=admin, render_email_method='sysop_email', defer_for=ten_minutes)
```

### Moderation

Emails are not sent immediately. This allows a chance for amendments and
for the messages to be blocked by admins if required. Once that time period
passes, messages are sent.

In addition, it allows for multiple changes to a model to be cached. If you
submit the same model instance, with the same parameters (apart from when to send
the email), it will update the scheduled time for sending the existing pigeon.

For example, the below code sends the same pigeon twice:

```python
    u = User.objects.get(username='bob')
    p = u.profile # Has a render_email method
    ten_minutes = 10*60
    pigeonpost_queue.send(sender=p, defer_for=ten_minutes) # send in 10 minutes
    from time import sleep
    sleep(ten_minutes/5)
    pigeonpost_queue.send(sender=p, defer_for=10*60) # send in 10 minutes
```

Due to the sleep function, and the pigeon being resubmitted, the actual email
won't be scheduled until 15 minutes after this code begins execution.

## Example

### Send everyone an email once a Post is saved.

```python
from django.db import models
from django.core.mail import EmailMessage

from pigeonpost.signals import pigeonpost_queue

class Post(models.Model):
   text = models.TextField()
   title = models.CharField()
   
   def render_email(self, user):
      subject = self.title
      body = self.text
      return EmailMessage(subject, body, to=[user.email])
   
   def save(self, *args, **kwargs):
       """
       Post the message when it is saved. Defer sending for 6 hours
       """
       super(Post, self).save(*args, **kwargs)
       pigeonpost_queue.send(sender=self, defer_for=6*60*60) 
```

### Sending email to people from a common domain 

```python
class RestrictedPost(Post):
    def render_email(self, user):
        if user.email.rsplit('@')[1] == 'example.com':
            return EmailMessage(self.title, self.text, to=[user.email])
```

### Cron

Check for any new messages to send every 10 minutes. 

```
*/10 * * * * python /path/to/project/manage.py deploy_pigeons
```

## Available signals

Pigeonpost provides several signals to support advanced functionality:

* `pigeonpost_immediate`  
   A message has been created to be sent immediately.
* `pigeonpost_queue`  
   A message has been created, to be added to the queue.
* `pigeonpost_pre_send`  
* `pigeonpost_post_send`

## Other mailers

Maybe you should use this [other django mailing solution by James Tauber](https://github.com/jtauber/django-mailer/).

## Release Notes

### 0.1.3

Minor changes to improve the admin display and slight logic change to updating
pigeons that have already been sent.

### 0.1.2

This version supports targetted delivery and allows multiple pigeons per model
instance. To upgrade from 0.1.1, the appropriate sql patches in
pigeonpost/sql-migrations should be applied.


## The Kereru

The kereru or [New Zealand wood pigeon](http://en.wikipedia.org/wiki/New_Zealand_Pigeon) is a large 
fruit-eating forest pigeon, endemic to New Zealand. The population declined considerably duing the 20th century, due
to pressure form habitat destruction and from introduced mammalian pests. while it is beautiful bird, it is a clumsy, noisy flyer. As far as we know,
it has not been used for carrying either letters or email.


![Kereru](http://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Hemiphaga_novaeseelandiae_-Kapiti_Island-8.jpg/320px-Hemiphaga_novaeseelandiae_-Kapiti_Island-8.jpg)

