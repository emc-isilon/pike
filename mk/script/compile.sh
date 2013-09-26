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

do_compile()
{
    _object="$1"
    _source="$2"

    IFLAGS=""
    
    for _dir in ${INCLUDEDIRS}
    do
        case "$_dir" in
            /*)
                IFLAGS="$IFLAGS -I${MK_STAGE_DIR}$_dir"
                ;;
            *)
                IFLAGS="$IFLAGS -I${MK_SOURCE_DIR}${MK_SUBDIR}/$_dir -I${MK_OBJECT_DIR}${MK_SUBDIR}/$_dir"
                ;;
        esac
    done
    
    case "$COMPILER" in
        c)
            CPROG="$MK_CC"
            FLAGS="$MK_ISA_CFLAGS $MK_CFLAGS $CFLAGS $IFLAGS $MK_ISA_CPPFLAGS $MK_CPPFLAGS $CPPFLAGS"
            ;;
        c++)
            CPROG="$MK_CXX"
            FLAGS="$MK_ISA_CXXFLAGS $MK_CXXFLAGS $CXXFLAGS $IFLAGS $MK_ISA_CPPFLAGS $MK_CPPFLAGS $CPPFLAGS"
            ;;
    esac
    
    if [ -z "$CONFTEST" ]
    then
        FLAGS="$FLAGS -I${MK_STAGE_DIR}${MK_INCLUDEDIR}"
    fi
    mk_defname "$MK_CANONICAL_SYSTEM"
    FLAGS="$FLAGS -DHAVE_CONFIG_H -D_MK_$result"
    mk_defname "${MK_CANONICAL_SYSTEM%/*}"
    FLAGS="$FLAGS -D_MK_$result"
    
    PCH_FLAGS=""
    if [ -n "$PCH" ]
    then
        mk_append_list PCH_FLAGS "-include" "${PCH%.*}"
    fi

    mk_msg_domain compile
    
    if [ -z "$CONFTEST" ]
    then
        mk_mkdir ".MakeKitDeps"
        _mk_slashless_name "${_object%.o}"
        DEP_FILE=".MakeKitDeps/$result.dep"
        mk_quote "$DEP_FILE.new"
        DEP_FLAGS="-MMD -MP -MF $result $DEP_TARGET"
    fi

    if [ "$PIC" = "yes" ]
    then
        FLAGS="$FLAGS -fPIC"
    fi
    
    case "$MK_OS" in
        darwin)
            FLAGS="$FLAGS -fno-common"
            ;;
    esac
    
    mk_msg "$pretty ($MK_CANONICAL_SYSTEM)"
    
    mk_mkdirname "$_object"
    
    mk_unquote_list "$DEP_FLAGS" "$PCH_FLAGS"
    mk_run_or_fail ${CPROG} \
        ${FLAGS} \
        "$@" \
        -o "$_object" \
        -c "$_source"

    if [ -n "$DEP_FILE" -a -f "$DEP_FILE.new" ]
    then
        if diff -q -- "$DEP_FILE" "$DEP_FILE.new" >/dev/null 2>&1
        then
            mk_safe_rm "$DEP_FILE.new"
        else
            mk_run_or_fail mv -f "$DEP_FILE.new" "$DEP_FILE"
            mk_incremental_deps_changed
        fi
    fi
}

object="$1"
shift
mk_pretty_path "$1"
pretty="$result"

if [ -z "$CONFTEST" -a "$MK_SYSTEM" = "host" -a "$MK_MULTIARCH" = "combine" ]
then
    DEP_TARGET="-MT $object"
    parts=""
    for _isa in ${MK_HOST_ISAS}
    do
        mk_system "host/$_isa"
        part="${object%.o}.$_isa.o"
        do_compile "$part" "$@"
        mk_append_list parts "$part"
    done
    mk_unquote_list "$parts"
    _mk_compiler_multiarch_combine "$object" "$@"
    for part
    do
        mk_safe_rm "$part"
    done
else
    do_compile "$object" "$@"
fi
