from gevent import monkey
monkey.patch_all()

import json

from loads.case import TestCase

WORKER_URL = "ws://localhost:8765/worker"
CLIENT_URL = "ws://localhost:8765"

BEARER_TOKEN = "13cbb5664aaccd662d803e71e547cdb58485ce25477f" \
               "635bc5051aa550eed00d"


class TestRemoteServer(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestRemoteServer, self).__init__(*args, **kwargs)

    def setUp(self):
        self.wss = []
        self.gecko_ice_received = False

    def tearDown(self):
        for ws in self.wss:
            self.close(ws)

    def close(self, ws):
        ws.close()
        # XXX this is missing in ws4py
        ws._th.join()
        if ws.sock:
            ws.sock.close()

    def test_all(self):
        self._test_basic_scenario()

    def _send_ws_message(self, ws, **msg):
        message = json.dumps(msg)
        print("> %s" % message)
        return ws.send(message)

    def create_ws(self, *args, **kw):
        ws = TestCase.create_ws(self, *args, **kw)
        self.wss.append(ws)
        return ws

    def _test_basic_scenario(self):
        def _handle_gecko(message_data):
            self.incr_counter("gecko-message-recv")
            print("Gecko < %s" % message_data.data)
            standza = json.loads(message_data.data)
            message_type = standza.get('messageType')
            # 3. Gecko answer with the WebRTC answer
            if message_type == "new-worker":
                worker_id = standza.get("workerId")
                self.incr_counter("gecko-message-send")
                self._send_ws_message(
                    gecko_ws,
                    messageType="worker-created",
                    workerId=worker_id,
                    webrtcAnswer="<sdp-answer>")
                client_ws.receive()
            elif message_type == "ice":
                if not self.gecko_ice_received:
                    # 5. Gecko send an ICE candidate
                    self.incr_counter("gecko-message-send")
                    self._send_ws_message(
                        gecko_ws,
                        messageType="ice",
                        action="worker-candidate",
                        workerId=worker_id,
                        webrtcAnswer={
                            "candidate": "candidate:2 1 UDP 2122187007 "
                            "10.252.27.213 41683 typ host",
                            "sdpMid": "",
                            "sdpMLineIndex": 0
                        })
                    client_ws.receive()
                    self.gecko_ice_received = True
                else:
                    # 7. Gecko send connected
                    self.incr_counter("gecko-message-send")
                    self._send_ws_message(
                        gecko_ws,
                        messageType="connected",
                        workerId=worker_id)
                    client_ws.receive()
                    # 9. Gecko quit
                    self.close(gecko_ws)

        def _handle_client(message_data):
            self.incr_counter("client-message-recv")
            print("Client < %s" % message_data.data)
            standza = json.loads(message_data.data)
            message_type = standza.get('messageType')
            # 4. Client receive WebRTCAnswer
            if message_type == "worker-created":
                # 4. Client send a ICE candidate
                self.incr_counter("client-message-send")
                self._send_ws_message(
                    client_ws,
                    messageType="ice",
                    action="client-candidate",
                    webrtcAnswer={
                        "candidate": "candidate:2 1 UDP 2122187007 "
                        "10.252.27.213 41683 typ host",
                        "sdpMid": "",
                        "sdpMLineIndex": 0
                    })
                gecko_ws.receive()
            elif message_type == "ice":
                # 6. Client send another ICE candidate
                self.incr_counter("client-message-send")
                self._send_ws_message(
                    client_ws,
                    messageType="ice",
                    action="client-candidate",
                    webrtcAnswer={
                        "candidate": "candidate:2 1 UDP 2122187007 "
                        "10.252.27.213 41683 typ host",
                        "sdpMid": "",
                        "sdpMLineIndex": 0
                    })
                gecko_ws.receive()
            elif message_type == "connected":
                # 8. Client is connected
                self.incr_counter("client-connected")

        # 1. Gecko headless connects
        print("\rCreate Gecko Websocket")
        gecko_ws = self.create_ws(WORKER_URL, callback=_handle_gecko)
        self.incr_counter("gecko-message-send")
        print("Send Gecko Hello")
        self._send_ws_message(
            gecko_ws,
            messageType='hello',
            action='worker-hello',
            geckoId="gecko-headless-1")

        # 2. Client connects and send a WebRTC Offer
        print("Create client websocket")
        client_ws = self.create_ws(CLIENT_URL, callback=_handle_client)
        self.incr_counter("client-message-send")
        print("Send Client WebRTC Offer")
        self._send_ws_message(
            client_ws,
            messageType="hello",
            action="client-hello",
            authorization="Bearer %s" % BEARER_TOKEN,
            source="http://localhost:8080/worker.js",
            webrtcOffer="<sdp-offer>")
        print("Wait for gecko")
        gecko_ws.receive()
