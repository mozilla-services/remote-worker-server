Rationale
#########

The remote worker server is a signaling service helping client-side user agents
(local workers) to connect to gecko instances running in the cloud (remote
workers).

The goal of the remote worker server is to connect clients with
remotely-running gecko instances, in order to execute javascript workers code
in a distant way.

On the gecko side, the code will be ran in a service worker.


Philosophy
==========

The message broker doesn't handle the message passing between the
Firefox Client and the Firefox headless server, but does the preliminary work
(WebRTC data channel setup) to make this happen. Once the connection is setup,
gecko talks directly with the clients using a WebRTC peer connection.

On startup, all geckos registers on the server and wait for clients to connect.

On the client side, local workers send an URL that should be run remotely, as
well as a Firefox Accounts authentication information.

One Firefox Account will always be tied to one remote gecko instance.

As soon as the WebRTC data channel is up, the remote worker server
connection is closed and the following exchanges are made P2P using
the WebRTC data channel.
