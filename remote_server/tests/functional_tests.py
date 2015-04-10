import json
import os
import random

from remote_server.tests import ClientServerTests

BEARER_TOKEN = "13cbb5664aaccd662d803e71e547cdb58485ce25477f" \
               "635bc5051aa550eed00d"

ERRORS = {}

with open(os.path.join(os.path.dirname(__file__), '../../errors.json')) as f:
    ERRORS = json.loads(f.read())


class ClientServerTestCase(ClientServerTests):
    def setUp(self):
        super(ClientServerTestCase, self).setUp()
        self.client_hello = json.dumps({
            "messageType": "hello",
            "action": "client-hello",
            "authorization": "Bearer %s" % BEARER_TOKEN,
            "source": "http://localhost:8080/worker.js",
            "webrtcOffer": "<sdp-offer>"
        })
        self.client_ice = json.dumps({
            "messageType": "ice",
            "action": "client-candidate",
            "candidate": {
                "candidate": "candidate:2 1 UDP 2122187007 "
                "10.252.27.213 41683 typ host",
                "sdpMid": "",
                "sdpMLineIndex": 0
            }
        })

        self.gecko_ice = {
            "messageType": "ice",
            "action": "worker-candidate",
            "candidate": {
                "candidate": "candidate:2 1 UDP 2122187007 "
                "10.252.27.213 41683 typ host",
                "sdpMid": "",
                "sdpMLineIndex": 0
            }
        }

    def test_when_client_asks_an_offer_gecko_receives_it(self):
        self.start_client()
        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(self.client_hello))

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

    def test_when_gecko_answers_an_offer_client_receives_it(self):
        self.start_client()
        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(self.client_hello))

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

    def test_when_gecko_answers_an_error_client_receives_it(self):
        self.start_client()
        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(self.client_hello))

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

    def test_when_client_sends_ice_candidate_before_answer_gecko_gets_it(self):
        self.start_client()
        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(self.client_hello))

        # 2. Gecko receive the offer
        gecko_received = self.loop.run_until_complete(self.gecko.recv())
        data = json.loads(gecko_received)

        # 3. Client sends ICE Candidates
        self.loop.run_until_complete(self.client.send(self.client_ice))

        # 4. Gecko receive the ICE standza
        gecko_received = self.loop.run_until_complete(self.gecko.recv())
        data = json.loads(gecko_received)

        answer = json.loads(self.client_ice)
        answer['workerId'] = data['workerId']
        self.assertDictEqual(data, answer)

    def test_when_client_sends_ice_candidate_after_answer_gecko_gets_it(self):
        self.start_client()
        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(self.client_hello))

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

        # 3. Client sends ICE Candidates
        self.loop.run_until_complete(self.client.send(self.client_ice))

        # 4. Gecko receive the ICE standza
        gecko_received = self.loop.run_until_complete(self.gecko.recv())
        data = json.loads(gecko_received)

        answer = json.loads(self.client_ice)
        answer['workerId'] = data['workerId']
        self.assertDictEqual(data, answer)

    def test_when_gecko_answers_ice_candidates_client_receives_them(self):
        self.start_client()
        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(self.client_hello))

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

        # 5. Gecko send ICE candidate
        self.gecko_ice['workerId'] = worker_id
        self.gecko_ice['candidate']['sdpMid'] = "1234"
        answer = json.dumps(self.gecko_ice)
        self.loop.run_until_complete(self.gecko.send(answer))

        # 6. Check that client received the ICE
        client_received = self.loop.run_until_complete(self.client.recv())
        data = json.loads(client_received)

        self.assertDictEqual(data, self.gecko_ice)

        # 7. Gecko send ICE candidate
        self.gecko_ice['workerId'] = worker_id
        self.gecko_ice['candidate']['sdpMid'] = "5678"
        answer = json.dumps(self.gecko_ice)
        self.loop.run_until_complete(self.gecko.send(answer))

        # 8. Check that client received the ICE
        client_received = self.loop.run_until_complete(self.client.recv())
        data = json.loads(client_received)

        self.assertDictEqual(data, self.gecko_ice)

    def test_when_gecko_answers_connected_client_connection_is_closed(self):
        self.start_client()
        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(self.client_hello))

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

        # 6. Gecko send connected
        self.loop.run_until_complete(self.gecko.send(json.dumps({
            "messageType": "connected",
            "workerId": worker_id
        })))

        # 7. Check that client received connected
        client_received = self.loop.run_until_complete(self.client.recv())
        data = json.loads(client_received)

        self.assertDictEqual(data, {
            "messageType": "connected",
            "workerId": worker_id
        })

        # 8. Make sure client websocket is closed.
        self.loop.run_until_complete(self.client.worker)

    def test_when_client_sends_wrong_json_as_hello(self):
        self.start_client()

        # 1. Client send the offer
        message = self.client_hello[:10]
        self.loop.run_until_complete(self.client.send(message))

        # 2. Client receive error message
        client_received = self.loop.run_until_complete(self.client.recv())
        data = json.loads(client_received)

        self.assertDictEqual(data, {
            "messageType": "progress",
            "status": "terminated",
            "workerId": None,
            "reason": "Message from client is not valid JSON: %s" % message
        })

        # 3. Make sure client websocket is closed.
        self.loop.run_until_complete(self.client.worker)

    def test_when_client_sends_wrong_json_as_ice(self):
        self.start_client()

        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(self.client_hello))

        # 2. Client send the wrong ice
        message = self.client_ice[:10]
        self.loop.run_until_complete(self.client.send(message))

        # 3. Client receive error message
        client_received = self.loop.run_until_complete(self.client.recv())
        data = json.loads(client_received)

        self.assertDictEqual(data, {
            "messageType": "progress",
            "status": "terminated",
            "workerId": None,
            "reason": "Message from client is not valid JSON: %s" % message
        })

        # 4. Make sure client websocket is closed.
        self.loop.run_until_complete(self.client.worker)

    def test_when_client_sends_unknown_action(self):
        self.start_client()

        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(self.client_hello))

        # 2. Client send the wrong ice
        answer = json.dumps(self.gecko_ice)
        self.loop.run_until_complete(
            self.client.send(answer)
        )

        # 3. Client receive error message
        client_received = self.loop.run_until_complete(self.client.recv())
        data = json.loads(client_received)
        self.maxDiff = None
        self.assertDictEqual(data, {
            "messageType": "progress",
            'reason': 'Wrong client ICE message type: %s' % answer,
            'status': 'terminated',
            'workerId': None
        })

        # 4. Make sure client websocket is closed.
        self.loop.run_until_complete(self.client.worker)

    def test_when_gecko_sends_wrong_json_as_answer(self):
        self.start_client()

        # 1. Client send the offer
        self.loop.run_until_complete(self.client.send(self.client_hello))

        # 2. Gecko receive the offer
        gecko_received = self.loop.run_until_complete(self.gecko.recv())
        data = json.loads(gecko_received)

        # 3. Gecko send back the answer
        worker_id = data["workerId"]
        answer = json.dumps({
            "messageType": "worker-created",
            "workerId": worker_id,
            "webrtcAnswer": "<sdp-answer>"
        })
        malformed_answer = answer[:10]
        self.loop.run_until_complete(self.gecko.send(malformed_answer))

        # 4. Check that client received the answer
        client_received = self.loop.run_until_complete(self.client.recv())
        data = json.loads(client_received)

        self.assertDictEqual(data, {
            "messageType": "progress",
            'reason': 'Wrong JSON gecko message: %s' % malformed_answer,
            'status': 'terminated',
            'workerId': None
        })
