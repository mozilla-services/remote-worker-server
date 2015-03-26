#!/usr/bin/env python

import asyncio
import json
import websockets
import sys

GECKO_ID = "gecko-headless-1"


@asyncio.coroutine
def gecko(gecko_id=GECKO_ID):
    websocket = yield from websockets.connect('ws://localhost:8765/worker')
    yield from websocket.send(json.dumps({
        "messageType": "hello",
        "action": "worker-hello",
        "geckoId": gecko_id
    }))

    # Iniatialize do_while
    standza = yield from websocket.recv()

    while standza:
        request = json.loads(standza)
        print("< %s" % standza)
        answer = json.dumps({
            "messageType": "worker-created",
            "workerId": request['workerId'],
            "webrtcAnswer": "<sdp-answer>"
        })
        yield from websocket.send(answer)
        print("> %s" % answer)

        # Start again
        standza = yield from websocket.recv()

try:
    gecko_id = sys.argv[1].decode('utf-8')
    print(gecko_id)
except:
    gecko_id = GECKO_ID

asyncio.get_event_loop().run_until_complete(gecko(gecko_id))
