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

#<
# @module chain-autotools
# @brief Chain into autotools C/C++ projects
#
# The <lit>chain-autotools</lit> module extends the
# <modref>chain-compiler</modref> module to integrate
# autotools (autoconf, automake, libtool) components
# into your project.
#>

DEPENDS="chain-compiler"

### section configure

_mk_at_system_string()
{
    mk_get "MK_${1}_OS"

    case "${result}" in
        linux)
            __os="linux-gnu"
            ;;
        freebsd)
            mk_get "MK_${1}_DISTRO_VERSION"
            __os="freebsd${result%.0}.0"
            ;;
        solaris)
            mk_get "MK_${1}_DISTRO_VERSION"
            __os="solaris2.${result}"
            ;;
        darwin)
            __os="darwin`uname -r`"
            ;;
        aix)
            mk_get "MK_${1}_DISTRO_VERSION"
            __os="aix${result}.0.0"
            ;;
        hpux)
            mk_get "MK_${1}_DISTRO_VERSION"
            __os="hpux${result}"
            ;;
        *)
            __os="unknown"
            ;;
    esac

    case "${2}" in
        x86_32)
            case "$__os" in
                darwin*)
                    __arch="i386-apple"
                    ;;
                *)
                    __arch="i686-pc"
                    ;;
            esac
            ;;
        x86_64)
            case "$__os" in
                darwin*)
                    __arch="x86_64-apple"
                    ;;
                *)
                    __arch="x86_64-unknown"
                    ;;
            esac
            ;;
        ppc32)
            case "$__os" in
                darwin*)
                    __arch="ppc-apple"
                    ;;
                aix*)
                    __arch="powerpc-ibm"
                    ;;
                *)
                    __arch="powerpc-unknown"
                    ;;
            esac
            ;;
        ppc64)
            case "$__os" in
                darwin*)
                    __arch="ppc64-apple"
                    ;;
                aix*)
                    __arch="powerpc-ibm"
                    ;;
                *)
                    __arch="powerpc-unknown"
                    ;;
            esac
            ;;
        sparc*)
            __arch="sparc-sun"
            ;;
        hppa32)
            __arch="hppa2.0-hp"
            ;;
        hppa64)
            __arch="hppa64-hp"
            ;;
        ia64*)
            case "$__os" in
                hpux*)
                    __arch="ia64-hp"
                    ;;
                *)
                    __arch="ia64-unknown"
                    ;;
            esac
            ;;
        *)
            __arch="unknown-unknown"
            ;;
    esac

    result="${__arch}-${__os}"
}

_mk_at_expand_srcdir_patterns()
{
    _include="$1"
    _exclude="$2"
    _args=""

    set -f
    mk_unquote_list "$_exclude"
    set +f
    for _pattern
    do
        mk_quote_list -o -name "$_pattern"
        _args="$_args $result"
    done
    
    _args="$_args -prune"

    set -f
    mk_unquote_list "$_include"
    set +f
    for _pattern
    do
        mk_quote_list -o -name "$_pattern"
        _args="$_args $result"
    done

    mk_unquote_list "$_args"
    shift

    _IFS="$IFS"
    IFS='
'
    set -- `find "$MK_SOURCE_DIR$MK_SUBDIR${SOURCEDIR:+/$SOURCEDIR}" '(' "$@" ')' -print | sed 's/^/@/g'`
    IFS="$_IFS"

    mk_quote_list "$@"
}

