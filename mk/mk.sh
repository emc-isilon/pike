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

##
#
# mk.sh -- foundational functions, aliases, etc.
#
##

### section common

# Make bash more POSIX-friendly
if [ -n "$BASH_VERSION" ]
then
    # Make bash process aliases in non-interactive mode
    shopt -s expand_aliases
    # Unset special variables
    unset GROUPS
fi

# Detect broken variable expansion (FreeBSD sh)
_test="t*"
_star="*"
if [ "${_test%"$_star"}" != "t" ]
then
    MK_BROKEN_VAREXP=yes
else
    MK_BROKEN_VAREXP=no
fi

# Aliases are expanded within functions when they are
# defined, so we set up aliases first

#<
# @function mk_unquote_list
# @brief Unquote list into positional parameters
# @usage quoted...
#
# Unquotes an internally quoted list, such as one
# produced by <funcref>mk_quote_list</funcref>, placing
# each item in the list into the positional parameters
# (<var>$1</var>, <var>$2</var>, etc.).
#
# @example
# # This is a no-op
# mk_quote_list "$@"
# mk_unquote_list "$result"
# @endexample
#>
alias mk_unquote_list='eval set --'

#<
# @brief Append to list variable
# @usage var items...
#
# Quotes and appends <param>items</param> to
# the variable <param>var</param>.
#
# @example
# FOO="'foo'"
# mk_append_list FOO bar
# # FOO is now: 'foo' 'bar'
#>
mk_append_list()
{
    __result="$result"
    __var="$1"
    shift
    mk_quote_list "$@"
    [ -n "$result" ] && eval "$__var=\"\${$__var:+\$$__var }\$result\""
    result="$__result"
    unset __result __var
}

##
#
# Extended parameter support
#
# The following functions/aliases implement keyword parameters and
# local variables on top of basic POSIX sh:
#
# mk_push_vars var1 [ var2 ... ]
#
#   Saves the given list of variables to a safe location and unsets them
#
# mk_pop_vars
#
#   Restores the variables saved by the last mk_push_vars
#
# mk_parse_params
#
#   Parses all keyword parameters in $@ by setting the corresponding variables
#   The non-keyword parameters remain in $@
#
# A command pattern for MakeKit functions uses all of these to parse
# keyword paremeters and simultaneously avoid stepping on someone else's
# variables:
#
# example_function()
# {
#     mk_push_vars PARAM1 PARAM2 PARAM3
#     mk_parse_params
#
#     ...
#
#     mk_pop_vars
# }

#<
# @function mk_push_vars
# @brief Save variables
# @usage vars..
# @usage var=value...
# 
# Saves each variable in <param>vars</param> to a safe location
# and then sets it to the empty string, or if the second form is used,
# to <param>value</param>.  This provides a mechanism for "local
# variables" that works in any POSIX-compliant shell.
#
# This should only be used once per function, perferably near the top.
# When used, you must ensure that <funcref>mk_pop_vars</funcref> appears
# near the end of the function, and that it is always reached in any
# code path.
#>

#<
# @function mk_pop_vars
# @brief Restore variables
# @usage
# 
# Restores the variables previously saved by <funcref>mk_push_vars</funcref>.
# This function must be called precisely once near the end of any function
# that uses <funcref>mk_push_vars</funcref>, and you must ensure that it is
# reached in all code paths.
#>

#<
# @function mk_parse_params
# @brief Parse special parameters
# @usage
# 
# Processes any positional parameters that fit the following forms:
# <deflist>
#   <defentry>
#     <term><var>VAR</var><lit>=</lit><param>value</param></term>
#     <item>Sets <var>VAR</var> to <param>value</param>.</item>
#   </defentry>
#   <defentry>
#     <term><lit>@</lit><var>VAR</var><lit>={</lit> <param>val1</param> <param>val2</param> <param>...</param> <lit>}</lit></term>
#     <item>Sets <var>VAR</var> to a quoted, space-separated list of values.</item>
#   </defentry>
#   <defentry>
#     <term><lit>--</lit></term>
#     <item>Treat subsequent parameters as ordinary.</item>
#   </defentry>
# </deflist>
#
# Remaining parameters will be shifted such that <var>$1</var> becomes the
# first ordinary parameter.
#
# This should be used in combination with <funcref>mk_push_vars</funcref>
# and <funcref>mk_pop_vars</funcref> to ensure variables you expect to
# be passed are set only for the duration of the function.
#>

if [ -n "$BASH_VERSION" ]
then
    # If we are running in bash, implement these features in terms
    # of the 'local' builtin.  Compared to dash or FreeBSD /bin/sh,
    # bash is sluggish and needs all the help it can get.
    alias mk_parse_params='
