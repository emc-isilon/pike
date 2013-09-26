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
DEPENDS="core platform path"

#<
# @module compiler
# @brief Build C/C++ projects
#
# <lit>compiler</lit> is the standard MakeKit module which provides an interface
# to the system C compiler.  It contains functions to check for available headers, libraries,
# functions, types, and system and compiler characteristics, and to build programs, libraries,
# and dynamically-loadable objects from C source code.
#
# Most <lit>compiler</lit> functions support a set of common parameters which are
# listed here rather than duplicated in the references for every individual function.
#
# <deflist>
#   <defentry>
#     <term><lit>DEPS=</lit><param>targets</param></term>
#     <item>
#           Specifies additional arbitrary dependencies in MakeKit target notation.  This is useful,
#           for example, if one of your source files depends on a header file which you generate on
#           the fly (e.g. from <command>yacc</command> or <command>lex</command>).
#           Alternatively, you could specify dependencies for individual source files using
#           <funcref>mk_target</funcref> with an empty command.
#           Applicable to all functions.
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>INCLUDEDIRS=</lit><param>paths</param></term>
#     <item>
#           A space-separated list of relative paths where the compiler should search for header files.
#           Even if you only use header files in the same directory as <lit>MakeKitBuild</lit>,
#           you must explicitly specify <lit>.</lit>.
#           Applicable functions: 
#         <funcref>mk_compile</funcref>,
#         <funcref>mk_program</funcref>,
#         <funcref>mk_group</funcref>,
#         <funcref>mk_library</funcref>,
#         <funcref>mk_dlo</funcref>
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>HEADERDEPS=</lit><param>headers</param></term>
#     <item>
#           A space-separated list of public header files (e.g. in <lit>/usr/local/include</lit>)
#           that one or more source files depend on.  You only need to specify header files installed by other
#           MakeKit projects.  If you are careful about specifying dependencies in this way, it allows you
#           to structure your larger project as multiple subprojects which can be configured and built either
#           individually or together.  When building individually, <lit>HEADERDEPS</lit> ensures sure you
#           are performing configure checks for the headers.  When building together, <lit>HEADERDEPS</lit>
#           ensures source files are compiled only once the header files they need have been installed.
#           Applicable functions: 
#         <funcref>mk_compile</funcref>,
#         <funcref>mk_program</funcref>,
#         <funcref>mk_group</funcref>,
#         <funcref>mk_library</funcref>,
#         <funcref>mk_dlo</funcref>
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>LIBDEPS=</lit><param>libs</param></term>
#     <item>
#           A space-separated list of library names to link into the resulting binary,
#           without filename extensions or <lit>lib</lit> prefixed to the name.
#           Applicable functions: 
#         <funcref>mk_program</funcref>,
#         <funcref>mk_group</funcref>,
#         <funcref>mk_library</funcref>,
#         <funcref>mk_prebuilt_library</funcref>,
#         <funcref>mk_dlo</funcref>
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>LIBDIRS=</lit><param>paths</param></term>
#     <item>
#           A space-separated list of additional directories to look for libraries
#           when linking.  The paths should be absolute (e.g. <lit>/usr/foobar/lib</lit>),
#           but they are taken to reference the staging directory.  This is only useful
#           if you need to install and link against a library in a location other than
#           <var>$MK_LIBDIR</var>.  To look for system libaries in non-standard locations,
#           use <lit>LDFLAGS</lit> or <var>MK_LDFLAGS</var>, or a helper
#           module like <lit>pkg-config</lit> when possible.
#           Applicable functions: 
#         <funcref>mk_program</funcref>,
#         <funcref>mk_group</funcref>,
#         <funcref>mk_library</funcref>,
#         <funcref>mk_dlo</funcref>
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>GROUPS=</lit><param>groups</param></term>
#     <item>
#       <para>
#           A space-separated list of object file groups which should be merged
#           into the resulting binary.
#       </para>
#       <para>
#           Applicable functions: 
#         <funcref>mk_program</funcref>,
#         <funcref>mk_library</funcref>,
#         <funcref>mk_dlo</funcref>
#       </para>
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>OBJECTS=</lit><param>objects</param></term>
#     <item>
#       <para>
#           A space-separated list of additional object files to link into the resulting
#           binary.  This is useful if you use <funcref>mk_compile</funcref> to control
#           compiler flags on a per-source-file basis and need to combine the resulting
#           objects into a binary, or if you have object files without source code that
#           you need to link.  If this parameter is specified, you do not need to
#           specify <lit>SOURCES</lit>, but you may.
#       </para>
#       <para>
#           Applicable functions: 
#         <funcref>mk_program</funcref>,
#         <funcref>mk_group</funcref>,
#         <funcref>mk_library</funcref>,
#         <funcref>mk_dlo</funcref>
#       </para>
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>INSTALLDIR=</lit><param>path</param></term>
#     <item>
#       <para>
#           If specified, changes the location where the resulting binary will
#           be installed in the filesystem.  Defaults to what you would expect for the
#           kind of binary being produced, e.g. program executables go in
#           <var>$MK_BINDIR</var>, usually <lit>/usr/local/bin</lit>.
#       </para>
#       <para>
#           Applicable functions: 
#         <funcref>mk_program</funcref>,
#         <funcref>mk_library</funcref>,
#         <funcref>mk_prebuilt_library</funcref>,
#         <funcref>mk_dlo</funcref>
#       </para>
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>EXT=</lit><param>extension</param></term>
#     <item>
#       <para>
#           Overrides the extension of the resulting file.
#       </para>
#       <para>
#           Applicable functions: 
#         <funcref>mk_library</funcref>,
#         <funcref>mk_prebuilt_library</funcref>,
#         <funcref>mk_dlo</funcref>
#       </para>
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>CPPFLAGS=</lit><param>flags</param></term>
#     <term><lit>CFLAGS=</lit><param>flags</param></term>
#     <term><lit>LDFLAGS=</lit><param>flags</param></term>
#     <item>
#       <para>
#           Specifies additional flags passed to the compiler when preprocessing,
#           compiling, and linking, respectively.  These parameters are added to
#           and do not override those in the <var>MK_CPPFLAGS</var>,
#           <var>MK_CFLAGS</var>, and <var>MK_LDFLAGS</var>
#           variables.  All default to being empty.
#       </para>
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>PCH=</lit><param>header</param></term>
#     <item>
#       <para>
#         Specifies a header to automatically precompile and include when
#         building source files.  Precompiled headers can speed up
#         compilation of some projects.  If the header is also included
#         directly by the source code, it should use include guards to
#         avoid being processed twice.
#       </para>
#       <para>
#         The <var>result</var> of an explict call to
#         <funcref>mk_pch</funcref> may be used instead of a plain header.
#         This allows sharing a single precompiled header across multiple build
#         targets, but care must be taken to ensure that compiler
#         flags match or the precompiled header may be rejected.
#       </para>
#       <para>
#         Applicable functions: 
#         <funcref>mk_compile</funcref>,
#         <funcref>mk_group</funcref>,
#         <funcref>mk_program</funcref>,
#         <funcref>mk_library</funcref>,
#         <funcref>mk_dlo</funcref>
#       </para>
#     </item>
#   </defentry>
#   <defentry>
#     <term><lit>COMPILER=</lit><param>compiler</param></term>
#     <item>
#       <para>
#         Explicitly overrides the compiler used to build source files.
#         Must be precisely <lit>c</lit> or <lit>c++</lit>.
#       </para>
#       <para>
#         Applicable functions: 
#         <funcref>mk_compile</funcref>,
#         <funcref>mk_pch</funcref>,
#         <funcref>mk_group</funcref>,
#         <funcref>mk_program</funcref>,
#         <funcref>mk_library</funcref>,
#         <funcref>mk_dlo</funcref>
#       </para>
#     </item>
#   </defentry>
# </deflist>
#>

#<
# @var MK_CC
# @brief C compiler
# @export
# @system
#
# Set to the executable and arguments used to invoke the C compiler.
# Note that this variable is system-dependent and may have separate
# values for each target system and ISA.
#>

#<
# @var MK_CXX
# @brief C++ compiler
# @export
# @system
#
# Set to the executable and arguments used to invoke the C++ compiler.
# Note that this variable is system-dependent and may have separate
# values for each target system and ISA.
#>

#<
# @var MK_CPPFLAGS
# @brief Global C preprocessor flags
# @export
# @inherit
#
# The flags in this variable will be passed to any compiler operation
# involving the C or C++ preprocessor.
#>

#<
# @var MK_CFLAGS
# @brief Global C compiler flags
# @export
# @inherit
#
# The flags in this variable will be passed to any compiler operation
# involving C source code.
#>

#<
# @var MK_CXXFLAGS
# @brief Global C++ compiler flags
# @export
# @inherit
#
# The flags in this variable will be passed to any compiler operation
# involving C++ source code.
#>

#<
# @var MK_LDFLAGS
# @brief Global linker compiler flags
# @export
# @inherit
#
# The flags in this variable will be passed to any compiler operation
# involving linking an executable, library, or dynamically-loadable object.
#>

#<
# @var MK_ISA_CPPFLAGS
# @brief Per-ISA C preprocessor flags
# @export
# @inherit
# @system
#
# The flags in this variable will be passed to any compiler operation
# involving the C or C++ preprocessor.  Because it is a system-dependent
# variable, it may be used to set flags that apply to only one particular
# target system and ISA.
#>

#<
# @var MK_ISA_CFLAGS
# @brief Per-ISA C compiler flags
# @export
# @inherit
# @system
#
# The flags in this variable will be passed to any compiler operation
# involving C source code.  Because it is a system-dependent
# variable, it may be used to set flags that apply to only one particular
# target system and ISA.
#>

#<
# @var MK_ISA_CXXFLAGS
# @brief Per-ISA C++ compiler flags
# @export
# @inherit
# @system
#
# The flags in this variable will be passed to any compiler operation
# involving C++ source code.  Because it is a system-dependent
# variable, it may be used to set flags that apply to only one particular
# target system and ISA.
#>

#<
# @var MK_ISA_LDFLAGS
# @brief Per-ISA linker flags
# @export
# @inherit
# @system
#
# The flags in this variable will be passed to any compiler operation
# involving linking an executable, library, or dynamically-loadable object.
# Because it is a system-dependent variable, it may be used to set flags
# that apply to only one particular target system and ISA.
#>

#<
# @var MK_CC_STYLE
# @brief Style of C compiler
# @export
# @system
# @value none No working C compiler is available
# @value gcc The C compiler is gcc or gcc-compatible
# @value unknown The C compiler style is unknown
#
# Defines the style of the C compiler.  This does not indicate the precise
# vendor of the compiler but is an abstract classification of its supported
# parameters, extensions, etc.  For example, <lit>clang</lit> is highly
# compatible with <lit>gcc</lit> and would be classified as the same style.
#>

#<
# @var MK_CXX_STYLE
# @brief Style of C++ compiler
# @export
# @system
# @value none No working C++ compiler is available
# @value gcc The C++ compiler is g++ or g++-compatible
# @value unknown The C++ compiler style is unknown
#
# Like <varref>MK_CC_STYLE</varref>, but for the C++ compiler.
#>

#<
# @var MK_CC_LD_STYLE
# @brief Linker style for C
# @export
# @system
# @value gnu GNU ld or compatible
# @value native Native OS linker
#
# Defines the style of the linker used for linking objects
# derived from C code.  This is an abstract classification which
# encompasses the behavior and supported parameters of the linker.
#>

#<
# @var MK_CXX_LD_STYLE
# @brief Linker style for C++
# @export
# @system
# @value gnu GNU ld or compatible
# @value native Native OS linker
#
# Like <varref>MK_CC_LD_STYLE</varref>, but for C++-derived objects.
#>

#<
# @var MK_RPATHFLAGS
# @brief Runtime library path flags
# @export
# @system
#
# The flags in this variable will be passed to any compiler operation
# involving linking an executable, library, or dynamically-loadable object
# for the purpose of defining the runtime search path that should be
# used when resolving dependent libraries.  The values of this variable
# are usually autodetected based on the system and compiler.
#>

#<
# @var MK_HEADERDEPS
# @brief Common header dependencies
# @inherit
#
# All headers listed in this variable will be implicitly added to the
# <lit>HEADERDEPS</lit> list of compiler functions such as
# <funcref>mk_program</funcref>.  It does not affect configure tests.
#
# This helps avoid repetition of consistently-used header dependencies
# across a larger project.  Care should be taken to avoid abusing it,
# however, as bloated dependency lists needlessly slow down
# <lit>make</lit>.
#>

#<
# @var MK_LIBDEPS
# @brief Common library dependencies
# @inherit
#
# All libraries listed in this variable will be implicitly added to the
# <lit>LIBDEPS</lit> list of compiler functions such as
# <funcref>mk_program</funcref>.  It does not affect configure tests.
#
# This can help avoid repetition when building multiple libraries, programs,
# etc. that share common library dependencies.  Take special care to
# avoid abusing it as linking extraneous libraries slows down the linker
# and incurs startup time and memory overhead at runtime.
#>

### section common

