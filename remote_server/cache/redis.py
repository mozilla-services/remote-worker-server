from __future__ import absolute_import
from functools import wraps

import asyncio
import aioredis
import time

from six.moves.urllib import parse as urlparse

from remote_server.cache import CacheBase
from remote_server.exceptions import BackendError


def wrap_redis_error(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (redis.RedisError, ValueError) as e:
            raise BackendError(original=e)
    return wrapped


class Redis(CacheBase):
    """Cache backend implementation using Redis.

    Enable in configuration::

        remote_server.cache_backend = remote_server.cache.redis

    *(Optional)* Instance location URI can be customized::

        remote_server.cache_url = redis://localhost:6379/1
    """

    def __init__(self, host, port, *args, **kwargs):
        super(Redis, self).__init__(*args, **kwargs)
        self.host = host
        self.port = port

    @asyncio.coroutine
    def setup_pooler(self):
        self._pool = yield from aioredis.create_pool(
            (self.host, self.port), encoding="utf-8", minsize=5, maxsize=10)

    @asyncio.coroutine
    @wrap_redis_error
    def flush(self):
        with (yield from self._pool) as redis:
            yield from redis.flushdb()

    @asyncio.coroutine
    def ping(self):
        with (yield from self._pool) as redis:
            try:
                yield from redis.setex('heartbeat', 3600, time.time())
                return True
            except redis.RedisError:
                return False

    @asyncio.coroutine
    @wrap_redis_error
    def ttl(self, key):
        with (yield from self._pool) as redis:
            yield from redis.ttl(key)

    @asyncio.coroutine
    @wrap_redis_error
    def expire(self, key, value):
        with (yield from self._pool) as redis:
            yield from redis.pexpire(key, int(value * 1000))

    @asyncio.coroutine
    @wrap_redis_error
    def set(self, key, value, ttl=None):
        with (yield from self._pool) as redis:
            if ttl:
                yield from redis.psetex(key, int(ttl * 1000), value)
            else:
                yield from redis.set(key, value)

    @asyncio.coroutine
    @wrap_redis_error
    def get(self, key):
        with (yield from self._pool) as redis:
            value = yield from redis.get(key)
        if value:
            return value

    @asyncio.coroutine
    @wrap_redis_error
    def delete(self, key):
        with (yield from self._pool) as redis:
            yield from redis.delete(key)

    @asyncio.coroutine
    @wrap_redis_error
    def add_to_set(self, key, value):
        with (yield from self._pool) as redis:
            yield from redis.sadd(key, value)

    @asyncio.coroutine
    @wrap_redis_error
    def remove_from_set(self, key, value):
        with (yield from self._pool) as redis:
            yield from redis.srem(key, value)

    @asyncio.coroutine
    @wrap_redis_error
    def get_random(self, key):
        with (yield from self._pool) as redis:
            value = yield from redis.srandmember(key)
            return value

    @asyncio.coroutine
    @wrap_redis_error
    def get_from_set(self, key):
        with (yield from self._pool) as redis:
            value = yield from redis.smembers(key)
            return value

    @asyncio.coroutine
    @wrap_redis_error
    def blpop(self, key, timeout=0):
        with (yield from self._pool) as redis:
            result = yield from redis.blpop(key, timeout)
            return result[1].decode('utf-8')

    @asyncio.coroutine
    @wrap_redis_error
    def lpush(self, key, value):
        with (yield from self._pool) as redis:
            yield from redis.lpush(key, value.encode('utf-8'))


def load_from_config(settings):
    uri = settings['remote_server.cache_url']
    uri = urlparse.urlparse(uri)

    return Redis(host=uri.hostname or 'localhost',
                 port=uri.port or 6739,
                 password=uri.password or None,
                 db=int(uri.path[1:]) if uri.path else 0)
