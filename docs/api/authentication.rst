##############
Authentication
##############

.. _authentication:

The authentication is using :term:`Firefox Accounts`, to verify
the *OAuth2 bearer tokens* on a remote server


OAuth Bearer token
==================

Use the OAuth token with this header:

.. code-block:: json

    {
        "authorization": "Bearer <oauth_token>"
    }


:notes:

    If the token is not valid, this will result in a ``INVALID_TOKEN`` error response.


Firefox Account
===============

Obtain the token
----------------

XXX: Endpoint still to be done.

The ``GET /v1/fxa-oauth/params`` endpoint can be use to get the
configuration in order to trade the Firefox Account BrowserID with a
Bearer Token. `See Firefox Account documentation about this behavior
<https://developer.mozilla.org/en-US/Firefox_Accounts#Firefox_Accounts_BrowserID_API>`_

.. code-block:: http

    $ http GET http://localhost:8000/v0/fxa-oauth/params -v

    GET /v0/fxa-oauth/params HTTP/1.1
    Accept: */*
    Accept-Encoding: gzip, deflate
    Host: localhost:8000
    User-Agent: HTTPie/0.8.0


    HTTP/1.1 200 OK
    Content-Length: 103
    Content-Type: application/json; charset=UTF-8
    Date: Thu, 19 Feb 2015 09:28:37 GMT
    Server: waitress

    {
        "oauth_uri": "https://oauth-stable.dev.lcip.org",
        "scope": "remote-worker-server"
    }