#<
# @brief Build autotools source component
# @usage options... -- configure_params...
# @option MAKE_BUILD_TARGET=name The target name to pass to make
# when building the component.  Defaults to nothing (e.g. the
# default target in the Makefile, usually "all").
# @option MAKE_INSTALL_TARGET=name The target name to pass to make
# when installing the component.  Defaults to "install".
# @option INSTALL_PRE=func Specifies a custom function to run
# before installing the component into the output directory.
# The function is passed the path to the output directory.
# @option INSTALL_POST=func Specifies a custom function to
# run after installing the component into the output directory.
# The function is passed the path to the output directory.
# @option BUILDDEP_PATTERNS=inc_patterns An optional list of patterns
# that will be passed to <lit>find</lit> to identify files within
# the source tree that should trigger a rebuild when changed.
# A reasonable default will be used if not specified that works
# for most C/C++ autotools projects.
# @option BUILDDEP_EXCLUDE_PATTERNS=exc_patterns An optional list
# of patterns that will be passed to <lit>find</lit> to prune when
# looking for files in the source tree.  A reasonable default that
# skips all hidden files and directories will be used if not
# specified.
# @option ... Any option supported by <funcref>mk_chain_compiler</funcref>.
# @option configure_params Additional parameters to pass to
# the component's configure script.
#
# Builds and installs an autotools (autoconf, automake, libtool) source
# component using <funcref>mk_chain_compiler</funcref>.  Default configure
# and build functions are used that take the component through
# the usual <lit>configure</lit>, <lit>make</lit>, <lit>make install</lit>
# procedure.
#
# The trailing positional arguments to this function are passed verbatim
# to the configure script of the component.  In addition, flags such as
# <lit>--prefix</lit> are passed automatically according to how the
# MakeKit project was configured.
#
# @example
# make()
# {
#     # Build popt in the popt-1.15 directory
#     mk_autotools \
#         SOURCEDIR="popt-1.15" HEADERS="popt.h" LIBS="popt" -- \
#         --disable-nls
# }
# @endexample
#>
mk_chain_autotools()
{
    mk_push_vars \
        SOURCEDIR NAME HEADERS LIBS PROGRAMS \
        DLOS LIBDEPS HEADERDEPS CPPFLAGS CFLAGS CXXFLAGS \
        LDFLAGS TARGETS DEPS BUILDDEPS INSTALL_PRE INSTALL_POST \
        MULTIARCH="$MK_MULTIARCH" \
        STAGE="mk_chain_compiler_stage" \
        SET_LIBRARY_PATH=yes MAKE_BUILD_TARGET="" \
        MAKE_INSTALL_TARGET="install" \
        BUILDDEP_PATTERNS="$_MK_AT_BUILDDEP_PATTERNS" \
        BUILDDEP_EXCLUDE_PATTERNS="$_MK_AT_BUILDDEP_EXCLUDE_PATTERNS" \
        PASSVARS PARAMS NAME stamp
    mk_parse_params

    mk_quote_list "$@"
    PARAMS="$result"

    PASSVARS="$PASSVARS PARAMS INSTALL_PRE INSTALL_POST SET_LIBRARY_PATH"
    PASSVARS="$PASSVARS MAKE_BUILD_TARGET MAKE_INSTALL_TARGET"

    if [ -d "${MK_SOURCE_DIR}${MK_SUBDIR}/$SOURCEDIR" ]
    then
        _mk_at_expand_srcdir_patterns "$BUILDDEP_PATTERNS" "$BUILDDEP_EXCLUDE_PATTERNS"
        BUILDDEPS="$BUILDDEPS $result"
    fi

    if ! [ -d "${MK_SOURCE_DIR}${MK_SUBDIR}/$SOURCEDIR" ]
    then
        mk_quote "$SOURCEDIR"
        DEPS="$DEPS $result"
    elif ! [ -f "${MK_SOURCE_DIR}${MK_SUBDIR}/${SOURCEDIR}/configure" ]
    then
        if [ -f "${MK_SOURCE_DIR}${MK_SUBDIR}/${SOURCEDIR}/autogen.sh" ]
        then
            _command="./autogen.sh"
            _msg="running autogen.sh"
        else
            _command="autoreconf -fi"
            _msg="running autoreconf"
        fi

        if [ -n "$SOURCEDIR" ]
        then
            _msg="$_msg for $SOURCEDIR"
        fi

        mk_msg "$_msg"
        mk_cd_or_fail "${MK_SOURCE_DIR}${MK_SUBDIR}/${SOURCEDIR}"
        mk_run_quiet_or_fail ${_command}
        mk_cd_or_fail "${MK_ROOT_DIR}"
    fi

    mk_chain_compiler \
        SOURCEDIR="$SOURCEDIR" \
        NAME="$NAME" \
        TARGETS="$TARGETS" \
        HEADERS="$HEADERS" \
        LIBS="$LIBS" \
        PROGRAMS="$PROGRAMS" \
        DLOS="$DLOS" \
        LIBDEPS="$LIBDEPS" \
        HEADERDEPS="$HEADERDEPS" \
        CPPFLAGS="$CPPFLAGS" \
        CXXFLAGS="$CXXFLAGS" \
        LDFLAGS="$LDFLAGS" \
        DEPS="$DEPS" \
        BUILDDEPS="$BUILDDEPS" \
        CONFIGURE="_mk_at_configure" \
        BUILD="_mk_at_build" \
        PASSVARS="$PASSVARS" \
        STAGE="$STAGE" \
        MULTIARCH="$MULTIARCH"

    mk_pop_vars
}

mk_autotools()
{
    mk_deprecated "mk_autotools is deprecated; use mk_chain_autotools"
    mk_chain_autotools "$@"
}