while true 
do
  case "$1" in
    "@"*"={")
      __var="${1%%=*}"
      __var="${__var#@}"
      __val=""
      __result="$result"
      shift
      while test "$1" != "}"
      do
          mk_quote "$1"
          __val="$__val $result"
          shift
      done
      result="$__result"
      shift
      local "$__var=${__val# }"
      ;;
    *"="*)
      local "$1"
      shift
    ;;
    --)
      shift
      break
    ;;
    *)
      break
    ;;
  esac
done'
    # Simply declare variables we wish to save as local to avoid overwriting them
    alias mk_push_vars=local
    # Pop becomes a no-op since local variables go out of scope automatically
    alias mk_pop_vars=:
elif type mk_parse_params >/dev/null 2>&1
then
    # Built in to shell, just set up an aliases
    alias mk_push_vars=_mk_push_vars
    alias mk_pop_vars=:
else
    # These versions work on any POSIX-compliant sh implementation
    alias mk_parse_params='
while true 
do
  case "$1" in
    "@"*"={")
      __var="${1%%=*}"
      __var="${__var#@}"
      __val=""
      __result="$result"
      shift
      while test "$1" != "}"
      do
          mk_quote "$1"
          __val="$__val $result"
          shift
      done
      result="$__result"
      shift
      mk_set "$__var" "${__val# }"
      ;;
    *"="*)
      mk_set "${1%%=*}" "${1#*=}"
      shift
    ;;
    --)
      shift
      break
    ;;
    *)
      break
    ;;
  esac
done'

    # We push variables by setting them to a shadow variable of the form:
    #
    # _MK_VAR_{SP}_{NAME}
    #
    # where {SP} is a "stack pointer" which is incremented with each push,
    # and {NAME} is the name of the variable.  The list of pushed variables
    # is saved in _MK_VARS, which is always implicitly pushed and popped as well.
    # The upshot of all this is that we can restore the last set of pushed variables
    # by decrementing the stack pointer _MK_VAR_SP, iterating over _MK_VARS, 
    # and setting each one to the value of its shadow, including _MK_VARS itself.
    #
    # This is admittedly convoluted, but it is preferable to random, difficult-to-debug
    # failures from functions accidentally stepping on each other's variables.
    # Dynamically-scoped variables are a blessing for ad-hoc scripting but can
    # become a curse in anything rigorous, which is why most shells have a local
    # variable mechanism.
    _MK_VAR_SP="0"
    
    mk_push_vars()
    {
        eval "_MK_VAR_${_MK_VAR_SP}__MK_VARS=\"\$_MK_VARS\""
        _MK_VARS=""
        for ___var in "$@"
        do
            case "$___var" in
                *=*)
                    eval "_MK_VAR_${_MK_VAR_SP}_${___var%%=*}=\"\$${___var%%=*}\""
                    mk_set "${___var%%=*}" "${___var#*=}"
                    _MK_VARS="$_MK_VARS ${___var%%=*}"
                    ;;
                *)
                    eval "_MK_VAR_${_MK_VAR_SP}_${___var}=\"\$${___var}\""
                    unset "$___var"
                    _MK_VARS="$_MK_VARS $___var"
                    ;;
            esac
        done
        
        _MK_VAR_SP=$(( $_MK_VAR_SP + 1 ))
    }
    
    mk_pop_vars()
    {
        _MK_VAR_SP=$(( $_MK_VAR_SP - 1 ))

        for ___var in ${_MK_VARS} _MK_VARS
        do
            eval "$___var=\"\$_MK_VAR_${_MK_VAR_SP}_${___var}\""
            unset "_MK_VAR_${_MK_VAR_SP}_${___var}"
        done
    }
fi

#<
# @brief Check for missing keyword parameters
# @usage funcname params..
#
# Checks that each variable in <param>params</param> is
# not the empty string or fails with an error message.
# The provided <param>funcname</param> will be used in the
# message to identify to the user which function expected
# the missing parameter.
#
# This function is intended for use after
# <funcref>mk_parse_params</funcref> in order to verify
# that all non-optional parameters were passed.
#>
mk_require_params()
{
    __func="$1"
    shift
    for __param
    do
        eval [ -n "\"\$${__param}\"" ] || 
            mk_fail "$__func parameter unspecified: $__param"
    done

    unset __param __func
}

##
#
# mk_msg_domain
#
# Sets the message domain for all subsequent messages
#
##
mk_msg_domain()
{
    MK_MSG_DOMAIN="$1"
}

##
#
# mk_msg_format
#
# Prints a message with pretty formatting.  The user could
# import a module to override this if they so desired...
#
# $1 = message domain
# $2 = message
#
##
mk_msg_format()
{
    printf "%20s %s\n" "[$1]" "$2"
}

mk_msg_format_begin()
{
    printf "%20s %s" "[$1]" "$2"
}

mk_msg_format_end()
{
    printf "%s\n" "$1"
}

#<
# @brief Print message to the user
# @usage message...
#
# Prints <param>message</param> to the user.
#
#>
mk_msg()
{
    mk_log "$@"
    mk_msg_format "$MK_MSG_DOMAIN" "$*"
}