if [ "$MK_BROKEN_VAREXP" = "no" ]
then
#<
# @brief Convert a string to #define form 
# @usage str
#
# Converts a string to a form suitable for use as a variable name
# or #define.  This implements the same rules that autoconf uses:
# all letters are uppercased, all non-letter, non-number characters
# are converted to _, except for *, which is converted to P.
# Sets <var>result</var> to the result.
#>
mk_defname()
{
    __rem="$1"
    result=""

    while [ -n "$__rem" ]
    do
        # This little dance sets __char to the first character of
        # the string and __rem to the rest of it
        __rem2="${__rem#?}"
        __char="${__rem%"$__rem2"}"
        __rem="$__rem2"
        
        case "$__char" in
            # Convert lowercase letters to uppercase
            a) __char="A";; h) __char="H";; o) __char="O";; v) __char="V";;
            b) __char="B";; i) __char="I";; p) __char="P";; w) __char="W";; 
            c) __char="C";; j) __char="J";; q) __char="Q";; x) __char="X";; 
            d) __char="D";; k) __char="K";; r) __char="R";; y) __char="Y";; 
            e) __char="E";; l) __char="L";; s) __char="S";; z) __char="Z";; 
            f) __char="F";; m) __char="M";; t) __char="T";;
            g) __char="G";; n) __char="N";; u) __char="U";;
            # Leave uppercase letters and numbers alone
            A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|T|S|U|V|W|X|Y|Z|1|2|3|4|5|6|7|8|9) :;;
            # Convert * to P
            \*) __char="P";;
            # Convert everything else to _
            *) __char="_";;
        esac

        result="${result}${__char}"
    done
}
else
mk_defname()
{
    __rem="$1"
    result=""

    while [ -n "$__rem" ]
    do
        # This little dance sets __char to the first character of
        # the string and __rem to the rest of it
        __char="$__rem"
        while [ "${#__char}" -gt 1 ]
        do
            __char="${__char%?}"
        done
        __rem="${__rem#?}"
        
        case "$__char" in
            # Convert lowercase letters to uppercase
            a) __char="A";; h) __char="H";; o) __char="O";; v) __char="V";;
            b) __char="B";; i) __char="I";; p) __char="P";; w) __char="W";; 
            c) __char="C";; j) __char="J";; q) __char="Q";; x) __char="X";; 
            d) __char="D";; k) __char="K";; r) __char="R";; y) __char="Y";; 
            e) __char="E";; l) __char="L";; s) __char="S";; z) __char="Z";; 
            f) __char="F";; m) __char="M";; t) __char="T";;
            g) __char="G";; n) __char="N";; u) __char="U";;
            # Leave uppercase letters and numbers alone
            A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|T|S|U|V|W|X|Y|Z|1|2|3|4|5|6|7|8|9) :;;
            # Convert * to P
            \*) __char="P";;
            # Convert everything else to _
            *) __char="_";;
        esac

        result="${result}${__char}"
    done
}
fi

### section configure

#
# Utility functions
#

mk_resolve_header()
{
    case "$1" in
        /*)
            result="@${MK_STAGE_DIR}$1"
            ;;
        *)
            result="@${MK_STAGE_DIR}${MK_INCLUDEDIR}/$1"
            ;;
    esac
}

#
# Extension functions
#

_mk_compiler_run_hooks()
{
    mk_push_vars result hook hooks="$1"
    shift

    for hook in ${hooks}
    do
        ${hook} "$@"
    done

    mk_pop_vars
}

mk_add_link_target_posthook()
{
    _MK_LINK_TARGET_HOOKS="$_MK_LINK_TARGET_HOOKS $*"
}

mk_add_link_posthook()
{
    _MK_LINK_HOOKS="$_MK_LINK_HOOKS $*"
}

mk_run_link_target_posthooks()
{
    _mk_compiler_run_hooks "$_MK_LINK_TARGET_HOOKS" "$@"
}

mk_add_link_target_prehook()
{
    _MK_LINK_TARGET_PREHOOKS="$_MK_LINK_TARGET_PREHOOKS $*"
}

mk_run_link_target_prehooks()
{
    _mk_compiler_run_hooks "$_MK_LINK_TARGET_PREHOOKS" "$@"
}

mk_add_compile_target_prehook()
{
    _MK_COMPILE_TARGET_PREHOOKS="$_MK_COMPILE_TARGET_PREHOOKS $*"
}

mk_run_compile_target_prehooks()
{
    _mk_compiler_run_hooks "$_MK_COMPILE_TARGET_PREHOOKS" "$@"
}

#
# Helper functions for make() stage
#

# Generates name for object file
# $1 = source file
# $2 = suffix (avoids collisions for same source file)
# $3 = extension
_mk_objname()
{
    result="${1%.*}${2}.${MK_SYSTEM%/*}"
    if [ "${MK_SYSTEM#*/}" != "${MK_SYSTEM}" ]
    then
        result="$result.${MK_SYSTEM#*/}"
    fi
    result="$result$3"
}

# Generates name for pch file
# $1 = source file
# $2 = compiler
# $3 = extension
_mk_pchname()
{
    result="${1%.*}${2}.${MK_SYSTEM%/*}"
    if [ "${MK_SYSTEM#*/}" != "${MK_SYSTEM}" ]
    then
        result="$result.${MK_SYSTEM#*/}"
    fi
    result="$result.${1##*.}$3"
}

_mk_process_headerdeps()
{
    for _header in ${MK_HEADERDEPS} ${HEADERDEPS}
    do
        if _mk_contains "$_header" ${MK_INTERNAL_HEADERS}
        then
            mk_resolve_header "$_header"
            mk_quote "$result"
            DEPS="$DEPS $result"
        else
            mk_defname "HAVE_${_header}"
            mk_get "$result"
            
            if [ "$result" = "no" ]
            then
                mk_fail "$1 depends on missing header $_header"
            elif [ -z "$result" ]
            then
                mk_warn "$1 depends on unchecked header $_header"
            fi
        fi
    done
}

_mk_set_compiler_for_link()
{
    COMPILER=c
    $USED_CXX && COMPILER=c++
}

_mk_compile()
{
    # Preserve variables so prehooks can change them
    mk_push_vars \
        CPPFLAGS="$CPPFLAGS" \
        CFLAGS="$CFLAGS" \
        CXXFLAGS="$CXXFLAGS" \
        DEPS="$DEPS" \
        SOURCE="$SOURCE" \
        OBJECT="$OBJECT" \
        INCLUDEDIRS="$INCLUDEDIRS" \
        COMPILER="$COMPILER" \
        PCH="$PCH"

    mk_run_compile_target_prehooks

    # Resolve PCH
    case "$PCH" in
        "")
            : # Nothing to do
            ;;
        *.gch)
            # Already resolved (likely result of manual mk_pch invocation)
            mk_resolve_file "$PCH"
            PCH="$result"
            mk_append_list DEPS "@$result"
            ;;
        *)
            # Resolve to specific file for compiler and ISA
            mk_basename "$PCH"
            _mk_pchname "$result" "$OSUFFIX.$COMPILER" ".gch"
            mk_resolve_file "$result"
            PCH="$result"
            mk_append_list DEPS "@$result"
            ;;
    esac

    mk_resolve_target "${SOURCE}"
    mk_append_list DEPS "$result"
    
    mk_target \
        TARGET="$OBJECT" \
        DEPS="$DEPS" \
        mk_run_script compile %INCLUDEDIRS %CPPFLAGS %CFLAGS %CXXFLAGS %COMPILER %PIC %PCH '$@' "$result"

    mk_pop_vars
}

_mk_compile_detect()
{
    # Detect COMPILER and OBJECT if not set
    mk_push_vars OBJECT="$OBJECT" COMPILER="$COMPILER"
    
    if [ -z "$COMPILER" ]
    then
        case "${SOURCE##*.}" in
            c|s)
                COMPILER="c"
                ;;
            [cC][pP]|[cC][pP][pP]|[cC][xX][xX]|[cC][cC]|C)
                COMPILER="c++"
                ;;
            *)
                mk_fail "unsupported source file type: .${SOURCE##*.}"
                ;;
        esac
    fi
        
    # Update USED_{CC,CXX} so caller knows how to link or generate PCHs
    [ "$COMPILER" = "c++" ] && USED_CXX=true
    [ "$COMPILER" = "c" ] && USED_CC=true

    if [ -z "$OBJECT" ]
    then
        mk_basename "$SOURCE"
        _mk_objname "$result" "$OSUFFIX" ".o"
        OBJECT="$result"
    fi
  
    _mk_compile

    mk_pop_vars
}

#<
# @brief Build an object file
# @usage SOURCE=source options...
# @option SOURCE=source Indicates the source file to compile.
# @option OBJECT=object Sets explicit output object file.
# @option ... Common options are documented in the
# <modref>compiler</modref> module.
#
# Defines a target to build a C/C++ source file.  Sets
# <var>result</var> to the generated object file target.
#>
mk_compile()
{
    mk_push_vars \
        SOURCE HEADERDEPS DEPS INCLUDEDIRS CPPFLAGS CFLAGS CXXFLAGS PIC \
        OBJECT OSUFFIX COMPILER USED_CXX USED_CC
    mk_parse_params
    
    _mk_process_headerdeps "$SOURCE"
    _mk_compile_detect
    
    mk_pop_vars
}

_mk_pch()
{
    mk_push_vars \
        COMPILER="$COMPILER" \
        OBJECT="$OBJECT" \
        CFLAGS="$CFLAGS -x c-header" \
        CXXFLAGS="$CXXFLAGS -x c++-header" \
        PCH

    if [ -z "$COMPILER" ]
    then
        case "$SOURCE" in
            *.h)
                COMPILER="c"
                ;;
            *.[hH][pP][pP])
                COMPILER="c++"
                ;;
            *)
                mk_fail "unsupported source file type: .${SOURCE##*.}"
                ;;
        esac
    fi

    if [ -z "$OBJECT" ]
    then
        mk_basename "$SOURCE"
        _mk_pchname "$result" "$OSUFFIX.$COMPILER" ".gch"
        OBJECT="$result"
    fi
    
    _mk_compile
    
    mk_pop_vars
}

_mk_gen_pch()
{
    mk_push_vars COMPILER SOURCE

    case "$PCH" in
        *.gch|"")
            : # Already resolved or not used, nothing to do
            ;;
        *)
            # We were given a plain header, so we need
            # to generate rules for building the PCH now
            SOURCE="$PCH"
            
            if $USED_CC
            then
                COMPILER=c
                _mk_pch
            fi
            
            if $USED_CXX
            then
                COMPILER=c++
                _mk_pch
            fi
            ;;
    esac

    mk_pop_vars
}

#<
# @brief Build pre-compiled header
# @usage SOURCE=source options...
# @option SOURCE=source Indicates the header file to compile.
# @option ... Common options are documented in the
# <modref>compiler</modref> module.
#
# Defines a target to build a pre-compiled C/C++ header file.  Sets
# <var>result</var> to the generated target.  By default, the correct
# language to use is guessed based on the file extension.  Use
# the <param>COMPILER</param> option to choose explicitly (e.g. compile
# a <filename>.h</filename> file with the C++ compiler).
#
# It is generally preferable to avoid explicitly building pre-compiled
# headers and instead pass the header to compile directly to the
# <param>PCH</param> option to <funcref>mk_program</funcref> et al.
# This helps ensure that the header is compiled with the same set of
# compiler flags and for the correct language.
#>
mk_pch()
{
    mk_push_vars \
        SOURCE HEADERDEPS DEPS INCLUDEDIRS CPPFLAGS CFLAGS CXXFLAGS PIC \
        OBJECT OSUFFIX COMPILER USED_CXX USED_CC
    mk_parse_params
    
    _mk_process_headerdeps "$SOURCE"

    _mk_pch
    
    mk_pop_vars
}

_mk_verify_libdeps()
{
    for __dep in ${2}
    do
        _mk_contains "$__dep" ${MK_INTERNAL_LIBS} && continue
        mk_defname "HAVE_LIB_${__dep}"
        
        mk_get "$result"

        if [ "$result" = "no" ]
        then
            mk_fail "$1 depends on missing library $__dep ($MK_SYSTEM)"
        elif [ -z "$result" ]
        then
            mk_warn "$1 depends on unchecked library $__dep ($MK_SYSTEM)"
        fi
    done
}

_mk_process_symfile_gnu_ld()
{
    mk_resolve_file "$SYMFILE"
    __input="$result"
    mk_resolve_file "$SYMFILE.ver"
    __output="$result"

    {
        echo "{ global:"
        awk '{ print $0, ";"; }' < "$__input"
        echo "local: *; };"
    } > "$__output.new"

    if ! [ -f "$__output" ] || ! diff -q "$__output" "$__output.new" >/dev/null 2>&1
    then
        mv -f "$__output.new" "$__output"
    else
        rm -f "$__output.new"
    fi

    mk_add_configure_input "@$__input"
    mk_add_configure_output "@$__output"

    LDFLAGS="$LDFLAGS -Wl,-version-script,$__output"
    DEPS="$DEPS @$__output"
}

