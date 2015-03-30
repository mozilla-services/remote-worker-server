import asyncio
import logging

import unittest
from unittest.mock import patch

from remote_server import main

# Avoid displaying stack traces at the ERROR logging level.
logging.basicConfig(level=logging.CRITICAL)


class ClientServerTests(unittest.TestCase):
    secure = False
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.start_server()

    def tearDown(self):
        self.stop_server()
        self.loop.close()

    def start_server(self, **kwds):
        self.server = main()

    def start_client(self, path='', **kwds):
        client = connect('ws://localhost:8765/' + path, **kwds)
        self.client = self.loop.run_until_complete(client)

    def stop_client(self):
        self.loop.run_until_complete(self.client.worker)

    def stop_server(self):
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())

    def test_when_client_ask_an_offer_it_gets_an_answer(self):
        self.start_client()
        self.loop.run_until_complete(self.client.send(
            "Hello!"))
        reply = self.loop.run_until_complete(self.client.recv())
        self.assertEqual(reply, "Hello!")
        self.stop_client()
