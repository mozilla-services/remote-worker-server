#!/usr/bin/env python

import asyncio
import json
import os
import random
import websockets
import sys

GECKO_ID = "gecko-headless-1"

ERRORS = {}

with open(os.path.join(os.path.dirname(__file__), '../errors.json')) as f:
    ERRORS = json.loads(f.read())


@asyncio.coroutine
def gecko(gecko_id=GECKO_ID):
    websocket = yield from websockets.connect('ws://localhost:8765/worker')
    request = json.dumps({
        "messageType": "hello",
        "action": "worker-hello",
        "geckoId": gecko_id
    })

    print("> %s" % request)
    yield from websocket.send(request)

    # Iniatialize do_while
    standza = yield from websocket.recv()

    while standza:
        request = json.loads(standza)
        print("< %s" % standza)

        if random.randint(0, 1) and len(ERRORS.keys()) != 0:
            key = random.choice(list(ERRORS.keys()))
            answer = json.dumps({
                "messageType": "worker-error",
                "workerId": request['workerId'],
                "errno": ERRORS[key]["errno"],
                "reason": ERRORS[key]["reason"]
            })
        else:
            answer = json.dumps({
                "messageType": "worker-created",
                "workerId": request['workerId'],
                "webrtcAnswer": "<sdp-answer>"
            })

        yield from websocket.send(answer)
        print("> %s" % answer)

        answer = json.dumps({
            "messageType": "connected",
            "workerId": request['workerId'],
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
