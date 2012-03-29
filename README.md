## Pigeonpost is a django application for sending emails

In your application, create a method on your model class called
`render_email`. This method takes a `User` and generates
an email message. 

When you save an instance of a model that you want to be emailed,
send a signal to pigeonpost. This signal tells pigeonpost when
to send the message. The instance is added to the queue, with the
`render_email` method being called for each user immediately
before the message is sent.

A cron job can be used to send any queued messages, using
standard django email machinery.

Pigeonpost is suitable for small applications that need to send
emails to subscribed users. The `render_email` method can contain
any logic you like to decide whether to send a message derived
from a model instance to each user. If you are sending thousands
of emails at once, you should probably not be using pigeons.

## Installation

### Get the code

The easiest way is to us the `pip` installer

`pip install git+ssh://git@github.com:dragonfly-science/django-pigeonpost.git`


### Setup

1. Add `pigeonpost` to `INSTALLED_APPS` in the settings file of your Django application
2. Make sure that [django is set up for sending email](https://docs.djangoproject.com/en/dev/topics/email/). This 
typically requires the `EMAIL_HOST`, `EMAIL_HOST_USER`, and `EMAIL_HOST_PASSWORD` to be set. Other 
settings include the `EMAIL_PORT` and `EMAIL_USE_TLS`.


## Usage

In order to use pigeonpost, you need to write a `render_email` method for
models whose instances you would like to be sent to users. This method takes
a `User` instance. It is expected to return an EmailMessage instance (from `django.core.mail`),
with the mail to address being the email address of the user. If it returns `None`, then no
message will be sent to the user. If it returns anything other than `None` or and `EmailMessage`
then an exception will be raised.


When the message is ready to be put on the queue, send a `pigeonpost_signal` to
let pigeonpost know what to do. This signal takes a `scheduled_time` argument
that allows the message to be deferred.

## Example model


## Other mailers

Maybe you should use this [other django mailing solution by James Tauber](https://github.com/jtauber/django-mailer/).


## The Kereru

The kereru or [New Zealand wood pigeon](http://en.wikipedia.org/wiki/New_Zealand_Pigeon) is a large 
fruit-eating forest pigeon, endemic to New Zealand. The population declined considerably duing the 20th century, due
to pressure form habitat destruction and from introduced mammalian pests. while it is beautiful bird, it is a clumsy, noisy flyer. As far as we know,
it has not been used for carrying either letters or email.


![Kereru](http://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Hemiphaga_novaeseelandiae_-Kapiti_Island-8.jpg/320px-Hemiphaga_novaeseelandiae_-Kapiti_Island-8.jpg)

