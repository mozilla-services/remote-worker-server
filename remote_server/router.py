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
                return
            except Exception as e:
                yield from self.error('Something went wrong: %s' % e)
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

        # 2. Build worker_id
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

        reply = yield from self.cache.blpop('worker.%s' % worker_id,
                                            CLIENT_TIMEOUT_SECONDS)
        if not reply:
            yield from self.error('Gecko is not answering')
            return

        reply_body = json.loads(reply)

        if reply_body['messageType'] != "worker-created":
            yield from self.error('Something went wrong: %s' % reply_body.get('reason'))
            return

        answer = json.dumps({
            "messageType": "hello",
            "action": "worker-hello",
            "workerId": worker_id,
            "webrtcAnswer": reply_body['webrtcAnswer']
        })
        print("> %s" % answer)
        yield from self.websocket.send(answer)
        yield from self.websocket.close()


class WorkerRouter(Router):

    @asyncio.coroutine
    def dispatch(self):
        standza = yield from self.websocket.recv()
        print("< %s" % standza)
        if standza:
            standza = json.loads(standza)

            if standza.get('action') == 'worker-hello':
                gecko_id = standza['geckoID']
                yield from self.cache.add_to_set('geckos', gecko_id)
                print("# Register new gecko %s" % gecko_id)

                while self.websocket.open:
                    task = yield from self.cache.blpop('gecko.%s' % gecko_id)
                    task_body = json.loads(task)
                    print("# Processing task %s" % task_body['workerId'])
                    yield from self.websocket.send(task)

                    reply = yield from self.websocket.recv()
                    if reply:
                        reply_body = json.loads(reply)
                        worker_id = 'worker.%s' % reply_body['workerId']
                        print("# Answering task %s" % task_body['workerId'])
                        yield from self.cache.lpush(worker_id, reply)

                yield from self.cache.remove_from_set('geckos', gecko_id)