_mk_process_symfile_aix()
{
    mk_resolve_file "$SYMFILE"

    LDFLAGS="$LDFLAGS -Wl,-bexport:$result"
    DEPS="$DEPS @$result"
}

_mk_process_symfile()
{
    case "$MK_OS:$MK_CC_LD_STYLE" in
        *:gnu)
            _mk_process_symfile_gnu_ld "$@"
            ;;
        aix:native)
            _mk_process_symfile_aix
            ;;
        *)
            ;;
    esac   
}

_mk_library_form_name()
{
    # $1 = name
    # $2 = version
    # $3 = release
    # $4 = ext
    [ "$2" = "-" ] && set -- "$1" "" "$3" "$4"

    case "$MK_OS" in
        darwin)
            result="lib${1}${3:+-$3}${2:+.$2}${4}"
            ;;
        *)
            result="lib${1}${3:+-$3}${4}${2:+.$2}"
            ;;
    esac
}

_mk_library_process_version()
{
    if [ "$VERSION" != "no" ]
    then
        case "$VERSION" in
            *,*)
                _IFS="$IFS"
                IFS=","
                set -- ${VERSION}
                IFS="$_IFS"
                LINKS=""
                for ver
                do
                    case "$ver" in
                        '*'*)
                            ver="${ver#?}"
                            _mk_library_form_name "$LIB" "$ver" "" "$EXT"
                            SONAME="$result"
                            mk_quote "$result"
                            LINKS="$LINKS $result"
                            ;;
                        *)
                            _mk_library_form_name "$LIB" "$ver" "" "$EXT"
                            mk_quote "$result"
                            LINKS="$LINKS $result"
                            ;;
                    esac
                done
                return
                ;;
            *-*)
                RELEASE="${VERSION#*-}"
                VERSION="${VERSION%-*}"
                ;;
            *)
                RELEASE=""
                ;;
        esac

        case "$VERSION" in
            *:*)
                _rest="${VERSION}:"
                _cur="${_rest%%:*}"
                _rest="${_rest#*:}"
                _rev="${_rest%%:*}"
                _rest="${_rest#*:}"
                _age="${_rest%:}"
                case "$MK_OS" in
                    hpux)
                        MAJOR="$_cur"
                        MINOR="$_rev"
                        MICRO=""
                        ;;
                    freebsd)
                        MAJOR="$_cur"
                        MINOR=""
                        MICRO=""
                        ;;
                    darwin)
                        MAJOR="$(($_cur - $_age))"
                        MINOR=""
                        MICRO=""
                        ;;
                    *)
                        MAJOR="$(($_cur - $_age))"
                        MINOR="$(($_age))"
                        MICRO="$_rev"
                        ;;
                esac
                ;;
            *)
                _rest="${VERSION}."
                MAJOR="${_rest%%.*}"
                _rest="${_rest#*.}"
                MINOR="${_rest%%.*}"
                _rest="${_rest#*.}"
                MICRO="${_rest%.}"
                case "$MK_OS" in
                    freebsd|darwin)
                        MINOR=""
                        MICRO=""
                        ;;
                    hpux)
                        MICRO=""
                        ;;
                esac
                ;;
        esac
    else
        MAJOR=""
        MINOR=""
        MICRO=""
        RELEASE=""
    fi

    _mk_library_form_name "$LIB" "" "" "$EXT"
    SONAME="$result"
    mk_quote "$result"
    LINKS="$result"

    if [ -n "$MAJOR" ]
    then
        _mk_library_form_name "$LIB" "$MAJOR" "$RELEASE" "$EXT"
        SONAME="$result"
        mk_quote "$SONAME"
        LINKS="$result $LINKS"
    fi
    
    if [ -n "$MINOR" ]
    then
        _mk_library_form_name "$LIB" "$MAJOR.$MINOR${MICRO:+.$MICRO}" "$RELEASE" "$EXT"
        mk_quote "$result"
        LINKS="$result $LINKS"
    fi
}

_mk_dlo_form_name()
{
    # $1 = name
    # $2 = version
    # $3 = release
    # $4 = ext
    case "$MK_OS" in
        darwin)
            result="${1%.la}${3:+-$3}${2:+.$2}${4}"
            ;;
        *)
            result="${1%.la}${3:+-$3}${4}${2:+.$2}"
            ;;
    esac
}

_mk_dlo_process_version()
{
    if [ "$VERSION" != "no" ]
    then
        case "$VERSION" in
            *-*)
                RELEASE="${VERSION#*-}"
                VERSION="${VERSION%-*}"
                ;;
            *)
                RELEASE=""
                ;;
        esac

        case "$VERSION" in
            *:*)
                _rest="${VERSION}:"
                _cur="${_rest%%:*}"
                _rest="${_rest#*:}"
                _rev="${_rest%%:*}"
                _rest="${_rest#*:}"
                _age="${_rest%:}"
                case "$MK_OS" in
                    hpux)
                        MAJOR="$_cur"
                        MINOR="$_rev"
                        MICRO=""
                        ;;
                    freebsd)
                        MAJOR="$_cur"
                        MINOR=""
                        MICRO=""
                        ;;
                    darwin)
                        MAJOR="$(($_cur - $_age))"
                        MINOR=""
                        MICRO=""
                        ;;
                    *)
                        MAJOR="$(($_cur - $_age))"
                        MINOR="$(($_age))"
                        MICRO="$_rev"
                        ;;
                esac
                ;;
            *)
                _rest="${VERSION}."
                MAJOR="${_rest%%.*}"
                _rest="${_rest#*.}"
                MINOR="${_rest%%.*}"
                _rest="${_rest#*.}"
                MICRO="${_rest%.}"
                case "$MK_OS" in
                    freebsd|darwin)
                        MINOR=""
                        MICRO=""
                        ;;
                    hpux)
                        MICRO=""
                        ;;
                esac
                ;;
        esac
    else
        MAJOR=""
        MINOR=""
        MICRO=""
        RELEASE=""
    fi

    _mk_dlo_form_name "$DLO" "" "" "$EXT"
    SONAME="$result"
    LINKS="$result"

    if [ -n "$MAJOR" ]
    then
        _mk_dlo_form_name "$DLO" "$MAJOR" "$RELEASE" "$EXT"
        SONAME="$result"
        mk_quote "$SONAME"
        LINKS="$result $LINKS"
    fi
    
    if [ -n "$MINOR" ]
    then
        _mk_dlo_form_name "$DLO" "$MAJOR.$MINOR${MICRO:+.$MICRO}" "$RELEASE" "$EXT"
        mk_quote "$result"
        LINKS="$result $LINKS"
    fi
}

_mk_library()
{
    mk_push_vars PIC=yes
    unset _deps _objects

    mk_comment "library ${LIB} ($MK_SYSTEM) from ${MK_SUBDIR#/}"

    # Create object prefix based on library name
    _mk_slashless_name "$LIB"
    OSUFFIX=".$result"

    # Perform pathname expansion on SOURCES
    mk_expand_pathnames "${SOURCES}" "${MK_SOURCE_DIR}${MK_SUBDIR}"
    
    mk_unquote_list "$result"
    for SOURCE
    do
        _mk_compile_detect
        mk_quote "$result"
        _deps="$_deps $result"
        _objects="$_objects $result"
    done
    
    _mk_gen_pch

    _mk_add_groups
    _objects="$_objects $result"
    _deps="$_deps $result"
    
    for result in ${LIBDEPS} ${MK_LIBDEPS}
    do
        if _mk_contains "$result" ${MK_INTERNAL_LIBS}
        then
            mk_quote "$MK_LIBDIR/lib${result}.la"
            _deps="$_deps $result"
        fi
    done
    
    _mk_set_compiler_for_link

    mk_target \
        TARGET="$TARGET" \
        DEPS="${_deps}" \
        mk_run_script link \
        MODE=library \
        LIBDEPS="$LIBDEPS $MK_LIBDEPS" %LIBDIRS %LDFLAGS %SONAME %EXT %COMPILER \
        '$@' "*${OBJECTS} ${_objects}"

    mk_pop_vars
}

_mk_library_static()
{
    mk_push_vars PIC=no
    unset _deps _objects

    mk_comment "static library ${LIB} ($MK_SYSTEM) from ${MK_SUBDIR#/}"

    # Create object prefix based on library name
    _mk_slashless_name "$LIB"
    OSUFFIX=".$result.static"

    # Perform pathname expansion on SOURCES
    mk_expand_pathnames "${SOURCES}" "${MK_SOURCE_DIR}${MK_SUBDIR}"
    
    mk_unquote_list "$result"
    for SOURCE
    do
        _mk_compile_detect
        mk_quote "$result"
        _deps="$_deps $result"
        _objects="$_objects $result"
    done
    
    _mk_gen_pch

    _mk_add_groups
    _objects="$_objects $result"
    _deps="$_deps $result"
    
    for result in ${LIBDEPS} ${MK_LIBDEPS}
    do
        if _mk_contains "$result" ${MK_INTERNAL_LIBS}
        then
            mk_quote "$MK_LIBDIR/lib${result}.la"
            _deps="$_deps $result"
        fi
    done
    
    mk_target \
        TARGET="$TARGET" \
        DEPS="${_deps}" \
        mk_run_script link \
        MODE=ar \
        LIBDEPS="$LIBDEPS $MK_LIBDEPS" %LIBDIRS \
        '$@' "*${OBJECTS} ${_objects}"

    mk_pop_vars
}

_mk_library_need_static()
{
    __name="$1"
    [ "$MK_STATIC_LIBS" = "yes" ] && return 0
    mk_unquote_list "$MK_STATIC_LIBS"
    _mk_contains "$__name" "$@"
}

#<
# @brief Build a library
# @usage LIB=name options...
# @option LIB=name Sets the name of the library.
# Do not specify a leading <lit>lib</lit> or file extension.
# @option VERSION=verspec Sets the version
# information on the created library.  There are several
# possible formats for <param>verspec</param>:
# <deflist>
#     <defentry><term><param>cur</param><lit>:</lit><param>rev</param><lit>:</lit><param>age</param>[<lit>-</lit><param>release</param>]</term>
#     <item>
#        This defines the version using the libtool version information
#        convention, which is the preferred method.  <param>cur</param>
#        is the current version of the interface, <param>rev</param> is
#        the current revision of the implementation, and <param>age</param>
#        is how many interface versions into the past with which you remain
#        compatible.  If you specify <param>release</param>, it will be suffixed
#        to the name of the physical library prior to any extensions.
#     </item>
#     </defentry>
#     <defentry><term><param>major</param><lit>.</lit><param>minor</param><lit>.</lit><param>micro</param></term>
#     <item>
#        This defines the version in terms of the literal major, minor, and micro
#        numbers that appear in the library name.  Note that not all three numbers
#        are used on every platform; on these, the unused numbers are omitted.
#     </item>
#     </defentry>
#     <defentry><term><param>ver1</param><lit>,</lit><param>ver2</param><lit>,</lit><param>...</param></term>
#     <item>
#        This explicitly defines the versions numbers that will appear in the filenames
#        of the physical library and its symbolic links.  <param>ver1</param> is for the
#        binary itself, and all subsequent versions will be symlinks.  If you specify
#        <lit>-</lit> as a version, it will create a file or link with no version suffixes
#        (e.g. <lit>libfoo.so</lit>).
#     </item>
#     </defentry>
# </deflist>
# @option SYMFILE=file Specifies a file which contains a list
# of symbol names, one per line, which should be exported by
# the library.  If this is option is not used, it defaults
# to the behavior of the compiler and linker, which typically
# export all non-static symbols.  This option will be silently
# ignored on platforms where it is not supported.
# @option ... Other common options documented in the <modref>compiler</modref>
# module.
# 
# Defines a target to build a C/C++ shared library.
#
# A libtool-compatible .la file will also be generated.
# This is actually the canonical representation of a library
# in MakeKit and is the target which is placed in <var>result</var>.
#>
mk_library()
{
    mk_push_vars \
        INSTALLDIR="$MK_LIBDIR" LIB SOURCES SOURCE GROUPS CPPFLAGS CFLAGS CXXFLAGS LDFLAGS LIBDEPS \
        HEADERDEPS LIBDIRS INCLUDEDIRS PCH VERSION=0:0:0 DEPS OBJECTS \
        SYMFILE SONAME LINKS COMPILER USED_CXX=false USED_CC=false \
        EXT="${MK_LIB_EXT}" TARGET STATIC_NAME static_deps
    mk_parse_params
    mk_require_params mk_library LIB

    mk_run_link_target_prehooks mk_library

    _mk_verify_libdeps "lib$LIB${EXT}" "$LIBDEPS $MK_LIBDEPS"
    _mk_process_headerdeps "lib$LIB${EXT}"

    if [ -n "$SYMFILE" ]
    then
        _mk_process_symfile
    fi

    _mk_library_process_version

    mk_unquote_list "$LINKS"
    TARGET="${INSTALLDIR:+$INSTALLDIR/}$1"
    
    _mk_library "$@"
    
    if _mk_library_need_static "$LIB"
    then
        TARGET="${INSTALLDIR:+$INSTALLDIR/}lib$LIB.a"
        _mk_library_static "$@"
        mk_quote "$result"
        static_deps="$result"
        STATIC_NAME="lib$LIB.a"
    fi

    mk_unquote_list "$LINKS"
    _lib="$1"
    _links=""
    shift
    
    mk_resolve_target "$INSTALLDIR/$_lib"
    mk_run_link_target_posthooks "$result"

    for _link
    do
        mk_symlink \
            TARGET="$_lib" \
            LINK="${INSTALLDIR}/$_link"
        mk_quote "$result"
        _links="$_links $result"
    done
    
    mk_quote "$INSTALLDIR/$_lib"

    mk_target \
        TARGET="${INSTALLDIR}/lib${LIB}.la" \
        DEPS="$_links $result $static_deps" \
        mk_run_script link MODE=la \
        LIBDEPS="$LIBDEPS $MK_LIBDEPS" %LIBDIRS %COMPILER %LINKS %SONAME %STATIC_NAME %EXT \
        '$@'

    MK_INTERNAL_LIBS="$MK_INTERNAL_LIBS $LIB"
    
    mk_pop_vars
}

