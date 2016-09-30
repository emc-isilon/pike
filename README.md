Pike
====

Pike is a (nearly) pure-Python framework for writing SMB2/3 protocol correctness tests.
See [LICENSE](LICENSE) for licensing information.

There is also [API documentation from epydoc](http://emc-isilon.github.io/pike/api/index.html).

Prerequisites
=============

Required for basic functionality:
    * Python 2.7
    * PyCryptodome

Required for building kerberos library:
    * Python development headers
    * MIT gssapi\_krb5 (plus devel headers)
        * Ubuntu: krb5-user, libkrb5-dev

Optional: epydoc for doc generation

Build instructions
==================

    python setup.py build
    python setup.py install

Running tests
=============

The tests in the test subdirectory are ordinary Python unittest tests and
can be run as usual.  The following environment variables are used by
the tests:

    PIKE_SERVER=<host name or address>
    PIKE_SHARE=<share name>
    PIKE_CREDS=DOMAIN\User%Passwd
    PIKE_LOGLEVEL=info|warning|error|critical|debug

If PIKE\_TRACE is set to "yes", then incoming/outgoing packets
will be logged at debug level.

    $ python -m unittest discover -s test -p *.py

To run an individual test file:

    $ python -m unittest discover -s test -p echo.py EchoTest.test_echo

If PIKE\_CREDS is not specified, your current Kerberos credentials will be used
to authenticate.  Use kinit if you need to acquire a ticket.

Note that you will probably need to specify the server by fully-qualified
hostname in order for Kerberos to figure out which ticket to use.  If you
get errors during session setup when using an IP address, this is probably
the reason.
