Pike
====

Pike is a (nearly) pure-Python framework for writing SMB2/3 protocol correctness tests.
See [LICENSE](LICENSE) for licensing information.

There is also [API documentation from epydoc](http://emc-isilon.github.io/pike/api/index.html).

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

Building on OS X
----------------

As of 10.8, OS X still ships with versions of python and MIT krb5 that are
too old for Pike to work.  The following instructions are one way of getting
it to build and run successfully:

Download and install python 2.7: http://python.org/ftp/python/2.7.5/python-2.7.5-macosx10.6.dmg

Download and unpack PyCrypto: https://ftp.dlitz.net/pub/dlitz/crypto/pycrypto/pycrypto-2.6.tar.gz

In the resulting directory, run:

    $ python2.7 setup.py build && python2.7 setup.py install
    
Download and unpack MIT krb5: http://web.mit.edu/kerberos/dist/krb5/1.11/krb5-1.11.3-signed.tar

Unpack krb5-1.11.3.tar.gz

We will install it to ${HOME}/.local, but you can choose another prefix if you wish.

    $ cd krb5-1.11.3/src
    $ ./configure --prefix=${HOME}/.local
    $ make -j8 && make install
    
Now, you can configure Pike as follows:

    $ ../configure CPPFLAGS="-I${HOME}/.local/include" LDFLAGS="-L${HOME}/.local/lib" \
                   PYTHON=python2.7 PYTHON_CONFIG=python2.7-config --host-isas=x86_64                    

You should now be able to build as usual.  Before attempting to run, you will need to
create ${HOME}/.local/etc/krb5.conf as follows:

    [libdefaults]
            dns_lookup_kdc = true
            
You should now be able to acquire credentials with:

    $ ~/.local/bin/kinit <user>@<domain>
    
If you installed krb5 to a different prefix, you will need to adjust the above
commands accordingly.

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

Note that you will probably need to specify the server by fully-qualified
hostname in order for Kerberos to figure out which ticket to use.  If you
get errors during session setup when using an IP address, this is probably
the reason.
