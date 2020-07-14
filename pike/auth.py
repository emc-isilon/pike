#
# Copyright (c) 2016, Dell Technologies
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Module Name:
#
#        auth.py
#
# Abstract:
#
#        Authentication Plugins for Pike
#
# Authors: Masen Furer (masen.furer@dell.com)
#

"""
Authentication Plugins for Pike

This module contains wrappers around external authentication mechanisms and APIs.
"""
from __future__ import absolute_import


from builtins import object
import array
import warnings
try:
    import kerberos
except ImportError:
    kerberos = None
try:
    from . import ntlm
except ImportError:
    ntlm = None


def split_credentials(creds):
    if isinstance(creds, bytes):
        warnings.warn("Pass creds as unicode string, got {!r}".format(creds),
                      UnicodeWarning)
        creds = creds.decode("utf-8")
    user, password = creds.split('%')
    if '\\' in user:
        domain, user = user.split('\\')
    else:
        domain = "NONE"
    return (domain, user, password)


class KerberosProvider(object):
    def __init__(self, conn, creds=None):
        if creds:
            # XXX: NTLM support is only provided in likewise gssapi
            raise NotImplementedError("NTLM via GSSAPI is not functional")
            # This API doesn't accept strings with null terminators, so it cannot take
            # utf-16-le (which is what would be expected), so prefer instead to be
            # safe and only allow ascii characters.
            cred_encoding = "ascii"
            domain, user, password = split_credentials(creds)
            (self.result,
             self.context) = kerberos.authGSSClientInit(
                "cifs/" + conn.server,
                gssmech=2,
                user=user.encode(cred_encoding),
                password=password.encode(cred_encoding),
                domain=domain.encode(cred_encoding))
        else:
            (self.result,
             self.context) = kerberos.authGSSClientInit("cifs/" + conn.server,
                                                        gssmech=1)

    def step(self, sec_buf):
        self.result = kerberos.authGSSClientStep(
                self.context,
                sec_buf.tobytes())
        if self.result == 0:
            return (array.array(
                    'B',
                    kerberos.authGSSClientResponse(self.context)),
                    None)
        else:
            kerberos.authGSSClientSessionKey(self.context)
            return (None,
                    array.array('B',
                        kerberos.authGSSClientResponse(self.context)[:16]))

    def username(self):
        return kerberos.authGSSClientUserName(self.context)


class NtlmProvider(object):
    def __init__(self, conn, creds):
        self.authenticator = ntlm.NtlmAuthenticator(*split_credentials(creds))

    def step(self, sec_buf):
        if self.authenticator.negotiate_message is None:
            return (self.authenticator.negotiate(), None)
        elif self.authenticator.challenge_message is None:
            self.authenticator.authenticate(sec_buf)
        return (self.authenticator.authenticate_buffer, self.authenticator.exported_session_key)

    def username(self):
        return '{0}\{1}'.format(self.authenticator.domain, self.authenticator.username)
