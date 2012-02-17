from celery.task import task
from django.core.mail.backends.smtp import EmailBackend
from django.contrib.auth.models import User

from pigeonpost.models import ContentQueue, Outbox

def queue_to_send(sender, **kwargs):
    # Check to see if the object is mailable
    if hasattr(sender, 'email_render') and hasattr(sender, 'email_user'):
        now = datetime.today()
        countdown = 0
        if hasattr(sender, 'email_defer'):
            countdown = sender.email_defer()
            scheduled = now + datetime.timedelta(seconds=countdown)
        # Save it in the model
        try:
            post = ContentQueue.get(content_object=sender)
        except ContentQueue.DoesNotExist:
            post = ContentQueue(content_object=sender, scheduled=scheduled)
            post.save()
            # Create a task to send
            sendmessages.delay(sender, countdown=countdown)

@task
def sendmessages(content, backend = EmailBackend):
    users = User.objects.all()
    for user in users:
        if content.email_user(user):
            content.email_render(user)
            #send the message ...        
    
    
    
