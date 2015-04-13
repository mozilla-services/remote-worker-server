Contributing
############


Run tests
=========

::

    make tests


Run a single test
'''''''''''''''''

For Test-Driven Development, it is a possible to run a single test case, in order
to speed-up the execution:

::

    nosetests -s remote_server.tests.functional_tests:ClientServerTestCase.test_when_gecko_answers_an_offer_client_receives_it



Definition of done
==================

* Tests pass;
* Code added comes with tests;
* Documentation is up to date.
