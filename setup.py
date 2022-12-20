#!/usr/bin/env python
#
# Copyright (c) 2016-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
import ctypes
import os

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError

_HERED = os.path.abspath(os.path.dirname(__file__))


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
        include_dirs=[os.path.join(_HERED, "pykerb", "vendor")],
        libraries=["gssapi_krb5"],
        define_macros=defines,
    )
    setup(ext_modules=[lw_krb_module])
except (OSError, CCompilerError, DistutilsExecError, DistutilsPlatformError):
    print("libgssapi_krb5 not available, skipping kerberos module")
    setup()