mk_msg_begin()
{
    mk_log_begin "$@"
    mk_msg_format_begin "$MK_MSG_DOMAIN" "$*"
}

mk_msg_end()
{
    mk_log_end "$@"
    mk_msg_format_end "$@"
}

##
#
# mk_msg_verbose
#
# Like mk_msg, but only prints something when in verbose mode.
#
##
mk_msg_verbose()
{
    [ -n "${MK_VERBOSE}" ] && mk_msg "$@"
}

##
#
# mk_log
#
# Like mk_msg, but writes to $MK_LOG_FD, and only if it is set.
# This is used to log extra messages that show up in config.log
# but not in the console output when running configure.
#
##
mk_log()
{
    [ -n "${MK_LOG_FD}" ] && mk_msg_format "$MK_MSG_DOMAIN" "$*" >&${MK_LOG_FD}
}

mk_log_begin()
{
    [ -n "${MK_LOG_FD}" ] && mk_msg_format "$MK_MSG_DOMAIN" "$*" >&${MK_LOG_FD}
}

mk_log_end()
{
    [ -n "${MK_LOG_FD}" ] && mk_msg_format "result" "$*" >&${MK_LOG_FD}
}

##
#
# mk_log_verbose
#
# Like mk_log, but only logs when running in verbose mode
#
##
mk_log_verbose()
{
    [ -n "${MK_VERBOSE}" ] && mk_log "$@"
}

#<
# @brief Print error message and abort
# @usage message..
#
# Prints <param>message</param> to the user and aborts the current
# operation.
#
# Note that if this function is used from a subshell, it will only
# cause the subshell to exit.
#
#>
mk_fail()
{
    mk_msg "ERROR: $@" >&2
    exit 1
}

#<
# @brief Print warning
# @usage message...
#
# Prints <param>message</param> to the user.  If fail-on-warn
# is turned on, this will abort the current operation.  Otherwise,
# this function will pause for 1 second to catch the user's
# attention.
#>
mk_warn()
{
    if [ "$MK_FAIL_ON_WARN" = "yes" ]
    then
        mk_fail "$@"
    else
        mk_msg "WARNING: $*"
        sleep 1
    fi
}

#<
# @brief Check if a function is defined
# @usage name
#
# Returns 0 (logical true) if a function named <param>name</param>
# if defined or 1 otherwise.
#>
mk_function_exists()
{
    # To avoid detecting a program in the path with the same name,
    # we temporarily disable it and flush the shell's command cache
    __exists_PATH="$PATH"
    PATH=""
    hash -r
    type "$1" >/dev/null 2>&1
    __exists_ret="$?"
    PATH="$__exists_PATH"
    return "$__exists_ret"
}

##
#
# mk_safe_source
#
# Sources a file, or returns 1 if the file does not exist.
# This function is necessary because attempting to source a
# non-existant file causes the shell to unceremoniously exit.
# The explicit check here allows us to potentially handle the error.
##
mk_safe_source()
{
    # Prefix relative paths with ./
    # Sourcing is like running a program
    # in that the shell WILL NOT search the
    # current directory for the file
    case "$1" in
        "/"*)
            :
            ;;
        *)
            set -- "./$1"
            ;;
    esac
            
    if [ -f "$1" ]
    then
        . "$1"
    else
        return 1
    fi
}

##
#
# mk_source_or_fail
#
# Sources a file or immediately fails.  Since mk_fail logs
# with mk_msg, the error message will usually point to a
# particular module or MakeKitBuild file which is the culprit.
#
##
mk_source_or_fail()
{
    mk_safe_source "$1" || mk_fail "could not source file: $1"
}

#<
# @brief Recursively create directories
# @usage dirs...
#
# Attempts to recursively create each directory in <param>dirs</param>.
#
#>
mk_mkdir()
{
    for __dir
    do
        if ! mkdir -p -- "$__dir" >/dev/null 2>&1
        then
            # Back off and try to create components individually
            # This works around race conditions in some mkdir
            # implementations
            _IFS="$IFS"
            IFS="/"
            set -- ${__dir}
            IFS="$_IFS"
            __dir=""
            for __comp
            do
                __dir="$__dir/$__comp"
                [ -n "${__dir#/}" ] || continue
                __err=`mkdir -p -- "${__dir#/}" 2>&1`
                # If we succeeded or the directory was created
                # by someone else (race condition), keep going
                [ "$?" -eq 0 -o -d "${__dir#/}" ] && continue
                mk_fail "$__err"
            done
        fi
    done
}

#<
# @brief Get value of variable
# @usage var
#
# Gets the value of the variable <param>var</param> and
# places it in <var>result</var>.
#
#>
mk_get()
{
    eval result="\"\$$1\""
}

#<
# @brief Set value of variable
# @usage var value
#
# Sets the variable <param>var</param> to <param>value</param>.
#
#>
mk_set()
{
    eval "${1}=\${2}"
}

