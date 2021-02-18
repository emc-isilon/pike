##################
Pytest Integration
##################

Pike provides pytest marks and fixtures to assist in writing SMB2 protocol
tests using the `pytest <https://docs.pytest.org/en/stable/>`_ framework.

Typically, tests using these fixtures will leverage the ``PIKE_*`` environment
variables to determine where to connect and other protocol features.

.. automodule:: pike.pytest_support

********************
``pike_TreeConnect``
********************

.. autofunction:: pike.pytest_support.pike_TreeConnect


*****************
``pike_tmp_path``
*****************

.. autofunction:: pike.pytest_support.pike_tmp_path

This fixture is similar to pytest's built in
`tmp_path <https://docs.pytest.org/en/stable/tmpdir.html#the-tmp-path-fixture>`_
fixture.
