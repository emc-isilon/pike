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
# docbook.sh -- support for building DocBook documentation
#
# FIXME: move to contrib module area?
#
##

DEPENDS="program core"

### section configure

option()
{
    _default_docbook_dir="<none>"

    for candidate in \
        /usr/share/xml/docbook/stylesheet/docbook-xsl \
        /usr/share/sgml/docbook/xsl-stylesheets \
        /opt/local/share/xsl/docbook-xsl
    do
        if [ -d "$candidate" ]
        then
            _default_docbook_dir="$candidate"
            break
        fi
    done
    
    mk_option \
        OPTION=docbook-xsl-dir \
        PARAM="path" \
        VAR="MK_DOCBOOK_XSL_DIR" \
        DEFAULT="$_default_docbook_dir" \
        HELP="Location of DocBook XSL stylesheets"
}

#<
# @brief Check for DocBook prerequisites on the build system
# @usage
#
# Checks for the availability of DocBook XSL stylesheets
# and a usable XSLT processor (currently only xsltproc).
# The result can be tested with <funcref>mk_have_docbook</funcref>.
# If successful, you may then use functions such as
# <funcref>mk_docbook_html</funcref> to generate documentation
# from DocBook sources as part of your project.
#>
mk_check_docbook()
{
    mk_check_program "xsltproc"

    mk_msg_checking "docbook xsl dir"

    if [ -d "$MK_DOCBOOK_XSL_DIR" -a -n "$XSLTPROC" ]
    then
        MK_HAVE_DOCBOOK_XSL=yes
        result="$MK_DOCBOOK_XSL_DIR"
    else
        MK_HAVE_DOCBOOK_XSL=no
        result="no"
    fi
    
    mk_msg_result "$result"

    if [ -n "$XSLTPROC" -a "$MK_HAVE_DOCBOOK_XSL" = "yes" ]
    then
        MK_HAVE_DOCBOOK=yes
    else
        MK_HAVE_DOCBOOK=no
    fi

    mk_msg "docbook enabled: $MK_HAVE_DOCBOOK"

    mk_declare -i MK_HAVE_DOCBOOK_XSL MK_HAVE_DOCBOOK
}

#<
# @brief Check for PDF-specific DocBook prerequisites on the build system
# @usage
#
# Checks for the availability of Apache FOP, necessary to generate PDF
# documents from DocBook sources.  This Check must be issued after
# <funcref>mk_check_docbook</funcref> succeeds.  The result can be
# tested with <funcref>mk_have_docbook_pdf</funcref>.  If successful,
# you may then use functions such as <funcref>mk_docbook_pdf</funcref>
# to generate documentation from DocBook sources as part of your
# project.
#>
mk_check_docbook_pdf()
{
    MK_HAVE_DOCBOOK_PDF=no

    if mk_have_docbook
    then
        mk_check_program "fop"
        
        [ -n "$FOP" ] && MK_HAVE_DOCBOOK_PDF=yes
    fi

    mk_msg "docbook pdf enabled: $MK_HAVE_DOCBOOK_PDF"

    mk_declare -i MK_HAVE_DOCBOOK_PDF
}

#<
# @brief Test if DocBook processing is available
# @usage
#
# Returns <lit>0</lit> (logical true) if DocBook prerequistes
# were successfully found by <funcref>mk_check_docbook</funcref>,
# or <lit>1</lit> (logical false) otherwise.
#>
mk_have_docbook()
{
    [ "$MK_HAVE_DOCBOOK" = "yes" ]
}

#<
# @brief Test if DocBook pdf processing is available
# @usage
#
# Returns <lit>0</lit> (logical true) if DocBook pdf prerequistes
# were successfully found by <funcref>mk_check_docbook_pdf</funcref>,
# or <lit>1</lit> (logical false) otherwise.
#>
mk_have_docbook_pdf()
{
    [ "$MK_HAVE_DOCBOOK_PDF" = "yes" ]
}

