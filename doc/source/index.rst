.. Pike documentation master file

#########
pike-smb2
#########
Release |release| (:ref:`Installation <install>`)

************
What is pike
************

``pike`` is an `SMB2 <https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-smb2/5606ad47-5ee0-437a-817e-70c366052962>`_
client implemented in Python, with a focus on *testability* and *extensibility*.

It is not **NOT** fast.

********
Why pike
********

``pike`` provides access to windows, macOS, or samba (linux) shares
in a platform-indepent way.

``pike`` can be used to reproduce strange protocol interactions and
develop regression tests. It provides deep access to view and manipulate
protocol internals.

``pike`` is asynchronous, allowing many operations to be in flight at once.

.. _install:

*******
Install
*******

::

    $ python -m pip install pike-smb2

`pike-smb2 on pypi.org <https://pypi.org/project/pike-smb2/>`_

***********
Quick Start
***********

Connect to a share and write to a file
======================================

.. code-block:: python

   from pike import TreeConnect

   with TreeConnect(server="127.0.0.1", creds="myuser%S3cUrePassw0rd", share="stuff") as tc:
      subdir = tc / "fun_and_games"
      subdir.mkdir(exist_ok=True)
      (subdir / "pike1.txt").write_text("Pike makes SMB2 look easy")


Passing ``TreeConnect`` Environment Variables
=============================================

Hard coding addresses and credentials is fine at the REPL, but a script
should prefer to not specify these values and fall back to the default
environment variables:

    - ``PIKE_SERVER``
    - ``PIKE_PORT``
    - ``PIKE_CREDS`` (percent delimited)
    - ``PIKE_SHARE``

Subsequent examples will not pass these variables explicitly

Using the ``Pathlike`` interface
================================

the ``TreeConnect`` object can be used with the division operator
to construct a ``Pathlike`` object, ``PikePath``. The returned
instance is bound to the particular tree connect and session
and can perform most common `Path <https://docs.python.org/3/library/pathlib.html#methods>`_
operations.

.. code-block:: python

   from pike import TreeConnect
   from pike.smb2 import FILE_STANDARD_INFORMATION

   with TreeConnect() as tc:
      for item in (tc / ".").glob("*.txt"):
         eof = item.stat(file_information_class=FILE_STANDARD_INFORMATION).end_of_file
         print("{} EOF is {}".format(item, eof)

      smb_file = (tc / "filelike.txt")
      with smb_file.open("w+") as fh:
         fh.write("Treat is like a local file\n")
         fh.seek(0)
         print(fh.read())
      smb_file.unlink()

Pytest Integration
==================

A `pytest <https://docs.pytest.org/en/stable/>`_ fixture, ``pike_TreeConnect`` provides
access to the ``TreeConnect`` object with dialect and capability marks applied.

SMB2 Mapped Operations
======================

``pike.model`` provides access to the SMB2 protocol operations.

Of particular interest is ``pike.model.Channel.create`` which is used to open a
file, returning a ``Future`` for a ``pike.io.Open`` which provides the file-like
API as well as convenience wrappers into all other ``pike.model.Channel`` calls
that take an ``Open`` as a parameter.

*********
Contents:
*********

.. toctree::
   :maxdepth: 2

   High-Level API <high_level>
   API Summary <autosummary>
   Implementation Details <model>

******************
Indices and tables
******************

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