##
#
# mk_is_set
#
# Returns 0 if the variable whose name is $1 is set,
# or 1 otherwise.
#
##
mk_is_set()
{
    eval [ -n "\"\${$1+yes}\"" ]
}

if [ "$MK_BROKEN_VAREXP" = "no" ]
then
#<
# @brief Convert a string to a variable name 
# @usage str
#
# Converts a string to a form suitable for use as a variable name.
# All letters are uppercased, and all non-letter, non-number
# characters are converted to _.
# Sets <var>result</var> to the result.
#>
mk_varname()
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
            # Convert everything else to _
            *) __char="_";;
        esac

        result="${result}${__char}"
    done
}
else
mk_varname()
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
            # Convert everything else to _
            *) __char="_";;
        esac

        result="${result}${__char}"
    done 
}
fi

##
#
# _mk_slashless_name
#
# Converts all forward slashes in $1 to underlines.  This is useful
# for generating filenames.
#
# This function is private.
#
##
_mk_slashless_name()
{
    __rem="$1"
    result=""

    while [ -n "$__rem" ]
    do
        __rem2="${__rem#?}"
        __char="${__rem%"$__rem2"}"
        __rem="$__rem2"
        
        case "$__char" in
            # Convert / to _
            /) __char="_";;
            # Leave everything else alone
            *) :;;
        esac

        result="${result}${__char}"
    done
}

if ! type mk_quote >/dev/null 2>&1
then

##
#
# Possibly the most important function in MakeKit, this quotes a string
# so it can safely be read back in by the shell.  This is done by surrounding
# the string with single quotes, and replacing all single quotes within
# the string with the sequence '\''.  This function is called A LOT, so it
# uses only shell builtins to be as fast as possible.
#
##

#<
#
# @brief Quote string for the shell
# @usage str
#
# Quotes <param>str</param> so that it can be safely reinterpreted by the shell
# and sets <var>result</var> to the result.
#
# @example
# # Sets result to: 'hello '\'' world'
# mk_quote "hello ' world"
#>
mk_quote()
{
    result="'"
    __rem="$1"
    while true
    do
        # Get the largest prefix of the remaining string that
        # does not contain any single quotes
        __prefix=${__rem%%"'"*}

        # If this was not the remainder of the string itself,
        # we still have work to do...
        if [ "$__prefix" != "$__rem" ]
        then
            # Append the prefix along with the escape sequence for a single quote
            result="${result}${__prefix}'\\''"
            # Strip the single quote from the remaining string
            __rem=${__rem#*"'"}
        else
            # We are done!
            result="${result}${__rem}"
            break
        fi
    done

    # Add end quote
    result="${result}'"
}

#<
# @brief Quote list of strings for the shell
# @usage strings...
#
# Quotes each string in <param>strings</param> as by
# <funcref>mk_quote</funcref> and sets <var>result</var>
# to the space-separated concatenation.
#
#>
mk_quote_list()
{
    ___result=""
    for ___item in "$@"
    do
        mk_quote "$___item"
        ___result="$___result $result"
    done

    result="${___result# }"
}

##
#
# mk_quote_space
#
# Quotes only the spaces in $1 by prefixing them with backslashes.  This
# is primarily used in Makefiles for escaping spaces in filenames used
# as targets or dependencies.
#
##
mk_quote_space()
{
    result=""
    __rem="$1"
    while true
    do
        __prefix="${__rem%%\ *}"

        if [ "$__prefix" != "$__rem" ]
        then
            result="${result}${__prefix}\\ "
            __rem="${__rem#*\ }"
        else
            result="${result}${__rem}"
            break
        fi
    done
}

##
#
# mk_quote_list_space
#
# Runs mk_quote_space on each parameter and concatenates the results
# into a space-separated list.
#
##
mk_quote_list_space()
{
    ___result=""
    for ___item in "$@"
    do
        mk_quote_space "$___item"
        ___result="$___result $result"
    done

    result="${___result# }"
}

fi

##
#
# mk_quote_c_string
#
# Renders $1 as a C string literal.  This is useful for generating
# C source files or headers, awk scripts, etc.
#
##
mk_quote_c_string()
{
    result=""
    __rem="$1"
    while true
    do
        __prefix="${__rem%%[\"\\]*}"

        if [ "$__prefix" != "$__rem" ]
        then
            __rem="${__rem#$__prefix}"
            case "$__rem" in
                "\\"*)
                    result="${result}${__prefix}\\\\"
                    ;;
                "\""*)
                    result="${result}${__prefix}\\\""
                    ;;
            esac
            __rem="${__rem#?}"
        else
            result="${result}${__rem}"
            break
        fi
    done

    result="\"${result}\""
}

