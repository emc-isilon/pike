#
# Copyright (c) 2013, EMC Corporation
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
#        nttime.py
#
# Abstract:
#
#        NT time format utility class
#
# Authors: Rafal Szczesniak (rafal.szczesniak@isilon.com)
#

from datetime import datetime, timedelta
import time

_unix_time_offset = 11644473600L
_unix_epoch = datetime.fromtimestamp(0) + timedelta(hours=time.localtime().tm_isdst)
_intervals_per_second = 10000000L

def _unix_time_to_nt_time(t):
    return (t + _unix_time_offset) * _intervals_per_second

def _datetime_to_unix_time(t):
    td = (t - _unix_epoch)
    return td.seconds + (td.days * 24 * 3600)

def _datetime_to_nt_time(t):
    return _unix_time_to_nt_time(_datetime_to_unix_time(t))

def _nt_time_to_unix_time(t):
    result = (t / _intervals_per_second) - _unix_time_offset
    return result if result >= 0 else 0

def GMT_to_datetime(gmt_token):
    dt_obj = datetime.strptime(
            gmt_token,
            "@GMT-%Y.%m.%d-%H.%M.%S")
    # apply timezone conversion
    dt_obj -= timedelta(seconds=time.timezone)
    return dt_obj

class NtTime(long):
    def __new__(cls, value):
        if isinstance(value, basestring):
            if value.startswith("@GMT-"):
                dt = GMT_to_datetime(value)
            else:
                dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            value = _datetime_to_nt_time(dt)
        elif isinstance(value, datetime):
            value = _datetime_to_nt_time(value)
        
        return super(NtTime, cls).__new__(cls, long(value))

    def __repr__(self):
        return str(self)

    def __str__(self):
        return datetime.fromtimestamp(_nt_time_to_unix_time(self)).strftime("%Y-%m-%d %H:%M:%S")
