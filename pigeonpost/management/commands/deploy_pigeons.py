from django.core.management.base import BaseCommand, CommandError
from pigeonpost.tasks import send_email

class Command(BaseCommand):
    help = "Sends any pending emails in the ContentQueue"

    def handle(self, *args, **options):
        assert len(args) == 0, "We don't support any options."
        assert len(options) == 0, "We don't support any options."
        send_email()
