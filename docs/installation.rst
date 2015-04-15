Installation
############


By default, Remote Worker Server uses `Redis <http://redis.io/>`_ for
both cache, task queuing and message passing.


Distribute & Pip
================

Installing Remote Worker Server with pip in a python3 environment:

::

    pip install remote-worker-server


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