#<
# @brief Stage a pre-built library
# @usage LIB=name options...
# @option LIB=name Sets the name of the library.
# Do not specify a leading <lit>lib</lit> or file extension.
# @option SHARED=shared Specifies the shared library binary.
# @option STATIC=static Specifies the static library file.
# @option LA=la Specifies the libtool archive file.  If not
# specified, one will be generated.
# @option VERSION=verspec Sets the version as in
# <funcref>mk_library</funcref>.
# @option ... Other common options documented in the <modref>compiler</modref>
# module.
# 
# Defines a target to install a pre-built a C/C++ library.
# This may be useful if you do not have the source for
# a library you wish to use and bundle with your project.
#
# At least one of <param>shared</param> and <param>static</param>
# must be specified.
#
# Sets <var>result</var> to the staged <lit>.la</lit> file in
# canonical target notation.
#>
mk_prebuilt_library()
{
    mk_push_vars \
        INSTALLDIR="$MK_LIBDIR" VERSION=0:0:0 LIB SHARED STATIC LA DEPS \
        LIBDEPS SONAME LINKS EXT="${MK_LIB_EXT}" TARGET STATIC_NAME
        
    mk_parse_params
    mk_require_params mk_prebuilt_library LIB
    [ -z "$SHARED" -a -z "$STATIC" ] && 
        mk_fail "mk_prebuilt_library: at least one of SHARED and STATIC must be specified"

    _mk_verify_libdeps "lib$LIB${EXT}" "$LIBDEPS $MK_LIBDEPS"
    _mk_library_process_version

    if [ -n "$SHARED" ]
    then
        _mk_library_process_version
        mk_unquote_list "$LINKS"
        TARGET="${INSTALLDIR:+$INSTALLDIR/}$1"

        mk_stage \
            SOURCE="$SHARED" \
            DEST="$TARGET" \
            MODE=0644
        
        TARGET="$result"
        mk_run_link_target_posthooks "$TARGET"
        mk_quote "$TARGET"
        DEPS="$DEPS $result"
        TARGET="$1"
        shift

        for _link
        do
            mk_symlink \
                TARGET="$TARGET" \
                LINK="${INSTALLDIR:+$INSTALLDIR}/$_link"
            mk_quote "$result"
            DEPS="$DEPS $result"
        done
    fi

    if [ -n "$STATIC" ]
    then
        TARGET="${INSTALLDIR:+$INSTALLDIR/}lib$LIB.a"
        STATIC_NAME="lib$LIB.a"

        mk_stage \
            SOURCE="$STATIC" \
            DEST="$TARGET" \
            MODE=0644

        mk_quote "$result"
        DEPS="$DEPS $result"
    fi

    for result in ${LIBDEPS} ${MK_LIBDEPS}
    do
        if _mk_contains "$result" ${MK_INTERNAL_LIBS}
        then
            mk_quote "$MK_LIBDIR/lib${result}.la"
            DEPS="$DEPS $result"
        fi
    done

    TARGET="${INSTALLDIR:+$INSTALLDIR/}lib$LIB.la"

    if [ -n "$LA" ]
    then
        mk_stage \
            SOURCE="$LA" \
            DEST="$TARGET" \
            DEPS="$DEPS" \
            MODE=0644
    else
        mk_target \
            TARGET="$TARGET" \
            DEPS="$DEPS" \
            mk_run_script link MODE=la \
            LIBDEPS="$LIBDEPS $MK_LIBDEPS" %LINKS %SONAME %STATIC_NAME %EXT '$@'
    fi

    mk_declare_internal_library "$LIB"

    mk_pop_vars
}

_mk_dlo()
{
    unset _deps _objects
    
    mk_comment "dlo ${DLO} ($MK_SYSTEM) from ${MK_SUBDIR#/}"
    
    # Create object prefix based on dlo name
    _mk_slashless_name "$DLO"
    OSUFFIX=".$result"

    # Perform pathname expansion on SOURCES
    mk_expand_pathnames "${SOURCES}"
    mk_unquote_list "$result"
    for SOURCE
    do
        _mk_compile_detect
        
        mk_quote "$result"
        _deps="$_deps $result"
        _objects="$_objects $result"
    done
    
    _mk_gen_pch

    _mk_add_groups
    _objects="$_objects $result"
    _deps="$_deps $result"
    
    for _lib in ${LIBDEPS} ${MK_LIBDEPS}
    do
        if _mk_contains "$_lib" ${MK_INTERNAL_LIBS}
        then
            mk_quote "${MK_LIBDIR}/lib${_lib}.la"
            _deps="$_deps $result"
        fi
    done
    
    _mk_set_compiler_for_link

    mk_target \
        TARGET="$TARGET" \
        DEPS="$_deps" \
        mk_run_script link \
        MODE=dlo \
        LIBDEPS="$LIBDEPS $MK_LIBDEPS" %LIBDIRS %LDFLAGS %EXT %COMPILER \
        '$@' "*${OBJECTS} ${_objects}"
}

#<
# @brief Build a dynamically loadable object
# @usage DLO=name options...
# @option ... Accepts the same options as <funcref>mk_library</funcref>.
# 
# Defines a target to build a C/C++ dynamically loadable object --
# that is, an object suitable for loading with dlopen() or similar
# functions at runtime.  On some systems, Darwin in particular, this
# is not the same thing as a shared library.  See
# <topicref ref="compiler"/> for a list of common options.
#
# A libtool-compatible .la file will also be generated and is
# the target which is placed in <var>result</var>.
#>
mk_dlo()
{
    mk_push_vars \
        DLO SOURCES SOURCE GROUPS CPPFLAGS CFLAGS CXXFLAGS \
        LDFLAGS LIBDEPS HEADERDEPS LIBDIRS INCLUDEDIRS VERSION="no" \
        OBJECTS PCH DEPS INSTALLDIR EXT="${MK_DLO_EXT}" SYMFILE SONAME COMPILER \
        USED_CXX=false USED_CC=false OSUFFIX PIC=yes
    mk_parse_params
    mk_require_params mk_dlo DLO

    mk_run_link_target_prehooks mk_dlo

    [ -z "$INSTALLDIR" ] && INSTALLDIR="${MK_LIBDIR}"

    _mk_verify_libdeps "$DLO${EXT}" "$LIBDEPS $MK_LIBDEPS"
    _mk_process_headerdeps "$DLO${EXT}"

    if [ -n "$SYMFILE" ]
    then
        _mk_process_symfile
    fi

    _mk_dlo_process_version

    mk_unquote_list "$LINKS"
    TARGET="${INSTALLDIR:+$INSTALLDIR/}$1"
    
    _mk_dlo "$@"

    _dlo_target="$result"

    mk_unquote_list "$LINKS"
    _dlo="$1"
    _links=""
    shift
    
    mk_resolve_target "$INSTALLDIR/$_dlo"
    mk_run_link_target_posthooks "$result"

    for _link
    do
        mk_symlink \
            TARGET="$_dlo" \
            LINK="${INSTALLDIR}/$_link"
        mk_quote "$result"
        _links="$_links $result"
    done

    mk_quote "$_dlo_target"

    mk_target \
        TARGET="${INSTALLDIR}/${DLO}.la" \
        DEPS="$_links $result" \
        mk_run_script link MODE=la \
        LIBDEPS="$LIBDEPS $MK_LIBDEPS" %LIBDIRS %COMPILER %EXT \
        '$@'

    mk_pop_vars
}

_mk_add_group()
{
    mk_push_vars \
        COMPILER CPPFLAGS CFLAGS CXXFLAGS DEPS SOURCE INCLUDEDIRS PCH \
        MK_SUBDIR="$MK_SUBDIR" OSUFFIX="$OSUFFIX.${1##*/}" \
        sources cppflags cflags cxxflags ldflags subdir libdirs \
        libdeps pch deps groupdeps
    
    mk_resolve_file "$1.${MK_SYSTEM%/*}.${MK_SYSTEM#*/}.og"
    mk_source_or_fail "$result"

    MK_SUBDIR="$subdir"
    CPPFLAGS="$cppflags"
    CFLAGS="$cflags"
    CXXFLAGS="$cxxflags"
    DEPS="$deps"
    LDFLAGS="$LDFLAGS $ldflags"
    LIBDIRS="$LIBDIRS $libdirs"
    LIBDEPS="$LIBDEPS $libdeps"
    INCLUDEDIRS="$includedirs"
    PCH="$pch"
    groups="$groups $groupdeps"
    groups="${groups# }"

    mk_unquote_list "$sources"
    for SOURCE
    do
        _mk_compile_detect
        mk_quote "$result"
        objects="$objects $result"
    done

    _mk_gen_pch

    mk_pop_vars
}

_mk_add_groups()
{
    mk_push_vars groups="$GROUPS" objects=""

    while [ -n "$groups" ]
    do
        mk_unquote_list "$groups"
        groups=""
        for __group
        do
            _mk_add_group "$__group"
        done
    done

    result="$objects"
    mk_pop_vars
}

_mk_group()
{
    mk_resolve_file "$TARGET"
    mk_mkdirname "$result"
    {
        echo "# MakeKit group"
        mk_quote "$MK_SUBDIR"
        echo subdir="$result"
        mk_quote "$SOURCES"
        echo sources="$result"
        mk_quote "$CPPFLAGS"
        echo cppflags="$result"
        mk_quote "$CFLAGS"
        echo cflags="$result"
        mk_quote "$CXXFLAGS"
        echo cxxflags="$result"
        mk_quote "$LDFLAGS"
        echo ldflags="$result"
        mk_quote "$CFLAGS"
        echo cflags="$result"
        mk_quote "$LIBDEPS $MK_LIBDEPS"
        echo libdeps="$result"
        mk_quote "$LIBDIRS"
        echo libdirs="$result"
        mk_quote "$INCLUDEDIRS"
        echo includedirs="$result"
        mk_quote "$PCH"
        echo pch="$result"
        mk_quote "$DEPS"
        echo deps="$result"
        mk_quote "$GROUPDEPS"
        echo groupdeps="$result"
    } > "$result" || mk_fail "could not write $TARGET"
}

#<
# @brief Build a source group
# @usage GROUP=name options...
#
# Defines a target to build a C/C++ "group", which combines source
# files and associated build flags into a logical unit which can be
# added to <funcref>mk_program</funcref> and friends.  This feature is
# similar to "convenience libraries" with GNU libtool.
#
# See the <modref>compiler</modref> module for common options or
# <topicref ref="c-projects-groups"/> in the MakeKit guide for usage
# examples.
#>
mk_group()
{
    mk_push_vars \
        GROUP SOURCES SOURCE CPPFLAGS CFLAGS CXXFLAGS LDFLAGS LIBDEPS \
        HEADERDEPS GROUPDEPS LIBDIRS INCLUDEDIRS OBJECTS DEPS PCH \
        includedir
    mk_parse_params
    mk_require_params mk_group GROUP

    _mk_verify_libdeps "$GROUP" "$LIBDEPS $MK_LIBDEPS"
    _mk_process_headerdeps "$GROUP"

    # Perform pathname expansion on SOURCES
    mk_expand_pathnames "${SOURCES}" "${MK_SOURCE_DIR}${MK_SUBDIR}"

    # Resolve them
    mk_resolve_targets "$SOURCES"
    SOURCES="$result"

    # Resolve group deps
    mk_resolve_targets "$GROUPDEPS"
    GROUPDEPS="$result"

    # Resolve deps
    mk_resolve_targets "$DEPS"
    DEPS="$result"

    # Resolve PCH
    if [ -n "$PCH" ]
    then
        mk_resolve_target "$PCH"
        PCH="$result"
    fi

    TARGET="$GROUP.${MK_SYSTEM%/*}.${MK_SYSTEM#*/}.og"
    _mk_group "$@"

    mk_pop_vars
}

