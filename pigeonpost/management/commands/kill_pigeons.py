from django.core.management.base import BaseCommand, CommandError
from pigeonpost.models import kill_pigeons

class Command(BaseCommand):
    help = "The pigeonpost panicbutton. Stops any pigeons in the queue generating email messages"

    def handle(self, *args, **options):
        assert len(args) == 0, "We don't support any options."
        assert len(options) == 0, "We don't support any options."
        kill_pigeons()
