from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from pigeonpost.tasks import send_email

class Command(BaseCommand):
    help = "Sends any pending emails in the ContentQueue"
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dry-run',
            default=False,
            dest='dry_run'
            help="Create, but do not send messages that have been queued. Useful to help test a model's render_email method. Logs messages at level debug with the pigeonpost.dryrun logger."
        ),
    )

    def handle(self, *args, **options):
        send_email(dry_run=options['dry_run'])