#<
# @brief Generate html documentation
# @usage SOURCE=source_file
# @option SOURCE=source_file specifies the DocBook XML
# source file to process
# @option STYLESHEET=xsl_file specifies the XSL stylesheet
# for generating html.  Defaults to
# <lit>$MK_DOCBOOK_XSL_DIR/xhtml/profile-chunk.xsl</lit>.
# @option IMAGES=image_dir specifies the directory from which
# to copy images used in the generated html.  Defaults to
# <lit>$MK_DOCBOOK_XSL_DIR/images</lit>.
# @option INSTALLDIR=install_dir specifies the directory
# where the generated documentation will be placed.  Defaults
# to <lit>$MK_HTMLDIR</lit>.
# @option INCLUDES=source_list specifies a list of additional
# xml files that might be included by <param>source_file</param>,
# such as by XInclude.
# @option DEPS=deps specifies any additional dependencies
# needed to generate the documentation
#
# Processes the specified source file with XSLT to produce
# html documentation.
#
# To use this function, you must use <funcref>mk_check_docbook</funcref>
# in a <lit>configure</lit> section of your project, and it must succeed.
# You can test if DocBook processing is available with
# <funcref>mk_have_docbook</funcref>.  This function will fail
# if it is not.
#>
mk_docbook_html()
{
    mk_have_docbook || mk_fail "mk_docbook_html: docbook unavailable"

    mk_push_vars \
        STYLESHEET="@$MK_DOCBOOK_XSL_DIR/xhtml/profile-chunk.xsl" \
        IMAGES="@$MK_DOCBOOK_XSL_DIR/images" \
        INSTALLDIR="${MK_HTMLDIR}" \
        SOURCE \
        INCLUDES \
        DEPS

    mk_parse_params

    mk_target \
        TARGET="${INSTALLDIR}" \
        DEPS="$DEPS $SOURCE $STYLESHEET $INCLUDES" \
        _mk_docbook '$@' "&$INSTALLDIR" "&$SOURCE" "&$STYLESHEET" "$INCLUDES"

    DEPS=""

    # Install CSS file
    if [ -n "$CSS" ]
    then
        mk_stage SOURCE="$CSS" DESTDIR="${INSTALLDIR}" @DEPS={ "$INSTALLDIR" }
        mk_quote "$result"
        DEPS="$DEPS $result"
    fi

    # Install image files
    if [ -n "$IMAGES" ]
    then
        mk_stage SOURCE="$IMAGES" DEST="${INSTALLDIR}/images" @DEPS={ "$INSTALLDIR" }
        mk_quote "$result"
        DEPS="$DEPS $result"
    fi

    mk_basename "$SOURCE"

    mk_target \
        TARGET=".docbook-html.$result.stamp" \
        DEPS="$DEPS" \
        mk_run_or_fail touch '$@'

    mk_pop_vars
}

#<
# @brief Generate UNIX man pages
# @usage SOURCE=source_file MANPAGES=manpage_list
# @option SOURCE=source_file specifies the DocBook XML
# source file to process
# @option MANPAGES=manpage_list specifies a list of manpage
# files that will be output when the <param>source_file</param>
# is processed, e.g. <lit>foobar.3</lit> for the manpage
# <lit>foobar</lit> in section 3.
# @option STYLESHEET=xsl_file specifies the XSL stylesheet
# for generating man pages.  Defaults to
# <lit>$MK_DOCBOOK_XSL_DIR/manpages/profile-docbook.xsl</lit>.
# @option INSTALLDIR=install_dir specifies the directory
# where the generated documentation will be placed.  Defaults
# to <lit>$MK_MANDIR</lit>.  The generated files will be placed
# in subdirectories of this location according to their section.
# @option INCLUDES=source_list specifies a list of additional
# xml files that might be included by <param>source_file</param>,
# such as by XInclude.
# @option DEPS=deps specifies any additional dependencies
# needed to generate the documentation
#
# Processes the specified source file with XSLT to produce
# UNIX man pages.
#
# To use this function, you must use <funcref>mk_check_docbook</funcref>
# in a <lit>configure</lit> section of your project, and it must succeed.
# You can test if DocBook processing is available with
# <funcref>mk_have_doxygen</funcref>.  This function will fail
# if it is not.
#>
mk_docbook_man()
{
    mk_have_docbook || mk_fail "mk_docbook_html: docbook unavailable"

    mk_push_vars \
        STYLESHEET="@$MK_DOCBOOK_XSL_DIR/manpages/profile-docbook.xsl" \
        INSTALLDIR="${MK_MANDIR}" \
        SOURCE \
        MANPAGES \
        INCLUDES \
        DEPS
    mk_parse_params

    man_outdir="${SOURCE}.docbook-man"

    mk_target \
        TARGET="$man_outdir/.stamp" \
        DEPS="$DEPS $STYLESHEET $SOURCE $INCLUDES" \
        _mk_docbook '$@' "&$man_outdir" "&$SOURCE" "&$STYLESHEET" "$INCLUDES"

    mk_quote "$result"
    man_stamp="$result"

    DEPS=""

    mk_unquote_list "$MANPAGES"
    for manfile
    do
        section="${manfile##*.}"
        __tail="${section#?}"
        section="${section%$__tail}"
        
        mk_target \
            TARGET="$man_outdir/$manfile" \
            DEPS="$man_stamp" \
            mk_run_or_fail touch '$@'

        mk_stage \
            SOURCE="$man_outdir/$manfile" \
            DESTDIR="$INSTALLDIR/man${section}"

        mk_quote "$result"
        DEPS="$DEPS $result"
    done

    mk_basename "$SOURCE"

    mk_target \
        TARGET=".docbook-man.$result.stamp" \
        DEPS="$DEPS" \
        mk_run_or_fail touch '$@'

    mk_pop_vars
}