option()
{
    _mk_at_system_string BUILD "${MK_BUILD_PRIMARY_ISA}"

    mk_option \
        OPTION="at-build-string" \
        VAR=MK_AT_BUILD_STRING \
        DEFAULT="$result" \
        HELP="Build system string"

    for _isa in ${MK_HOST_ISAS}
    do   
        mk_varname "$_isa"
        _var="MK_AT_HOST_STRING_$result"
        _option="at-host-string-$(echo $_isa | tr '_' '-')"

        _mk_at_system_string HOST "$_isa"

        mk_option \
            OPTION="$_option" \
            VAR="$_var" \
            DEFAULT="$result" \
            HELP="Host system string ($_isa)"
    done

    mk_option \
        OPTION="at-pass-vars" \
        VAR=MK_AT_PASS_VARS \
        DEFAULT="" \
        HELP="List of additional variables to pass when configuring"
}

configure()
{
    mk_msg "build system string: $MK_AT_BUILD_STRING"

    mk_declare -e MK_AT_BUILD_STRING MK_AT_PASS_VARS
    mk_declare -s -e MK_AT_HOST_STRING
    
    for _isa in ${MK_HOST_ISAS}
    do
        mk_varname "$_isa"
        mk_get "MK_AT_HOST_STRING_$result"
        mk_msg "host system string ($_isa): $result"
        mk_set_system_var SYSTEM="host/$_isa" MK_AT_HOST_STRING "$result"
    done

    mk_msg "pass-through variables: $MK_AT_PASS_VARS"

    _MK_AT_BUILDDEP_PATTERNS="Makefile.am configure.in configure.ac *.c *.h *.cpp *.C *.cp *.s"
    _MK_AT_BUILDDEP_EXCLUDE_PATTERNS=".*"
}

### section build

_mk_at_log_command()
{
    # $1 = source directory
    # $2 = step

    _mk_slashless_name "$1_$2_$MK_CANONICAL_SYSTEM"
    _log="${MK_ROOT_DIR}/${MK_LOG_DIR}/${result}.log"

    shift 2

    mk_mkdir "${MK_ROOT_DIR}/${MK_LOG_DIR}"

    if [ -n "$MK_VERBOSE" ]
    then
        mk_quote_list "$@"
        mk_msg_verbose "+ $result"
    fi

    if ! "$@" >"$_log" 2>&1
    then
        mk_quote_list "$@"
        mk_msg "FAILED: $result"
        echo ""
        echo "Last 100 lines of ${_log#$MK_ROOT_DIR/}:"
        echo ""
        tail -100 "$_log"
        exit 1
    fi
}

_mk_at_hack_libtool()
{
    case "$MK_OS:$MK_ARCH" in
        hpux:ia64|darwin:*|freebsd:*)
            if [ -x libtool ]
            then
                sed \
                    -e 's/^hardcode_direct=no/hardcode_direct=yes/' \
                    -e 's/^hardcode_direct_absolute=no/hardcode_direct_absolute=yes/' \
                    -e 's/^hardcode_libdir_flag_spec=.*/hardcode_libdir_flag_spec=""/' \
                    < libtool > libtool.new
                mv -f libtool.new libtool
                chmod +x libtool
            fi
            ;;
        *)
            if [ -x libtool ]
            then
                sed \
                    -e 's/^hardcode_libdir_flag_spec=.*/hardcode_libdir_flag_spec=""/' \
                    < libtool > libtool.new
                mv -f libtool.new libtool
                chmod +x libtool
            fi
            ;;
    esac
}

