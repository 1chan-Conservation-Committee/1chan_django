from django.core.management.base import BaseCommand
from ws.server import start_server


class Command(BaseCommand):
    help = 'Запускает вебсокет-сервер'

    def handle(self, *args, **options):
        start_server()
