from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db import models
from pigeonpost.tasks import pigeonpost_signal

# Basic Usage
class Profile(models.Model):
    user = models.ForeignKey(User)
    subscribed_to_news = models.BooleanField()
    
class News(models.Model):
    subject = models.TextField()
    body = models.TextField()

    def render_email(self, user):
        """
        Render the email for sending to the given user
        """
        if user.subscribed_to_news:
            return EmailMessage(self.subject, self.body, from_email='anon@example.com', to=[user.email]) 

    def save(self, *args, **kwargs):
        """
        Post the message when it is saved. Defer sending for 6 hours
        """
        super(Message, self).save(*args, **kwargs)
        pigeonpost_queue.send(sender=self, defer_for=6*60*60) 


class ModeratedNews(models.Model):
    subject = models.TextField()
    body = models.TextField()
    published = models.BooleanField()
    
    def render_email(self, user):
        if self.published and (user.subscribed_to_news or user.is_staff):
            return EmailMessage(self.subject, self.body, from_email='anon@example.com', to=[user.email]) 
            
    def save(self, *args, **kwargs):
        super(Message, self).save(*args, **kwargs)
        if self.published:
            # sending ModeratedNews to moderators (nearly) immediately,
            # and sending them to users in 6 hours if the ModeratedNews
            # items remain published.
            pigeonpost_queue.send(sender=self, defer_for=6*60*60) 
            for user in Users.objects.filter(is_staff=True): 
                pigeonpost_message.send(sender=self, message=self.render_email(user=user))
        
        