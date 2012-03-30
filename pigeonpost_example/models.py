from django.core.mail import EmailMessage
from django.db import models
from pigeonpost.models import pigeonpost_signal

class Article(models.Model):
    text = models.TextField()
    title = models.TextField()

    def render_email(self, user):
        """
        render_email is expected to return None or a properly formed EmailMessage
        """
        if 'example.com' in user.email:
            return EmailMessage('New Post: ' + self.title, self.text, from_email='anon@example.com', to=[user.email]) 

    def save(self, *args, **kwargs):
        super(Article, self).save(*args, **kwargs)
        pigeonpost_signal.send(sender=self, scheduled_for=now() + datetime.timedelta(seconds=2)) 

class MessageToEveryone(models.Model):
    subject = models.TextField()
    body = models.TextField()

    def render_email(self, user):
        return EmailMessage(self.subject, self.body, from_email="agent@example.com", to=[user.email])

