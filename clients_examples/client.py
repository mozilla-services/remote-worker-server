#!/usr/bin/env python

import asyncio
import json
import websockets

BEARER_TOKEN = "13cbb5664aaccd662d803e71e547cdb58485ce25477f" \
               "635bc5051aa550eed00d"


@asyncio.coroutine
def browser():
    websocket = yield from websockets.connect('ws://localhost:8765/')
    print("> Send Hello on %s" % BEARER_TOKEN)
    # 1. Send hello
    yield from websocket.send(json.dumps({
        "messageType": "hello",
        "action": "client-hello",
        "authorization": "Bearer %s" % BEARER_TOKEN,
        "source": "https://localhost:8080/worker.js",
        "webrtcOffer": "<sdp-offer>"
    }))
    # 2. Wait for the WebRTC answer
    webrtc_answer = yield from websocket.recv()
    print("< {}".format(webrtc_answer))

asyncio.get_event_loop().run_until_complete(browser())
