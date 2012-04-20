from django.core.management.base import BaseCommand, CommandError
from pigeonpost.tasks import kill_pigeons

class Command(BaseCommand):
    help = "The pigeonpost panicbutton. Stops any pigeons in the queue generating email messages"

    def handle(self, *args, **options):
        kill_pigeons()
