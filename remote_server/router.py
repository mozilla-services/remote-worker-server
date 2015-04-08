import asyncio
import json
import traceback
from uuid import uuid4

from remote_server.authentication import authenticate
from remote_server.error import error
from remote_server.exceptions import NotAuthenticatedError

CLIENT_TIMEOUT_SECONDS = 30


class Router(object):
    def __init__(self, websocket, cache, config):
        self.websocket = websocket
        self.cache = cache
        self.config = config

    @asyncio.coroutine
    def error(self, *args, **kwargs):
        error_message = error(*args, **kwargs)
        print("# Error", error_message, args, kwargs)
        yield from self.websocket.send(json.dumps(error_message))


class ClientRouter(Router):

    @asyncio.coroutine
    def dispatch(self):
        standza = yield from self.websocket.recv()
        standza = json.loads(standza)
        if standza.get('action') == 'client-hello':
            try:
                yield from self.handler(standza)
            except Exception as e:
                yield from self.error('Something went wrong: %s %s'
                                      % (type(e), e))
                yield from self.error(traceback.format_exc())
            finally:
                yield from self.websocket.close()
                return
        else:
            yield from self.error('action not found: %s'
                                  % standza.get('action'))
            return

    def get_worker_id(self):
        return str(uuid4())

    @asyncio.coroutine
    def get_user_gecko(self, user_id):
        gecko = yield from self.cache.get('user_gecko.%s' % user_id)

        if not gecko:
            gecko = yield from self.cache.get_random('geckos')

        if not gecko:
            yield from self.error('no gecko headless server available.')
            return
        else:
            yield from self.cache.set('user_gecko.%s' % user_id, gecko)
        return gecko

    @asyncio.coroutine
    def handle_client_message(self, raw_message, gecko, worker_id):
        try:
            message = json.loads(raw_message)
        except ValueError:
            yield from self.error('Message from client is not valid JSON: %s'
                                  % raw_message)
            return True

        if message['messageType'] == "ice" and \
           message['action'] == "client-candidate" and \
           'candidate' in message:
            yield from self.publish_to_gecko(gecko, {
                "messageType": "ice",
                "workerId": worker_id,
                "action": "client-candidate",
                "candidate": message['candidate']
            })
            return False
        else:
            msg = 'Wrong client ICE message type: %s' % raw_message
            yield from self.error(msg)
            return True

    @asyncio.coroutine
    def handle_gecko_message(self, raw_message, worker_id):
        try:
            message = json.loads(raw_message)
        except ValueError:
            yield from self.error('Message from gecko is not valid JSON: %s'
                                  % raw_message)
            return True

        answer = None
        end = False
        if message['messageType'] == "worker-created":
            answer = json.dumps({
                "messageType": "hello",
                "action": "worker-hello",
                "workerId": worker_id,
                "webrtcAnswer": message['webrtcAnswer']
            })
        elif message['messageType'] in ("worker-error", "connected"):
            answer = raw_message
            end = True
        elif message['messageType'] == "ice":
            answer = raw_message
        else:
            yield from self.error('Wrong message from Gecko: %s'
                                  % raw_message)
            end = False

        if self.websocket.open and answer:
            print("> %s" % answer)
            yield from self.websocket.send(answer)

        return end

    @asyncio.coroutine
    def publish_to_gecko(self, gecko_id, obj):
        yield from self.cache.lpush('gecko.%s' % gecko_id, json.dumps(obj))

    def read_from_gecko(self, worker_id, timeout=0):
        return self.cache.blpop('worker.%s' % worker_id, timeout)

    @asyncio.coroutine
    def handler(self, standza):
        # 1. Validate Authorization
        try:
            user_id = yield from authenticate(
                standza.get('authorization'),
                self.config['fxa-oauth.server_url'],
                self.config['fxa-oauth.scope'],
                self.cache)
        except NotAuthenticatedError as e:
            yield from self.error('NotAuthenticatedError: %s' % e)
            return

        # 2. Build a new worker_id
        worker_id = self.get_worker_id()

        # 3. Get User Gecko
        gecko = yield from self.get_user_gecko(user_id)

        # 4. Publish to gecko
        yield from self.publish_to_gecko(gecko, {
            "messageType": "new-worker",
            "userId": user_id,
            "workerId": worker_id,
            "source": standza['source'],
            "webrtcOffer": standza['webrtcOffer']
        })

        # 5. Wait for Gecko WebRTCAnswer
        timeout = CLIENT_TIMEOUT_SECONDS
        reply = yield from self.read_from_gecko(worker_id, timeout)

        if not reply:
            yield from self.error('Gecko is not answering')
            return

        # 6. Send gecko answer back to the client
        end = yield from self.handle_gecko_message(reply, worker_id)

        if end:  # In case of error stop
            return

        # 7. Wait until connected and send back ice candidates.
        gecko_message = asyncio.Task(self.read_from_gecko(worker_id))
        client_message = asyncio.Task(self.websocket.recv())
        pending = {gecko_message, client_message}

        while self.websocket.open:
            try:
                done, pending = yield from asyncio.wait(
                    pending, return_when=asyncio.FIRST_COMPLETED)
            except asyncio.CancelledError:
                self.cache._conn._do_close(None)
                client_message.cancel()

            for task in done:
                if task is gecko_message:
                    # 8. Received gecko ice or connected message
                    raw_message = task.result()

                    end = yield from self.handle_gecko_message(raw_message,
                                                               worker_id)
                    if end:
                        client_message.cancel()
                        return

                    gecko_message = asyncio.Task(
                        self.read_from_gecko(worker_id))
                    pending.add(gecko_message)
                else:
                    # 9. Receive a client message
                    raw_message = task.result()

                    if not raw_message:
                        print("Client connection closed.")
                        self.cache._conn._do_close(None)
                        return

                    end = yield from self.handle_client_message(raw_message,
                                                                gecko,
                                                                worker_id)

                    if end:
                        self.cache._conn._do_close(None)
                        return

                    client_message = asyncio.Task(self.websocket.recv())
                    pending.add(client_message)


