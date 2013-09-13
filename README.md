Pike
====

Pike is a (nearly) pure-Python framework for writing SMB2/3 protocol correctness tests.
See LICENSE for licensing information.

Prerequisites
=============

Required: Python 2.7 (plus devel headers), PyCrypto, MIT gssapi_krb5 (plus devel headers)

Optional: epydoc, RPM/debian packaging tools

Build instructions
==================

From the top-level directory:

    $ mkdir output && cd output
    $ ../configure
    $ make

You can install the pike package globally with:

    $ sudo make install

If necessary tools to build RPM or debian packages were detected, you can
build them with:

    $ make package

You will then find the packages in output/package

Running tests
=============

The tests in the test subdirectory are ordinary Python unittest tests and
can be run as usual.  The following environment variables are used by
the tests:

    PIKE_SERVER=<host name or address>
    PIKE_SHARE=<share name>
    PIKE_LOGLEVEL=info|warning|error|critical|debug

If PIKE_TRACE is set to "yes", then incoming/outgoing packets
will be logged at debug level.

You can also run 'make test' to run the tests without even installing Pike.
In this case the above variables can be passed directly to make without
the PIKE_ prefix, e.g.:

    $ make test SERVER=server.example.com SHARE=foobar

This will run all tests.  You can specify a particular test or suite to run
with TEST=, e.g.:

    $ make test ... TEST=lease.LeaseTest.test_lease_upgrade_break

Your current Kerberos credentials will be used to authenticate.  Use
kinit if you need to acquire a ticket.
