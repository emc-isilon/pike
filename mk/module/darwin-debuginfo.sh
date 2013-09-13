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

_mk_darwin_debuginfo_post_target()
{
    [ "$MK_OS" = "darwin" ] || return 0

    case "$1" in
        "@$MK_STAGE_DIR"/*) :;;
        *) return 0;;
    esac

    mk_quote "$1"

    mk_target \
        TARGET="$1.dSYM/Contents/Info.plist" \
        DEPS="$result" \
        _mk_darwin_dsym "$1"

    mk_quote "$result"
    _dsym_targets="$result"

    mk_basename "$1"

    mk_target \
        TARGET="$1.dSYM/Contents/Resources/DWARF/$result" \
        DEPS="$_dsym_targets"

    mk_quote "$result"
    _dsym_targets="$_dsym_targets $result"

    _MK_DARWIN_DSYM_TARGETS="$_MK_DARWIN_DSYM_TARGETS $_dsym_targets"
    
    unset _dsym_targets
}

option()
{
    if [ "$MK_HOST_OS" = "darwin" ]
    then
        mk_option \
            OPTION="darwin-dsym" \
            VAR="MK_DARWIN_DSYM" \
            PARAM="yes|no" \
            DEFAULT="no" \
            HELP="Create Mach-O dSYM bundles"
    fi
}

configure()
{
    _MK_DARWIN_DSYM_TARGETS=""

    if [ "$MK_DARWIN_DSYM" = "yes" ]
    then
        mk_add_link_target_posthook _mk_darwin_debuginfo_post_target
    fi
}

make()
{
    if [ "$MK_DARWIN_DSYM" = "yes" ]
    then
        mk_target \
            TARGET="@debuginfo" \
            DEPS="$_MK_DARWIN_DSYM_TARGETS"

        mk_add_phony_target "$result"
    fi
}

### section build

_mk_darwin_dsym()
{
    mk_msg_domain "dsym"
    mk_msg "${1#$MK_STAGE_DIR}"
    mk_safe_rm "$1.dSYM"
    mk_run_or_fail dsymutil "$1"
}