##
#
# mk_expand_pathnames
#
# Performs pathname expansion (aka globbing) on $1, which should be a list of
# filename patterns (internally quoted if necessary).  The result is an
# internally quoted list of files, which you can break apart with
# mk_unquote_list.  You can optionally specify the directory to perform
# the expansion within as $2 -- the default is the current source subdirectory
# being processed.
#
##
mk_expand_pathnames()
{
    ___result=""
    ___pwd="$PWD"
    ___dir="${2-${MK_SOURCE_DIR}${MK_SUBDIR}}"

    cd "$___dir" || return 1
    mk_unquote_list "$1"
    cd "$___pwd" || mk_fail "where did my directory go?"
    
    for ___item in "$@"
    do
        mk_quote "$___item"
        ___result="$___result $result"
    done
    result="${___result# }"
}

##
#
# mk_expand_absolute_pathnames
#
# Performs pathname expansion on $1, which should be a list of
# filename patterns specifying absolute paths.  The patterns
# are not matched against / but against the directory $2, or
# the staging directory by default.  As an example,
# mk_expand_absolute_pathnames '${MK_LIBDIR}/*{MK_LIB_EXT}'
# would give you a list of all built libraries.
#
##
mk_expand_absolute_pathnames()
{
    ___result=""
    ___pwd="$PWD"
    ___dir="${2-${MK_STAGE_DIR}}"

    # Unquote list with globbing turned off
    # This gives us a list of unexpanded patterns in $@
    set -f
    mk_unquote_list "$1"
    set +f

    # Enter the directory where matching should take place
    cd "$___dir" || return 1

    for ___item in "$@"
    do
        # Prefix with .
        # For example, /usr/bin/* becomes ./usr/bin/*
        ___item=".${___item}"
        # Now we can actually expand the pattern
        # First, make IFS empty to prevent field splitting
        ___ifs="$IFS"
        IFS=""
        # Set $@ to the expansion.  Note that this doesn't
        # interfere with the outer for loop
        set -- ${___item}
        # Restore IFS
        IFS="$___ifs"

        # Now iterate over each match
        for ___item in "$@"
        do
            if [ -e "$___item" ]
            then
                # Strip the leading . we added
                mk_quote "${___item#.}"
                ___result="$___result $result"
            fi
        done
    done

    # Go back home
    cd "$___pwd" || mk_fail "where did my directory go?"

    result="${___result# }"
}

_mk_fnmatch_transform()
{
    # Field split by / with globbing off
    __tmp="$IFS"
    IFS="/"
    set -f
    set -- ${1}
    set +f
    IFS="$__tmp"

    # Now the path components are in positional parameters
    result=""
    __i=0
    for __tmp
    do
        result="${result}${__tmp}/${__i}/"
        __i=$(($__i + 1))
    done
    
    unset __tmp __i
}

#<
# @brief Perform glob matching on path
# @usage path pattern
#
# Performs glob matching on a path.  Unlike
# the shell's <lit>case</lit> syntax, wildcards
# will not match across path separators.
#
# Returns 0 (logical true) if <param>pattern</param>
# matches <param>path</param>, or 1 otherwise.
#
# This function does not change <var>result</var>.
#>
mk_fnmatch()
{
    # $1 = path
    # $2 = pattern
    case "$2" in
        *'/'*)
            set -- "$1" "$2" "$result"
            _mk_fnmatch_transform "$1"
            set -- "$result" "$2" "$3"
            _mk_fnmatch_transform "$2"
            set -- "$1" "$result" "$3"
            result="$3"
            ;;
        *)
            set -- "${1##*/}" "$2"
            ;;
    esac

    case "$1" in
        $2)
            return 0
            ;;
    esac

    return 1
}

_MK_COUNTER=0

