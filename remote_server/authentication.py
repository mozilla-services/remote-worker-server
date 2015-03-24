import asyncio
import aiohttp
import hashlib
import hmac
import json

from six.moves.urllib.parse import urljoin

from remote_server import exceptions

DEFAULT_SERVER_URL = "https://oauth.accounts.firefox.com/v1"
VERSION_SUFFIXES = ("/v1",)
DEFAULT_CACHE_EXPIRY = 300
TOKEN_HMAC_SECRET = 'PyFxA Token Cache Hmac Secret'


def get_hmac(data, secret, algorithm=hashlib.sha256):
    """Generate an hexdigest hmac for given data, secret and algorithm."""
    return hmac.new(secret.encode('utf-8'),
                    data.encode('utf-8'),
                    algorithm).hexdigest()


@asyncio.coroutine
def verify_token(server_url, token, scope, cache):
    """Verify an OAuth token, and retrieve user id and scopes.

    :param token: the string to verify.
    :param scope: optional scope expected to be provided for this token.
    :returns: a dict with user id and authorized scopes for this token.
    :raises fxa.errors.ClientError: if the provided token is invalid.
    :raises fxa.errors.TrustError: if the token scopes do not match.
    """
    if server_url is None:
        server_url = DEFAULT_SERVER_URL
    server_url = server_url.rstrip('/')
    if not server_url.endswith(VERSION_SUFFIXES):
        server_url += VERSION_SUFFIXES[0]

    key = 'fxa.oauth.verify_token:%s:%s' % (
        get_hmac(token, TOKEN_HMAC_SECRET), scope)

    body = None
    if cache is not None:
        body = yield from cache.get(key)

    if body is None:
        url = server_url + '/verify'
        request_body = {
            'token': token
        }
        resp = yield from aiohttp.request(
            'POST', url,
            data=json.dumps(request_body),
            headers={'content-type': 'application/json'})
        body = yield from resp.json()
        missing_attrs = ", ".join([
            k for k in ('user', 'scope', 'client_id') if k not in body
        ])
        if missing_attrs:
            error_msg = '{0} missing in OAuth response'.format(
                missing_attrs)
            raise exceptions.OutOfProtocolError(error_msg)

        if scope is not None:
            authorized_scope = body['scope']
            if not scope_matches(authorized_scope, scope):
                raise exceptions.ScopeMismatchError(authorized_scope, scope)

        if cache is not None:
            cache.set(key, json.dumps(body).encode('utf-8'))
    else:
        body = json.loads(resp.decode('utf-8'))

    return body


@asyncio.coroutine
def authenticate(authorization, server_url, oauth_scope, cache=None):
    if not authorization:
        raise exceptions.NotAuthenticatedError('Authorization is missing')

    authmeth, auth = authorization.split(' ', 1)

    if authmeth.lower() != 'bearer':
        raise exceptions.NotAuthenticatedError(
            'Authorization does not contains a Bearer Token.')

    try:
        profile = yield from verify_token(server_url=server_url,
                                          cache=cache,
                                          token=auth,
                                          scope=oauth_scope)
        user_id = profile['user'].encode('utf-8')
    except exceptions.BackendError as e:
        raise exceptions.NotAuthenticatedError(e)

    return user_id


def scope_matches(provided, required):
    """Check that required scopes match the ones provided. This is used during
    token verification to raise errors if expected scopes are not met.

    :note:

        Sub-scopes are expressed using semi-colons.

        A required sub-scope will always match if its root-scope is among those
        provided (e.g. ``profile:avatar`` will match ``profile`` if provided).

    :param provided: list of scopes provided for the current token.
    :param required: the scope required (e.g. by the application).
    :returns: ``True`` if all required scopes are provided, ``False`` if not.
    """
    if not isinstance(required, (list, tuple)):
        required = [required]

    def split_subscope(s):
        return tuple((s.split(':') + [None])[:2])

    provided = set([split_subscope(p) for p in provided])
    required = set([split_subscope(r) for r in required])

    root_provided = set([root for (root, sub) in provided])
    root_required = set([root for (root, sub) in required])

    if not root_required.issubset(root_provided):
        return False

    for (root, sub) in required:
        if (root, None) in provided:
            provided.add((root, sub))

    return required.issubset(provided)
