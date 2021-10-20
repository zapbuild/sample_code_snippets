from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Credit/debit leaves for employee\'s account in case of sudden holidays/working days in a month'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        pass