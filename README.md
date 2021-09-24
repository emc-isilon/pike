# Pike

Pike is a (nearly) pure-Python framework for writing SMB2/3 protocol correctness tests.

---

<!-- begin TOC -->
- [Pike](#pike)
  - [Prerequisites](#prerequisites)
  - [Install](#install)
  - [Build instructions](#build-instructions)
  - [Running tests](#running-tests)
  - [Kerberos Hints](#kerberos-hints)
  - [Decoding BufferOverrun](#decoding-bufferoverrun)
    - [With Pike](#with-pike)
    - [With Wireshark](#with-wireshark)
  - [License](#license)
  - [Other](#other)

<!-- end TOC -->

---

[![PyPI version](https://badge.fury.io/py/pike-smb2.svg)](https://badge.fury.io/py/pike-smb2)
[![Commits since](https://img.shields.io/github/commits-since/emc-isilon/pike/latest.svg)](https://img.shields.io/github/commits-since/emc-isilon/pike/latest.svg)
[![Python versions](https://img.shields.io/pypi/pyversions/pike-smb2?longCache=True)](https://pypi.org/project/pike-smb2/)
[![License](https://img.shields.io/badge/License-BSD-blue.svg)](https://opensource.org/licenses/BSD-2-Clause)

## Prerequisites

Required for basic functionality:

- Python 2.7, 3.6+
- PyCryptodomex

Required for building kerberos library:

- Python development headers
- MIT `gssapi_krb5` (plus development headers)
  - Ubuntu: `krb5-user`, `libkrb5-dev`

Optional: epydoc for doc generation

## Install

    $ python -m pip install pike-smb2

## Build instructions

Ubuntu 14.04 / 16.04

    apt-get install -y --no-install-recommends krb5-user libkrb5-dev python-dev build-essential python2.7 python-pip py3c-dev
    pip install setuptools pycryptodomex
    python setup.py install

## Running tests

The tests in the test subdirectory are ordinary Python unittest tests and
can be run as usual.  The following environment variables are used by
the tests:

    PIKE_SERVER=<host name or address>
    PIKE_SHARE=<share name>
    PIKE_CREDS=DOMAIN\User%Passwd
    PIKE_LOGLEVEL=info|warning|error|critical|debug
    PIKE_SIGN=yes|no
    PIKE_ENCRYPT=yes|no
    PIKE_MAX_DIALECT=DIALECT_SMBX_Y_Z
    PIKE_MIN_DIALECT=DIALECT_SMBX_Y_Z
    PIKE_TRACE=yes|no

If `PIKE_TRACE` is set to `yes` then incoming/outgoing packets will be
logged at the debug level.

    $ python -m unittest discover -s pike/test -p *.py

Alternatively, to build and run all tests

    $ python setup.py test

To run an individual test file

    $ python -m unittest discover -s pike/test -p echo.py

To run an individual test case

    $ python -m unittest pike.test.echo.EchoTest.test_echo

## Kerberos Hints

Setting up MIT Kerberos as provided by many Linux distributions to interoperate
with an existing Active Directory and Pike is relatively simple.

If `PIKE_CREDS` is not specified and the kerberos module was built while
installing pike then your current Kerberos credentials will be used to
authenticate.

Use a minimal `/etc/krb5.conf` on the client such as the following

    [libdefaults]
        default_realm = AD.EXAMPLE.COM

Retrieve a ticket for the desired user

    $ kinit user_1

(Optional) in leiu of DNS, add host entries for the server name + domain

    $ echo "10.1.1.150    smb-server.ad.example.com" >> /etc/hosts

Run pike tests

    $ PIKE_SERVER="smb-server.ad.example.com" PIKE_SHARE="C$" python -m unittest discover -s pike/test -p tree.py

Note that you will probably need to specify the server by fully-qualified
hostname in order for Kerberos to figure out which ticket to use.  If you
get errors during session setup when using an IP address, this is probably
the reason.

## Decoding BufferOverrun

When pike encounters a buffer or boundary problem, `BufferOverrun` is
raised with the full packet bytes. This can be used in two ways.

### With Pike

For some problems, it may be necessary to run pike with a debugger
while decoding the packet bytes to reproduce runtime parsing or decoding
issues.

    from binascii import unhexlify
    import array
    import pike.netbios

    buf = array.array("B", unhexlify(b'00000114fe534d4240000000000000000000040001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000041000100110302008a8c2a17f5f24e5eb278dd8aaa90d42e1e0000000000010000001000000010006c52c4c7e53dd60166157c68c63dd60180005500d8000000605306062b0601050502a0493047a019301706092a864886f712010202060a2b06010401823702020aa32a3028a0261b246e6f745f646566696e65645f696e5f5246433431373840706c656173655f69676e6f72650000000100260000000000010020000100c93dfb463f3e99ed9030a66d28548c330a4ae9a65856237d00e61f68c14eb09f0000020004000000000001000200'))
    nb = pike.netbios.Netbios()
    nb.parse(buf)

### With Wireshark

Other decoding problems may be easier to understand by looking at the packet
with a pcap analysis tool.

    $ echo '00000114fe534d4240000000000000000000040001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000041000100110302008a8c2a17f5f24e5eb278dd8aaa90d42e1e00000000000100000010000000100050cff0c2e43dd60166157c68c63dd60180005500d8000000605306062b0601050502a0493047a019301706092a864886f712010202060a2b06010401823702020aa32a3028a0261b246e6f745f646566696e65645f696e5f5246433431373840706c656173655f69676e6f7265000000010026000000000001002000010017af98eb38fdcd3db91bdca1303e9c72ef37b7e572abf897e47bd779aaa641d90000020004000000000001000200' \
      | xxd -r -p - \
      | od -Ax -tx1 -v \
      | text2pcap -i46 -T 445,445 - - \
      | tshark -P -V -r -

- `xxd` decodes the ascii hex bytestream output from the `BufferOverrun` exception into binary
- `od` dumps the output to a format [wireshark can read](https://www.wireshark.org/docs/wsug_html_chunked/ChIOImportSection.html)
- `text2pcap` (wireshark) appends fake ethernet and IP headers to the SMB packet and writes a pcap file to stdout
- `tshark` (wireshark) decodes the SMB packet and displays full packet details

## License

This project, _pike_ and _pike-smb2_, is released under a Simplified BSD License granted by Dell Inc.'s Open Source Project program,
except code under `pykerb/` which is released under an Apache 2.0 License granted by Apple Inc.<br />
All project contributions are entirely reflective of the respective author(s) and not of Dell Inc. or Apple Inc.

See file [LICENSE](LICENSE) for licensing information.

## Other

There is older [API documentation from epydoc](http://emc-isilon.github.io/pike/api/index.html).
