#
# Copyright (c) 2016-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
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
    from . import kerberos
except ImportError:
    kerberos = None
try:
    from . import ntlm
except ImportError:
    ntlm = None


def split_credentials(creds):
    if isinstance(creds, bytes):
        warnings.warn(
            "Pass creds as unicode string, got {!r}".format(creds), UnicodeWarning
        )
        creds = creds.decode("utf-8")
    user, password = creds.split("%", 1)
    if "\\" in user:
        domain, user = user.split("\\", 1)
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
            (self.result, self.context) = kerberos.authGSSClientInit(
                "cifs/" + conn.server,
                gssmech=2,
                user=user.encode(cred_encoding),
                password=password.encode(cred_encoding),
                domain=domain.encode(cred_encoding),
            )
        else:
            (self.result, self.context) = kerberos.authGSSClientInit(
                "cifs/" + conn.server, gssmech=1
            )

    def step(self, sec_buf):
        self.result = kerberos.authGSSClientStep(self.context, sec_buf.tobytes())
        if self.result == 0:
            return (
                array.array("B", kerberos.authGSSClientResponse(self.context)),
                None,
            )
        else:
            kerberos.authGSSClientSessionKey(self.context)
            return (
                None,
                array.array("B", kerberos.authGSSClientResponse(self.context)[:16]),
            )

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
        return (
            self.authenticator.authenticate_buffer,
            self.authenticator.exported_session_key,
        )

    def username(self):
        return "{0}\{1}".format(self.authenticator.domain, self.authenticator.username)
