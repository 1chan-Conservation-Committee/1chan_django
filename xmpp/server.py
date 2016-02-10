#!/usr/bin/env python3
import asyncio
import logging
import json
import asyncio_redis
from slixmpp import ClientXMPP
from django.conf import settings


class NewsBot(ClientXMPP):

    def __init__(self, jid, password):
        ClientXMPP.__init__(self, jid, password)

        self.add_event_handler("session_start", self.session_start)
        self.register_plugin('xep_0045')

    def session_start(self, event):
        logging.getLogger('xmpp_bot').info('XMPP bot connected')
        self.send_presence()
        self.get_roster()
        self.plugin['xep_0045'].joinMUC(settings.XMPP_MUC_ROOM, settings.XMPP_MUC_NICKNAME)


@asyncio.coroutine
def redis_listener(xmpp):
    conn = yield from asyncio_redis.Connection.create(**settings.XMPP_REDIS_CONN_SETTINGS)
    subscriber = yield from conn.start_subscribe()
    yield from subscriber.subscribe([settings.XMPP_REDIS_CHANNEL])
    logging.getLogger('redis').debug('listening for notifications')
    while True:
        reply = yield from subscriber.next_published()
        msg = json.loads(reply.value)
        logging.getLogger('redis').debug('got a message from redis: %r', reply.value)
        if msg['type'] == 'new_post':
            if 'category' in msg['data']:
                status = '{category!s} → {title!s}: {prefix}{url!s}'.format(
                    prefix=settings.XMPP_NEWS_URL_PREFIX,
                    **msg['data']
                )
            else:
                status = '{title!s}: {prefix}{url!s}'.format(
                    prefix=settings.XMPP_NEWS_URL_PREFIX,
                    **msg['data']
                )
            xmpp.send_presence(
                pto='{}/{}'.format(settings.XMPP_MUC_ROOM, settings.XMPP_MUC_NICKNAME),
                pstatus=status
            )
        elif False:
            pass # ...

def start_server():
    logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
    if settings.DEBUG:
        logging.getLogger('xmpp_bot').setLevel(logging.DEBUG)
        logging.getLogger('redis').setLevel(logging.DEBUG)
    xmpp = NewsBot(settings.XMPP_JID, settings.XMPP_PASSWORD)
    xmpp.connect(address=settings.XMPP_SERVER_ADDRESS)
    asyncio.async(redis_listener(xmpp))
    xmpp.process()

if __name__=='__main__':
    start_server()