#<
# @brief Compile glob patterns to a function
# @usage patterns...
#
# Generates a new shell function which acts
# as a matching predicate for <param>patterns</param>.
# When the generated function is invoked with the
# string <param>path</param>, it will return 0
# (logical true) if
# <lit><funcref>mk_fnmatch</funcref> <param>path</param> <param>pattern</param></lit>
# would succeed for any <param>pattern</param> in
# <param>patterns</param>, and 1 (logical false)
# otherwise.
#
# Sets <var>result</var> to the generated function.
# Be sure to use <lit>unset -f</lit> to undefine it
# when you are done.
#>
mk_fnmatch_compile()
{
    # ... = patterns
    __func="__fnmatch$_MK_COUNTER"
    _MK_COUNTER=$(($_MK_COUNTER+1))
    __trans=""
    __varlist=""
    __varlist2=""
    __var="3"

    for _pat
    do
        case "$_pat" in
            */*)
                _mk_fnmatch_transform "$_pat"
                mk_quote "$result"
                __trans="$__trans $result"
                __varlist="$__varlist|\${$__var}"
                ;;
            *)
                mk_quote "$_pat"
                __trans="$__trans $result"
                __varlist2="$__varlist2|\${$__var}"
                ;;
        esac
        __var=$(($__var+1))
    done

    __eval="
$__func()
{
    _result=\"\$result\"
    _mk_fnmatch_transform \"\$1\"
    set -- \"\$1\" \"\$result\" $__trans
    result=\"\$_result\""

    [ -n "$__varlist" ] && __eval="$__eval
    case \"\$2\" in
        ${__varlist#|})
            return 0
        ;;
    esac"

    [ -n "$__varlist2" ] && __eval="$__eval
    case \"\$1\" in
        ${__varlist2#|})
            return 0
        ;;
    esac"

    __eval="$__eval
    return 1
}"

    eval "$__eval"

    result="$__func"
    unset __func __trans __varlist __varlist2 __var __eval
}

mk_fnmatch_filter()
{
    __patterns="$1"
    __results=""
    
    shift

    for __path
    do
        set -f
        mk_unquote_list "$__patterns"
        set +f

        for __pattern
        do
            if mk_fnmatch "$__path" "$__pattern"
            then
                mk_quote "$__path"
                __results="$__results $result"
            fi
        done
    done

    result="${__results# }"
    unset __patterns __results __pattern __path
}

#<
# @brief Normalize path
# @usage path
#
# Normalizes <param>path</param> by attempting to remove all
# '.' and '..' components.  '..' components which attempt to escape
# the current directory or / are left in place, but are guaranteed
# to occur at the beginning of the string where they can be
# easily checked.  Sets <var>result</var> to the result.
#>
mk_normalize_path()
{
    case "$1" in
        /*)
            __leading="/"
            set -- "${1##/}"
            ;;
        *)
            __leading=""
            ;;
    esac

    __path_IFS="$IFS"
    IFS="/"
    set -f
    set -- ${1}
    set +f
    IFS="$__path_IFS"

    result=""
    __comps=0
    
    for __path_item in "$@"
    do
        case "$__path_item" in
            '.'|'')
                continue;
                ;;
            '..')
                if [ $__comps -eq 0 ]
                then
                    result="${result}/.."
                else
                    result="${result%/*}"
                    __comps=$(($__comps-1))
                fi
                ;;
            *)
                result="${result}/${__path_item}"
                __comps=$(($__comps+1))
                ;;
        esac
    done

    result="${__leading}${result#/}"
    unset __path_IFS __path_item __comps __leading
}

_mk_find_resource()
{
    __resource="$1"
    _IFS="$IFS"
    IFS=":"
    set -- ${MK_SEARCH_DIRS}
    IFS="$_IFS"
    for __dir
    do
        __file="${__dir}/$__resource"
        if [ -e "$__file" ]   
        then
            result="$__file"
            unset __resource __file
            return 0
        fi
    done

    unset __resource __file
    return 1
}

#<
# @brief Find resource in search path
# @usage relpath
#
# Locates a resource by searching the resource path
# list and sets <var>result</var> to the result.
# If the resource is not found, this function will abort.
#
# The resource path list includes any directories specified
# by the <var>MKLOCAL</var> variable in <lit>MakeKitBuild</lit>
# files in the current project, as well as the MakeKit home
# directory.
#>
mk_resolve_resource()
{
    _mk_find_resource "$1" || mk_fail "could not resolve resource: $1"
}

_mk_contains()
{
    ___needle="$1"
    shift
    
    for ___hay in "$@"
    do
        if [ "$___hay" = "$___needle" ]
        then
            return 0
        fi
    done

    return 1
}

_mk_reverse()
{
    result=""
    for ___item in "$@"
    do
        result="$___item $result"
    done

    result="${result% }"
}

#<
# @brief Strip last component from filename
# @usage filename
#
# Strips the last component from a filename,
# leaving the name of the directory containing
# the file, and sets <var>result</var> to the
# result.
#>
mk_dirname()
{
    result="."
    case "$1" in
        */*)
            result="${1%/*}"
    esac
}

#<
# @brief Strip leading directory from filename
# @usage filename
#
# Strips the leading directory components
# from a filename and sets <var>result</var>
# to the result.
#>
mk_basename()
{
    result="${1##*/}"
}

#<
# @brief Create leading directories for filename
# @usage filename
#
# Creates all leading directory components
# for a filename.
#>
mk_mkdirname()
{
    _result="$result"
    mk_dirname "$1"
    mk_mkdir "$result"
    result="$_result"
}

#<
# @brief Run a command and abort on failure
# @usage command...
# 
# Runs the specified command.  If it fails,
# the current operation will be aborted with
# an error message detailing the command that
# was run.
#>
mk_run_or_fail()
{
    mk_quote_list "$@"
    mk_msg_verbose "+ $result"
    
    if ! "$@"
    then
        mk_msg "FAILED: $result"
        exit 1
    fi
}

#<
# @brief Run a command quietly and abort on failure
# @usage command...
# 
# Like <funcref>mk_run_or_fail</funcref>, but suppresses
# all command output if the command succeeds.  On failure,
# the output is displayed.
#>
mk_run_quiet_or_fail()
{
    mk_quote_list "$@"
    mk_msg_verbose "+(q) $result"
    
    __log="`"$@" 2>&1`"

    if [ "$?" -ne 0 ]
    then
        echo "$__log" >&2
        mk_msg "FAILED: $result"
        exit 1
    fi
}

