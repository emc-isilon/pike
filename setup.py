#!/usr/bin/env python

import ctypes
import sys
import unittest
try:
    from setuptools import setup, Extension, Command
except ImportError:
    from distutils.core import setup, Extension, Command
from distutils.command.build_ext import build_ext
from distutils.command.build_py import build_py
from distutils.errors import CCompilerError, DistutilsExecError, \
                             DistutilsPlatformError
from pike import __version__

# attempt building the kerberos extension
try_krb = True

if sys.platform == 'win32' and sys.version_info > (2, 6):
   # 2.6's distutils.msvc9compiler can raise an IOError when failing to
   # find the compiler
   # It can also raise ValueError http://bugs.python.org/issue7511
   ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError,
                 IOError, ValueError)
else:
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
    defines = [("HAVE_GSS_SET_CRED_OPTION", hasattr(libgssapi_krb5,
                                                    "gss_set_cred_option")),
               ("HAVE_GSSSPI_SET_CRED_OPTION", hasattr(libgssapi_krb5,
                                                       "gssspi_set_cred_option"))]
    lw_krb_module = Extension('pike.kerberos',
                              ["pykerb/base64.c",
                               "pykerb/kerberosbasic.c",
                               "pykerb/kerberos.c",
                               "pykerb/kerberosgss.c",
                               "pykerb/kerberospw.c"],
                              libraries=['gssapi_krb5'],
                              define_macros=defines)
except OSError:
    try_krb = False

def pike_suite():
    return unittest.defaultTestLoader.discover('pike/test', pattern='*.py')

def run_setup(with_extensions):
    ext_modules = []
    cmdclass = { "build_py": ve_build_py }
    if with_extensions:
        ext_modules.append(lw_krb_module)
        cmdclass = dict(cmdclass, build_ext=ve_build_ext)
    setup(name='Pike',
          version=__version__,
          description='Pure python SMB client',
          author='Brian Koropoff',
          author_email='Brian.Koropoff@emc.com',
          url='https://github.com/emc-isilon/pike',
          packages=['pike', 'pike.test'],
          install_requires=['pycryptodome'],
          ext_modules=ext_modules,
          test_suite='setup.pike_suite',
          cmdclass=cmdclass,
          )
try:
    run_setup(with_extensions=try_krb)
except BuildFailed:
    run_setup(with_extensions=False)
