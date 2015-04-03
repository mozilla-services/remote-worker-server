#!/usr/bin/env python
import asyncio
import json
from random import randint
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
        "source": "http://localhost:8080/worker.js",
        "webrtcOffer": "<sdp-offer>"
    }))
    yield from websocket.send(json.dumps({
        "messageType": "ice",
        "action": "client-candidate",
        "candidate": {
            "candidate": "candidate:2 1 UDP 2122187007 "
            "10.252.27.213 41683 typ host",
            "sdpMid": "",
            "sdpMLineIndex": 0
        }
    }))

    # 2. Wait for the WebRTC answer
    standza = yield from websocket.recv()
    while standza:
        # Start again
        print("< {}".format(standza))

        if randint(0, 100) < 50 and websocket.open:
            print("# Send ICE candidate")
            yield from websocket.send(json.dumps({
                "messageType": "ice",
                "action": "client-candidate",
                "candidate": {
                    "candidate": "candidate:2 1 UDP 2122187007 "
                                 "10.252.27.213 41683 typ host",
                    "sdpMid": "",
                    "sdpMLineIndex": 0
                }
            }))

        standza = yield from websocket.recv()

asyncio.get_event_loop().run_until_complete(browser())
