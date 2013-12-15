Examples
========

Send everyone an email once a Post is saved
-------------------------------------------

If you had a blog ``Post``, and you wanted to send a notification
to all your subscribers::

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


Sending email to people from a particular domain 
------------------------------------------------

If you only want to announce to people who have an email address at
``example.com``::

    class RestrictedPost(Post):
        def render_email(self, user):
            if user.email.rsplit('@')[1] == 'example.com':
                return EmailMessage(self.title, self.text, to=[user.email])
