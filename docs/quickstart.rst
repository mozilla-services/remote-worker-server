Getting started
###############

Once storage engines and python dependencies have been installed, it's is
easy to get started!


Run locally
===========

By default, remote-worker-server persists its records inside a `Redis
<http://redis.io/>`_  database, so it has to be installed first (see the
"Install Redis" section below for more on this).

You will also need to have a Python 3.4 running.


The server
----------

::

    make serve


Add a fake worker
-----------------

::

    make mock_worker

Connect a fake client
---------------------

::

    make mock_client



Run tests
=========

::

    make tests