mk_cd_or_fail()
{
    mk_quote "$1"
    mk_msg_verbose "+ 'cd' $result"
    cd "$1" || mk_fail "FAILED: 'cd' $result"
}

#<
# @brief Read a line from stdin
# @usage
#
# Reads a single line from stdin and sets <var>result</var>
# to result.  If a line was read, this function returns 0
# (logical true).  If a line could not be read (e.g. due to end
# of file), 1 is returned.
#>
mk_read_line()
{
    _IFS="$IFS"
    IFS=""
    read -r result
    _res="$?"
    IFS="$_IFS"
    return "$_res"
}

#<
# @brief Get mode of file or directory in octal
# @usage path
#
# Sets <var>result</var> to the mode of <param>path</param>
# in octal.  If the mode could not be read, this function
# aborts via <funcref>mk_fail</funcref>.
#>
mk_get_file_mode()
{
    # $1 = path
    _res=0
    _extra=0
    _mode=`ls -ld "$1"` || mk_fail "could not read mode for file: $1"
    _mode="${_mode%% *}"
    # Strip off file type
    _mode="${_mode#?}"

    
    while [ -n "$_mode" ]
    do
        _rest="${_mode#?}"
        _bit="${_mode%$_rest}"
        _mode="${_rest}"
        case "$_bit" in
            r|w|x)
                _res=$(($_res * 2 + 1))
                ;;
            S|s)
                if [ "${#_mode}" -ge 6 ]
                then
                    # setuid
                    _extra=$(($_extra + 04000))
                else
                    # setgid
                    _extra=$(($_extra + 02000))
                fi

                if [ "$_bit" = "s" ]
                then
                    _res=$(($_res * 2 + 1))
                else
                    _res=$(($_res * 2))
                fi
                ;;
            T|t)
                _extra=$(($_extra + 01000))
                if [ "$_bit" = "t" ]
                then
                    _res=$(($_res * 2 + 1))
                else
                    _res=$(($_res * 2))
                fi
                ;;
            -)
                _res=$(($_res * 2))
                ;;
        esac
    done

    result=`printf "0%o" "$_res"`
}

#<
# @brief Read target of symlink
# @usage path
#
# Sets <var>result</var> to the target of <param>path</param>,
# which must be a symlink.
#>
mk_readlink()
{
    [ -h "$1" ] || mk_fail "mk_readlink: $1 is not a symlink"

    if type readlink >/dev/null 2>&1
    then
        result=`readlink "$1"`
    else
        result=`ls -ld "$1"`
        result="${result#*-> }"
    fi
}

#<
# @brief Clone files and directories
# @usage source dest
#
# Recursively copies source to dest while
# preserving symlinks.
#>
mk_clone()
{
    [ -z "$_MK_UNAME" ] && _MK_UNAME=`uname`
    case "$_MK_UNAME" in
        HP-UX)
            cp -R -- "$1" "$2"
            ;;
        SunOS)
            _mk_clone_solaris "$1" "$2"
            ;;
        *)
            cp -RP -- "$1" "$2"
            ;;
    esac
}

_mk_clone_solaris()
{
    if [ -d "$1" ]
    then
        { cd "$1" && find .; } | while mk_read_line
        do
            if [ -f "$1/$result" -o -h "$1/$result" ]
            then
                mk_mkdirname "$2/$result"
                _mk_clone_solaris "$1/$result" "$2/$result" || return "$?"
            fi
        done
    elif [ -h "$1" ]
    then
        mk_readlink "$1"
        ln -s "$result" "$2" || return "$?"
    else
        cp -- "$1" "$2" || return "$?"
    fi
}

mk_clone_filter()
{
    mk_fnmatch "$1" "$3" && return 0

    if [ -d "$1" ]
    then
        { cd "$1" && find .; } | while mk_read_line
        do
            if [ -f "$1/$result" -o -h "$1/$result" ]
            then
                mk_mkdirname "$2/$result"
                mk_clone_filter "$1/$result" "$2/$result" || return "$?"
            fi
        done
    elif [ -h "$1" ]
    then
        mk_readlink "$1"
        ln -s "$result" "$2" || return "$?"
    else
        cp -- "$1" "$2" || return "$?"
    fi
}

