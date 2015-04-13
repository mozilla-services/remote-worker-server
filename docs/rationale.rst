Rationale
#########

Philosophy
==========

Remote Worker Server doesn't handle the message passing between the
Firefox Client and the Firefox headless server.

It does just the WebRTC Data Channel setup in between both.

On startup, the gecko register on the server and wait for clients.

On Worker creation clients send the URL they want to run on the server
as well as a Firefox Account authentication.

The aims is to make sure a Firefox Account will always use the same gecko-headless.

It is also to make sure that both can send an receive ICE candidates from the other party.

As soon as the WebRTC data channel is up, the remote worker server
connection is closed and the following exchanges are made P2P using
the WebRTC data channel.


Context
=======

* Build on top of Firefox Account for authentication
* Build on top of WebRTC for scalability


Vision
======

* Build on top of Python3 and AsyncIO for scalability.
* Build for the Remote Worker project but aims to be used for any WebRTC connection setup.
