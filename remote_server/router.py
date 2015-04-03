import asyncio
import json
from uuid import uuid4

from remote_server.authentication import authenticate
from remote_server.error import error
from remote_server.exceptions import NotAuthenticatedError, BackendError

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
                yield from self.error('Something went wrong: %s %s' % (type(e), e))
            finally:
                yield from self.websocket.close()
                return
        else:
            yield from self.error('action not found: %s' % action)
            return

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
            yield from self.error('NotAuthenticatedError: %s' %e)
            return

        # 2. Build a new worker_id
        worker_id = str(uuid4())

        # 3. Choose a Gecko
        gecko = yield from self.cache.get('user_gecko.%s' % user_id)

        if not gecko:
            gecko = yield from self.cache.get_random('geckos')

        if not gecko:
            yield from self.error('no gecko headless server available.')
            return
        else:
            yield from self.cache.set('user_gecko.%s' % user_id, gecko)

        # 4. Publish to gecko
        yield from self.cache.lpush('gecko.%s' % gecko, json.dumps({
            "messageType": "new-worker",
            "userId": user_id,
            "workerId": worker_id,
            "source": standza['source'],
            "webrtcOffer": standza['webrtcOffer']
        }))

        # 5. Wait for Gecko WebRTCAnswer
        reply = yield from self.cache.blpop('worker.%s' % worker_id,
                                            CLIENT_TIMEOUT_SECONDS)
        if not reply:
            yield from self.error('Gecko is not answering')
            return

        reply_body = json.loads(reply)
        end = False

        if reply_body['messageType'] == "worker-created":
            answer = json.dumps({
                "messageType": "hello",
                "action": "worker-hello",
                "workerId": worker_id,
                "webrtcAnswer": reply_body['webrtcAnswer']
            })
        elif reply_body['messageType'] == "worker-error":
            answer = reply
            end = True
        elif reply_body['messageType'] == "ice":
            answer = reply
        else:
            yield from self.error('Client side something went wrong: %s'
                                  % reply)
            return

        # 6. Send gecko answer back to the client
        if self.websocket.open:
            print("> %s" % answer)
            yield from self.websocket.send(answer)

            if end:
                yield from self.websocket.close()

            # 7. Wait until connected and send back ice candidates.
            gecko_message = asyncio.Task(self.cache.blpop(
                'worker.%s' % worker_id,
                CLIENT_TIMEOUT_SECONDS))
            client_message = asyncio.Task(self.websocket.recv())

            done, pending = yield from asyncio.wait(
                [gecko_message, client_message],
                return_when=asyncio.FIRST_COMPLETED)

            while self.websocket.open:
                for task in done:
                    if task is gecko_message:
                        # 8. Received gecko ice or connected message
                        try:
                            reply = task.result()
                        except:
                            yield from self.error('Gecko is not answering')
                            return

                        reply_body = json.loads(reply)

                        if reply_body['messageType'] == "ice":
                            answer = reply
                            end = False
                        elif reply_body['messageType'] in ("connected",
                                                           "worker-error"):
                            answer = reply
                            end = True
                        else:
                            msg = 'Gecko side something went wrong: %s' % reply
                            yield from self.error(msg)
                            return

                        if self.websocket.open:
                            print("> %s" % answer)
                            yield from self.websocket.send(answer)

                            if end:
                                return

                            gecko_message = asyncio.Task(self.cache.blpop(
                                'worker.%s' % worker_id,
                                CLIENT_TIMEOUT_SECONDS))
                            pending.add(gecko_message)
                    else:
                        # 9. Receive a client ice message
                        try:
                            reply = task.result()
                        except:
                            yield from self.error('Gecko is not answering')
                            return

                        reply_body = json.loads(reply)

                        if reply_body['messageType'] == "ice" and \
                           reply_body['action'] == "client-candidate" and \
                           'candidate' in reply_body:
                            yield from self.cache.lpush(
                                'gecko.%s' % gecko, json.dumps({
                                    "messageType": "ice",
                                    "workerId": worker_id,
                                    "action": "client-candidate",
                                    "candidate": reply_body['candidate']
                                }))
                        else:
                            msg = 'Gecko ICE something went wrong: %s' % reply
                            yield from self.error(msg)
                            return

                        client_message = asyncio.Task(self.websocket.recv())
                        pending.add(client_message)

                done, pending = yield from asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED)


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
                yield from self.cache.add_to_set('geckos', gecko_id)
                print("# Register new gecko %s" % gecko_id)

                client_message = asyncio.Task(self.cache.blpop(
                    'gecko.%s' % gecko_id,
                    CLIENT_TIMEOUT_SECONDS))
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
                            try:
                                task = task.result()
                            except:
                                pass

                            if not self.websocket.open:
                                # The websocket connection was closed
                                # during the blpop Replay the task as
                                # soon as the gecko reappear.
                                yield from self.cache.lpush(
                                    'gecko.%s' % gecko_id, task)
                                return

                            task_body = json.loads(task)
                            print("# Processing task %s" %
                                  task_body['workerId'])
                            yield from self.websocket.send(task)

                            client_message = asyncio.Task(self.cache.blpop(
                                'gecko.%s' % gecko_id,
                                CLIENT_TIMEOUT_SECONDS))
                            pending.add(client_message)
                        elif task is gecko_message:
                            # Handle gecko_messages
                            reply = task.result()
                            if not reply:
                                # Websocket closed
                                yield from self.cache.remove_from_set('geckos',
                                                                      gecko_id)
                                return

                            reply_body = json.loads(reply)
                            worker_id = 'worker.%s' % reply_body['workerId']
                            print("# Answering task %s" %
                                  reply_body['workerId'])
                            yield from self.cache.lpush(worker_id, reply)

                            gecko_message = asyncio.Task(self.websocket.recv())
                            pending.add(gecko_message)
