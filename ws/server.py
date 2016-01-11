#!/usr/bin/env python3
import asyncio
import logging
import json
from aiohttp import web


class Room(object):
    def __init__(self, name):
        self.name = name
        self._clients = set()

    def add_client(self, client):
        self._clients.insert(client)

    def remove_client(self, client):
        self._clients.remove(client)
        # TODO: self.broadcast(disconnection msg)

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
        # TODO: ???

    def join_room(self, room):
        room.add_client(self)
        self._rooms[room.name] = room

    def shutdown(self):
        for room in self._rooms.items():
            room.remove_client(self)
        del self._rooms


@asyncio.coroutine
def ws_handler(request):
    ws = web.WebSocketResponse()
    yield from ws.prepare(request)
    #params = request.GET
    logging.getLogger('ws').info('%s connected', request.headers['X-Real-IP'])
    
    @asyncio.coroutine
    def ping():
        while not ws.closed:
            ws.ping()
            yield from asyncio.sleep(10)
    asyncio.async(ping())

    cl = Client(ws, request.headers['X-Real-IP'])
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


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger('ws').setLevel(logging.DEBUG)
    app = web.Application()
    app.router.add_route('GET', '/ws', ws_handler)
    loop = asyncio.get_event_loop()
    handler = app.make_handler()
    f = loop.create_server(handler, '0.0.0.0', 3000)
    srv = loop.run_until_complete(f)
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