_mk_program()
{
    unset _deps _objects
    
    mk_comment "program ${PROGRAM} ($MK_SYSTEM) from ${MK_SUBDIR#/}"

    # Create object prefix based on program name
    _mk_slashless_name "$PROGRAM"
    OSUFFIX=".$result"
    
    # Perform pathname expansion on SOURCES
    mk_expand_pathnames "${SOURCES}" "${MK_SOURCE_DIR}${MK_SUBDIR}"
    
    mk_unquote_list "$result"
    for SOURCE
    do
        _mk_compile_detect
        mk_quote "$result"
        _deps="$_deps $result"
        _objects="$_objects $result"
    done

    _mk_gen_pch
    
    _mk_add_groups
    _objects="$_objects $result"
    _deps="$_deps $result"

    for _lib in ${LIBDEPS} ${MK_LIBDEPS}
    do
        if _mk_contains "$_lib" ${MK_INTERNAL_LIBS}
        then
            mk_quote "$MK_LIBDIR/lib${_lib}.la"
            _deps="$_deps $result"
        fi
    done

    _mk_set_compiler_for_link
    
    mk_target \
        TARGET="$TARGET" \
        DEPS="$_deps" \
        mk_run_script link MODE=program LIBDEPS="$LIBDEPS $MK_LIBDEPS" \
        %LDFLAGS %COMPILER '$@' "*${OBJECTS} ${_objects}"
}

#<
# @brief Build a program
# @usage PROGRAM=name options...
# @option PROGRAM=name Sets the name of the program.  Do not include
# any file extension.
#
# Defines a target to build a C/C++ executable program.
# See <topicref ref="compiler"/> for a list of common
# options.
#>
mk_program()
{
    mk_push_vars \
        PROGRAM SOURCES SOURCE OBJECTS GROUPS CPPFLAGS CFLAGS CXXFLAGS \
        LDFLAGS LIBDEPS HEADERDEPS DEPS LIBDIRS INCLUDEDIRS INSTALLDIR \
        COMPILER PCH USED_CXX=false USED_CC=false PIC=no OSUFFIX
        EXT=""
    mk_parse_params
    mk_require_params mk_program PROGRAM

    mk_run_link_target_prehooks mk_program

    if [ -z "$INSTALLDIR" ]
    then
        # Default to installing programs in bin dir
        if [ "${MK_SYSTEM%/*}" = "build" ]
        then
            INSTALLDIR="@${MK_RUN_BINDIR}"
        else
            INSTALLDIR="$MK_BINDIR"
        fi
    fi

    _mk_verify_libdeps "$PROGRAM" "$LIBDEPS $MK_LIBDEPS"
    _mk_process_headerdeps "$PROGRAM"

    TARGET="$INSTALLDIR/$PROGRAM$EXT"

    _mk_program "$@"
    
    if [ "${MK_SYSTEM%/*}" = "build" ]
    then
        MK_INTERNAL_PROGRAMS="$MK_INTERNAL_PROGRAMS $PROGRAM"
    fi

    mk_run_link_target_posthooks "$result"

    mk_pop_vars
}

#<
# @brief Install headers
# @usage headers...
# @usage MASTER=master headers...
# @option INSTALLDIR=dir Specifies the location to install
# the headers.  By default, this is <var>MK_INCLUDEDIR</var>.
# @option ... See <topicref ref="compiler"/> for common options.
#
# Installs each header in <param>headers</param> into the system
# header directory.  If <param>master</param> is specified, it is
# also installed and marked as depending on all the other headers
# in the list.  This is useful when using HEADERDEPS elsewhere in
# the project, as depending on <param>master</param> will depend
# on all of the listed headers.
#>
mk_headers()
{
    mk_push_vars HEADERS MASTER INSTALLDIR HEADERDEPS DEPS
    INSTALLDIR="${MK_INCLUDEDIR}"
    mk_parse_params
    
    _mk_process_headerdeps "header" "$HEADERDEPS $MK_HEADERDEPS"

    unset _all_headers
    
    mk_comment "headers from ${MK_SUBDIR#/}"
    
    for _header in ${HEADERDEPS} ${MK_HEADERDEPS}
    do
        if _mk_contains "$_header" ${MK_INTERNAL_HEADERS}
        then
            DEPS="$DEPS '${MK_INCLUDEDIR}/${_header}'"
        fi
    done
    
    mk_expand_pathnames "${HEADERS} $*"
    mk_unquote_list "$result"

    mk_stage \
        DESTDIR="$INSTALLDIR" \
        DEPS="$DEPS" \
        "$@"
    DEPS="$DEPS $result"

    for _header in "$@"
    do
        _rel="${INSTALLDIR#$MK_INCLUDEDIR/}"
        
        if [ "$_rel" != "$INSTALLDIR" ]
        then
            _rel="$_rel/$_header"
        else
            _rel="$_header"
        fi
        
        MK_INTERNAL_HEADERS="$MK_INTERNAL_HEADERS $_rel"
    done

    mk_expand_pathnames "${MASTER}"   
    mk_unquote_list "$result"

    mk_stage \
        DESTDIR="$INSTALLDIR" \
        DEPS="$DEPS" \
        "$@"

    for _header in "$@"
    do
        _rel="${INSTALLDIR#$MK_INCLUDEDIR/}"
        
        if [ "$_rel" != "$INSTALLDIR" ]
        then
            _rel="$_rel/$_header"
        else
            _rel="$_header"
        fi
        
        MK_INTERNAL_HEADERS="$MK_INTERNAL_HEADERS $_rel"
    done
    
    mk_pop_vars
}

mk_declare_internal_header()
{
    MK_INTERNAL_HEADERS="$MK_INTERNAL_HEADERS $1"
}

mk_have_internal_header()
{
    _mk_contains "$1" $MK_INTERNAL_HEADERS
}

mk_declare_internal_library()
{
    MK_INTERNAL_LIBS="$MK_INTERNAL_LIBS $1"
}

mk_have_internal_library()
{
    _mk_contains "$1" $MK_INTERNAL_LIBS
}


#
# Helper functions for configure() stage
# 

#<
# @brief Define a macro in config header
# @usage def value
#
# Defines the C preprocessor macro <param>def</param> to
# <param>value</param> in the current config
# header created by <funcref>mk_config_header</funcref>.
#>
mk_define()
{
    mk_push_vars cond
    mk_parse_params
    
    if [ -n "$MK_CONFIG_HEADER" ]
    then
        _name="$1"
        
        mk_defname "$MK_SYSTEM"
        cond="_MK_$result"
        
        if [ "$#" -eq '2' ]
        then
            result="$2"
        else
            mk_get "$_name"
        fi
        
        mk_write_config_header "#if defined($cond) && !defined($_name)"
        mk_write_config_header "#define $_name $result"
        mk_write_config_header "#endif"
    fi
    
    mk_pop_vars
}

mk_define_always()
{
    if [ -n "$MK_CONFIG_HEADER" ]
    then
        _name="$1"
        
        if [ "$#" -eq '2' ]
        then
            result="$2"
        else
            mk_get "$_name"
        fi
        mk_write_config_header "#define $_name $result"
    fi
}

mk_write_config_header()
{
    echo "$*" >&5
}

_mk_close_config_header()
{
    if [ -n "${MK_LAST_CONFIG_HEADER}" ]
    then
        cat >&5 <<EOF

#endif
EOF
        exec 5>&-
        
        if [ -f "${MK_LAST_CONFIG_HEADER}" ] && diff "${MK_LAST_CONFIG_HEADER}" "${MK_LAST_CONFIG_HEADER}.new" >/dev/null 2>&1
        then
            # The config header has not changed, so don't touch the timestamp on the file */
            rm -f "${MK_LAST_CONFIG_HEADER}.new"
        else
            mv "${MK_LAST_CONFIG_HEADER}.new" "${MK_LAST_CONFIG_HEADER}"
        fi
        
        MK_LAST_CONFIG_HEADER=""
    fi
}

#<
# @brief Create config header
# @usage header
#
# Creates a config header named <param>header</param>.
# Any subsequent definitions made by <funcref>mk_define</funcref>
# or various configuration tests will be placed in the header
# most recently created with this function.
#>
mk_config_header()
{
    mk_push_vars HEADER
    mk_parse_params
    
    _mk_close_config_header
    
    [ -z "$HEADER" ] && HEADER="$1"
    
    MK_CONFIG_HEADER="${MK_OBJECT_DIR}${MK_SUBDIR}/${HEADER}"
    MK_LAST_CONFIG_HEADER="$MK_CONFIG_HEADER"
    
    mkdir -p "${MK_CONFIG_HEADER%/*}"
    
    mk_msg "config header ${MK_CONFIG_HEADER#${MK_OBJECT_DIR}/}"
    
    exec 5>"${MK_CONFIG_HEADER}.new"
    
    cat >&5 <<EOF
/* Generated by MakeKit */

#ifndef __MK_CONFIG_H__
#define __MK_CONFIG_H__

EOF
    
    mk_add_configure_output "@$MK_CONFIG_HEADER"
    
    mk_pop_vars
}

_mk_build_test()
{
    __test="${2%.*}"
    
    case "${1}" in
        compile|compile-keep)
            (
                eval "exec ${MK_LOG_FD}>&-"
                MK_LOG_FD=""
                mk_run_script compile \
                    COMPILER="$MK_CHECK_LANG" \
                    CONFTEST=yes \
                    CPPFLAGS="$CPPFLAGS" \
                    CFLAGS="$CFLAGS" \
                    "${__test}.o" "${__test}.c"
            ) >&${MK_LOG_FD} 2>&1            
            _ret="$?"
            if [ "${1}" != "compile-keep" ]
            then
                rm -f "${__test}.o"
            fi
            ;;
        link-program|run-program)
            (
                eval "exec ${MK_LOG_FD}>&-"
                MK_LOG_FD=""
                mk_run_script compile \
                    COMPILER="$MK_CHECK_LANG" \
                    CONFTEST=yes \
                    CPPFLAGS="$CPPFLAGS" \
                    CFLAGS="$CFLAGS" \
                    "${__test}.o" "${__test}.c"
                mk_run_script link \
                    COMPILER="$MK_CHECK_LANG" \
                    CONFTEST=yes \
                    MODE=program \
                    LIBDEPS="$LIBDEPS" \
                    LDFLAGS="$LDFLAGS" \
                    "${__test}" "${__test}.o"
            ) >&${MK_LOG_FD} 2>&1
            _ret="$?"
            if [ "$_ret" -eq 0 -a "$1" = "run-program" ]
            then
                ./"${__test}"
                _ret="$?"
            fi
            rm -f "${__test}"
            rm -f "${__test}.o"
            ;;
        *)
            mk_fail "Unsupported build type: ${1}"
            ;;
    esac

    if [ "$_ret" -ne 0 ]
    then
        {
            echo ""
            echo "Failed code:"
            echo ""
            cat "${__test}.c" | awk 'BEGIN { no = 1; } { printf("%3d  %s\n", no, $0); no++; }'
            echo ""
        } >&${MK_LOG_FD}
    fi

    rm -f "${__test}.c"

    return "$_ret"
}

_mk_c_check_prologue()
{
    if [ -n "$MK_CONFIG_HEADER" ]
    then
        cat "${MK_CONFIG_HEADER}.new"
        printf "#endif\n\n"
    fi
}

#<
# @brief Try to compile a code snippet
# @usage CODE=code
# @option HEADERDEPS=hdeps An optional list of
# headers which should be included if they are
# available.
#
# Wraps <param>code</param> in a <lit>main()</lit>
# function and attempts to compile it.  Returns 0
# (logical true) if it succeeds and 1 (logical false)
# otherwise.
#>
mk_try_compile()
{
    mk_push_vars CODE HEADERDEPS CPPFLAGS CFLAGS
    mk_parse_params
    
    {
        _mk_c_check_prologue
        for _header in ${HEADERDEPS}
        do
            mk_might_have_header "$_header" && echo "#include <${_header}>"
        done
        
        cat <<EOF
int main(int argc, char** argv)
{
${CODE}
}
EOF
    } > .check.c

    _mk_build_test compile ".check.c"
    _ret="$?"
    mk_safe_rm .check.c

    mk_pop_vars

    return "$_ret"
}

#<
# @brief Try to compile and link a code snippet
# @usage CODE=code
# @option HEADERDEPS=hdeps An optional list of
# headers which should be included if they are
# available.
# @option LIBDEPS=ldeps An optional list of
# libraries which should be linked.
#
# Wraps <param>code</param> in a <lit>main()</lit>
# function and attempts to compile it.  Returns 0
# (logical true) if it succeeds and 1 (logical false)
# otherwise.
#>
mk_try_link()
{
    mk_push_vars CODE HEADERDEPS CPPFLAGS CFLAGS LDFLAGS
    mk_parse_params
    
    {
        _mk_c_check_prologue
        for _header in ${HEADERDEPS}
        do
            mk_might_have_header "$_header" && echo "#include <${_header}>"
        done
        
        cat <<EOF
int main(int argc, char** argv)
{
${CODE}
}
EOF
    } > .check.c

    _mk_build_test link ".check.c"
    _ret="$?"
    mk_safe_rm .check.c

    mk_pop_vars

    return "$_ret"
}

