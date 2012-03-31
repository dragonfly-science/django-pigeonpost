from django.core.mail import EmailMessage
from django.db import models
from pigeonpost.tasks import pigeonpost_signal

class Message(models.Model):
    subject = models.TextField()
    body = models.TextField()

    def render_email(self, user):
        """
        Render the email for sending to the given user
        """
        if 'example.com' in user.email:
            return EmailMessage(self.subject, self.body, from_email='anon@example.com', to=[user.email]) 

    def save(self, *args, **kwargs):
        """
        Post the message when it is saved. Defer sending for 6 hours
        """
        super(Message, self).save(*args, **kwargs)
        pigeonpost_signal.send(sender=self, defer_for=6*60*60) 

