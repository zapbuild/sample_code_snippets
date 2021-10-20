from django.core.management.base import BaseCommand, CommandError
from account.crons import send_notifications

class Command(BaseCommand):
    help = 'Send pending notificaitons to the users'

    def handle(self, *args, **options):
        send_notifications()