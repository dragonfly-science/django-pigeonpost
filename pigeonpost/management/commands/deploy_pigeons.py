from django.core.management.base import BaseCommand, CommandError
from pigeonpost.tasks import send_email

class Command(BaseCommand):
    help = "Sends any pending emails in the ContentQueue"

    def add_arguments(self, parser):
        parser.add_argument(
            '-d', '--dry-run',
            default=False,
            action='store_true',
            dest='dry_run',
            help="Create, but do not send messages that have been queued. Useful to help test a model's render_email method. Logs messages at level debug with the pigeonpost.dryrun logger.")

    def handle(self, *args, **options):
        send_email(dry_run=options['dry_run'])
