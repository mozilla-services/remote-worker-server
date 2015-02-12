Remote Worker Server
====================

Remote server is the HTTP layer that let you create a remote Gecko
Worker and talk with it through a websocket.

|travis| |readthedocs|

.. |travis| image:: https://travis-ci.org/mozilla-services/remote-worker-server.svg?branch=master
    :target: https://travis-ci.org/mozilla-services/remote-worker-server

.. |readthedocs| image:: https://readthedocs.org/projects/remote-worker-server/badge/?version=latest
    :target: http://remote-worker-server.readthedocs.org/en/latest/
    :alt: Documentation Status

API
===

* `API Design proposal
  <https://github.com/mozilla-services/remote-worker-server/wiki/API-Design-proposal>`_
* `Online documentation <http://remote-worker-server.readthedocs.org/en/latest/>`_


Run locally
===========

By default, remote-worker-server persists its records inside a `Redis
<http://redis.io/>`_  database, so it has to be installed first (see the
"Install Redis" section below for more on this).

Once Redis is installed:

::

    make serve


Install Redis
=============

Linux
-----

On debian / ubuntu based systems::

    apt-get install redis-server


or::

    yum install redis


OS X
----

Assuming `brew <http://brew.sh/>`_ is installed, Redis installation becomes:

::

    brew install redis


To restart it (Bug after configuration update)::

    brew services restart redis


Run tests
=========

::

    make tests
