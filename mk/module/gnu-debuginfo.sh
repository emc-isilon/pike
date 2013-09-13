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

_mk_gnu_debuginfo_post_target()
{
    case "$1" in
        "@$MK_STAGE_DIR"/*) :;;
        *) return 0;;
    esac

    mk_basename "$1"
    _debugname="${result%%.*}.dbg"
    mk_dirname "$1"
    _debugfile="${result}/.debug/${_debugname}"
    _debugtemp="@${MK_OBJECT_DIR}/.debug${result#@$MK_STAGE_DIR}/${_debugname}"

    mk_quote "$1"

    mk_target \
        TARGET="$_debugtemp" \
        DEPS="$result"

    mk_stage \
        SOURCE="$_debugtemp" \
        DEST="$_debugfile"

    mk_quote "$result"
    _MK_GNU_DEBUGINFO_TARGETS="$_MK_GNU_DEBUGINFO_TARGETS $result"
}

option()
{
    case "$MK_HOST_OS" in
        linux|freebsd|solaris)
            mk_option \
                OPTION="gnu-split-debuginfo" \
                VAR="MK_GNU_SPLIT_DEBUGINFO" \
                PARAM="yes|no" \
                DEFAULT="no" \
                HELP="Split debug symbols into separate file when using GNU linker"
            ;;
    esac
}

configure()
{
    _MK_GNU_DEBUGINFO_TARGETS=""

    if [ "$MK_GNU_SPLIT_DEBUGINFO" = "yes" ]
    then
        mk_add_link_target_posthook _mk_gnu_debuginfo_post_target
        mk_add_link_posthook _mk_gnu_debuginfo_post
    fi
}

make()
{
    if [ "$MK_GNU_SPLIT_DEBUGINFO" = "yes" ]
    then
        mk_target \
            TARGET="@debuginfo" \
            DEPS="$_MK_GNU_DEBUGINFO_TARGETS"

        mk_add_phony_target "$result"
    fi

    mk_add_clean_target "@${MK_OBJECT_DIR}/.debug"
}

### section build

_mk_gnu_debuginfo_post()
{
    case "$1" in
        "$MK_STAGE_DIR"/*) : ;;
        *) return 0;
    esac

    mk_basename "$1"
    _debugname="${result%%.*}.dbg"
    mk_dirname "$1"
    _debugtemp="${MK_OBJECT_DIR}/.debug${result#$MK_STAGE_DIR}/${_debugname}"

    mk_mkdirname "$_debugtemp"
    mk_run_or_fail objcopy --only-keep-debug -- "$1" "$_debugtemp"
    mk_get_file_mode "$1"
    _old_mode="$result"
    mk_run_or_fail chmod u+w -- "$1"
    mk_run_or_fail objcopy --add-gnu-debuglink="$_debugtemp" -- "$1"
    mk_run_or_fail strip -g -- "$1"
    mk_run_or_fail chmod "$_old_mode" -- "$1"
}