#!/usr/bin/env python

import asyncio
import json
import websockets

from remote_server.error import error
from remote_server.exceptions import BackendError
from remote_server.router import ClientRouter, WorkerRouter
from remote_server.cache import redis

CONFIG = {
    'remote_server.cache_url': 'redis://localhost:6379',
    'fxa-oauth.server_url': 'https://oauth.accounts.firefox.com',
    'fxa-oauth.scope': 'remote_server'
}


def setup_handler(cache):
    @asyncio.coroutine
    def handler(websocket, path):
        try:
            if path == '/worker':
                router = WorkerRouter(websocket, cache, CONFIG)
            else:
                router = ClientRouter(websocket, cache, CONFIG)
            yield from router.dispatch()
        except Exception as e:
            raise
            error_message = error('Something went Wrong: %s' % e)
            yield from websocket.send(json.dumps(error_message))
            yield from websocket.close()
            return

    return handler


def setup_server():
    cache = redis.load_from_config(CONFIG)

    create_pooler = asyncio.async(cache.setup_pooler())
    asyncio.get_event_loop().run_until_complete(create_pooler)

    start_server = websockets.serve(setup_handler(cache), 'localhost', 8765)
    return asyncio.get_event_loop().run_until_complete(start_server)


def main():
    setup_server()
    print("Server running on ws://localhost:8765")
    return asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