_mk_at_configure()
{
    # $1 = source dir
    # $2 = build dir

    mk_mkdir "$MK_STAGE_DIR"

    if [ "${MK_SYSTEM%/*}" = "build" ]
    then
        _prefix="$MK_ROOT_DIR/$MK_RUN_PREFIX"
        _includedir="$MK_ROOT_DIR/$MK_RUN_INCLUDEDIR"
        _libdir="$MK_ROOT_DIR/$MK_RUN_LIBDIR"
        _bindir="$MK_ROOT_DIR/$MK_RUN_BINDIR"
        _sbindir="$MK_ROOT_DIR/$MK_RUN_SBINDIR"
        _sysconfdir="$MK_ROOT_DIR/$MK_RUN_SYSCONFDIR"
        _localstatedir="$MK_ROOT_DIR/$MK_RUN_LOCALSTATEDIR"
        _stage_dir="`cd ${MK_STAGE_DIR} && pwd`"
        _include_dir="$_includedir"
        _lib_dir="$_libdir"
    else
        _prefix="$MK_PREFIX"
        _includedir="$MK_INCLUDEDIR"
        _libdir="$MK_LIBDIR"
        _bindir="$MK_BINDIR"
        _sbindir="$MK_SBINDIR"
        _sysconfdir="$MK_SYSCONFDIR"
        _localstatedir="$MK_LOCALSTATEDIR"
        _stage_dir="`cd ${MK_STAGE_DIR} && pwd`"
        _include_dir="${_stage_dir}${_includedir}"
        _lib_dir="${_stage_dir}${_libdir}"
    fi

    _src_dir="`cd $1 && pwd`"
    _libpath=""
    
    if [ "$MK_CROSS_COMPILING" = "no" -a "$SET_LIBRARY_PATH" = "yes" ]
    then
        mk_get "$MK_LIBPATH_VAR"
        mk_set "$MK_LIBPATH_VAR" "$_lib_dir:$result"
        export "$MK_LIBPATH_VAR"
    fi

    # Make the linker happy, etc.
    case "$MK_OS" in
        linux|freebsd)
            _ldflags="-L${_lib_dir}"
            ;;
        aix)
            _ldflags="-L${_lib_dir} -Wl,-brtl"
            ;;
        *)
            _ldflags="-L${_lib_dir}"
            ;;
    esac
    
    if [ -d "$MK_RUN_BINDIR" ]
    then
        PATH="`cd $MK_RUN_BINDIR && pwd`:$PATH"
        export PATH
    fi

    # If the build system supports the host ISA we will build for,
    # pretend that the build system is the same.  This avoids making
    # autoconf believe we are cross compiling and failing any run
    # tests.
    if [ "$MK_HOST_OS" = "$MK_BUILD_OS" ] && _mk_contains "$MK_ISA" ${MK_BUILD_ISAS}
    then
        _build_string="$MK_AT_HOST_STRING"
    else
        _build_string="$MK_AT_BUILD_STRING"
    fi
    
    for var in ${MK_AT_PASS_VARS}
    do
        mk_get "$var"
        mk_quote "$var=$result"
        PARAMS="$PARAMS $result"
    done

    mk_cd_or_fail "$2"

    mk_unquote_list "$PARAMS"

    _mk_at_log_command "$NAME" "configure" "${_src_dir}/configure" \
        CC="$MK_CC" \
        CXX="$MK_CXX" \
        CPPFLAGS="-I${_include_dir} $MK_ISA_CPPFLAGS $MK_CPPFLAGS $CPPFLAGS" \
        CFLAGS="$MK_ISA_CFLAGS $MK_CFLAGS $CFLAGS" \
        CXXFLAGS="$MK_ISA_CXXFLAGS $MK_CXXFLAGS $CXXFLAGS" \
        LDFLAGS="$MK_ISA_LDFLAGS $MK_LDFLAGS $LDFLAGS ${_ldflags} $MK_RPATHFLAGS" \
        --build="${_build_string}" \
        --host="${MK_AT_HOST_STRING}" \
        --prefix="${_prefix}" \
        --libdir="${_libdir}" \
        --bindir="${_bindir}" \
        --sbindir="${_sbindir}" \
        --sysconfdir="${_sysconfdir}" \
        --localstatedir="${_localstatedir}" \
        --enable-fast-install \
        --disable-rpath \
        "$@"

    # Does what it says
    _mk_at_hack_libtool

    mk_cd_or_fail "$MK_ROOT_DIR"
}

_mk_at_build()
{
    # $1 = build dir
    # $2 = output dir

    if [ -d "$MK_RUN_BINDIR" ]
    then
        PATH="`cd $MK_RUN_BINDIR && pwd`:$PATH"
        export PATH
    fi

    case "$MK_OS:$MK_ISA" in
        aix:ppc32)
            OBJECT_MODE="32"
            export OBJECT_MODE
            ;;
        aix:ppc64)
            OBJECT_MODE="64"
            export OBJECT_MODE
            ;;
    esac
    
    mk_cd_or_fail "$1"
    _mk_at_log_command "$NAME" "build" ${MAKE} ${MFLAGS} ${MAKE_BUILD_TARGET}
    [ -n "$INSTALL_PRE" ] && ${INSTALL_PRE} "$MK_ROOT_DIR/$2"
    _mk_at_log_command "$NAME" "install" ${MAKE} ${MFLAGS} ${MAKE_INSTALL_TARGET} DESTDIR="$MK_ROOT_DIR/$2"
    [ -n "$INSTALL_POST" ] && ${INSTALL_POST} "$MK_ROOT_DIR/$2"
    mk_cd_or_fail "$MK_ROOT_DIR"
}