#<
# @brief Make path absolute
# @usage path [rel]
#
# Converts a path to an absolute path and sets <var>result</var>
# to the result.  If <param>path</param> is already absolute, it
# is returned verbatim.  If it is relative, and <param>rel</param>
# is specified, it is appended to it.  If <param>rel</param> is
# not specified, the current working directory is used instead.
#>
mk_absolute_path()
{
    [ -z "$2" ] && set -- "$1" "$PWD"
    
    case "$1" in
        /*) result="$1";;
        *) result="$2/$1";;
    esac
}

_mk_canonical_path()
{
    if [ -d "$1" ]
    then
        __canon=`cd "$1" && pwd` || return 1
    else
        mk_dirname "$1"
        __canon=`cd "$result" && pwd` || return 1
        mk_basename "$1"
        __canon="$__canon/$result"
    fi
    _IFS="$IFS"
    IFS="/"
    set -- $__canon
    IFS="$_IFS"
    __canon=""

    for __part
    do
        if [ -h "$__canon/$__part" ]
        then
            mk_readlink "$__canon/$__part"
            __part="$result"
        fi
        
        case "$__part" in
            /*)
                __canon="/$__part"
                ;;
            .)
                :
                ;;
            ..)
                __canon="${__canon%/*}"
                ;;
            *)
                __canon="${__canon}/$__part"
                ;;
        esac
    done
    
    result="${__canon#/}"
    unset __canon __part
}

#<
# @brief Canonicalize file system path
# @usage path
#
# Sets <var>result</var> to the canonical version of
# <param>path</param>.  A canonical path is absolute
# and contains no symlinks.
#
# Returns <lit>1</lit> (logical false) if the path
# is invalid, or <lit>0</lit> (logical true) otherwise.
#>
mk_canonical_path()
{
    result=""
    while [ "$result" != "$1" ]
    do
        set -- "$result"
        _mk_canonical_path "$1" || return 1
    done
}

#<
# @brief Test if two paths are identical
# @usage path1 path2
#
# Returns <lit>0</lit> (logical true) if <param>path1</param>
# and <param>path2</param> represent the same physical file
# system path.  Returns <lit>1</lit> (logical false) if they
# do not, or if either path is invalid.
#>
mk_are_same_path()
{
    [ "$1" = "$2" ] && return 0
    mk_push_vars result
    mk_canonical_path "$1" || result="NOPE1"
    set -- "$result" "$2"
    mk_canonical_path "$2" || result="NOPE2"
    set -- "$1" "$result"
    mk_pop_vars
    [ "$1" = "$2" ]
}

#<
# @brief Read quoted list from here document
# @usage [var]
#
# Returns a quoted list by reading each line from stdin
# and stripping leading and trailing whitespace. 
# If <param>var</param> is specified, it is taken as the
# name of the variable to set to the result; otherwise,
# <var>result</var> is used.
#
# This function allows quoted lists to be constructed
# from so-called here documents with a single item per line.
#
# @example
# FOO=foo
# mk_text_list HUGE_TARGET_LIST &lt;&lt;EOF
#     ${FOO}/bar
#     ${FOO}/baz
#     ...
# EOF
# echo "$HUGE_TARGET_LIST"
# # Output: 'foo/bar' 'foo/baz' ...
# @endexample
#>
mk_here_list()
{
    __list=""
    while mk_read_line
    do
        while true
        do
            case "$result" in
                " "*) result="${result# }";;
                "	"*) result="${result#	}";;
                *" ") result="${result% }";;
                *"	") result="${result%	}";;
                *) break;;
            esac
        done
        
        mk_quote "$result"
        __list="$__list $result"
    done
    if [ -n "$1" ]
    then
        mk_set "$1" "${__list# }"
    else
        result="${__list# }"
    fi
}

#<
# @brief Capture output of command as list
# @usage command...
#
# Executes <param>command</param> and sets
# <var>result</var> to a quoted list of its
# lines of output.
#
# @example
# mk_capture_lines find . -name "*.txt"
# @endexample
#>
mk_capture_lines()
{
    _IFS="$IFS"
    IFS=""
    result=`"$@"`
    IFS='
'
    set -- $result
    IFS="$_IFS"
    mk_quote_list "$@"
}

_MK_TMPCOUNT=0
_MK_TMPLIST=""

mk_tempfile()
{
    _result=".$$.$_MK_TMPCOUNT.$1"
    _MK_TMPCOUNT=$(($_MK_TMPCOUNT+1))
    mk_quote "$_result"
    _MK_TMPLIST="$_MK_TMPLIST $result"
    result="$_result"
}

mk_tempfile_delete()
{
    mk_unquote_list "$_MK_TMPLIST"
    _MK_TMPLIST=""
    for _tmp
    do
        if [ "$_tmp" = "$1" ]
        then
            rm -rf -- "$_tmp"
        else
            mk_quote "$_tmp"
            _MK_TMPLIST="$_MK_TMPLIST $result"
        fi
    done
}

mk_tempfile_clear()
{
    mk_unquote_list "$_MK_TMPLIST"
    _MK_TMPLIST=""
    for _tmp
    do
        rm -rf -- "$_tmp"
    done
}

_mk_cleanup_handler()
{
    cd "$MK_ROOT_DIR" || exit 1
    mk_tempfile_clear
    exit "$1"
}

trap '_mk_cleanup_handler $?' EXIT
trap '_mk_cleanup_handler 130' INT
trap '_mk_cleanup_handler 143' TERM
