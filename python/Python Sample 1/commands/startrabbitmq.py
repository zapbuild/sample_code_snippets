from django.core.management.base import BaseCommand, CommandError
from pubsub.factory import BrokerFactory

class Command(BaseCommand):
    help = 'Starts the Rabbit MQ consumer'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        consumer = BrokerFactory.get_broker()
        self.stdout.write(self.style.SUCCESS('Successfully started the Rabbit MQ consumer'))
        consumer.run()