class WorkerRouter(Router):

    @asyncio.coroutine
    def dispatch(self):
        standza = yield from self.websocket.recv()
        print("< %s" % standza)
        if standza:
            standza = json.loads(standza)

            # 1. Register new gecko
            if standza.get('action') == 'worker-hello':
                gecko_id = standza['geckoId']
                yield from self.register_gecko(gecko_id)

                client_message = asyncio.Task(self.read_from_worker(gecko_id))
                gecko_message = asyncio.Task(self.websocket.recv())
                pending = {client_message, gecko_message}

                while self.websocket.open:
                    # 2. Wait for messages on both client and gecko streams.
                    done, pending = yield from asyncio.wait(
                        pending,
                        return_when=asyncio.FIRST_COMPLETED)

                    for task in done:
                        if task is client_message:
                            # 3. Handle client messages
                            raw_message = task.result()

                            if not self.websocket.open:
                                # The websocket connection was closed
                                # during the blpop Replay the task as
                                # soon as the gecko reappear.
                                yield from self.publish_to_gecko(gecko_id,
                                                                 raw_message)
                                return

                            yield from self.handle_client_message(raw_message)
                            future = self.read_from_worker(gecko_id)
                            client_message = asyncio.Task(future)
                            pending.add(client_message)
                        elif task is gecko_message:
                            # Handle gecko_messages
                            raw_message = task.result()
                            if not raw_message:
                                # Websocket closed
                                self.cache._conn._do_close(None)
                                yield from self.unregister_gecko(gecko_id)
                                return

                            yield from self.handle_gecko_message(raw_message)

                            gecko_message = asyncio.Task(self.websocket.recv())
                            pending.add(gecko_message)

    @asyncio.coroutine
    def publish_to_gecko(self, gecko_id, obj):
        yield from self.cache.lpush('gecko.%s' % gecko_id, json.dumps(obj))

    @asyncio.coroutine
    def register_gecko(self, gecko_id):
        yield from self.cache.add_to_set('geckos', gecko_id)
        print("# Register new gecko %s" % gecko_id)

    @asyncio.coroutine
    def unregister_gecko(self, gecko_id):
        yield from self.cache.remove_from_set('geckos', gecko_id)

    @asyncio.coroutine
    def publish_to_worker(self, worker_id, obj):
        yield from self.cache.lpush('worker.%s' % worker_id, json.dumps(obj))

    def read_from_worker(self, gecko_id):
        return self.cache.blpop('gecko.%s' % gecko_id)

    @asyncio.coroutine
    def handle_client_message(self, raw_message):
        message = json.loads(raw_message)
        print("# Processing worker %s" % message['workerId'])
        yield from self.websocket.send(raw_message)

    @asyncio.coroutine
    def handle_gecko_message(self, raw_message):
        try:
            message = json.loads(raw_message)
        except ValueError:
            # Impossible to build an error because we don't know which
            # workerId it is related to.
            raise

        worker_id = message['workerId']
        print("# Answering task %s" % worker_id)
        yield from self.publish_to_worker(worker_id, message)
