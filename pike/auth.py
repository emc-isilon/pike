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


import array
try:
    import kerberos
except ImportError:
    kerberos = None
try:
    import ntlm
except ImportError:
    ntlm = None


def split_credentials(creds):
    nt4, password = creds.split('%')
    domain, user = nt4.split('\\')
    return (domain, user, password)


class KerberosProvider(object):
    def __init__(self, conn, creds=None):
        if creds:
            domain, user, password = split_credentials(creds)
            (self.result,
             self.context) = kerberos.authGSSClientInit(
                "cifs/" + conn.server,
                gssmech=2,
                user=user,
                password=password,
                domain=domain)
        else:
            (self.result,
             self.context) = kerberos.authGSSClientInit("cifs/" + conn.server,
                                                        gssmech=1)

    def step(self, sec_buf):
        self.result = kerberos.authGSSClientStep(
                self.context,
                sec_buf.tostring())
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
