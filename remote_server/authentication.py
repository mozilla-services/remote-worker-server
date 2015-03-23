from fxa.oauth import Client as OAuthClient
from fxa import errors as fxa_errors

from remote_server.exceptions import NotAuthenticatedError


def authenticate(authorization, server_url, oauth_scope, cache=None):
    if not authorization:
        raise NotAuthenticatedError(ValueError('Authorization is missing'))

    authmeth, auth = authorization.split(' ', 1)

    if authmeth.lower() != 'bearer':
        raise NotAuthenticatedError(
            ValueError('Authorization does not contains a Bearer Token.'))

    auth_client = OAuthClient(server_url=server_url, cache=cache)
    try:
        profile = auth_client.verify_token(token=auth, scope=oauth_scope)
        user_id = profile['user'].encode('utf-8')
    except (fxa_errors.InProtocolError, fxa_errors.TrustError,
            fxa_errors.OutOfProtocolError) as e:
        raise NotAuthenticatedError(e)

    return user_id
