#!/usr/bin/env python3
import asyncio
import logging
import json
import asyncio_redis
from aiohttp import web
from django.conf import settings


DEFAULT_ROOM_NAME = 'default'


class Room(object):
    _rooms = {}

    @classmethod
    def get_room(cls, name):
        if name not in cls._rooms:
            cls._rooms[name] = Room(name)
            logging.getLogger('ws').debug('created a room named %s', name)
        return cls._rooms[name]

    @classmethod
    def broadcast_to_room(cls, name, msg):
        room = cls._rooms.get(name)
        if room:
            room.broadcast(msg)

    def __init__(self, name):
        self.name = name
        self._clients = set()
        self._writers = set()
        self._rooms[self.name] = self

    def add_client(self, client):
        self._clients.add(client)
        self.broadcast({
            'room': self.name,
            'type': 'count',
            'data': {'count': len(self._clients)}
        })
        client.send({
            'room': self.name,
            'type': 'writer_count',
            'data': {'count': len(self._writers)}
        })

    def remove_client(self, client):
        self._clients.remove(client)
        self.broadcast({
            'room': self.name,
            'type': 'count',
            'data': {'count': len(self._clients)}
        })
        if not self._clients:
            del self._rooms[self.name]
            logging.getLogger('ws').debug('deleted a room named %s', self.name)

    def set_writing(self, client, state):
        if client not in self._clients:
            return
        if state:
            self._writers.add(client)
        else:
            self._writers.remove(client)
        self.broadcast({
            'room': self.name,
            'type': 'writer_count',
            'data': {'count': len(self._writers)}
        })

    def broadcast(self, message):
        for cl in self._clients:
            cl.send(message)


class Client(object):
    def __init__(self, ws, ip):
        self._ws = ws
        self._ip = ip
        self._rooms = {}

    def send(self, msg):
        self._ws.send_str(json.dumps(msg))

    def on_message(self, msg):
        data = json.loads(msg.data)
        logging.getLogger('ws').debug('ws message %s from %s', data, self._ip)
        if data['type'] == 'join' and 'room' in data:
            self.join_room(Room.get_room(data['room']))
        elif data['type'] == 'writing' and data.get('room', DEFAULT_ROOM_NAME) != DEFAULT_ROOM_NAME:
            Room.get_room(data['room']).set_writing(self, data['data']['state'])

    def join_room(self, room):
        room.add_client(self)
        self._rooms[room.name] = room

    def shutdown(self):
        for room in self._rooms.values():
            room.remove_client(self)
        del self._rooms


@asyncio.coroutine
def ws_handler(request):
    ws = web.WebSocketResponse()
    yield from ws.prepare(request)
    #params = request.GET
    logging.getLogger('ws').debug('%s connected', request.headers['X-Real-IP'])
    
    @asyncio.coroutine
    def ping():
        while not ws.closed:
            ws.ping()
            yield from asyncio.sleep(10)
    asyncio.async(ping())

    cl = Client(ws, request.headers['X-Real-IP'])
    cl.join_room(Room.get_room(DEFAULT_ROOM_NAME))
    try:
        while True:
            msg = yield from ws.receive()
            if msg.tp == web.MsgType.text:
                cl.on_message(msg)
            elif msg.tp == web.MsgType.close:
                logging.getLogger('ws').debug('%s disconected', request.headers['X-Real-IP'])
                break
            elif msg.tp == web.MsgType.error:
                logging.getLogger('ws').warning(
                    'ws error %s from %s', msg.data, request.headers['X-Real-IP']
                )
                yield from ws.close()
                break
    finally:
        cl.shutdown()
        return ws


@asyncio.coroutine
def redis_listener():
    conn = yield from asyncio_redis.Connection.create(**settings.WS_REDIS_CONN_SETTINGS)
    subscriber = yield from conn.start_subscribe()
    yield from subscriber.subscribe([settings.WS_REDIS_CHANNEL])
    logging.getLogger('redis').debug('listening for notifications')
    while True:
        reply = yield from subscriber.next_published()
        msg = json.loads(reply.value)
        logging.getLogger('redis').debug('got a message from redis: %r', reply.value)
        if 'new_' in msg['type']:
            room = msg.get('room') or DEFAULT_ROOM_NAME
            msg['room'] = room
        elif False:
            pass # ...
        Room.broadcast_to_room(room, msg)


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
    if settings.DEBUG:
        logging.getLogger('ws').setLevel(logging.DEBUG)
        logging.getLogger('redis').setLevel(logging.DEBUG)
    app = web.Application()
    app.router.add_route('GET', '/ws', ws_handler)
    loop = asyncio.get_event_loop()
    handler = app.make_handler()
    f = loop.create_server(handler, *settings.WS_LISTEN_ADDRESS)
    srv = loop.run_until_complete(f)
    asyncio.async(redis_listener())
    logging.getLogger('ws').info('server started')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(handler.finish_connections(1.0))
        loop.run_until_complete(app.finish())
    loop.close()
