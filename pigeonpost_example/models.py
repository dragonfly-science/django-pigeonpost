from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db import models

from pigeonpost.signals import pigeonpost_queue

class Profile(models.Model):
    user = models.ForeignKey(User, unique=True)
    subscribed_to_news = models.BooleanField()
    
class News(models.Model):
    subject = models.TextField()
    body = models.TextField()

    def render_email(self, user):
        """
        Render the email for sending to the given user
        """
        if user.get_profile().subscribed_to_news:
            return EmailMessage(self.subject, self.body, from_email='anon@example.com', to=[user.email]) 

    def save(self, *args, **kwargs):
        """
        Post the message when it is saved. Defer sending for 6 hours
        """
        super(News, self).save(*args, **kwargs)
        pigeonpost_queue.send(sender=self, defer_for=6*60*60) 


class ModeratedNews(models.Model):
    subject = models.TextField()
    body = models.TextField()
    published = models.BooleanField()
    
    def email_news(self, user):
        if self.published and user.get_profile().subscribed_to_news:
            return EmailMessage(self.subject, self.body, from_email='anon@example.com', to=[user.email]) 
    
    def email_moderators(self, user):
        if user.is_staff:
            return EmailMessage(self.subject, self.body, from_email='anon@example.com', to=[user.email]) 
            
    def save(self, *args, **kwargs):
        super(ModeratedNews, self).save(*args, **kwargs)
        if self.published:
            # sending ModeratedNews to moderators (nearly) immediately,
            # and sending them to users in 6 hours if the ModeratedNews
            # items remain published.
            pigeonpost_queue.send(sender=self, render_email_method='email_news', defer_for=6*60*60) 
            pigeonpost_queue.send(sender=self, render_email_method='email_moderators')
        

class BobsNews(models.Model):
    """ News... news only for people called Bob, and no one else! """
    subject = models.TextField()
    body = models.TextField()

    def email_news(self, user):
        assert user.first_name.lower() == 'bob'
        return EmailMessage(self.subject, self.body, from_email='anon@example.com', to=[user.email]) 

    def get_everyone_called_bob(self):
        return User.objects.filter(first_name__iexact='bob')


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
