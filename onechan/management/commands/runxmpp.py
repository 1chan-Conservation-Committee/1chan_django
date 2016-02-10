from django.core.management.base import BaseCommand
from xmpp.server import start_server


class Command(BaseCommand):
    help = 'Запускает новостного XMPP-бота'

    def handle(self, *args, **options):
        start_server()
