###############
Client endpoint
###############

.. _client-endpoint:

Websocket endpoint
==================

**Requires authentication**

Clients connects the websocket directly on ``/``

::

    ws://localhost:8765/


Creating a new worker
=====================

In order to ask for a worker creation client need to send this first standza:

.. code-block:: json
    
    {
        "messageType": "hello",
        "action": "client-hello",
        "authorization": "Bearer <oauth token>",
        "source": "<worker_js_url>",
        "webrtcOffer": "<sdp-offer>"
    }


Hello fields
------------

* **messageType**: hello
* **action**: client-hello
* **authorization**: Bearer token
* **source**: The worker JavaScript code URL
* **webrtcOffer**: The WebRTC SDP offer


Sending ICE Candidates
======================

Once the Hello has been sent client can start to send ICE Candidates.

.. code-block:: json
    
    {
        "messageType": "ice",
        "action": "client-candidate",
        "candidate": {
            "candidate": "candidate:2 1 UDP 2122187007 10.252.27.213 41683 typ host",
            "sdpMid": "",
            "sdpMLineIndex": 0
        }
    }


ICE Candidate fields
--------------------

* **messageType**: ice
* **action**: client-candidate
* **candidate**: A candidate object

Candidate object fields
-----------------------

* **candidate**: The candidate content
* **sdpMid**: The candidate mid
* **sdpLineIndex**: The SDP Line Index


Receiving errors
================

In case the gecko is not available or was not able to start the
worker, you will receive an error.

.. code-block:: json

    {
        "messageType": "worker-error",
        "workerId": "<worker-id>",
        "errno": "<worker error number>",
        "reason": "<error reason>"
    }


Receiving WebRTC Answer
=======================

If everything worked, you should receive the Gecko Answer.

.. code-block:: json

    {
        "messageType": "hello",
        "action": "worker-hello",
        "workerId": "<Worker ID >",
        "webrtcAnswer": "<Gecko WebRTC Answer>"
    }


Receiving Gecko ICE Candidates
==============================

In order to setup the WebRTC data channel, you may receive the Gecko
ICE Candidates.

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
