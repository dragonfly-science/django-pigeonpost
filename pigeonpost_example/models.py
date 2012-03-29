from django.core.mail import EmailMessage
from django.db import models

class Article(models.Model):
    text = models.TextField()
    title = models.TextField()

    def render_email(self, user):
        """
        render_email is expected to return None or a properly formed EmailMessage
        """
        if 'example.com' in user.email:
            return EmailMessage('New Post: ' + self.title, self.text, from_email='anon@example.com', to=[user.email]) 
    
