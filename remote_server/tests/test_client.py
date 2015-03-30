import json

from remote_server.tests import ClientServerTests

BEARER_TOKEN = "13cbb5664aaccd662d803e71e547cdb58485ce25477f" \
               "635bc5051aa550eed00d"


class ClientTestCase(ClientServerTests):

    def test_when_client_ask_an_offer_it_gets_an_answer(self):
        self.start_client()
        self.loop.run_until_complete(self.client.send(json.dumps({
            "messageType": "hello",
            "action": "client-hello",
            "authorization": "Bearer %s" % BEARER_TOKEN,
            "source": "http://localhost:8080/worker.js",
            "webrtcOffer": "<sdp-offer>"
        })))

        print("listen to gecko")
        gecko_received = self.loop.run_until_complete(self.gecko.recv())
        data = json.loads(gecko_received)
        print("received", data)
        self.assertEqual(data, {
            "messageType": "new-worker",
            "userId": "e2dda4218656438bb7c4a34ceea1aa18",
            "workerId": "",
            "source": "http://localhost:8080/worker.js",
            "webrtcOffer": "<sdp-offer>"
        })
        print("Are you there?")
        print("yes")
        self.stop_client()
        print("yo")