#<
# @brief Check for a header
# @usage HEADER=header
# @option HEADERDEPS=headers Specifies additional headers
# which might be needed in order for <param>header</param>
# to be compilable.  If a header has been determined to be
# unavailable by a previous <funcref>mk_check_headers</funcref>,
# it will be silently omitted from this list as a convenience.
#
# Checks for the availability of a system header and sets
# <var>result</var> to the result.  If the header was found
# on the system, the result will be "external".  If the header
# is provided by <funcref>mk_headers</funcref> within the current
# project, the result will be "internal".  Otherwise, the result
# will be "no".
#>
mk_check_header()
{
    mk_push_vars HEADER HEADERDEPS CPPFLAGS CFLAGS
    mk_parse_params

    [ -z "$HEADER" ] && HEADER="$1"

    CFLAGS="$CFLAGS -Wall -Werror"

    if _mk_contains "$HEADER" ${MK_INTERNAL_HEADERS}
    then
        result="internal"
    else
        {
            _mk_c_check_prologue
            for _header in ${HEADERDEPS}
            do
                mk_might_have_header "$_header" && echo "#include <${_header}>"
            done

            echo "#include <${HEADER}>"
            echo ""
            
            cat <<EOF
int main(int argc, char** argv)
{
    return 0;
}
EOF
        } > .check.c
        mk_log "running compile test for header: $HEADER"
        if _mk_build_test compile ".check.c"
        then
            result="external"
        else
            result="no"
        fi
    fi

    mk_pop_vars
    [ "$result" != "no" ]
}

#<
# @brief Check for headers
# @usage headers...
#
# For each header in <param>headers</param>, <funcref>mk_check_header</funcref>
# is invoked to check for its availability.  <var>HAVE_<varname>header</varname></var>
# is set to the result, and if the header was available, <def>HAVE_<varname>header</varname></def>
# is defined in the current config header.  A message is printed indicating the result
# of each test.
#>
mk_check_headers()
{
    mk_push_vars HEADERDEPS FAIL CPPFLAGS CFLAGS DEFNAME HEADER
    mk_parse_params
    
    for HEADER
    do
        mk_defname "$HEADER"
        DEFNAME="$result"

        mk_msg_checking "header $HEADER"

        if ! mk_check_cache "HAVE_$DEFNAME"
        then
            mk_check_header \
                HEADER="$HEADER" \
                HEADERDEPS="$HEADERDEPS" \
                CPPFLAGS="$CPPFLAGS" \
                CFLAGS="$CFLAGS"

            mk_cache "HAVE_$DEFNAME" "$result"
        fi

        mk_msg_result "$result"

        if [ "$result" != no ]
        then
            mk_define "HAVE_$DEFNAME" "1"
        elif [ "$FAIL" = yes ]
        then
            mk_fail "missing header: $HEADER"
        fi
        
    done

    mk_pop_vars
}

mk_have_header()
{
    mk_defname "HAVE_$1"
    mk_get "$result"
    [ "$result" = "external" -o "$result" = "internal" ]
}

mk_might_have_header()
{
    mk_defname "HAVE_$1"
    mk_get "$result"
    [ "$result" != "no" ]
}

#<
# @brief Check for a function
# @usage FUNCTION=func
#
# @option HEADERDEPS=headers Specifies any headers
# which might be needed in order for a prototype of
# the function to be available.  Unlike autoconf, MakeKit
# checks that both the function prototype and symbol are
# available, so specifying this option correctly is vital.
# @option LIBDEPS=deps Specifies any libraries which
# might be needed for the function to be available.
#
# Checks for the availability of a function, setting
# <var>result</var> to the result ("yes" or "no").
# If <param>func</param> is specified as a full function prototype,
# the test will only succeed if the function which was found
# had the same prototype.  If <param>func</param> is specified as
# a simple name, the test will succeed as long as the function
# has an available prototype and symbol.
#>
mk_check_function()
{
    mk_push_vars LIBDEPS FUNCTION HEADERDEPS CPPFLAGS LDFLAGS CFLAGS FAIL PROTOTYPE
    mk_parse_params

    CFLAGS="$CFLAGS -Wall -Werror"

    [ -z "$FUNCTION" ] && FUNCTION="$1"
    [ -z "$PROTOTYPE" ] && PROTOTYPE="$FUNCTION"
    
    case "$PROTOTYPE" in
        *'('*)
            _parts="`echo "$PROTOTYPE" | sed 's/^\(.*[^a-zA-Z_]\)\([a-zA-Z_][a-zA-Z0-9_]*\) *(\([^)]*\)).*$/\1|\2|\3/g'`"
            _ret="${_parts%%|*}"
            _parts="${_parts#*|}"
            FUNCTION="${_parts%%|*}"
            _args="${_parts#*|}"
            ;;
        *)
            FUNCTION="$PROTOTYPE"
            _args=""
            ;;
    esac
    
    {
        _mk_c_check_prologue
        for _header in ${HEADERDEPS}
        do
            mk_might_have_header "$_header" && echo "#include <${_header}>"
        done
        
        echo ""
        
        if [ -n "$_args" ]
        then
            cat <<EOF
int main(int argc, char** argv)
{
    $_ret (*__func)($_args) = &$FUNCTION;
    return (char*) __func < (char*) &main ? 0 : 1;
}
EOF
            else
                cat <<EOF
int main(int argc, char** argv)
{
    void* __func = &$FUNCTION;
    return (char*) __func < (char*) &main ? 0 : 1;
}
EOF
            fi
    } >.check.c
    
    mk_log "running link test for $PROTOTYPE"
    if _mk_build_test 'link-program' ".check.c"
    then
        result="yes"
    else
        result="no"
    fi

    mk_pop_vars
    [ "$result" != "no" ]
}

#<
# @brief Check for functions
# @usage funcs...
#
# For each function in <param>funcs</param>, <funcref>mk_check_function</funcref>
# is invoked to check for its availability.  <var>HAVE_<varname>func</varname></var>
# is set to the result, and if the function was available, <def>HAVE_<varname>func</varname></def>
# is defined in the current config header.  <def>HAVE_DECL_<varname>func</varname></def>
# is defined to 1 if the function was available and 0 otherwise.  A message is printed indicating
# the result of each test.
#>
mk_check_functions()
{
    mk_push_vars \
        LIBDEPS HEADERDEPS CPPFLAGS LDFLAGS CFLAGS FAIL \
        PROTOTYPE DEFNAME
    mk_parse_params
    
    for PROTOTYPE
    do
        mk_defname "$PROTOTYPE"
        DEFNAME="$result"

        mk_msg_checking "function $PROTOTYPE"

        if ! mk_check_cache "HAVE_$DEFNAME"
        then
            mk_check_function \
                PROTOTYPE="$PROTOTYPE" \
                HEADERDEPS="$HEADERDEPS" \
                CPPFLAGS="$CPPFLAGS" \
                LDFLAGS="$LDFLAGS" \
                CFLAGS="$CFLAGS" \
                LIBDEPS="$LIBDEPS"

            mk_cache "HAVE_$DEFNAME" "$result"
        fi

        mk_msg_result "$result"

        if [ "$result" = "yes" ]
        then
            mk_define "HAVE_$DEFNAME" 1
            mk_define "HAVE_DECL_$DEFNAME" 1
        elif [ "$FAIL" = "yes" ]
        then
            mk_fail "missing function: $PROTOTYPE"
        else
            mk_define "HAVE_DECL_$DEFNAME" 0
        fi
    done

    mk_pop_vars
}

#<
# @brief Check for a library
# @usage LIB=lib
#
# @option LIBDEPS=libs Specifies any additional
# libraries might be needed in order to link against
# <param>lib</param>.  Note that MakeKit will respect
# .la files when checking for linkability, so
# this is generally not necessary if the library in
# question was produced with MakeKit or libtool.
#
# Checks for the availability of a library, setting
# <var>result</var> to the result.  If the library
# was found on the system, the result will be "external".
# If it is produced by <funcref>mk_library</funcref> within
# the current project, the result will be "internal".
# Otherwise, the result will be "no".
#>
mk_check_library()
{
    mk_push_vars LIBDEPS LIB CPPFLAGS LDFLAGS CFLAGS
    mk_parse_params

    [ -z "$LIB" ] && LIB="$1"

    CFLAGS="$CFLAGS -Wall -Werror"
    LIBDEPS="$LIBDEPS $LIB"
    
    if _mk_contains "$LIB" ${MK_INTERNAL_LIBS}
    then
        result="internal"
    else
        {
            _mk_c_check_prologue
            cat <<EOF
int main(int argc, char** argv)
{
    return 0;
}
EOF
        } >.check.c
        mk_log "running link test for library: $LIB"
        if _mk_build_test 'link-program' ".check.c"
        then
            result="external"
        else
            result="no"
        fi
    fi

    mk_pop_vars
    [ "$result" != "no" ]
}

#<
# @brief Check for libraries
# @usage libs...
#
# For each library in <param>libs</param>, <funcref>mk_check_library</funcref>
# is invoked to check for its availability.  <var>HAVE_LIB_<varname>lib</varname></var>
# is set to the result.  If the library was available, <def>HAVE_LIB_<varname>lib</varname></def>
# is defined in the current config header and <var>LIB_<varname>lib</varname></var> is
# set to <param>lib</param> (this is useful for conditionally linking to the library
# with LIBDEPS= later on).  A message is printed indicating the result of each test.
#>
mk_check_libraries()
{
    mk_push_vars LIBS LIBDEPS CPPFLAGS LDFLAGS CFLAGS FAIL LIB DEFNAME
    mk_parse_params
    
    for LIB
    do
        mk_defname "$LIB"
        DEFNAME="$result"

        mk_declare -s -i "LIB_$DEFNAME"

        mk_msg_checking "library $LIB"

        if ! mk_check_cache "HAVE_LIB_$DEFNAME"
        then
            mk_check_library \
                LIB="$LIB" \
                CPPFLAGS="$CPPFLAGS" \
                LDFLAGS="$LDFLAGS" \
                CFLAGS="$CFLAGS" \
                LIBDEPS="$LIBDEPS"
            
            mk_cache "HAVE_LIB_$DEFNAME" "$result"
        fi

        mk_msg_result "$result"

        if [ "$result" != "no" ]
        then
            mk_set_all_isas "LIB_$DEFNAME" "$LIB"
            mk_define "HAVE_LIB_$DEFNAME" "1"
        elif [ "$FAIL" = "yes" ]
        then
            mk_fail "missing library: $LIB"
        fi
    done

    mk_pop_vars
}

_mk_check_type()
{
    {
        _mk_c_check_prologue
        for _header in ${HEADERDEPS}
        do
            mk_might_have_header "$_header" && echo "#include <${_header}>"
        done
        
        echo ""
        
        cat <<EOF
int main(int argc, char** argv)
{ 
    return (int) sizeof($TYPE);
}
EOF
    } > .check.c
    mk_log "running compile test for sizeof($TYPE)"
    if _mk_build_test 'compile' .check.c
    then
        result="yes"
    else
        result="no"
    fi

    [ "$result" != "no" ]
}

#<
# @brief Check for a type
# @usage TYPE=type
# @option HEADERDEPS=headers Specifies any headers that
# are necessary to find a declaration of the type.
#
# Checks if the specified type is declared and sets <var>result</var>
# to the result ("yes" or "no").
#>
mk_check_type()
{
    mk_push_vars TYPE HEADERDEPS CPPFLAGS CFLAGS
    mk_parse_params

    [ -z "$TYPE" ] && TYPE="$1"

    CFLAGS="$CFLAGS -Wall -Werror"

    _mk_check_type

    mk_pop_vars
    [ "$result" != "no" ]
}

#<
# @brief Check for types
# @usage typess...
#
# For each type in <param>types</param>, <funcref>mk_check_type</funcref>
# is invoked to check for its availability.  <var>HAVE_<varname>type</varname></var>
# is set to the result.  If the type was available, <def>HAVE_<varname>type</varname></def>
# is defined in the current config header. A messsage is printed indicating the result of
# each test.
#>
mk_check_types()
{
    mk_push_vars TYPES HEADERDEPS CPPFLAGS CFLAGS TYPE FAIL DEFNAME
    mk_parse_params

    CFLAGS="$CFLAGS -Wall -Werror"

    for TYPE
    do
        mk_defname "$TYPE"
        DEFNAME="$result"

        mk_msg_checking "type $TYPE"

        if ! mk_check_cache "HAVE_$DEFNAME"
        then
            _mk_check_type
            
            mk_cache "HAVE_$DEFNAME" "$result"
        fi

        mk_msg_result "$result"

        if [ "$result" = "yes" ]
        then
            mk_define "HAVE_$DEFNAME" "1"
        elif [ "$FAIL" = "yes" ]
        then
            mk_fail "missing type: $TYPE"
        fi
    done

    mk_pop_vars
}

