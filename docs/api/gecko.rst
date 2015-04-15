###############
Worker endpoint
###############

.. _worker-endpoint:

Websocket endpoint
==================

Worker connects the websocket on the ``/worker`` path.

::

    ws://localhost:8765/worker


Registering the gecko
=====================

The first thing to do is to register the gecko server.

.. code-block:: json
    
    {
        "messageType": "hello",
        "action": "worker-hello",
        "geckoId": "<gecko-id>"
    }


Hello fields
------------

* **messageType**: hello
* **action**: worker-hello
* **geckoId**: The unique gecko identifier (should stay the same accross restarts)


Answering new worker demands
============================

Receiving new worker demands
----------------------------

As soon as the gecko is register it will start to receive worker
creation demands, of the form:

.. code-block:: json
    
    {
        "messageType": "new-worker",
        "userId": "<Firefox Account UserID>",
        "workerId": "<Generated Worker UUID>",
        "source": "<worker JS code source URL>",
        "webrtcOffer": "<client sdp-offer>"
    }


When receiving this kind of request, the gecko-server should try to
start the worker.


Answering with errors
---------------------

In case of errors, the response should looks like:

.. code-block:: json

    {
        "messageType": "worker-error",
        "workerId": "<worker-id>",
        "errno": "<worker error number>",
        "reason": "<error reason>"
    }

Answering with WebRTC Answer
----------------------------

If the Gecko was able to start the worker, it should answer with:

.. code-block:: json

    {
        "messageType": "worker-created",
        "workerId": "<worker-id>",
        "webrtcAnswer": "<gecko WebRTC answer>"
    }



Sending ICE Candidates
======================

Once the Answer has been sent, gecko can start to send ICE candidates.

.. code-block:: json
    
    {
        "messageType": "ice",
        "action": "worker-candidate",
        "candidate": {
            "candidate": "candidate:2 1 UDP 2122187007 10.252.27.213 41683 typ host",
            "sdpMid": "",
            "sdpMLineIndex": 0
        }
    }


ICE Candidate fields
--------------------

* **messageType**: ice
* **action**: worker-candidate
* **candidate**: A candidate object

Candidate object fields
-----------------------

* **candidate**: The candidate content
* **sdpMid**: The candidate mid
* **sdpLineIndex**: The SDP Line Index


Sending the connected status
============================

Gecko is responsible to close the connection as soon as the WebRTC
data channel is up.

This is done sending this final standza:

.. code-block:: json

    {
        "messageType": "connected",
        "workerId": "<worker id>"
    }
