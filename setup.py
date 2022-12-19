#!/usr/bin/env python
#
# Copyright (c) 2016-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
import ctypes

try:
    from setuptools import setup, Extension, Command
except ImportError:
    from distutils.core import setup, Extension, Command
from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError

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
    setup(
        ext_modules=[lw_krb_module],
        cmdclass={"build_ex": ve_build_ext},
    )
except (OSError, BuildFailed):
    print("libgssapi_krb5 not available, skipping kerberos module")
    setup()