_mk_check_member()
{
    {
        _mk_c_check_prologue
        for _header in ${HEADERDEPS}
        do
            mk_might_have_header "$_header" && echo "#include <${_header}>"
        done
        
        echo ""
        
        cat <<EOF
int main(int argc, char** argv)
{ 
    return argc + sizeof(&(($TYPE *)0)->$MEMBER);
}
EOF
    } > .check.c
    mk_log "running compile test for $TYPE.$MEMBER"
    if _mk_build_test 'compile' .check.c
    then
        result="yes"
    else
        result="no"
    fi

    [ "$result" != "no" ]
}

#<
# @brief Check for a member of type
# @usage TYPE=type MEMBER=member
# @option HEADERDEPS=headers Specifies any headers that
# are necessary to find a declaration of the type.
#
# Checks if the specified type has the specified member
# (e.g. struct field, union arm) and sets <var>result</var>
# to the result ("yes" or "no").
#>
mk_check_member()
{
    mk_push_vars TYPE MEMBER HEADERDEPS CPPFLAGS CFLAGS
    mk_parse_params

    [ -n "$TYPE" -a -n "$MEMBER" ] ||
       mk_fail "invalid parameters to mk_check_member"

    CFLAGS="$CFLAGS -Wall -Werror"

    _mk_check_member

    mk_pop_vars
    [ "$result" != "no" ]
}

#<
# @brief Check for members of types
# @usage specs...
#
# For for each type/member pair in <param>specs</param>,
# specified as <param>type</param><lit>.</lit><param>member</param>,
# <funcref>mk_check_member</funcref> is invoked to check
# for its availability.  <var>HAVE_<varname>type</varname>_<varname>member</varname></var>
# is set to the result.  If the member was available, <def>HAVE_<varname>type</varname>_<varname>member</varname></def>
# is defined in the current config header. A messsage is printed indicating the result of
# each test.
#>
mk_check_members()
{
    mk_push_vars HEADERDEPS CPPFLAGS CFLAGS SPEC TYPE MEMBER FAIL DEFNAME
    mk_parse_params

    CFLAGS="$CFLAGS -Wall -Werror"

    for SPEC
    do
        TYPE="${SPEC%%.*}"
        MEMBER="${SPEC#*.}"

        [ -n "$TYPE" -a -n "$MEMBER" ] ||
            mk_fail "invalid parameter to mk_check_members: $SPEC"

        mk_defname "${TYPE}_${MEMBER}"
        DEFNAME="$result"

        mk_msg_checking "member $TYPE.$MEMBER"

        if ! mk_check_cache "HAVE_$DEFNAME"
        then
            _mk_check_member
            
            mk_cache "HAVE_$DEFNAME" "$result"
        fi

        mk_msg_result "$result"

        if [ "$result" = "yes" ]
        then
            mk_define "HAVE_$DEFNAME" "1"
        elif [ "$FAIL" = "yes" ]
        then
            mk_fail "missing type: $TYPE"
        fi
    done

    mk_pop_vars
}

mk_check_static_predicate()
{
    mk_push_vars EXPR
    mk_parse_params

    {
        _mk_c_check_prologue
        for _header in ${HEADERDEPS}
        do
            mk_might_have_header "$_header" && echo "#include <${_header}>"
        done
        echo ""
        cat <<EOF
int main(int argc, char** argv)
{
     int __array[($EXPR) ? 1 : -1] = {0};

     return __array[0];
}
EOF
    } > .check.c

    _mk_build_test 'compile' .check.c
    _res="$?"

    mk_pop_vars

    return "$_res"
}

_mk_check_sizeof()
{
    # Make sure the type actually exists
    _mk_check_type || return 1

    # Algorithm to derive the size of a type even
    # when cross-compiling.  mk_check_static_predicate()
    # lets us evaluate a boolean expression involving
    # compile-time constants.  Using this, we can perform
    # a binary search for the correct size of the type.
    upper="1024"
    lower="0"
        
    while [ "$upper" -ne "$lower" ]
    do
        mid="$((($upper + $lower)/2))"
        if mk_check_static_predicate EXPR="sizeof($TYPE) <= $mid"
        then
            upper="$mid"
        else
            lower="$(($mid + 1))"
        fi
    done

    result="$upper"
    unset upper lower mid
}

#<
# @brief Check size of a type
#
# @usage TYPE=type
# @usage type
#
# Runs a test for the size of <param>type</param> and sets
# <var>result</var> to the result.  If the type cannot be
# found at all, configuration will be aborted.
#
# This test will work in cross-compiling configurations.
# It will not work on types with sizes over 1024 bytes.
#>
mk_check_sizeof()
{
    mk_push_vars TYPE HEADERDEPS CPPFLAGS LDFLAGS CFLAGS LIBDEPS
    mk_parse_params

    [ -z "$TYPE" ] && TYPE="$1"

    CFLAGS="$CFLAGS -Wall -Werror"
    HEADERDEPS="$HEADERDEPS stdio.h"

    _mk_check_sizeof

    mk_pop_vars
}

#<
# @brief Check sizes of several types
#
# @usage types...
#
# Runs <funcref>mk_check_sizeof</funcref> on each type in <param>types</param>.
# For each type, the variable <var>SIZEOF_<varname>type</varname></var> will be
# set to the result, and <def>SIZEOF_<varname>type</varname></def> will be
# similarly defined in the current config header.
#>
mk_check_sizeofs()
{
    mk_push_vars HEADERDEPS CPPFLAGS LDFLAGS CFLAGS LIBDEPS
    mk_parse_params

    CFLAGS="$CFLAGS -Wall -Werror"
    HEADERDEPS="$HEADERDEPS stdio.h"

    for TYPE
    do
        mk_defname "$TYPE"
        DEFNAME="$result"

        mk_msg_checking "sizeof $TYPE"

        if ! mk_check_cache "SIZEOF_$DEFNAME"
        then
            _mk_check_sizeof
            
            mk_cache "SIZEOF_$DEFNAME" "$result"
        fi

        mk_msg_result "$result"

	[ "$result" != "no" ] && mk_define "SIZEOF_$DEFNAME" "$result"
    done

    mk_pop_vars
}

#<
# @brief Check endianness of system
# @usage
#
# Checks the endianness of the current system and sets the variable
# <var>ENDIANNESS</var> to the result ("little" or "big").  If the
# result was "big", it also defines <def>WORDS_BIGENDIAN</def> in
# the current config header.
#
# This function will work in cross-compiling configurations.
#>
mk_check_endian()
{
    mk_push_vars CPPFLAGS LDFLAGS CFLAGS LIBDEPS
    mk_parse_params

    CFLAGS="$CFLAGS -Wall -Werror"
    HEADERDEPS="$HEADERDEPS stdio.h"

    mk_msg_checking "endianness"
    
    if mk_check_cache "ENDIANNESS"
    then
        result="$result"
    else
        # Check for endianness in a (hacky) manner that supports
        # cross-compiling. This is done by compiling a C file that
        # contains arrays of 16-bit integers that happen to form
        # ASCII strings under particular byte orders.  The strings
        # are then searched for in the resulting object file.
        #
        # The character sequences were designed to be extremely unlikely
        # to occur otherwise.
        {
            cat <<EOF
#include <stdio.h>

/* Spells "aArDvArKsOaP" on big-endian systems */
static const unsigned short aardvark[] =
{0x6141, 0x7244, 0x7641, 0x724b, 0x734f, 0x6150, 0x0};
/* Spells "zEbRaBrUsH" on little-endian systems */
static const unsigned short zebra[] = 
{0x457a, 0x5262, 0x4261, 0x5572, 0x4873, 0x0};

int main(int argc, char** argv)
{ 
    return (int) aardvark[argc] + zebra[argc];
}
EOF
        } > .check.c
        if _mk_build_test 'compile-keep' .check.c
        then
            if strings .check.o | grep "aArDvArKsOaP" >/dev/null
            then
                result="big"
            elif strings .check.o | grep "zEbRaBrUsH" >/dev/null
            then
                result="little"
            else
                rm -f .check.o
                mk_fail "could not determine endianness"
            fi
        else
            rm -f .check.o
            mk_fail "could not determine endianness"
        fi
        
        mk_cache "ENDIANNESS" "$result"
    fi

    if [ "$ENDIANNESS" = "big" ]
    then
        mk_define WORDS_BIGENDIAN 1
    fi
    
    mk_msg_result "$ENDIANNESS"
    
    mk_pop_vars
}

#<
# @brief Set language for configure checks
# @usage lang
#
# Sets the language used for subsequent configuration checks.
# Valid values are "c" and "c++".  This function will fail
# if a working compiler for the language is not available.
#>
mk_check_lang()
{
    case "$1" in
        c)
            [ "$MK_CC_STYLE" = "none" ] &&
               mk_fail "C compiler unavailable"
            ;;
        c++)
            [ "$MK_CXX_STYLE" = "none" ] &&
               mk_fail "C++ compiler unavailable"
            ;;
        *)
            mk_fail "Unsupported language: $1"
            ;;
    esac
    MK_CHECK_LANG="$1"
}

#<
# @brief Turn on compiler warnings
# @usage warning...
#
# Turns on the given list of warning flags
# (<lit>-W</lit><param>warning</param>).
# The <lit>error</lit> flag will be ignored
# if the user disallowed it via the
# <lit>--allow-werror</lit> option to
# <filename>configure</filename>.
#
# @example
# # Turn on all warnings and promote warnings to errors
# mk_compiler_warnings all error
# @endexample
#>
mk_compiler_warnings()
{
    mk_push_vars flag

    for flag
    do
        case "$flag" in
            all)
                MK_CFLAGS="$MK_CFLAGS $MK_WARN_ALL_FLAGS"
                MK_CXXFLAGS="$MK_CXXFLAGS $MK_WARN_ALL_FLAGS"
                continue
                ;;
            error)
                [ "$MK_ALLOW_WERROR" = "no" ] && continue
                ;;
        esac
        
        flag="-W$flag"
        _mk_contains "$flag" ${MK_CFLAGS} ||
           MK_CFLAGS="$MK_CFLAGS $flag"
        _mk_contains "$flag" ${MK_CXXFLAGS} ||
           MK_CXXFLAGS="$MK_CXXFLAGS $flag"
    done

    mk_pop_vars
}

