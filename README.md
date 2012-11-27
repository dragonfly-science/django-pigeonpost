## Pigeonpost is a django application for sending emails

## About

Pigeonpost is a tool to make it very easy to send emails as a model is saved.
It is designed for fairly small sites that want to avoid the administrative
burden of managing an entire mailing list. 

## Overview

To send mail, implementers should

1. Create a model with a `render_email` method
2. Have that method return a `django.core.mail.EmailMessage`, according to the
   implementer's preferred business logic per active user.
3. Establish a periodic crontab (or equivalent) which calls 
   `python manage.py deploy_pigeons`

Moderation is explained within Usage, below.

## Limitations

* Pigeonpost will not scale gracefully to many hundreds of active users. The
  implementation iterates through every active user in the database. While this
  is done asyncronously, 
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
`None`. 

When you save an instance of a model that you want to be emailed, send a signal
to pigeonpost. This signal tells pigeonpost when to send the message. The
instance is added to the queue, with the `render_email` method being called for
each user immediately before the message is sent.

A cron job can be used to send any queued messages, using standard django email
machinery.

Pigeonpost is suitable for small applications that need to send emails to
subscribed users. The `render_email` method can contain any logic you like to
decide whether to send a message derived from a model instance to each user. If
you are sending thousands of emails at once, you should probably not be using
pigeons.

When the message is ready to be put on the queue, send a `pigeonpost_message` to
let pigeonpost know what to do. This signal takes a `scheduled_time` argument
that allows the message to be deferred.

### Moderation

Emails are not sent immediately. This allows a chance for amendments and
for the messages to be blocked by admins if required. Once that time period
passes, messages are sent.

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


## The Kereru

The kereru or [New Zealand wood pigeon](http://en.wikipedia.org/wiki/New_Zealand_Pigeon) is a large 
fruit-eating forest pigeon, endemic to New Zealand. The population declined considerably duing the 20th century, due
to pressure form habitat destruction and from introduced mammalian pests. while it is beautiful bird, it is a clumsy, noisy flyer. As far as we know,
it has not been used for carrying either letters or email.


![Kereru](http://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Hemiphaga_novaeseelandiae_-Kapiti_Island-8.jpg/320px-Hemiphaga_novaeseelandiae_-Kapiti_Island-8.jpg)

