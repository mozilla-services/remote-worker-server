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
        task = asyncio.Task(websocket.recv())

        if random.randint(0, 100) < 50 and len(ERRORS.keys()) != 0:
            key = random.choice(list(ERRORS.keys()))
            answer = json.dumps({
                "messageType": "worker-error",
                "workerId": request['workerId'],
                "errno": ERRORS[key]["errno"],
                "reason": ERRORS[key]["reason"]
            })
            yield from websocket.send(answer)
            print("> %s" % answer)
        else:
            answer = json.dumps({
                "messageType": "worker-created",
                "workerId": request['workerId'],
                "webrtcAnswer": "<sdp-answer>"
            })
            yield from websocket.send(answer)
            print("> %s" % answer)

            while random.randint(0, 100) < 50 and websocket.open:
                yield from websocket.send(json.dumps({
                    "messageType": "ice",
                    "action": "worker-candidate",
                    "workerId": request['workerId'],
                    "candidate": {
                        "candidate": "candidate:2 1 UDP 2122187007 "
                        "10.252.27.213 41683 typ host",
                        "sdpMid": "",
                        "sdpMLineIndex": 0
                    }
                }))
                print("# Send ICE worker-candidate")

            try:
                while True:
                    response = yield from asyncio.wait_for(task, 1)
                    print("< %s" % response)
                    task = asyncio.Task(websocket.recv())
            except asyncio.TimeoutError:
                pass

            answer = json.dumps({
                "messageType": "connected",
                "workerId": request['workerId'],
            })
            yield from websocket.send(answer)
            print("> %s" % answer)

            yield from websocket.close()
            websocket = yield from websockets.connect('ws://localhost:8765/worker')

            request = json.dumps({
                "messageType": "hello",
                "action": "worker-hello",
                "geckoId": gecko_id
            })

            print("> %s" % request)
            yield from websocket.send(request)


        standza = yield from websocket.recv()

try:
    gecko_id = sys.argv[1].decode('utf-8')
    print(gecko_id)
except:
    gecko_id = GECKO_ID

asyncio.get_event_loop().run_until_complete(gecko(gecko_id))
