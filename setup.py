#!/usr/bin/env python
#
# Copyright (c) 2016-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#

import ctypes
import os
import unittest

try:
    from setuptools import setup, Extension, Command
except ImportError:
    from distutils.core import setup, Extension, Command
from distutils.command.build_ext import build_ext
from distutils.command.build_py import build_py
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError

_HERED = os.path.abspath(os.path.dirname(__file__))
_README = os.path.join(_HERED, 'README.md')

# attempt building the kerberos extension
try_krb = True
ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)


class BuildFailed(Exception):
    pass


class ve_build_ext(build_ext):
    # This class allows C extension building to fail.

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except ext_errors:
            raise BuildFailed()


class ve_build_py(build_py):
    def run(self, *args, **kwds):
        if not try_krb:
            print("libgssapi_krb5 not available, skipping kerberos module")
        build_py.run(self, *args, **kwds)


try:
    libgssapi_krb5 = ctypes.CDLL("libgssapi_krb5.so")
    defines = [
        ("HAVE_GSS_SET_CRED_OPTION", hasattr(libgssapi_krb5, "gss_set_cred_option")),
        (
            "HAVE_GSSSPI_SET_CRED_OPTION",
            hasattr(libgssapi_krb5, "gssspi_set_cred_option"),
        ),
    ]
    lw_krb_module = Extension(
        "pike.kerberos",
        [
            "pykerb/base64.c",
            "pykerb/kerberosbasic.c",
            "pykerb/kerberos.c",
            "pykerb/kerberosgss.c",
            "pykerb/kerberospw.c",
        ],
        libraries=["gssapi_krb5"],
        define_macros=defines,
    )
except OSError:
    try_krb = False


def pike_suite():
    return unittest.defaultTestLoader.discover("pike/test", pattern="*.py")


# Get the long description from the README.md file
with open(_README, 'rb') as f_:
    long_description = f_.read().decode("utf-8")


def run_setup(with_extensions):
    ext_modules = []
    cmdclass = {"build_py": ve_build_py}
    if with_extensions:
        ext_modules.append(lw_krb_module)
        cmdclass = dict(cmdclass, build_ext=ve_build_ext)
    setup(
        name="pike-smb2",
        use_scm_version=True,
        setup_requires=[
            'setuptools_scm==5.0.2; python_version ~= "2.7"',
            'setuptools_scm; python_version >= "3.6"',
        ],
        description="Pure python SMB client",
        long_description_content_type='text/markdown',
        long_description=long_description,
        author="Brian Koropoff",
        author_email="Brian.Koropoff@emc.com",
        maintainer="Masen Furer",
        maintainer_email="Masen.Furer@dell.com",
        url="https://github.com/emc-isilon/pike",
        project_urls={
           "Source": "https://github.com/emc-isilon/pike",
           "Bug Reports": "https://github.com/emc-isilon/pike/issues",
        },
        license="Simplified BSD License",
        packages=["pike", "pike.test"],
        entry_points={"pytest11": ["pike = pike.pytest_support",]},
        python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*",
        install_requires=[
            'enum34~=1.1.6;  python_version ~= "2.7"',
            'attrs~=19.3.0',
            "pycryptodomex",
            "future",
            "six",
        ],
        ext_modules=ext_modules,
        test_suite="setup.pike_suite",
        cmdclass=cmdclass,
        # see https://pypi.org/classifiers/
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: Testing",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: Implementation :: CPython",
            "Operating System :: OS Independent",
            "Environment :: Console",
            "License :: OSI Approved :: BSD License",
        ],
        keywords='smb smb-testing smb-client',
    )


try:
    run_setup(with_extensions=try_krb)
except BuildFailed:
    run_setup(with_extensions=False)
