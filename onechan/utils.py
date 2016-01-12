import json
from django_redis import get_redis_connection
from django.conf import settings


def notify(msg):
    conn = get_redis_connection('default')
    conn.publish(settings.WS_REDIS_CHANNEL, json.dumps(msg))
