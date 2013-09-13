#
# Copyright (c) Brian Koropoff
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the MakeKit project nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
#
DEPENDS="compiler"

### section configure

option()
{
    mk_option \
        OPTION="harden-pie" \
        VAR=MK_HARDEN_PIE \
        PARAM="yes|no" \
        DEFAULT="no" \
        HELP="Enable position-independent executables"

    mk_option \
        OPTION="harden-stack" \
        VAR=MK_HARDEN_STACK \
        PARAM="all|yes|no" \
        DEFAULT="no" \
        HELP="Enable stack smash protection"
}

configure()
{
    if [ "$MK_HARDEN_PIE" = "yes" ]
    then
        mk_add_link_target_prehook _mk_pie_link_hook
        mk_add_compile_target_prehook _mk_pie_compile_hook
    fi
    if [ "$MK_HARDEN_STACK" = "all" ]
    then
        MK_CFLAGS="$MK_CFLAGS -fstack-protector -fstack-protector-all"
        MK_CXXFLAGS="$MK_CXXFLAGS -fstack-protector -fstack-protector-all"
    elif [ "$MK_HARDEN_STACK" = "yes" ]
    then
        MK_CFLAGS="$MK_CFLAGS -fstack-protector"
        MK_CXXFLAGS="$MK_CXXFLAGS -fstack-protector"
    fi
}

_mk_pie_link_hook()
{
    if [ "$1" = "mk_program" ]
    then
        LDFLAGS="$LDFLAGS -pie"
    fi
}

_mk_pie_compile_hook()
{
    if [ "$PIC" = "no" ]
    then
        CFLAGS="$CFLAGS -fPIE"
        CXXFLAGS="$CXXFLAGS -fPIE"
    fi
}
