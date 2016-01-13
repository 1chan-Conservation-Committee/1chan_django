import json
from django_redis import get_redis_connection
from django.conf import settings
from django.core.cache import cache
from .models import Smiley

def notify(msg):
    conn = get_redis_connection('default')
    conn.publish(settings.WS_REDIS_CHANNEL, json.dumps(msg))


class SmileyCacheMiddleware(object):

    def process_request(self, request):
        cache.set('smiley_list',
            { s.name: s.img.url for s in Smiley.objects.all() },
            timeout=None
        )

    def process_response(self, request, response):
        cache.delete('smiley_list')
        return response
