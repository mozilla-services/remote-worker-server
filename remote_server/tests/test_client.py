import json
import os
import random

from remote_server.tests import ClientServerTests

BEARER_TOKEN = "13cbb5664aaccd662d803e71e547cdb58485ce25477f" \
               "635bc5051aa550eed00d"

ERRORS = {}

with open(os.path.join(os.path.dirname(__file__), '../../errors.json')) as f:
    ERRORS = json.loads(f.read())


class ClientTestCase(ClientServerTests):
    def test_when_client_ask_an_offer_gecko_receive_it(self):
        self.start_client()
        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(json.dumps({
            "messageType": "hello",
            "action": "client-hello",
            "authorization": "Bearer %s" % BEARER_TOKEN,
            "source": "http://localhost:8080/worker.js",
            "webrtcOffer": "<sdp-offer>"
        })))

        # 2. Gecko receive the offer
        gecko_received = self.loop.run_until_complete(self.gecko.recv())
        data = json.loads(gecko_received)
        self.assertIn("workerId", data)
        del data["workerId"]
        self.assertDictEqual(data, {
            "messageType": "new-worker",
            "userId": "e2dda4218656438bb7c4a34ceea1aa18",
            "source": "http://localhost:8080/worker.js",
            "webrtcOffer": "<sdp-offer>"
        })

    def test_when_gecko_answer_an_offer_client_receive_it(self):
        self.start_client()
        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(json.dumps({
            "messageType": "hello",
            "action": "client-hello",
            "authorization": "Bearer %s" % BEARER_TOKEN,
            "source": "http://localhost:8080/worker.js",
            "webrtcOffer": "<sdp-offer>"
        })))

        # 2. Gecko receive the offer
        gecko_received = self.loop.run_until_complete(self.gecko.recv())
        data = json.loads(gecko_received)

        # 3. Gecko send back the answer
        worker_id = data["workerId"]
        self.loop.run_until_complete(self.gecko.send(json.dumps({
            "messageType": "worker-created",
            "workerId": worker_id,
            "webrtcAnswer": "<sdp-answer>"
        })))

        # 4. Check that client received the anwser
        client_received = self.loop.run_until_complete(self.client.recv())
        data = json.loads(client_received)

        self.assertDictEqual(data, {
            "messageType": "hello",
            "action": "worker-hello",
            "workerId": worker_id,
            "webrtcAnswer": "<sdp-answer>"
        })

    def test_when_gecko_answer_an_error_client_receive_it(self):
        self.start_client()
        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(json.dumps({
            "messageType": "hello",
            "action": "client-hello",
            "authorization": "Bearer %s" % BEARER_TOKEN,
            "source": "http://localhost:8080/worker.js",
            "webrtcOffer": "<sdp-offer>"
        })))

        # 2. Gecko receive the offer
        gecko_received = self.loop.run_until_complete(self.gecko.recv())
        data = json.loads(gecko_received)

        # 3. Gecko send back the answer
        worker_id = data["workerId"]
        key = random.choice(list(ERRORS.keys()))
        answer = {
            "messageType": "worker-error",
            "workerId": worker_id,
            "errno": ERRORS[key]["errno"],
            "reason": ERRORS[key]["reason"]
        }
        self.loop.run_until_complete(self.gecko.send(json.dumps(answer)))

        # 4. Check that client received the anwser
        client_received = self.loop.run_until_complete(self.client.recv())
        data = json.loads(client_received)
        self.assertDictEqual(data, answer)