#<
# @brief Generate PDF documentation
# @usage SOURCE=source_file PDF=pdf_name
# @option SOURCE=source_file Specifies the DocBook XML
# source file to process.
# @option STYLESHEET=xsl_file Specifies the XSL stylesheet
# for generating Formatting Objects.  Defaults to
# <lit>$MK_DOCBOOK_XSL_DIR/fo/profile-docbook.xsl</lit>.
# @option INSTALLDIR=install_dir Specifies the directory
# where the generated PDF will be placed.  Defaults
# to <lit>$MK_DOCDIR/pdf</lit>.
# @option INCLUDES=source_list Specifies a list of additional
# files that might be included or referenced by
# <param>source_file</param>, such as included xml files
# or images.
# @option DEPS=deps Specifies any additional dependencies
# needed to generate the documentation
#
# Processes the specified source file with XSLT and Apache FOP
# to produce a PDF file called <param>pdf_name</param>.
#
# To use this function, you must use <funcref>mk_check_docbook</funcref>
# as well as <funcref>mk_check_docbook_pdf</funcref> to check for all
# prerequisits in a <lit>configure</lit> section of your project,
# and both must succeed.
#
# You can test if DocBook processing is available with
# <funcref>mk_have_docbook</funcref> and if PDF generation is available
# with <funcref>mk_have_docbook_pdf</funcref>.
# This function will fail it is not available.
#>
mk_docbook_pdf()
{
    mk_have_docbook_pdf || mk_fail "mk_docbook_pdf: docbook pdf unavailable"

    mk_push_vars \
        STYLESHEET="@$MK_DOCBOOK_XSL_DIR/fo/profile-docbook.xsl" \
        INSTALLDIR="$MK_DOCDIR/pdf" \
        PDF="docbook.pdf" \
        SOURCE \
        INCLUDES \
        DEPS \
        FOP_PARAMS

    mk_parse_params
    mk_require_params mk_docbook_pdf SOURCE

    mk_target \
        TARGET="$INSTALLDIR/$PDF" \
        DEPS="$DEPS $SOURCE $STYLESHEET $INCLUDES" \
        _mk_docbook_pdf %FOP_PARAMS \
        '$@' "&$SOURCE" "&$STYLESHEET" "$INCLUDES"

    mk_pop_vars
}

### section build

_mk_docbook_pdf()
{
    mk_push_vars FOP_PARAMS
    mk_parse_params

    mk_msg_domain "docbook-pdf"

    mk_pretty_path "$1"
    mk_msg "$result"

    mk_absolute_path "$1"
    OUTPUT="$result"
    SOURCE="$2"
    mk_absolute_path "$3"
    SHEET="$result"

    mk_tempfile "docbook-pdf"
    TMPDIR="$result"

    mk_mkdir "$TMPDIR"
    mk_run_or_fail cp "$SOURCE" "$TMPDIR/in.xml"

    mk_expand_pathnames "$4"
    mk_unquote_list "$result"

    for f
    do
        mk_resolve_file "$f"
        mk_mkdirname "$TMPDIR/$f"
        mk_run_or_fail mk_clone "$result" "$TMPDIR/$f"
    done

    mk_cd_or_fail "$TMPDIR"

    mk_run_or_fail \
        "${XSLTPROC}" \
        --xinclude \
        --output "fo.xml" \
        "$SHEET" \
        "in.xml"

    mk_mkdirname "$OUTPUT"

    mk_unquote_list "$FOP_PARAMS"

    mk_run_or_fail \
        "${FOP}" \
        -fo "fo.xml" \
        -pdf "$OUTPUT" \
        "$@"

    mk_cd_or_fail "$MK_ROOT_DIR"

    mk_pop_vars
}

_mk_docbook()
{
    mk_msg_domain "xsltproc"
    STAMP="$1"
    OUTPUT="$2/"
    SOURCE="$3"
    SHEET="$4"
    TMPDIR=".docbook$$"

    case "$SHEET" in
        /*)
            # Absolute path -- leave alone
            :
            ;;
        *)
            # Convert to absolute path
            SHEET="${MK_ROOT_DIR}/${SHEET}"
            ;;
    esac

    trap "cd \"$MK_ROOT_DIR\"; mk_safe_rm \"$TMPDIR\"" EXIT

    mk_mkdir "$TMPDIR"
    mk_run_or_fail cp "$SOURCE" "$TMPDIR/in.xml"

    mk_expand_pathnames "$5"
    mk_unquote_list "$result"

    for f
    do
        case "$f" in
            *'/'*)
                mk_mkdir "$TMPDIR/${f%/*}"
                ;;
        esac
        mk_resolve_file "$f"
        mk_run_or_fail cp "$result" "$TMPDIR/$f"
    done

    mk_msg "${OUTPUT#${MK_STAGE_DIR}}"
    mk_mkdir "${OUTPUT%/*}"
    mk_cd_or_fail "$TMPDIR"
    mk_run_or_fail \
        "${XSLTPROC}" \
        --nonet \
        --xinclude \
        --output "$MK_ROOT_DIR/$OUTPUT" \
        "$SHEET" \
        "in.xml"
    mk_cd_or_fail "$MK_ROOT_DIR"
    mk_mkdirname "$STAMP"
    mk_run_or_fail touch "$STAMP"
}
