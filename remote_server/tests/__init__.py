import asyncio
import logging
import json
import unittest
from websockets.client import connect

from remote_server import setup_server

# Avoid displaying stack traces at the ERROR logging level.
logging.basicConfig(level=logging.CRITICAL)


class ClientServerTests(unittest.TestCase):
    secure = False

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.start_server()
        self.start_gecko()

    def tearDown(self):
        self.stop_server()
        self.stop_gecko()
        self.stop_client()
        self.loop.close()

    def start_server(self, **kwds):
        self.server = setup_server()

    def stop_server(self):
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())

    def start_client(self, path='', **kwds):
        client = connect('ws://localhost:8765/' + path, **kwds)
        self.client = self.loop.run_until_complete(client)

    def stop_client(self):
        self.loop.run_until_complete(self.client.worker)

    def start_gecko(self, path='', **kwds):
        gecko = connect('ws://localhost:8765/worker', **kwds)
        self.gecko = self.loop.run_until_complete(gecko)
        self.loop.run_until_complete(self.gecko.send(json.dumps({
            "messageType": "hello",
            "action": "worker-hello",
            "geckoId": "gecko-1243"
        })))

    def stop_gecko(self):
        self.loop.run_until_complete(self.gecko.worker)