option()
{
    if [ "$MK_DEBUG" = yes ]
    then
        _default_OPTFLAGS="-O0 -g"
    else
        _default_OPTFLAGS="-O2 -g"
    fi

    mk_option \
        OPTION="warn-all-flags" \
        VAR="MK_WARN_ALL_FLAGS" \
        PARAM="flags" \
        DEFAULT="-Wall" \
        HELP="Compiler flags to enable all warnings"

    mk_option \
        OPTION="allow-werror" \
        VAR=MK_ALLOW_WERROR \
        PARAM="yes|no" \
        DEFAULT="yes" \
        HELP="Allow failing on compiler warnings"

    mk_option \
        OPTION="static-libs" \
        VAR="MK_STATIC_LIBS" \
        PARAM="yes|no|list" \
        DEFAULT="no" \
        HELP="Build static libraries"

    mk_option \
        VAR="CC" \
        PARAM="program" \
        DEFAULT="gcc" \
        HELP="Default C compiler"

    MK_DEFAULT_CC="$CC"

    mk_option \
        VAR="CXX" \
        PARAM="program" \
        DEFAULT="g++" \
        HELP="Default C++ compiler"

    MK_DEFAULT_CXX="$CXX"

    if [ "$MK_STATIC_LIBS" != "no" ]
    then
        mk_option \
            VAR="AR" \
            PARAM="program" \
            DEFAULT="ar" \
            HELP="Default ar program"
        
        MK_DEFAULT_AR="$AR"
        
        mk_option \
            VAR="RANLIB" \
            PARAM="program" \
            DEFAULT="ranlib" \
            HELP="Default ranlib program"
        
        MK_DEFAULT_RANLIB="$RANLIB"
    fi

    mk_option \
        VAR="CPPFLAGS" \
        PARAM="flags" \
        DEFAULT="" \
        HELP="C preprocessor flags"

    MK_CPPFLAGS="$CPPFLAGS"

    mk_option \
        VAR="CFLAGS" \
        PARAM="flags" \
        DEFAULT="$_default_OPTFLAGS" \
        HELP="C compiler flags"

    MK_CFLAGS="$CFLAGS"

    mk_option \
        VAR="CXXFLAGS" \
        PARAM="flags" \
        DEFAULT="$_default_OPTFLAGS" \
        HELP="C++ compiler flags"

    MK_CXXFLAGS="$CXXFLAGS"

    mk_option \
        VAR="LDFLAGS" \
        PARAM="flags" \
        DEFAULT="" \
        HELP="Linker flags"

    MK_LDFLAGS="$LDFLAGS"

    unset CC CXX CPPFLAGS CFLAGS CXXFLAGS LDFLAGS AR RANLIB

    for _sys in build host
    do
        mk_defname "MK_${_sys}_ISAS"
        mk_get "$result"
        
        for _isa in ${result}
        do
            mk_defname "$_sys/${_isa}"
            _def="$result"

            mk_defname "MK_${_sys}_OS"
            mk_get "$result"
            
            _default_cc="$MK_DEFAULT_CC"
            _default_cxx="$MK_DEFAULT_CXX"
            _default_ar="$MK_DEFAULT_AR"
            _default_ranlib="$MK_DEFAULT_RANLIB"

            case "${MK_DEFAULT_CC}-${result}-${_isa}" in
                *-darwin-x86_32)
                    _default_cflags="-arch i386"
                    _default_cxxflags="-arch i386"
                    ;;
                *-darwin-x86_64)
                    _default_cflags="-arch x86_64"
                    _default_cxxflags="-arch x86_64"
                    ;;
                *-darwin-ppc32)
                    _default_cflags="-arch ppc"
                    _default_cxxflags="-arch ppc"
                    ;;
                *-darwin-ppc64)
                    _default_cflags="-arch ppc64"
                    _default_cxxflags="-arch ppc64"
                    ;;
                *-*-x86_32)
                    _default_cflags="-m32"
                    _default_cxxflags="-m32"
                    ;;
                *-*-x86_64)
                    _default_cflags="-m64"
                    _default_cxxflags="-m64"
                    ;;
                *-*-sparc_32)
                    _default_cflags="-m32"
                    _default_cxxflags="-m32"
                    ;;
                *-*-sparc_64)
                    _default_cflags="-m64"
                    _default_cxxflags="-m64"
                    ;;
                *-aix-ppc32)
                    _default_cflags="-maix32"
                    _default_cxxflags="-maix32"
                    ;;
                *-aix-ppc64)
                    _default_cflags="-maix64"
                    _default_cxxflags="-maix64"
                    ;;
                *-hpux-ia64_32)
                    _default_cflags="-milp32"
                    _default_cxxflags="-milp32"
                    ;;
                *-hpux-ia64_64)
                    _default_cflags="-mlp64"
                    _default_cxxflags="-mlp64"
                    ;;
                *)
                    _default_cflags=""
                    _default_cxxflags=""
                    ;;
            esac

            mk_option \
                VAR="${_def}_CC" \
                PARAM="program" \
                DEFAULT="$_default_cc" \
                HELP="C compiler ($_sys/$_isa)"

            mk_option \
                VAR="${_def}_CXX" \
                PARAM="program" \
                DEFAULT="$_default_cxx" \
                HELP="C++ compiler ($_sys/$_isa)"
            
            if [ "$MK_STATIC_LIBS" != "no" ]
            then
                mk_option \
                    VAR="${_def}_AR" \
                    PARAM="program" \
                    DEFAULT="$_default_ar" \
                    HELP="ar program ($_sys/$_isa)"
                
                mk_option \
                    VAR="${_def}_RANLIB" \
                    PARAM="program" \
                    DEFAULT="$_default_ranlib" \
                    HELP="ar program ($_sys/$_isa)"
            fi
            
            mk_option \
                VAR="${_def}_CPPFLAGS" \
                PARAM="flags" \
                DEFAULT="" \
                HELP="C preprocessor flags ($_sys/$_isa)"
            
            mk_option \
                VAR="${_def}_CFLAGS" \
                PARAM="flags" \
                DEFAULT="$_default_cflags" \
                HELP="C compiler flags ($_sys/$_isa)"

            mk_option \
                VAR="${_def}_CXXFLAGS" \
                PARAM="flags" \
                DEFAULT="$_default_cxxflags" \
                HELP="C++ compiler flags ($_sys/$_isa)"
            
            mk_option \
                VAR="${_def}_LDFLAGS" \
                PARAM="flags" \
                DEFAULT="" \
                HELP="Linker flags ($_sys/$_isa)"

            mk_option \
                VAR="${_def}_RPATHFLAGS" \
                PARAM="flags" \
                DEFAULT="<autodetect>" \
                HELP="Runtime library path flags ($_sys/$_isa)"
        done
    done
}

_mk_cc_primitive()
{
    cat >.check.c || mk_fail "could not write .check.c"
    ${MK_CC} ${MK_CFLAGS} -o .check.o -c .check.c
    _res="$?"
    rm -f .check.o .check.c
    return "$_res"
}

_mk_cxx_primitive()
{
    cat >.check.cpp || mk_fail "could not write .check.cpp"
    ${MK_CXX} ${MK_CXXFLAGS} -o .check.o -c .check.cpp
    _res="$?"
    rm -f .check.o .check.cpp
    return "$_res"
}

_mk_check_cc_style()
{
    mk_msg_checking "C compiler style"

    if cat <<EOF | _mk_cc_primitive >/dev/null 2>&1
int main(int argc, char** argv) { return 0; }
EOF
    then
        if cat <<EOF | _mk_cc_primitive >/dev/null 2>&1
#ifndef __GNUC__
#error nope
#endif
EOF
        then
            result="gcc"
        else
            result="unknown"
        fi
    else
        result="none"
    fi
    
    MK_CC_STYLE="$result"
    mk_msg_result "$MK_CC_STYLE"
}

_mk_check_cxx_style()
{
    mk_msg_checking "C++ compiler style"
    if cat <<EOF | _mk_cxx_primitive >/dev/null 2>&1
int main(int argc, char** argv) { return 0; }
EOF
    then
        if cat <<EOF | _mk_cxx_primitive >/dev/null 2>&1
#ifndef __GNUC__
#error nope
#endif
EOF
        then
            result="gcc"
        else
            result="unknown"
        fi
    else
        result="none"
    fi
        
    MK_CXX_STYLE="$result"
    mk_msg_result "$MK_CXX_STYLE"
}

_mk_check_cc_ld_style()
{
    mk_msg_checking "C compiler linker style"

    case "$MK_CC_STYLE" in
        none)
            result="none"
            ;;
        gcc)
            _ld="`${MK_CC} -print-prog-name=ld`"
            case "`"$_ld" -v 2>&1`" in
                *"GNU"*)
                    result="gnu"
                    ;;
                *)
                    result="native"
                    ;;
            esac
            ;;
        *)
            result="native"
    esac

    MK_CC_LD_STYLE="$result"
    mk_msg_result "$MK_CC_LD_STYLE"
}

_mk_check_cxx_ld_style()
{
    mk_msg_checking "C++ compiler linker style"

    case "$MK_CXX_STYLE" in
        none)
            result="none"
            ;;
        gcc)
            _ld="`${MK_CXX} -print-prog-name=ld`"
            case "`"$_ld" -v 2>&1`" in
                *"GNU"*)
                    result="gnu"
                    ;;
                *)
                    result="native"
                    ;;
            esac
            ;;
        *)
            result="native"
    esac

    MK_CXX_LD_STYLE="$result"
    mk_msg_result "$MK_CXX_LD_STYLE"
}

_mk_check_rpath_flags()
{
    mk_varname "${MK_SYSTEM%/*}_${MK_SYSTEM#*/}_RPATHFLAGS"
    _var="$result"
    mk_get "$_var"

    if [ "$result" = "<autodetect>" ]
    then
        if [ "${MK_SYSTEM%/*}" = "build" ]
        then
            _libdir="$MK_ROOT_DIR/$MK_RUN_LIBDIR"
            _linkdir="$_libdir"
        else
            _libdir="$MK_LIBDIR"
            _linkdir="$MK_ROOT_DIR/$MK_STAGE_DIR$MK_LIBDIR"
        fi

        case "${MK_OS}:${MK_CC_LD_STYLE}" in
            *:gnu)
                mk_set "$_var" "-Wl,-rpath,$_libdir -Wl,-rpath-link,$_linkdir"
                ;;
            solaris:native)
                mk_set "$_var" "-Wl,-R$_libdir"
                ;;
            aix:native)
                mk_set "$_var" "-Wl,-blibpath:$_libdir:/usr/lib:/lib"
                ;;
            hpux:native)
                mk_set "$_var" "-Wl,+b,$_libdir"
                ;;
            *)
                mk_set "$_var" ""
                ;;
        esac
    fi
}

_mk_compiler_check()
{
    for _sys in build host
    do
        mk_system "$_sys"

        for _isa in ${MK_ISAS}
        do
            mk_system "$_sys/$_isa"

            _mk_check_cc_style
            _mk_check_cxx_style
            _mk_check_cc_ld_style
            _mk_check_cxx_ld_style
            _mk_check_rpath_flags
        done
    done
}

configure()
{
    _MK_LINK_TARGET_HOOKS=""
    _MK_LINK_HOOKS=""

    mk_declare -e _MK_LINK_HOOKS
    mk_declare -i MK_CONFIG_HEADER="" MK_HEADERDEPS="" MK_LIBDEPS=""
    mk_declare -s -e \
        MK_CC MK_CXX MK_CC_STYLE MK_CC_LD_STYLE MK_CXX_STYLE MK_CXX_LD_STYLE

    if [ "$MK_STATIC_LIBS" != "no" ]
    then
        mk_declare -s -e MK_AR MK_RANLIB
    fi

    mk_declare -i -e MK_CPPFLAGS MK_CFLAGS MK_CXXFLAGS MK_LDFLAGS
    mk_declare -s -i -e \
        MK_ISA_CPPFLAGS MK_ISA_CFLAGS MK_ISA_CXXFLAGS MK_ISA_LDFLAGS \
        MK_RPATHFLAGS
    mk_declare -s MK_INTERNAL_LIBS

    mk_msg "default C compiler: $MK_DEFAULT_CC"
    mk_msg "default C++ compiler: $MK_DEFAULT_CXX"
    if [ "$MK_STATIC_LIBS" != "no" ]
    then
        mk_msg "default ar program: $MK_DEFAULT_AR"
        mk_msg "default ranlib program: $MK_DEFAULT_RANLIB"
    fi
    mk_msg "global C preprocessor flags: $MK_CPPFLAGS"
    mk_msg "global C compiler flags: $MK_CFLAGS"
    mk_msg "global C++ compiler flags: $MK_CXXFLAGS"
    mk_msg "global linker flags: $MK_LDFLAGS"

    for _sys in build host
    do
        mk_varname "MK_${_sys}_ISAS"
        mk_get "$result"
        
        for _isa in ${result}
        do
            mk_varname "$_sys/$_isa"
            _def="$result"

            mk_get "${_def}_CC"
            mk_msg "C compiler ($_sys/$_isa): $result"
            mk_set_system_var SYSTEM="$_sys/$_isa" MK_CC "$result"

            mk_get "${_def}_CXX"
            mk_msg "C++ compiler ($_sys/$_isa): $result"
            mk_set_system_var SYSTEM="$_sys/$_isa" MK_CXX "$result"

            if [ "$MK_STATIC_LIBS" != "no" ]
            then
                mk_get "${_def}_AR"
                mk_msg "ar program ($_sys/$_isa): $result"
                mk_set_system_var SYSTEM="$_sys/$_isa" MK_AR "$result"
                
                mk_get "${_def}_RANLIB"
                mk_msg "ranlib program ($_sys/$_isa): $result"
                mk_set_system_var SYSTEM="$_sys/$_isa" MK_RANLIB "$result"
            fi

            mk_get "${_def}_CPPFLAGS"
            mk_msg "C preprocessor flags ($_sys/$_isa): $result"
            mk_set_system_var SYSTEM="$_sys/$_isa" MK_ISA_CPPFLAGS "$result"

            mk_get "${_def}_CFLAGS"
            mk_msg "C compiler flags ($_sys/$_isa): $result"
            mk_set_system_var SYSTEM="$_sys/$_isa" MK_ISA_CFLAGS "$result"

            mk_get "${_def}_CXXFLAGS"
            mk_msg "C++ compiler flags ($_sys/$_isa): $result"
            mk_set_system_var SYSTEM="$_sys/$_isa" MK_ISA_CXXFLAGS "$result"

            mk_get "${_def}_LDFLAGS"
            mk_msg "linker flags ($_sys/$_isa): $result"
            mk_set_system_var SYSTEM="$_sys/$_isa" MK_ISA_LDFLAGS "$result"
        done
    done

    _mk_compiler_check

    for _sys in build host
    do
        mk_varname "MK_${_sys}_ISAS"
        mk_get "$result"
        
        for _isa in ${result}
        do
            mk_varname "$_sys/$_isa"
            _def="$result"

            mk_get "${_def}_RPATHFLAGS"
            mk_msg "rpath flags ($_sys/$_isa): $result"
            mk_set_system_var SYSTEM="$_sys/$_isa" MK_RPATHFLAGS "$result"
        done
    done

    # Each invocation of mk_config_header closes and finishes up
    # the previous header.  In order to close the final config
    # header in the project, we register a completion hook as well.
    mk_add_complete_hook _mk_close_config_header

    mk_add_configure_prehook _mk_compiler_preconfigure
}

_mk_compiler_preconfigure()
{
    MK_CHECK_LANG="c"
}

### section build

_mk_compiler_multiarch_combine()
{
    mk_msg_domain "combine"
    mk_pretty_path "$1"
    mk_msg "$result (${MK_SYSTEM})"
    
    mk_mkdirname "$1"

    case "$MK_OS" in
        darwin)
            mk_run_or_fail lipo -create -output "$@"
            ;;
        *)
            mk_fail "unsupported OS"
            ;;
    esac
}

mk_run_link_posthooks()
{
    for _hook in ${_MK_LINK_HOOKS}
    do
        ${_hook} "$@"
    done
}
