/*
Copyright (c) 1989-1994
	The Regents of the University of California.  All rights reserved.
Copyright (c) 1997 Christos Zoulas.  All rights reserved.
Copyright (c) 1997-2005
	Herbert Xu <herbert@gondor.apana.org.au>.  All rights reserved.

This code is derived from software contributed to Berkeley by Kenneth Almquist.


Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. Neither the name of the University nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
*/
#define SMOOSH 1
#define SMALL 1
#define BSD 1
#define SHELL 1
#define IFS_BROKEN 1
#define _LARGEFILE64_SOURCE 1
#if defined(__linux__)
#define _GNU_SOURCE 1
#define HAVE_ALLOCA_H 1
#define HAVE_PATHS_H 1
#define HAVE_DECL_ISBLANK 1
#define HAVE_DECL_STRTOIMAX 1
#define HAVE_DECL_STRTOUMAX 1
#define HAVE_BSEARCH 1
#define HAVE_GETPWNAM 1
#define HAVE_GETRLIMIT 1
#define HAVE_ISALPHA 1
#define HAVE_KILLPG 1
#define HAVE_STPCPY 1
#define HAVE_STRSIGNAL 1
#define HAVE_STRTOD 1
#define HAVE_SYSCONF 1
#define HAVE_DECL_STAT64 0
#define HAVE_MEMPCPY 1
#elif defined(__FreeBSD__)
#define HAVE_PATHS_H 1
#define HAVE_DECL_ISBLANK 1
#define HAVE_DECL_STRTOIMAX 1
#define HAVE_DECL_STRTOUMAX 1
#define HAVE_BSEARCH 1
#define HAVE_GETPWNAM 1
#define HAVE_GETRLIMIT 1
#define HAVE_ISALPHA 1
#define HAVE_KILLPG 1
#define HAVE_STPCPY 1
#define HAVE_STRSIGNAL 1
#define HAVE_STRTOD 1
#define HAVE_SYSCONF 1
#define HAVE_DECL_STAT64 0
#elif defined(__sun)
#define HAVE_DECL_STRTOIMAX 0
#define HAVE_DECL_STRTOUMAX 0
#define HAVE_BSEARCH 1
#define HAVE_GETPWNAM 1
#define HAVE_GETRLIMIT 1
#define HAVE_ISALPHA 1
#define HAVE_KILLPG 1
#define HAVE_STRSIGNAL 1
#define HAVE_STRTOD 1
#define HAVE_SYSCONF 1
#define HAVE_DECL_STAT64 0
#include <ctype.h>
#ifdef isblank
#define HAVE_DECL_ISBLANK 1
#else
#define HAVE_DECL_ISBLANK 0
#endif
#elif defined(__APPLE__)
#define HAVE_ALLOCA_H 1
#define HAVE_PATHS_H 1
#define HAVE_DECL_ISBLANK 1
#define HAVE_DECL_STRTOIMAX 1
#define HAVE_DECL_STRTOUMAX 1
#define HAVE_BSEARCH 1
#define HAVE_GETPWNAM 1
#define HAVE_GETRLIMIT 1
#define HAVE_ISALPHA 1
#define HAVE_KILLPG 1
#define HAVE_STPCPY 1
#define HAVE_STRSIGNAL 1
#define HAVE_STRTOD 1
#define HAVE_SYSCONF 1
#define HAVE_DECL_STAT64 0
#elif defined(_AIX)
#define HAVE_ALLOCA_H 1
#define HAVE_PATHS_H 1
#define HAVE_DECL_ISBLANK 1
#define HAVE_DECL_STRTOIMAX 1
#define HAVE_DECL_STRTOUMAX 1
#define HAVE_BSEARCH 1
#define HAVE_GETPWNAM 1
#define HAVE_GETRLIMIT 1
#define HAVE_ISALPHA 1
#define HAVE_KILLPG 1
#define HAVE_STPCPY 1
#define HAVE_STRSIGNAL 1
#define HAVE_STRTOD 1
#define HAVE_SYSCONF 1
#define HAVE_DECL_STAT64 0
#elif defined(__hpux)
#define HAVE_ALLOCA_H 1
#define HAVE_DECL_ISBLANK 1
#define HAVE_DECL_STRTOIMAX 1
#define HAVE_DECL_STRTOUMAX 1
#define HAVE_BSEARCH 1
#define HAVE_GETPWNAM 1
#define HAVE_GETRLIMIT 1
#define HAVE_ISALPHA 1
#define HAVE_KILLPG 1
#define HAVE_STRTOD 1
#define HAVE_SYSCONF 1
#define HAVE_DECL_STAT64 0
#else
#error Unsupported platform
#endif
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#ifdef AT_EACCESS
#define HAVE_FACCESSAT 1
#endif
#if !HAVE_DECL_STAT64
#define fstat64 fstat
#define lstat64 lstat
#define stat64 stat
#define open64 open
#endif
#ifndef HAVE_PATHS_H
#define _PATH_BSHELL "/bin/sh"
#define _PATH_DEVNULL "/dev/null"
#define _PATH_TTY "/dev/tty"
#endif
#include <inttypes.h>
#include <stdlib.h>
#include <sys/param.h>
#ifndef JOBS
#define JOBS 1
#endif
#ifndef BSD
#define BSD 1
#endif
#ifndef DO_SHAREDVFORK
#if __NetBSD_Version__ >= 104000000
#define DO_SHAREDVFORK
#endif
#endif
typedef void *pointer;
#ifndef NULL
#define NULL (void *)0
#endif
#define STATIC static
#define MKINIT 
extern char nullstr[1]; 
#ifdef DEBUG
#define TRACE(param) trace param
#define TRACEV(param) tracev param
#else
#define TRACE(param)
#define TRACEV(param)
#endif
#if defined(__GNUC__) && __GNUC__ < 3
#define va_copy __va_copy
#endif
#if !defined(__GNUC__) || (__GNUC__ == 2 && __GNUC_MINOR__ < 96)
#define __builtin_expect(x, expected_value) (x)
#endif
#define likely(x) __builtin_expect(!!(x),1)
#define unlikely(x) __builtin_expect(!!(x),0)
static inline int max_int_length(int bytes)
{
return (bytes * 8 - 1) * 0.30102999566398119521 + 14;
}
#define ALIASCMD (builtincmd + 4)
#define BGCMD (builtincmd + 5)
#define BREAKCMD (builtincmd + 6)
#define CDCMD (builtincmd + 7)
#define COMMANDCMD (builtincmd + 9)
#define DOTCMD (builtincmd + 0)
#define ECHOCMD (builtincmd + 11)
#define EVALCMD (builtincmd + 12)
#define EXECCMD (builtincmd + 13)
#define EXITCMD (builtincmd + 14)
#define EXPORTCMD (builtincmd + 15)
#define FALSECMD (builtincmd + 16)
#define FGCMD (builtincmd + 17)
#define GETOPTSCMD (builtincmd + 18)
#define HASHCMD (builtincmd + 19)
#define JOBSCMD (builtincmd + 20)
#define KILLCMD (builtincmd + 21)
#define LOCALCMD (builtincmd + 22)
#define MK_PARSE_PARAMSCMD (builtincmd + 23)
#define MK_PUSH_VARSCMD (builtincmd + 3)
#define MK_QUOTE_SPACECMD (builtincmd + 26)
#define MK_QUOTECMD (builtincmd + 24)
#define PRINTFCMD (builtincmd + 28)
#define PWDCMD (builtincmd + 29)
#define READCMD (builtincmd + 30)
#define RETURNCMD (builtincmd + 32)
#define SETCMD (builtincmd + 33)
#define SHIFTCMD (builtincmd + 34)
#define TESTCMD (builtincmd + 2)
#define TIMESCMD (builtincmd + 36)
#define TRAPCMD (builtincmd + 37)
#define TRUECMD (builtincmd + 1)
#define TYPECMD (builtincmd + 39)
#define ULIMITCMD (builtincmd + 40)
#define UMASKCMD (builtincmd + 41)
#define UNALIASCMD (builtincmd + 42)
#define UNSETCMD (builtincmd + 43)
#define WAITCMD (builtincmd + 44)
#define NUMBUILTINS 45
#define BUILTIN_SPECIAL 0x1
#define BUILTIN_REGULAR 0x2
#define BUILTIN_ASSIGN 0x4
struct builtincmd {
const char *name;
int (*builtin)(int, char **);
unsigned flags;
};
extern const struct builtincmd builtincmd[];
#define NCMD 0
#define NPIPE 1
#define NREDIR 2
#define NBACKGND 3
#define NSUBSHELL 4
#define NAND 5
#define NOR 6
#define NSEMI 7
#define NIF 8
#define NWHILE 9
#define NUNTIL 10
#define NFOR 11
#define NCASE 12
#define NCLIST 13
#define NDEFUN 14
#define NARG 15
#define NTO 16
#define NCLOBBER 17
#define NFROM 18
#define NFROMTO 19
#define NAPPEND 20
#define NTOFD 21
#define NFROMFD 22
#define NHERE 23
#define NXHERE 24
#define NNOT 25
struct ncmd {
int type;
int linno;
union node *assign;
union node *args;
union node *redirect;
};
struct npipe {
int type;
int backgnd;
struct nodelist *cmdlist;
};
struct nredir {
int type;
int linno;
union node *n;
union node *redirect;
};
struct nbinary {
int type;
union node *ch1;
union node *ch2;
};
struct nif {
int type;
union node *test;
union node *ifpart;
union node *elsepart;
};
struct nfor {
int type;
int linno;
union node *args;
union node *body;
char *var;
};
struct ncase {
int type;
int linno;
union node *expr;
union node *cases;
};
struct nclist {
int type;
union node *next;
union node *pattern;
union node *body;
};
struct ndefun {
int type;
int linno;
char *text;
union node *body;
};
struct narg {
int type;
union node *next;
char *text;
struct nodelist *backquote;
};
struct nfile {
int type;
union node *next;
int fd;
union node *fname;
char *expfname;
};
struct ndup {
int type;
union node *next;
int fd;
int dupfd;
union node *vname;
};
struct nhere {
int type;
union node *next;
int fd;
union node *doc;
};
struct nnot {
int type;
union node *com;
};
union node {
int type;
struct ncmd ncmd;
struct npipe npipe;
struct nredir nredir;
struct nbinary nbinary;
struct nif nif;
struct nfor nfor;
struct ncase ncase;
struct nclist nclist;
struct ndefun ndefun;
struct narg narg;
struct nfile nfile;
struct ndup ndup;
struct nhere nhere;
struct nnot nnot;
};
struct nodelist {
struct nodelist *next;
union node *n;
};
struct funcnode {
int count;
union node n;
};
struct funcnode *copyfunc(union node *);
void freefunc(struct funcnode *);
#include <ctype.h>
#define CWORD 0 
#define CNL 1 
#define CBACK 2 
#define CSQUOTE 3 
#define CDQUOTE 4 
#define CENDQUOTE 5 
#define CBQUOTE 6 
#define CVAR 7 
#define CENDVAR 8 
#define CLP 9 
#define CRP 10 
#define CEOS 11 
#define CCTL 12 
#define CSPCL 13 
#define CIGN 14 
#define ISDIGIT 01 
#define ISUPPER 02 
#define ISLOWER 04 
#define ISUNDER 010 
#define ISSPECL 020 
#define SYNBASE 130
#define PEOF -130
#define PEOA -129
#define BASESYNTAX (basesyntax + SYNBASE)
#define DQSYNTAX (dqsyntax + SYNBASE)
#define SQSYNTAX (sqsyntax + SYNBASE)
#define ARISYNTAX (arisyntax + SYNBASE)
#define is_digit(c) ((unsigned)((c) - '0') <= 9)
#define is_alpha(c) isalpha((unsigned char)(c))
#define is_name(c) ((c) == '_' || isalpha((unsigned char)(c)))
#define is_in_name(c) ((c) == '_' || isalnum((unsigned char)(c)))
#define is_special(c) ((is_type+SYNBASE)[(signed char)(c)] & (ISSPECL|ISDIGIT))
#define digit_val(c) ((c) - '0')
extern const char basesyntax[];
extern const char dqsyntax[];
extern const char sqsyntax[];
extern const char arisyntax[];
extern const char is_type[];
#define TEOF 0
#define TNL 1
#define TSEMI 2
#define TBACKGND 3
#define TAND 4
#define TOR 5
#define TPIPE 6
#define TLP 7
#define TRP 8
#define TENDCASE 9
#define TENDBQUOTE 10
#define TREDIR 11
#define TWORD 12
#define TNOT 13
#define TCASE 14
#define TDO 15
#define TDONE 16
#define TELIF 17
#define TELSE 18
#define TESAC 19
#define TFI 20
#define TFOR 21
#define TIF 22
#define TIN 23
#define TTHEN 24
#define TUNTIL 25
#define TWHILE 26
#define TBEGIN 27
#define TEND 28
static const char tokendlist[] = {
1,
0,
0,
0,
0,
0,
0,
0,
1,
1,
1,
0,
0,
0,
0,
1,
1,
1,
1,
1,
1,
0,
0,
0,
1,
0,
0,
0,
1,
};
static const char *const tokname[] = {
"end of file",
"newline",
"\";\"",
"\"&\"",
"\"&&\"",
"\"||\"",
"\"|\"",
"\"(\"",
"\")\"",
"\";;\"",
"\"`\"",
"redirection",
"word",
"\"!\"",
"\"case\"",
"\"do\"",
"\"done\"",
"\"elif\"",
"\"else\"",
"\"esac\"",
"\"fi\"",
"\"for\"",
"\"if\"",
"\"in\"",
"\"then\"",
"\"until\"",
"\"while\"",
"\"{\"",
"\"}\"",
};
#define KWDOFFSET 13
static const char *const parsekwd[] = {
"!",
"case",
"do",
"done",
"elif",
"else",
"esac",
"fi",
"for",
"if",
"in",
"then",
"until",
"while",
"{",
"}"
};
#define ALIASINUSE 1
#define ALIASDEAD 2
struct alias {
struct alias *next;
char *name;
char *val;
int flag;
};
struct alias *lookupalias(const char *, int);
int aliascmd(int, char **);
int unaliascmd(int, char **);
void rmaliases(void);
int unalias(const char *);
void printalias(const struct alias *);
#define ARITH_ASS 1
#define ARITH_OR 2
#define ARITH_AND 3
#define ARITH_BAD 4
#define ARITH_NUM 5
#define ARITH_VAR 6
#define ARITH_NOT 7
#define ARITH_BINOP_MIN 8
#define ARITH_LE 8
#define ARITH_GE 9
#define ARITH_LT 10
#define ARITH_GT 11
#define ARITH_EQ 12
#define ARITH_REM 13
#define ARITH_BAND 14
#define ARITH_LSHIFT 15
#define ARITH_RSHIFT 16
#define ARITH_MUL 17
#define ARITH_ADD 18
#define ARITH_BOR 19
#define ARITH_SUB 20
#define ARITH_BXOR 21
#define ARITH_DIV 22
#define ARITH_NE 23
#define ARITH_BINOP_MAX 24
#define ARITH_ASS_MIN 24
#define ARITH_REMASS 24
#define ARITH_BANDASS 25
#define ARITH_LSHIFTASS 26
#define ARITH_RSHIFTASS 27
#define ARITH_MULASS 28
#define ARITH_ADDASS 29
#define ARITH_BORASS 30
#define ARITH_SUBASS 31
#define ARITH_BXORASS 32
#define ARITH_DIVASS 33
#define ARITH_ASS_MAX 34
#define ARITH_LPAREN 34
#define ARITH_RPAREN 35
#define ARITH_BNOT 36
#define ARITH_QMARK 37
#define ARITH_COLON 38
union yystype {
intmax_t val;
char *name;
};
extern union yystype yylval;
int yylex(void);
int cdcmd(int, char **);
int pwdcmd(int, char **);
void setpwd(const char *, int);
#include <setjmp.h>
#include <signal.h>
#define E_OPEN 01 
#define E_CREAT 02 
#define E_EXEC 04 
struct jmploc {
jmp_buf loc;
};
extern struct jmploc *handler;
extern int exception;
#define EXINT 0 
#define EXERROR 1 
#define EXEXIT 4 
extern int suppressint;
extern volatile sig_atomic_t intpending;
#define barrier() ({ __asm__ __volatile__ ("": : :"memory"); })
#define INTOFF \
({ \
suppressint++; \
barrier(); \
0; \
})
#ifdef REALLY_SMALL
void __inton(void);
#define INTON __inton()
#else
#define INTON \
({ \
barrier(); \
if (--suppressint == 0 && intpending) onint(); \
0; \
})
#endif
#define FORCEINTON \
({ \
barrier(); \
suppressint = 0; \
if (intpending) onint(); \
0; \
})
#define SAVEINT(v) ((v) = suppressint)
#define RESTOREINT(v) \
({ \
barrier(); \
if ((suppressint = (v)) == 0 && intpending) onint(); \
0; \
})
#define CLEAR_PENDING_INT intpending = 0
#define int_pending() intpending
void exraise(int) __attribute__((__noreturn__));
#ifdef USE_NORETURN
void onint(void) __attribute__((__noreturn__));
#else
void onint(void);
#endif
extern int errlinno;
void sh_error(const char *, ...) __attribute__((__noreturn__));
void exerror(int, const char *, ...) __attribute__((__noreturn__));
const char *errmsg(int, int);
void sh_warnx(const char *, ...);
extern char *commandname; 
extern int exitstatus; 
extern int back_exitstatus; 
struct backcmd { 
int fd; 
char *buf; 
int nleft; 
struct job *jp; 
};
#define EV_EXIT 01 
#define EV_TESTED 02 
int evalstring(char *, int);
union node; 
void evaltree(union node *, int);
void evalbackcmd(union node *, struct backcmd *);
extern int evalskip;
#define SKIPBREAK (1 << 0)
#define SKIPCONT (1 << 1)
#define SKIPFUNC (1 << 2)
#define CMDUNKNOWN -1 
#define CMDNORMAL 0 
#define CMDFUNCTION 1 
#define CMDBUILTIN 2 
struct cmdentry {
int cmdtype;
union param {
int index;
const struct builtincmd *cmd;
struct funcnode *func;
} u;
};
#define DO_ERR 0x01 
#define DO_ABS 0x02 
#define DO_NOFUNC 0x04 
#define DO_ALTPATH 0x08 
#define DO_ALTBLTIN 0x20 
extern const char *pathopt; 
void shellexec(char **, const char *, int)
__attribute__((__noreturn__));
char *padvance(const char **, const char *);
int hashcmd(int, char **);
void find_command(char *, struct cmdentry *, int, const char *);
struct builtincmd *find_builtin(const char *);
void hashcd(void);
void changepath(const char *);
#ifdef notdef
void getcmdentry(char *, struct cmdentry *);
#endif
void defun(union node *);
void unsetfunc(const char *);
int typecmd(int, char **);
int commandcmd(int, char **);
#include <inttypes.h>
struct strlist {
struct strlist *next;
char *text;
};
struct arglist {
struct strlist *list;
struct strlist **lastp;
};
#define EXP_FULL 0x1 
#define EXP_TILDE 0x2 
#define EXP_VARTILDE 0x4 
#define EXP_REDIR 0x8 
#define EXP_CASE 0x10 
#define EXP_QPAT 0x20 
#define EXP_VARTILDE2 0x40 
#define EXP_WORD 0x80 
#define EXP_QUOTED 0x100 
union node;
void expandarg(union node *, struct arglist *, int);
void expari(int);
#define rmescapes(p) _rmescapes((p), 0)
char *_rmescapes(char *, int);
int casematch(union node *, char *);
void recordregion(int, int, int);
void removerecordregions(int); 
void ifsbreakup(char *, struct arglist *);
void ifsfree(void);
intmax_t arith(const char *);
int expcmd(int , char **);
#ifdef USE_LEX
void arith_lex_reset(void);
#else
#define arith_lex_reset()
#endif
int yylex(void);
void hetio_init(void);
int hetio_read_input(int fd);
void hetio_reset_term(void);
extern int hetio_inter;
void init(void);
void reset(void);
void initshellproc(void);
enum {
INPUT_PUSH_FILE = 1,
INPUT_NOFILE_OK = 2,
};
extern int plinno;
extern int parsenleft; 
extern char *parsenextc; 
int pgetc(void);
int pgetc2(void);
int preadbuffer(void);
void pungetc(void);
void pushstring(char *, void *);
void popstring(void);
int setinputfile(const char *, int);
void setinputstring(char *);
void popfile(void);
void popallfiles(void);
void closescript(void);
#define pgetc_macro() \
(--parsenleft >= 0 ? (signed char)*parsenextc++ : preadbuffer())
#include <inttypes.h>
#include <sys/types.h>
#define FORK_FG 0
#define FORK_BG 1
#define FORK_NOJOB 2
#define SHOW_PGID 0x01 
#define SHOW_PID 0x04 
#define SHOW_CHANGED 0x08 
struct procstat {
pid_t pid; 
int status; 
char *cmd; 
};
struct job {
struct procstat ps0; 
struct procstat *ps; 
#if JOBS
int stopstatus; 
#endif
uint32_t
nprocs: 16, 
state: 8,
#define JOBRUNNING 0 
#define JOBSTOPPED 1 
#define JOBDONE 2 
#if JOBS
sigint: 1, 
jobctl: 1, 
#endif
waited: 1, 
used: 1, 
changed: 1; 
struct job *prev_job; 
};
extern pid_t backgndpid; 
extern int job_warning; 
#if JOBS
extern int jobctl; 
#else
#define jobctl 0
#endif
void setjobctl(int);
int killcmd(int, char **);
int fgcmd(int, char **);
int bgcmd(int, char **);
int jobscmd(int, char **);
struct output;
void showjobs(struct output *, int);
int waitcmd(int, char **);
struct job *makejob(union node *, int);
int forkshell(struct job *, union node *, int);
int waitforjob(struct job *);
int stoppedjobs(void);
#if ! JOBS
#define setjobctl(on) ((void)(on)) 
#endif
#define SHELL_SIZE (sizeof(union {int i; char *cp; double d; }) - 1)
#define SHELL_ALIGN(nbytes) (((nbytes) + SHELL_SIZE) & ~SHELL_SIZE)
void chkmail(void);
void changemail(const char *);
#include <errno.h>
extern int rootpid;
extern int shlvl;
#define rootshell (!shlvl)
#ifdef __GLIBC__
extern int *dash_errno;
#undef errno
#define errno (*dash_errno)
#endif
void readcmdfile(char *);
int dotcmd(int, char **);
int exitcmd(int, char **);
#include <stddef.h>
struct stackmark {
struct stack_block *stackp;
char *stacknxt;
size_t stacknleft;
};
extern char *stacknxt;
extern size_t stacknleft;
extern char *sstrend;
pointer ckmalloc(size_t);
pointer ckrealloc(pointer, size_t);
char *savestr(const char *);
pointer stalloc(size_t);
void stunalloc(pointer);
void pushstackmark(struct stackmark *mark, size_t len);
void setstackmark(struct stackmark *);
void popstackmark(struct stackmark *);
void growstackblock(void);
void *growstackstr(void);
char *makestrspace(size_t, char *);
char *stnputs(const char *, size_t, char *);
char *stputs(const char *, char *);
static inline void grabstackblock(size_t len)
{
stalloc(len);
}
static inline char *_STPUTC(int c, char *p) {
if (p == sstrend)
p = growstackstr();
*p++ = c;
return p;
}
#define stackblock() ((void *)stacknxt)
#define stackblocksize() stacknleft
#define STARTSTACKSTR(p) ((p) = stackblock())
#define STPUTC(c, p) ((p) = _STPUTC((c), (p)))
#define CHECKSTRSPACE(n, p) \
({ \
char *q = (p); \
size_t l = (n); \
size_t m = sstrend - q; \
if (l > m) \
(p) = makestrspace(l, q); \
0; \
})
#define USTPUTC(c, p) (*p++ = (c))
#define STACKSTRNUL(p) ((p) == sstrend? (p = growstackstr(), *p = '\0') : (*p = '\0'))
#define STUNPUTC(p) (--p)
#define STTOPC(p) p[-1]
#define STADJUST(amount, p) (p += (amount))
#define grabstackstr(p) stalloc((char *)(p) - (char *)stackblock())
#define ungrabstackstr(s, p) stunalloc((s))
#define stackstrend() ((void *)sstrend)
#define ckfree(p) free((pointer)(p))
int readcmd(int, char **);
int umaskcmd(int, char **);
int ulimitcmd(int, char **);
#include <inttypes.h>
#include <string.h>
extern const char snlfmt[];
extern const char spcstr[];
extern const char dolatstr[];
#define DOLATSTRLEN 6
extern const char qchars[];
extern const char illnum[];
extern const char homestr[];
#if 0
void scopyn(const char *, char *, int);
#endif
char *prefix(const char *, const char *);
void badnum(const char *s) __attribute__ ((noreturn));
intmax_t atomax(const char *, int);
intmax_t atomax10(const char *);
int number(const char *);
int is_number(const char *);
char *single_quote(const char *);
char *sstrdup(const char *);
int pstrcmp(const void *, const void *);
const char *const *findstring(const char *, const char *const *, size_t);
#define equal(s1, s2) (strcmp(s1, s2) == 0)
#define scopy(s1, s2) ((void)strcpy(s2, s1))
struct shparam {
int nparam; 
unsigned char malloc; 
char **p; 
int optind; 
int optoff; 
};
#define eflag optlist[0]
#define fflag optlist[1]
#define Iflag optlist[2]
#define iflag optlist[3]
#define mflag optlist[4]
#define nflag optlist[5]
#define sflag optlist[6]
#define xflag optlist[7]
#define vflag optlist[8]
#define Vflag optlist[9]
#define Eflag optlist[10]
#define Cflag optlist[11]
#define aflag optlist[12]
#define bflag optlist[13]
#define uflag optlist[14]
#define nolog optlist[15]
#define debug optlist[16]
#define NOPTS 17
extern const char optletters[NOPTS];
extern char optlist[NOPTS];
extern char *minusc; 
extern char *arg0; 
extern struct shparam shellparam; 
extern char **argptr; 
extern char *optionarg; 
extern char *optptr; 
int procargs(int, char **);
void optschanged(void);
void setparam(char **);
void freeparam(volatile struct shparam *);
int shiftcmd(int, char **);
int setcmd(int, char **);
int getoptscmd(int, char **);
int nextopt(const char *);
void getoptsreset(const char *);
#ifndef OUTPUT_INCL
#include <stdarg.h>
#ifdef USE_GLIBC_STDIO
#include <stdio.h>
#endif
#include <sys/types.h>
struct output {
#ifdef USE_GLIBC_STDIO
FILE *stream;
#endif
char *nextc;
char *end;
char *buf;
size_t bufsize;
int fd;
int flags;
};
extern struct output output;
extern struct output errout;
extern struct output preverrout;
#ifdef notyet
extern struct output memout;
#endif
extern struct output *out1;
extern struct output *out2;
void outstr(const char *, struct output *);
#ifndef USE_GLIBC_STDIO
void outcslow(int, struct output *);
#endif
void flushall(void);
void flushout(struct output *);
void outfmt(struct output *, const char *, ...)
__attribute__((__format__(__printf__,2,3)));
void out1fmt(const char *, ...)
__attribute__((__format__(__printf__,1,2)));
int fmtstr(char *, size_t, const char *, ...)
__attribute__((__format__(__printf__,3,4)));
#ifndef USE_GLIBC_STDIO
void doformat(struct output *, const char *, va_list);
#endif
int xwrite(int, const void *, size_t);
#ifdef notyet
#ifdef USE_GLIBC_STDIO
void initstreams(void);
void openmemout(void);
int __closememout(void);
#endif
#endif
static inline void
freestdout()
{
output.nextc = output.buf;
output.flags = 0;
}
#define OUTPUT_ERR 01 
#ifdef USE_GLIBC_STDIO
static inline void outc(int ch, struct output *file)
{
putc(ch, file->stream);
}
#define doformat(d, f, a) vfprintf((d)->stream, (f), (a))
#else
static inline void outc(int ch, struct output *file)
{
if (file->nextc == file->end)
outcslow(ch, file);
else {
*file->nextc = ch;
file->nextc++;
}
}
#endif
#define out1c(c) outc((c), out1)
#define out2c(c) outcslow((c), out2)
#define out1str(s) outstr((s), out1)
#define out2str(s) outstr((s), out2)
#define outerr(f) (f)->flags
#define OUTPUT_INCL
#endif
#define CTL_FIRST -127 
#define CTLESC -127 
#define CTLVAR -126 
#define CTLENDVAR -125
#define CTLBACKQ -124
#define CTLARI -122 
#define CTLENDARI -121
#define CTLQUOTEMARK -120
#define CTL_LAST -120 
#define VSTYPE 0x0f 
#define VSNUL 0x10 
#define VSNORMAL 0x1 
#define VSMINUS 0x2 
#define VSPLUS 0x3 
#define VSQUESTION 0x4 
#define VSASSIGN 0x5 
#define VSTRIMRIGHT 0x6 
#define VSTRIMRIGHTMAX 0x7 
#define VSTRIMLEFT 0x8 
#define VSTRIMLEFTMAX 0x9 
#define VSLENGTH 0xa 
#define CHKALIAS 0x1
#define CHKKWD 0x2
#define CHKNL 0x4
#define CHKEOFMARK 0x8
extern int lasttoken;
extern int tokpushback;
#define NEOF ((union node *)&tokpushback)
extern int whichprompt; 
extern int checkkwd;
union node *parsecmd(int);
void fixredir(union node *, const char *, int);
const char *getprompt(void *);
const char *const *findkwd(const char *);
char *endofname(const char *);
const char *expandstr(const char *);
static inline int
goodname(const char *p)
{
return !*endofname(p);
}
static inline int parser_eof(void)
{
return tokpushback && lasttoken == TEOF;
}
#define REDIR_PUSH 01 
#ifdef notyet
#define REDIR_BACKQ 02 
#endif
#define REDIR_SAVEFD2 03 
struct redirtab;
union node;
void redirect(union node *, int);
void popredir(int);
void clearredir(void);
int savefd(int, int);
int redirectsafe(union node *, int);
void unwindredir(struct redirtab *stop);
struct redirtab *pushredir(union node *redir);
#include <stdarg.h>
#ifdef DEBUG
union node;
void showtree(union node *);
void trace(const char *, ...);
void tracev(const char *, va_list);
void trargs(char **);
void trputc(int);
void trputs(const char *);
void opentrace(void);
#endif
#include <limits.h>
#include <signal.h>
#include <sys/types.h>
#ifndef SSIZE_MAX
#define SSIZE_MAX ((ssize_t)((size_t)-1 >> 1))
#endif
static inline void sigclearmask(void)
{
#ifdef HAVE_SIGSETMASK
sigsetmask(0);
#else
sigset_t set;
sigemptyset(&set);
sigprocmask(SIG_SETMASK, &set, 0);
#endif
}
#ifndef HAVE_MEMPCPY
void *mempcpy(void *, const void *, size_t);
#endif
#ifndef HAVE_STPCPY
char *stpcpy(char *, const char *);
#endif
#ifndef HAVE_STRCHRNUL
char *strchrnul(const char *, int);
#endif
#ifndef HAVE_STRSIGNAL
char *strsignal(int);
#endif
#ifndef HAVE_STRTOD
static inline double strtod(const char *nptr, char **endptr)
{
*endptr = (char *)nptr;
return 0;
}
#endif
#if !HAVE_DECL_STRTOIMAX
#define strtoimax strtoll
#endif
#if !HAVE_DECL_STRTOUMAX
#define strtoumax strtoull
#endif
#ifndef HAVE_BSEARCH
void *bsearch(const void *, const void *, size_t, size_t,
int (*)(const void *, const void *));
#endif
#ifndef HAVE_KILLPG
static inline int killpg(pid_t pid, int signal)
{
#ifdef DEBUG
if (pid < 0)
abort();
#endif
return kill(-pid, signal);
}
#endif
#ifndef HAVE_SYSCONF
#define _SC_CLK_TCK 2
long sysconf(int) __attribute__((__noreturn__));
#endif
#if !HAVE_DECL_ISBLANK
int isblank(int c);
#endif
#define uninitialized_var(x) x = x
#include <signal.h>
extern int trapcnt;
extern char sigmode[];
extern volatile sig_atomic_t pendingsigs;
extern int gotsigchld;
int trapcmd(int, char **);
void clear_traps(void);
void setsignal(int);
void ignoresig(int);
void onsig(int);
void dotrap(void);
void setinteractive(int);
void exitshell(void) __attribute__((__noreturn__));
int decode_signal(const char *, int);
static inline int have_traps(void)
{
return trapcnt;
}
#include <inttypes.h>
#define VEXPORT 0x01 
#define VREADONLY 0x02 
#define VSTRFIXED 0x04 
#define VTEXTFIXED 0x08 
#define VSTACK 0x10 
#define VUNSET 0x20 
#define VNOFUNC 0x40 
#define VNOSET 0x80 
#define VNOSAVE 0x100 
struct var {
struct var *next; 
int flags; 
const char *text; 
void (*func)(const char *);
};
struct localvar {
struct localvar *next; 
struct var *vp; 
int flags; 
const char *text; 
};
struct localvar_list;
extern struct localvar *localvars;
extern struct var varinit[];
#if ATTY
#define vatty varinit[0]
#define vifs varinit[1]
#else
#define vifs varinit[0]
#endif
#define vmail (&vifs)[1]
#define vmpath (&vmail)[1]
#define vpath (&vmpath)[1]
#define vps1 (&vpath)[1]
#define vps2 (&vps1)[1]
#define vps4 (&vps2)[1]
#define voptind (&vps4)[1]
#define vlineno (&voptind)[1]
#ifndef SMALL
#define vterm (&vlineno)[1]
#define vhistsize (&vterm)[1]
#endif
#ifdef IFS_BROKEN
extern const char defifsvar[];
#define defifs (defifsvar + 4)
#else
extern const char defifs[];
#endif
extern const char defpathvar[];
#define defpath (defpathvar + 5)
extern int lineno;
extern char linenovar[];
#define ifsval() (vifs.text + 4)
#define ifsset() ((vifs.flags & VUNSET) == 0)
#define mailval() (vmail.text + 5)
#define mpathval() (vmpath.text + 9)
#define pathval() (vpath.text + 5)
#define ps1val() (vps1.text + 4)
#define ps2val() (vps2.text + 4)
#define ps4val() (vps4.text + 4)
#define optindval() (voptind.text + 7)
#define linenoval() (vlineno.text + 7)
#ifndef SMALL
#define histsizeval() (vhistsize.text + 9)
#define termval() (vterm.text + 5)
#endif
#if ATTY
#define attyset() ((vatty.flags & VUNSET) == 0)
#endif
#define mpathset() ((vmpath.flags & VUNSET) == 0)
void initvar(void);
struct var *setvar(const char *name, const char *val, int flags);
intmax_t setvarint(const char *, intmax_t, int);
struct var *setvareq(char *s, int flags);
struct strlist;
void listsetvar(struct strlist *, int);
char *lookupvar(const char *);
intmax_t lookupvarint(const char *);
char **listvars(int, int, char ***);
#define environment() listvars(VEXPORT, VUNSET, 0)
int showvars(const char *, int, int);
int exportcmd(int, char **);
int localcmd(int, char **);
void mklocal(char *);
struct localvar_list *pushlocalvars(void);
void poplocalvars(int);
void unwindlocalvars(struct localvar_list *stop);
int unsetcmd(int, char **);
void unsetvar(const char *);
int varcmp(const char *, const char *);
static inline int varequal(const char *a, const char *b) {
return !varcmp(a, b);
}
static inline char *bltinlookup(const char *name)
{
return lookupvar(name);
}
#ifdef SHELL
#ifndef USE_GLIBC_STDIO
#define blt_stdout out1
#define blt_stderr out2
#define blt_printf out1fmt
#define blt_putc(c, file) outc(c, file)
#define blt_putchar(c) out1c(c)
#define BLT_FILE struct output
#define blt_fprintf outfmt
#define blt_fputs outstr
#define blt_fflush flushout
#define blt_fileno(f) ((f)->fd)
#define blt_ferror outerr
#else
#define blt_stdout stdout
#define blt_stderr stderr
#define blt_printf printf
#define blt_putc(c, file) putc(c, file)
#define blt_putchar(c) putchar(c)
#define BLT_FILE FILE
#define blt_fprintf fprintf
#define blt_fputs fputs
#define blt_fflush fflush
#define blt_fileno(f) fileno(f)
#define blt_ferror ferror
#endif
#define INITARGS(argv)
#define error sh_error
#define warn sh_warn
#define warnx sh_warnx
#define exit sh_exit
#define setprogname(s)
#define getprogname() commandname
#define setlocate(l,s) 0
#define blt_getenv(p) bltinlookup((p),0)
#else
#undef NULL
#include <stdio.h>
#undef main
#define INITARGS(argv) if ((commandname = argv[0]) == NULL) {fputs("Argc is zero\n", stderr); exit(2);} else
#endif
int echocmd(int, char **);
extern char *commandname;
#include <stdlib.h>
#define ATABSIZE 39
struct alias *atab[ATABSIZE];
STATIC void setalias(const char *, const char *);
STATIC struct alias *freealias(struct alias *);
STATIC struct alias **__lookupalias(const char *);
STATIC
void
setalias(const char *name, const char *val)
{
struct alias *ap, **app;
app = __lookupalias(name);
ap = *app;
INTOFF;
if (ap) {
if (!(ap->flag & ALIASINUSE)) {
ckfree(ap->val);
}
ap->val = savestr(val);
ap->flag &= ~ALIASDEAD;
} else {
ap = ckmalloc(sizeof (struct alias));
ap->name = savestr(name);
ap->val = savestr(val);
ap->flag = 0;
ap->next = 0;
*app = ap;
}
INTON;
}
int
unalias(const char *name)
{
struct alias **app;
app = __lookupalias(name);
if (*app) {
INTOFF;
*app = freealias(*app);
INTON;
return (0);
}
return (1);
}
void
rmaliases(void)
{
struct alias *ap, **app;
int i;
INTOFF;
for (i = 0; i < ATABSIZE; i++) {
app = &atab[i];
for (ap = *app; ap; ap = *app) {
*app = freealias(*app);
if (ap == *app) {
app = &ap->next;
}
}
}
INTON;
}
struct alias *
lookupalias(const char *name, int check)
{
struct alias *ap = *__lookupalias(name);
if (check && ap && (ap->flag & ALIASINUSE))
return (NULL);
return (ap);
}
int
aliascmd(int argc, char **argv)
{
char *n, *v;
int ret = 0;
struct alias *ap;
if (argc == 1) {
int i;
for (i = 0; i < ATABSIZE; i++)
for (ap = atab[i]; ap; ap = ap->next) {
printalias(ap);
}
return (0);
}
while ((n = *++argv) != NULL) {
if ((v = strchr(n+1, '=')) == NULL) { 
if ((ap = *__lookupalias(n)) == NULL) {
outfmt(out2, "%s: %s not found\n", "alias", n);
ret = 1;
} else
printalias(ap);
} else {
*v++ = '\0';
setalias(n, v);
}
}
return (ret);
}
int
unaliascmd(int argc, char **argv)
{
int i;
while ((i = nextopt("a")) != '\0') {
if (i == 'a') {
rmaliases();
return (0);
}
}
for (i = 0; *argptr; argptr++) {
if (unalias(*argptr)) {
outfmt(out2, "%s: %s not found\n", "unalias", *argptr);
i = 1;
}
}
return (i);
}
STATIC struct alias *
freealias(struct alias *ap) {
struct alias *next;
if (ap->flag & ALIASINUSE) {
ap->flag |= ALIASDEAD;
return ap;
}
next = ap->next;
ckfree(ap->name);
ckfree(ap->val);
ckfree(ap);
return next;
}
void
printalias(const struct alias *ap) {
out1fmt("%s=%s\n", ap->name, single_quote(ap->val));
}
STATIC struct alias **
__lookupalias(const char *name) {
unsigned int hashval;
struct alias **app;
const char *p;
unsigned int ch;
p = name;
ch = (unsigned char)*p;
hashval = ch << 4;
while (ch) {
hashval += ch;
ch = (unsigned char)*++p;
}
app = &atab[hashval % ATABSIZE];
for (; *app; app = &(*app)->next) {
if (equal(name, (*app)->name)) {
break;
}
}
return app;
}
#include <inttypes.h>
#include <stdlib.h>
#if ARITH_BOR + 11 != ARITH_BORASS || ARITH_ASS + 11 != ARITH_EQ
#error Arithmetic tokens are out of order.
#endif
static const char *arith_startbuf;
const char *arith_buf;
union yystype yylval;
static int last_token;
#define ARITH_PRECEDENCE(op, prec) [op - ARITH_BINOP_MIN] = prec
static const char prec[ARITH_BINOP_MAX - ARITH_BINOP_MIN] = {
ARITH_PRECEDENCE(ARITH_MUL, 0),
ARITH_PRECEDENCE(ARITH_DIV, 0),
ARITH_PRECEDENCE(ARITH_REM, 0),
ARITH_PRECEDENCE(ARITH_ADD, 1),
ARITH_PRECEDENCE(ARITH_SUB, 1),
ARITH_PRECEDENCE(ARITH_LSHIFT, 2),
ARITH_PRECEDENCE(ARITH_RSHIFT, 2),
ARITH_PRECEDENCE(ARITH_LT, 3),
ARITH_PRECEDENCE(ARITH_LE, 3),
ARITH_PRECEDENCE(ARITH_GT, 3),
ARITH_PRECEDENCE(ARITH_GE, 3),
ARITH_PRECEDENCE(ARITH_EQ, 4),
ARITH_PRECEDENCE(ARITH_NE, 4),
ARITH_PRECEDENCE(ARITH_BAND, 5),
ARITH_PRECEDENCE(ARITH_BXOR, 6),
ARITH_PRECEDENCE(ARITH_BOR, 7),
};
#define ARITH_MAX_PREC 8
static void yyerror(const char *s) __attribute__ ((noreturn));
static void yyerror(const char *s)
{
sh_error("arithmetic expression: %s: \"%s\"", s, arith_startbuf);
}
static inline int arith_prec(int op)
{
return prec[op - ARITH_BINOP_MIN];
}
static inline int higher_prec(int op1, int op2)
{
return arith_prec(op1) < arith_prec(op2);
}
static intmax_t do_binop(int op, intmax_t a, intmax_t b)
{
#ifdef HAVE_IMAXDIV
imaxdiv_t div;
#endif
switch (op) {
default:
case ARITH_REM:
case ARITH_DIV:
if (!b)
yyerror("division by zero");
#ifdef HAVE_IMAXDIV
div = imaxdiv(a, b);
return op == ARITH_REM ? div.rem : div.quot;
#else
return op == ARITH_REM ? a % b : a / b;
#endif
case ARITH_MUL:
return a * b;
case ARITH_ADD:
return a + b;
case ARITH_SUB:
return a - b;
case ARITH_LSHIFT:
return a << b;
case ARITH_RSHIFT:
return a >> b;
case ARITH_LT:
return a < b;
case ARITH_LE:
return a <= b;
case ARITH_GT:
return a > b;
case ARITH_GE:
return a >= b;
case ARITH_EQ:
return a == b;
case ARITH_NE:
return a != b;
case ARITH_BAND:
return a & b;
case ARITH_BXOR:
return a ^ b;
case ARITH_BOR:
return a | b;
}
}
static intmax_t assignment(int var, int noeval);
static intmax_t primary(int token, union yystype *val, int op, int noeval)
{
intmax_t result;
again:
switch (token) {
case ARITH_LPAREN:
result = assignment(op, noeval);
if (last_token != ARITH_RPAREN)
yyerror("expecting ')'");
last_token = yylex();
return result;
case ARITH_NUM:
last_token = op;
return val->val;
case ARITH_VAR:
last_token = op;
return noeval ? val->val : lookupvarint(val->name);
case ARITH_ADD:
token = op;
*val = yylval;
op = yylex();
goto again;
case ARITH_SUB:
*val = yylval;
return -primary(op, val, yylex(), noeval);
case ARITH_NOT:
*val = yylval;
return !primary(op, val, yylex(), noeval);
case ARITH_BNOT:
*val = yylval;
return ~primary(op, val, yylex(), noeval);
default:
yyerror("expecting primary");
}
}
static intmax_t binop2(intmax_t a, int op, int prec, int noeval)
{
for (;;) {
union yystype val;
intmax_t b;
int op2;
int token;
token = yylex();
val = yylval;
b = primary(token, &val, yylex(), noeval);
op2 = last_token;
if (op2 >= ARITH_BINOP_MIN && op2 < ARITH_BINOP_MAX &&
higher_prec(op2, op)) {
b = binop2(b, op2, arith_prec(op), noeval);
op2 = last_token;
}
a = noeval ? b : do_binop(op, a, b);
if (op2 < ARITH_BINOP_MIN || op2 >= ARITH_BINOP_MAX ||
arith_prec(op2) >= prec)
return a;
op = op2;
}
}
static intmax_t binop(int token, union yystype *val, int op, int noeval)
{
intmax_t a = primary(token, val, op, noeval);
op = last_token;
if (op < ARITH_BINOP_MIN || op >= ARITH_BINOP_MAX)
return a;
return binop2(a, op, ARITH_MAX_PREC, noeval);
}
static intmax_t and(int token, union yystype *val, int op, int noeval)
{
intmax_t a = binop(token, val, op, noeval);
intmax_t b;
op = last_token;
if (op != ARITH_AND)
return a;
token = yylex();
*val = yylval;
b = and(token, val, yylex(), noeval | !a);
return a && b;
}
static intmax_t or(int token, union yystype *val, int op, int noeval)
{
intmax_t a = and(token, val, op, noeval);
intmax_t b;
op = last_token;
if (op != ARITH_OR)
return a;
token = yylex();
*val = yylval;
b = or(token, val, yylex(), noeval | !!a);
return a || b;
}
static intmax_t cond(int token, union yystype *val, int op, int noeval)
{
intmax_t a = or(token, val, op, noeval);
intmax_t b;
intmax_t c;
if (last_token != ARITH_QMARK)
return a;
b = assignment(yylex(), noeval | !a);
if (last_token != ARITH_COLON)
yyerror("expecting ':'");
token = yylex();
*val = yylval;
c = cond(token, val, yylex(), noeval | !!a);
return a ? b : c;
}
static intmax_t assignment(int var, int noeval)
{
union yystype val = yylval;
int op = yylex();
intmax_t result;
if (var != ARITH_VAR)
return cond(var, &val, op, noeval);
if (op != ARITH_ASS && (op < ARITH_ASS_MIN || op >= ARITH_ASS_MAX))
return cond(var, &val, op, noeval);
result = assignment(yylex(), noeval);
if (noeval)
return result;
return setvarint(val.name,
op == ARITH_ASS ? result :
do_binop(op - 11, lookupvarint(val.name), result), 0);
}
intmax_t arith(const char *s)
{
intmax_t result;
arith_buf = arith_startbuf = s;
result = assignment(yylex(), 0);
if (last_token)
yyerror("expecting EOF");
return result;
}
#include <inttypes.h>
#include <stdlib.h>
#include <string.h>
#if ARITH_BOR + 11 != ARITH_BORASS || ARITH_ASS + 11 != ARITH_EQ
#error Arithmetic tokens are out of order.
#endif
extern const char *arith_buf;
int
yylex()
{
int value;
const char *buf = arith_buf;
const char *p;
for (;;) {
value = *buf;
switch (value) {
case ' ':
case '\t':
case '\n':
buf++;
continue;
default:
return ARITH_BAD;
case '0':
case '1':
case '2':
case '3':
case '4':
case '5':
case '6':
case '7':
case '8':
case '9':
yylval.val = strtoimax(buf, (char **)&arith_buf, 0);
return ARITH_NUM;
case 'A':
case 'B':
case 'C':
case 'D':
case 'E':
case 'F':
case 'G':
case 'H':
case 'I':
case 'J':
case 'K':
case 'L':
case 'M':
case 'N':
case 'O':
case 'P':
case 'Q':
case 'R':
case 'S':
case 'T':
case 'U':
case 'V':
case 'W':
case 'X':
case 'Y':
case 'Z':
case '_':
case 'a':
case 'b':
case 'c':
case 'd':
case 'e':
case 'f':
case 'g':
case 'h':
case 'i':
case 'j':
case 'k':
case 'l':
case 'm':
case 'n':
case 'o':
case 'p':
case 'q':
case 'r':
case 's':
case 't':
case 'u':
case 'v':
case 'w':
case 'x':
case 'y':
case 'z':
p = buf;
while (buf++, is_in_name(*buf))
;
yylval.name = stalloc(buf - p + 1);
*(char *)mempcpy(yylval.name, p, buf - p) = 0;
value = ARITH_VAR;
goto out;
case '=':
value += ARITH_ASS - '=';
checkeq:
buf++;
checkeqcur:
if (*buf != '=')
goto out;
value += 11;
break;
case '>':
switch (*++buf) {
case '=':
value += ARITH_GE - '>';
break;
case '>':
value += ARITH_RSHIFT - '>';
goto checkeq;
default:
value += ARITH_GT - '>';
goto out;
}
break;
case '<':
switch (*++buf) {
case '=':
value += ARITH_LE - '<';
break;
case '<':
value += ARITH_LSHIFT - '<';
goto checkeq;
default:
value += ARITH_LT - '<';
goto out;
}
break;
case '|':
if (*++buf != '|') {
value += ARITH_BOR - '|';
goto checkeqcur;
}
value += ARITH_OR - '|';
break;
case '&':
if (*++buf != '&') {
value += ARITH_BAND - '&';
goto checkeqcur;
}
value += ARITH_AND - '&';
break;
case '!':
if (*++buf != '=') {
value += ARITH_NOT - '!';
goto out;
}
value += ARITH_NE - '!';
break;
case 0:
goto out;
case '(':
value += ARITH_LPAREN - '(';
break;
case ')':
value += ARITH_RPAREN - ')';
break;
case '*':
value += ARITH_MUL - '*';
goto checkeq;
case '/':
value += ARITH_DIV - '/';
goto checkeq;
case '%':
value += ARITH_REM - '%';
goto checkeq;
case '+':
value += ARITH_ADD - '+';
goto checkeq;
case '-':
value += ARITH_SUB - '-';
goto checkeq;
case '~':
value += ARITH_BNOT - '~';
break;
case '^':
value += ARITH_BXOR - '^';
goto checkeq;
case '?':
value += ARITH_QMARK - '?';
break;
case ':':
value += ARITH_COLON - ':';
break;
}
break;
}
buf++;
out:
arith_buf = buf;
return value;
}
#include <sys/types.h>
#include <sys/stat.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <limits.h>
#define CD_PHYSICAL 1
#define CD_PRINT 2
STATIC int docd(const char *, int);
STATIC const char *updatepwd(const char *);
STATIC char *getpwd(void);
STATIC int cdopt(void);
STATIC char *curdir = nullstr; 
STATIC char *physdir = nullstr; 
STATIC int
cdopt()
{
int flags = 0;
int i, j;
j = 'L';
while ((i = nextopt("LP"))) {
if (i != j) {
flags ^= CD_PHYSICAL;
j = i;
}
}
return flags;
}
int
cdcmd(int argc, char **argv)
{
const char *dest;
const char *path;
const char *p;
char c;
struct stat statb;
int flags;
flags = cdopt();
dest = *argptr;
if (!dest)
dest = bltinlookup(homestr);
else if (dest[0] == '-' && dest[1] == '\0') {
dest = bltinlookup("OLDPWD");
flags |= CD_PRINT;
}
if (!dest)
dest = nullstr;
if (*dest == '/')
goto step6;
if (*dest == '.') {
c = dest[1];
dotdot:
switch (c) {
case '\0':
case '/':
goto step6;
case '.':
c = dest[2];
if (c != '.')
goto dotdot;
}
}
if (!*dest)
dest = ".";
path = bltinlookup("CDPATH");
while (path) {
c = *path;
p = padvance(&path, dest);
if (stat(p, &statb) >= 0 && S_ISDIR(statb.st_mode)) {
if (c && c != ':')
flags |= CD_PRINT;
docd:
if (!docd(p, flags))
goto out;
goto err;
}
}
step6:
p = dest;
goto docd;
err:
sh_error("can't cd to %s", dest);
out:
if (flags & CD_PRINT)
out1fmt(snlfmt, curdir);
return 0;
}
STATIC int
docd(const char *dest, int flags)
{
const char *dir = 0;
int err;
TRACE(("docd(\"%s\", %d) called\n", dest, flags));
INTOFF;
if (!(flags & CD_PHYSICAL)) {
dir = updatepwd(dest);
if (dir)
dest = dir;
}
err = chdir(dest);
if (err)
goto out;
setpwd(dir, 1);
hashcd();
out:
INTON;
return err;
}
STATIC const char *
updatepwd(const char *dir)
{
char *new;
char *p;
char *cdcomppath;
const char *lim;
cdcomppath = sstrdup(dir);
STARTSTACKSTR(new);
if (*dir != '/') {
if (curdir == nullstr)
return 0;
new = stputs(curdir, new);
}
new = makestrspace(strlen(dir) + 2, new);
lim = stackblock() + 1;
if (*dir != '/') {
if (new[-1] != '/')
USTPUTC('/', new);
if (new > lim && *lim == '/')
lim++;
} else {
USTPUTC('/', new);
cdcomppath++;
if (dir[1] == '/' && dir[2] != '/') {
USTPUTC('/', new);
cdcomppath++;
lim++;
}
}
p = strtok(cdcomppath, "/");
while (p) {
switch(*p) {
case '.':
if (p[1] == '.' && p[2] == '\0') {
while (new > lim) {
STUNPUTC(new);
if (new[-1] == '/')
break;
}
break;
} else if (p[1] == '\0')
break;
default:
new = stputs(p, new);
USTPUTC('/', new);
}
p = strtok(0, "/");
}
if (new > lim)
STUNPUTC(new);
*new = 0;
return stackblock();
}
inline
STATIC char *
getpwd()
{
#ifdef __GLIBC__
char *dir = getcwd(0, 0);
if (dir)
return dir;
#else
char buf[PATH_MAX];
if (getcwd(buf, sizeof(buf)))
return savestr(buf);
#endif
sh_warnx("getcwd() failed: %s", strerror(errno));
return nullstr;
}
int
pwdcmd(int argc, char **argv)
{
int flags;
const char *dir = curdir;
flags = cdopt();
if (flags) {
if (physdir == nullstr)
setpwd(dir, 0);
dir = physdir;
}
out1fmt(snlfmt, dir);
return 0;
}
void
setpwd(const char *val, int setold)
{
char *oldcur, *dir;
oldcur = dir = curdir;
if (setold) {
setvar("OLDPWD", oldcur, VEXPORT);
}
INTOFF;
if (physdir != nullstr) {
if (physdir != oldcur)
free(physdir);
physdir = nullstr;
}
if (oldcur == val || !val) {
char *s = getpwd();
physdir = s;
if (!val)
dir = s;
} else
dir = savestr(val);
if (oldcur != dir && oldcur != nullstr) {
free(oldcur);
}
curdir = dir;
INTON;
setvar("PWD", dir, VEXPORT);
}
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
struct jmploc *handler;
int exception;
int suppressint;
volatile sig_atomic_t intpending;
int errlinno;
static void exverror(int, const char *, va_list)
__attribute__((__noreturn__));
void
exraise(int e)
{
#ifdef DEBUG
if (handler == NULL)
abort();
#endif
INTOFF;
exception = e;
longjmp(handler->loc, 1);
}
void
onint(void) {
intpending = 0;
sigclearmask();
if (!(rootshell && iflag)) {
signal(SIGINT, SIG_DFL);
raise(SIGINT);
}
exraise(EXINT);
}
static void
exvwarning2(const char *msg, va_list ap)
{
struct output *errs;
const char *name;
const char *fmt;
errs = out2;
name = arg0 ? arg0 : "sh";
if (!commandname)
fmt = "%s: %d: ";
else
fmt = "%s: %d: %s: ";
outfmt(errs, fmt, name, errlinno, commandname);
doformat(errs, msg, ap);
#if FLUSHERR
outc('\n', errs);
#else
outcslow('\n', errs);
#endif
}
#define exvwarning(a, b, c) exvwarning2(b, c)
static void
exverror(int cond, const char *msg, va_list ap)
{
#ifdef DEBUG
if (msg) {
va_list aq;
TRACE(("exverror(%d, \"", cond));
va_copy(aq, ap);
TRACEV((msg, aq));
va_end(aq);
TRACE(("\") pid=%d\n", getpid()));
} else
TRACE(("exverror(%d, NULL) pid=%d\n", cond, getpid()));
if (msg)
#endif
exvwarning(-1, msg, ap);
flushall();
exraise(cond);
}
void
sh_error(const char *msg, ...)
{
va_list ap;
exitstatus = 2;
va_start(ap, msg);
exverror(EXERROR, msg, ap);
va_end(ap);
}
void
exerror(int cond, const char *msg, ...)
{
va_list ap;
va_start(ap, msg);
exverror(cond, msg, ap);
va_end(ap);
}
void
sh_warnx(const char *fmt, ...)
{
va_list ap;
va_start(ap, fmt);
exvwarning(-1, fmt, ap);
va_end(ap);
}
const char *
errmsg(int e, int action)
{
if (e != ENOENT && e != ENOTDIR)
return strerror(e);
if (action & E_OPEN)
return "No such file";
else if (action & E_CREAT)
return "Directory nonexistent";
else
return "not found";
}
#ifdef REALLY_SMALL
void
__inton() {
if (--suppressint == 0 && intpending) {
onint();
}
}
#endif
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <sys/types.h>
#ifndef SMALL
#endif
int evalskip; 
STATIC int skipcount; 
MKINIT int loopnest; 
static int funcline; 
char *commandname;
int exitstatus; 
int back_exitstatus; 
#if !defined(__alpha__) || (defined(__GNUC__) && __GNUC__ >= 3)
STATIC
#endif
void evaltreenr(union node *, int) __attribute__ ((__noreturn__));
STATIC void evalloop(union node *, int);
STATIC void evalfor(union node *, int);
STATIC void evalcase(union node *, int);
STATIC void evalsubshell(union node *, int);
STATIC void expredir(union node *);
STATIC void evalpipe(union node *, int);
#ifdef notyet
STATIC void evalcommand(union node *, int, struct backcmd *);
#else
STATIC void evalcommand(union node *, int);
#endif
STATIC int evalbltin(const struct builtincmd *, int, char **, int);
STATIC int evalfun(struct funcnode *, int, char **, int);
STATIC void prehash(union node *);
STATIC int eprintlist(struct output *, struct strlist *, int);
STATIC int bltincmd(int, char **);
STATIC const struct builtincmd bltin = {
name: nullstr,
builtin: bltincmd
};
#ifdef mkinit
INCLUDE "eval.h"
RESET {
evalskip = 0;
loopnest = 0;
}
#endif
static int doevalcmd(int argc, char **argv, int flags)
{
char *p;
char *concat;
char **ap;
if (argc > 1) {
p = argv[1];
if (argc > 2) {
STARTSTACKSTR(concat);
ap = argv + 2;
for (;;) {
concat = stputs(p, concat);
if ((p = *ap++) == NULL)
break;
STPUTC(' ', concat);
}
STPUTC('\0', concat);
p = grabstackstr(concat);
}
return evalstring(p, flags & EV_TESTED);
}
return 0;
}
int
evalstring(char *s, int flags)
{
union node *n;
struct stackmark smark;
int status;
setinputstring(s);
setstackmark(&smark);
status = 0;
while ((n = parsecmd(0)) != NEOF) {
evaltree(n, flags & ~(parser_eof() ? 0 : EV_EXIT));
status = exitstatus;
popstackmark(&smark);
if (evalskip)
break;
}
popfile();
return status;
}
void
evaltree(union node *n, int flags)
{
int checkexit = 0;
void (*evalfn)(union node *, int);
unsigned isor;
int status;
if (n == NULL) {
TRACE(("evaltree(NULL) called\n"));
goto out;
}
#ifndef SMALL
displayhist = 1; 
#endif
TRACE(("pid %d, evaltree(%p: %d, %d) called\n",
getpid(), n, n->type, flags));
switch (n->type) {
default:
#ifdef DEBUG
out1fmt("Node type = %d\n", n->type);
#ifndef USE_GLIBC_STDIO
flushout(out1);
#endif
break;
#endif
case NNOT:
evaltree(n->nnot.com, EV_TESTED);
status = !exitstatus;
goto setstatus;
case NREDIR:
errlinno = lineno = n->nredir.linno;
if (funcline)
lineno -= funcline - 1;
expredir(n->nredir.redirect);
pushredir(n->nredir.redirect);
status = redirectsafe(n->nredir.redirect, REDIR_PUSH);
if (!status) {
evaltree(n->nredir.n, flags & EV_TESTED);
status = exitstatus;
}
if (n->nredir.redirect)
popredir(0);
goto setstatus;
case NCMD:
#ifdef notyet
if (eflag && !(flags & EV_TESTED))
checkexit = ~0;
evalcommand(n, flags, (struct backcmd *)NULL);
break;
#else
evalfn = evalcommand;
checkexit:
if (eflag && !(flags & EV_TESTED))
checkexit = ~0;
goto calleval;
#endif
case NFOR:
evalfn = evalfor;
goto calleval;
case NWHILE:
case NUNTIL:
evalfn = evalloop;
goto calleval;
case NSUBSHELL:
case NBACKGND:
evalfn = evalsubshell;
goto checkexit;
case NPIPE:
evalfn = evalpipe;
goto checkexit;
case NCASE:
evalfn = evalcase;
goto calleval;
case NAND:
case NOR:
case NSEMI:
#if NAND + 1 != NOR
#error NAND + 1 != NOR
#endif
#if NOR + 1 != NSEMI
#error NOR + 1 != NSEMI
#endif
isor = n->type - NAND;
evaltree(
n->nbinary.ch1,
(flags | ((isor >> 1) - 1)) & EV_TESTED
);
if (!exitstatus == isor)
break;
if (!evalskip) {
n = n->nbinary.ch2;
evaln:
evalfn = evaltree;
calleval:
evalfn(n, flags);
break;
}
break;
case NIF:
evaltree(n->nif.test, EV_TESTED);
if (evalskip)
break;
if (exitstatus == 0) {
n = n->nif.ifpart;
goto evaln;
} else if (n->nif.elsepart) {
n = n->nif.elsepart;
goto evaln;
}
goto success;
case NDEFUN:
defun(n);
success:
status = 0;
setstatus:
exitstatus = status;
break;
}
out:
if (checkexit & exitstatus)
goto exexit;
if (pendingsigs)
dotrap();
if (flags & EV_EXIT) {
exexit:
exraise(EXEXIT);
}
}
#if !defined(__alpha__) || (defined(__GNUC__) && __GNUC__ >= 3)
STATIC
#endif
void evaltreenr(union node *n, int flags)
#ifdef HAVE_ATTRIBUTE_ALIAS
__attribute__ ((alias("evaltree")));
#else
{
evaltree(n, flags);
abort();
}
#endif
STATIC void
evalloop(union node *n, int flags)
{
int status;
loopnest++;
status = 0;
flags &= EV_TESTED;
for (;;) {
int i;
evaltree(n->nbinary.ch1, EV_TESTED);
if (evalskip) {
skipping: if (evalskip == SKIPCONT && --skipcount <= 0) {
evalskip = 0;
continue;
}
if (evalskip == SKIPBREAK && --skipcount <= 0)
evalskip = 0;
break;
}
i = exitstatus;
if (n->type != NWHILE)
i = !i;
if (i != 0)
break;
evaltree(n->nbinary.ch2, flags);
status = exitstatus;
if (evalskip)
goto skipping;
}
loopnest--;
exitstatus = status;
}
STATIC void
evalfor(union node *n, int flags)
{
struct arglist arglist;
union node *argp;
struct strlist *sp;
struct stackmark smark;
errlinno = lineno = n->nfor.linno;
if (funcline)
lineno -= funcline - 1;
setstackmark(&smark);
arglist.lastp = &arglist.list;
for (argp = n->nfor.args ; argp ; argp = argp->narg.next) {
expandarg(argp, &arglist, EXP_FULL | EXP_TILDE);
if (evalskip)
goto out;
}
*arglist.lastp = NULL;
exitstatus = 0;
loopnest++;
flags &= EV_TESTED;
for (sp = arglist.list ; sp ; sp = sp->next) {
setvar(n->nfor.var, sp->text, 0);
evaltree(n->nfor.body, flags);
if (evalskip) {
if (evalskip == SKIPCONT && --skipcount <= 0) {
evalskip = 0;
continue;
}
if (evalskip == SKIPBREAK && --skipcount <= 0)
evalskip = 0;
break;
}
}
loopnest--;
out:
popstackmark(&smark);
}
STATIC void
evalcase(union node *n, int flags)
{
union node *cp;
union node *patp;
struct arglist arglist;
struct stackmark smark;
errlinno = lineno = n->ncase.linno;
if (funcline)
lineno -= funcline - 1;
setstackmark(&smark);
arglist.lastp = &arglist.list;
expandarg(n->ncase.expr, &arglist, EXP_TILDE);
exitstatus = 0;
for (cp = n->ncase.cases ; cp && evalskip == 0 ; cp = cp->nclist.next) {
for (patp = cp->nclist.pattern ; patp ; patp = patp->narg.next) {
if (casematch(patp, arglist.list->text)) {
if (evalskip == 0) {
evaltree(cp->nclist.body, flags);
}
goto out;
}
}
}
out:
popstackmark(&smark);
}
STATIC void
evalsubshell(union node *n, int flags)
{
struct job *jp;
int backgnd = (n->type == NBACKGND);
int status;
errlinno = lineno = n->nredir.linno;
if (funcline)
lineno -= funcline - 1;
expredir(n->nredir.redirect);
if (!backgnd && flags & EV_EXIT && !have_traps())
goto nofork;
INTOFF;
jp = makejob(n, 1);
if (forkshell(jp, n, backgnd) == 0) {
INTON;
flags |= EV_EXIT;
if (backgnd)
flags &=~ EV_TESTED;
nofork:
redirect(n->nredir.redirect, 0);
evaltreenr(n->nredir.n, flags);
}
status = 0;
if (! backgnd)
status = waitforjob(jp);
exitstatus = status;
INTON;
}
STATIC void
expredir(union node *n)
{
union node *redir;
for (redir = n ; redir ; redir = redir->nfile.next) {
struct arglist fn;
fn.lastp = &fn.list;
switch (redir->type) {
case NFROMTO:
case NFROM:
case NTO:
case NCLOBBER:
case NAPPEND:
expandarg(redir->nfile.fname, &fn, EXP_TILDE | EXP_REDIR);
redir->nfile.expfname = fn.list->text;
break;
case NFROMFD:
case NTOFD:
if (redir->ndup.vname) {
expandarg(redir->ndup.vname, &fn, EXP_FULL | EXP_TILDE);
fixredir(redir, fn.list->text, 1);
}
break;
}
}
}
STATIC void
evalpipe(union node *n, int flags)
{
struct job *jp;
struct nodelist *lp;
int pipelen;
int prevfd;
int pip[2];
TRACE(("evalpipe(0x%lx) called\n", (long)n));
pipelen = 0;
for (lp = n->npipe.cmdlist ; lp ; lp = lp->next)
pipelen++;
flags |= EV_EXIT;
INTOFF;
jp = makejob(n, pipelen);
prevfd = -1;
for (lp = n->npipe.cmdlist ; lp ; lp = lp->next) {
prehash(lp->n);
pip[1] = -1;
if (lp->next) {
if (pipe(pip) < 0) {
close(prevfd);
sh_error("Pipe call failed");
}
}
if (forkshell(jp, lp->n, n->npipe.backgnd) == 0) {
INTON;
if (pip[1] >= 0) {
close(pip[0]);
}
if (prevfd > 0) {
dup2(prevfd, 0);
close(prevfd);
}
if (pip[1] > 1) {
dup2(pip[1], 1);
close(pip[1]);
}
evaltreenr(lp->n, flags);
}
if (prevfd >= 0)
close(prevfd);
prevfd = pip[0];
close(pip[1]);
}
if (n->npipe.backgnd == 0) {
exitstatus = waitforjob(jp);
TRACE(("evalpipe: job done exit status %d\n", exitstatus));
}
INTON;
}
void
evalbackcmd(union node *n, struct backcmd *result)
{
int pip[2];
struct job *jp;
result->fd = -1;
result->buf = NULL;
result->nleft = 0;
result->jp = NULL;
if (n == NULL) {
goto out;
}
if (pipe(pip) < 0)
sh_error("Pipe call failed");
jp = makejob(n, 1);
if (forkshell(jp, n, FORK_NOJOB) == 0) {
FORCEINTON;
close(pip[0]);
if (pip[1] != 1) {
dup2(pip[1], 1);
close(pip[1]);
}
ifsfree();
evaltreenr(n, EV_EXIT);
}
close(pip[1]);
result->fd = pip[0];
result->jp = jp;
out:
TRACE(("evalbackcmd done: fd=%d buf=0x%x nleft=%d jp=0x%x\n",
result->fd, result->buf, result->nleft, result->jp));
}
static char **
parse_command_args(char **argv, const char **path)
{
char *cp, c;
for (;;) {
cp = *++argv;
if (!cp)
return 0;
if (*cp++ != '-')
break;
if (!(c = *cp++))
break;
if (c == '-' && !*cp) {
if (!*++argv)
return 0;
break;
}
do {
switch (c) {
case 'p':
*path = defpath;
break;
default:
return 0;
}
} while ((c = *cp++));
}
return argv;
}
STATIC void
#ifdef notyet
evalcommand(union node *cmd, int flags, struct backcmd *backcmd)
#else
evalcommand(union node *cmd, int flags)
#endif
{
struct localvar_list *localvar_stop;
struct redirtab *redir_stop;
struct stackmark smark;
union node *argp;
struct arglist arglist;
struct arglist varlist;
char **argv;
int argc;
struct strlist *sp;
#ifdef notyet
int pip[2];
#endif
struct cmdentry cmdentry;
struct job *jp;
char *lastarg;
const char *path;
int spclbltin;
int execcmd;
int status;
char **nargv;
errlinno = lineno = cmd->ncmd.linno;
if (funcline)
lineno -= funcline - 1;
TRACE(("evalcommand(0x%lx, %d) called\n", (long)cmd, flags));
setstackmark(&smark);
localvar_stop = pushlocalvars();
back_exitstatus = 0;
cmdentry.cmdtype = CMDBUILTIN;
cmdentry.u.cmd = &bltin;
varlist.lastp = &varlist.list;
*varlist.lastp = NULL;
arglist.lastp = &arglist.list;
*arglist.lastp = NULL;
argc = 0;
for (argp = cmd->ncmd.args; argp; argp = argp->narg.next) {
struct strlist **spp;
spp = arglist.lastp;
expandarg(argp, &arglist, EXP_FULL | EXP_TILDE);
for (sp = *spp; sp; sp = sp->next)
argc++;
}
nargv = stalloc(sizeof (char *) * (argc + 2));
argv = ++nargv;
for (sp = arglist.list ; sp ; sp = sp->next) {
TRACE(("evalcommand arg: %s\n", sp->text));
*nargv++ = sp->text;
}
*nargv = NULL;
lastarg = NULL;
if (iflag && funcline == 0 && argc > 0)
lastarg = nargv[-1];
preverrout.fd = 2;
expredir(cmd->ncmd.redirect);
redir_stop = pushredir(cmd->ncmd.redirect);
status = redirectsafe(cmd->ncmd.redirect, REDIR_PUSH|REDIR_SAVEFD2);
path = vpath.text;
for (argp = cmd->ncmd.assign; argp; argp = argp->narg.next) {
struct strlist **spp;
char *p;
spp = varlist.lastp;
expandarg(argp, &varlist, EXP_VARTILDE);
mklocal((*spp)->text);
p = (*spp)->text;
if (varequal(p, path))
path = p;
}
if (xflag) {
struct output *out;
int sep;
out = &preverrout;
outstr(expandstr(ps4val()), out);
sep = 0;
sep = eprintlist(out, varlist.list, sep);
eprintlist(out, arglist.list, sep);
outcslow('\n', out);
#ifdef FLUSHERR
flushout(out);
#endif
}
execcmd = 0;
spclbltin = -1;
if (argc) {
const char *oldpath;
int cmd_flag = DO_ERR;
path += 5;
oldpath = path;
for (;;) {
find_command(argv[0], &cmdentry, cmd_flag, path);
if (cmdentry.cmdtype == CMDUNKNOWN) {
status = 127;
#ifdef FLUSHERR
flushout(&errout);
#endif
goto bail;
}
if (cmdentry.cmdtype != CMDBUILTIN)
break;
if (spclbltin < 0)
spclbltin = 
cmdentry.u.cmd->flags &
BUILTIN_SPECIAL
;
if (cmdentry.u.cmd == EXECCMD)
execcmd++;
if (cmdentry.u.cmd != COMMANDCMD)
break;
path = oldpath;
nargv = parse_command_args(argv, &path);
if (!nargv)
break;
argc -= nargv - argv;
argv = nargv;
cmd_flag |= DO_NOFUNC;
}
}
if (status) {
bail:
exitstatus = status;
if (spclbltin > 0)
exraise(EXERROR);
goto out;
}
switch (cmdentry.cmdtype) {
default:
if (!(flags & EV_EXIT) || have_traps()) {
INTOFF;
jp = makejob(cmd, 1);
if (forkshell(jp, cmd, FORK_FG) != 0) {
exitstatus = waitforjob(jp);
INTON;
break;
}
FORCEINTON;
}
listsetvar(varlist.list, VEXPORT|VSTACK);
shellexec(argv, path, cmdentry.u.index);
case CMDBUILTIN:
if (spclbltin > 0 || argc == 0) {
poplocalvars(1);
if (execcmd && argc > 1)
listsetvar(varlist.list, VEXPORT);
}
if (evalbltin(cmdentry.u.cmd, argc, argv, flags)) {
int status;
int i;
i = exception;
if (i == EXEXIT)
goto raise;
status = (i == EXINT) ? SIGINT + 128 : 2;
exitstatus = status;
if (i == EXINT || spclbltin > 0) {
raise:
longjmp(handler->loc, 1);
}
FORCEINTON;
}
break;
case CMDFUNCTION:
poplocalvars(1);
if (evalfun(cmdentry.u.func, argc, argv, flags))
goto raise;
break;
}
out:
if (cmd->ncmd.redirect)
popredir(execcmd);
unwindredir(redir_stop);
unwindlocalvars(localvar_stop);
if (lastarg)
setvar("_", lastarg, 0);
popstackmark(&smark);
}
STATIC int
evalbltin(const struct builtincmd *cmd, int argc, char **argv, int flags)
{
char *volatile savecmdname;
struct jmploc *volatile savehandler;
struct jmploc jmploc;
int status;
int i;
savecmdname = commandname;
savehandler = handler;
if ((i = setjmp(jmploc.loc)))
goto cmddone;
handler = &jmploc;
commandname = argv[0];
argptr = argv + 1;
optptr = NULL; 
if (cmd == EVALCMD)
status = doevalcmd(argc, argv, flags);
else
status = (*cmd->builtin)(argc, argv);
flushall();
status |= outerr(out1);
exitstatus = status;
cmddone:
freestdout();
commandname = savecmdname;
handler = savehandler;
return i;
}
STATIC int
evalfun(struct funcnode *func, int argc, char **argv, int flags)
{
volatile struct shparam saveparam;
struct jmploc *volatile savehandler;
struct jmploc jmploc;
int e;
int savefuncline;
saveparam = shellparam;
savefuncline = funcline;
savehandler = handler;
if ((e = setjmp(jmploc.loc))) {
goto funcdone;
}
INTOFF;
handler = &jmploc;
shellparam.malloc = 0;
func->count++;
funcline = func->n.ndefun.linno;
INTON;
shellparam.nparam = argc - 1;
shellparam.p = argv + 1;
shellparam.optind = 1;
shellparam.optoff = -1;
pushlocalvars();
evaltree(func->n.ndefun.body, flags & EV_TESTED);
poplocalvars(0);
funcdone:
INTOFF;
funcline = savefuncline;
freefunc(func);
freeparam(&shellparam);
shellparam = saveparam;
handler = savehandler;
INTON;
evalskip &= ~SKIPFUNC;
return e;
}
STATIC void
prehash(union node *n)
{
struct cmdentry entry;
if (n->type == NCMD && n->ncmd.args)
if (goodname(n->ncmd.args->narg.text))
find_command(n->ncmd.args->narg.text, &entry, 0,
pathval());
}
STATIC int
bltincmd(int argc, char **argv)
{
return back_exitstatus;
}
int
breakcmd(int argc, char **argv)
{
int n = argc > 1 ? number(argv[1]) : 1;
if (n <= 0)
badnum(argv[1]);
if (n > loopnest)
n = loopnest;
if (n > 0) {
evalskip = (**argv == 'c')? SKIPCONT : SKIPBREAK;
skipcount = n;
}
return 0;
}
int
returncmd(int argc, char **argv)
{
evalskip = SKIPFUNC;
return argv[1] ? number(argv[1]) : exitstatus;
}
int
falsecmd(int argc, char **argv)
{
return 1;
}
int
truecmd(int argc, char **argv)
{
return 0;
}
int
execcmd(int argc, char **argv)
{
if (argc > 1) {
iflag = 0; 
mflag = 0;
optschanged();
shellexec(argv + 1, pathval(), 0);
}
return 0;
}
STATIC int
eprintlist(struct output *out, struct strlist *sp, int sep)
{
while (sp) {
const char *p;
p = " %s" + (1 - sep);
sep |= 1;
outfmt(out, p, sp->text);
sp = sp->next;
}
return sep;
}
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdlib.h>
#ifdef HAVE_PATHS_H
#include <paths.h>
#endif
#define CMDTABLESIZE 31 
#define ARB 1 
struct tblentry {
struct tblentry *next; 
union param param; 
short cmdtype; 
char rehash; 
char cmdname[ARB]; 
};
STATIC struct tblentry *cmdtable[CMDTABLESIZE];
STATIC int builtinloc = -1; 
STATIC void tryexec(char *, char **, char **);
STATIC void printentry(struct tblentry *);
STATIC void clearcmdentry(int);
STATIC struct tblentry *cmdlookup(const char *, int);
STATIC void delete_cmd_entry(void);
STATIC void addcmdentry(char *, struct cmdentry *);
STATIC int describe_command(struct output *, char *, int);
void
shellexec(char **argv, const char *path, int idx)
{
char *cmdname;
int e;
char **envp;
int exerrno;
envp = environment();
if (strchr(argv[0], '/') != NULL) {
tryexec(argv[0], argv, envp);
e = errno;
} else {
e = ENOENT;
while ((cmdname = padvance(&path, argv[0])) != NULL) {
if (--idx < 0 && pathopt == NULL) {
tryexec(cmdname, argv, envp);
if (errno != ENOENT && errno != ENOTDIR)
e = errno;
}
stunalloc(cmdname);
}
}
switch (e) {
case EACCES:
exerrno = 126;
break;
case ENOENT:
exerrno = 127;
break;
default:
exerrno = 2;
break;
}
exitstatus = exerrno;
TRACE(("shellexec failed for %s, errno %d, suppressint %d\n",
argv[0], e, suppressint ));
exerror(EXEXIT, "%s: %s", argv[0], errmsg(e, E_EXEC));
}
STATIC void
tryexec(char *cmd, char **argv, char **envp)
{
char *const path_bshell = _PATH_BSHELL;
repeat:
#ifdef SYSV
do {
execve(cmd, argv, envp);
} while (errno == EINTR);
#else
execve(cmd, argv, envp);
#endif
if (cmd != path_bshell && errno == ENOEXEC) {
*argv-- = cmd;
*argv = cmd = path_bshell;
goto repeat;
}
}
const char *pathopt;
char *
padvance(const char **path, const char *name)
{
const char *p;
char *q;
const char *start;
size_t len;
if (*path == NULL)
return NULL;
start = *path;
for (p = start ; *p && *p != ':' && *p != '%' ; p++);
len = p - start + strlen(name) + 2; 
while (stackblocksize() < len)
growstackblock();
q = stackblock();
if (p != start) {
memcpy(q, start, p - start);
q += p - start;
*q++ = '/';
}
strcpy(q, name);
pathopt = NULL;
if (*p == '%') {
pathopt = ++p;
while (*p && *p != ':') p++;
}
if (*p == ':')
*path = p + 1;
else
*path = NULL;
return stalloc(len);
}
int
hashcmd(int argc, char **argv)
{
struct tblentry **pp;
struct tblentry *cmdp;
int c;
struct cmdentry entry;
char *name;
while ((c = nextopt("r")) != '\0') {
clearcmdentry(0);
return 0;
}
if (*argptr == NULL) {
for (pp = cmdtable ; pp < &cmdtable[CMDTABLESIZE] ; pp++) {
for (cmdp = *pp ; cmdp ; cmdp = cmdp->next) {
if (cmdp->cmdtype == CMDNORMAL)
printentry(cmdp);
}
}
return 0;
}
c = 0;
while ((name = *argptr) != NULL) {
if ((cmdp = cmdlookup(name, 0)) != NULL
&& (cmdp->cmdtype == CMDNORMAL
|| (cmdp->cmdtype == CMDBUILTIN && builtinloc >= 0)))
delete_cmd_entry();
find_command(name, &entry, DO_ERR, pathval());
if (entry.cmdtype == CMDUNKNOWN)
c = 1;
argptr++;
}
return c;
}
STATIC void
printentry(struct tblentry *cmdp)
{
int idx;
const char *path;
char *name;
idx = cmdp->param.index;
path = pathval();
do {
name = padvance(&path, cmdp->cmdname);
stunalloc(name);
} while (--idx >= 0);
out1str(name);
out1fmt(snlfmt, cmdp->rehash ? "*" : nullstr);
}
void
find_command(char *name, struct cmdentry *entry, int act, const char *path)
{
struct tblentry *cmdp;
int idx;
int prev;
char *fullname;
struct stat64 statb;
int e;
int updatetbl;
struct builtincmd *bcmd;
if (strchr(name, '/') != NULL) {
entry->u.index = -1;
if (act & DO_ABS) {
while (stat64(name, &statb) < 0) {
#ifdef SYSV
if (errno == EINTR)
continue;
#endif
entry->cmdtype = CMDUNKNOWN;
return;
}
}
entry->cmdtype = CMDNORMAL;
return;
}
updatetbl = (path == pathval());
if (!updatetbl) {
act |= DO_ALTPATH;
if (strstr(path, "%builtin") != NULL)
act |= DO_ALTBLTIN;
}
if ((cmdp = cmdlookup(name, 0)) != NULL) {
int bit;
switch (cmdp->cmdtype) {
default:
#if DEBUG
abort();
#endif
case CMDNORMAL:
bit = DO_ALTPATH;
break;
case CMDFUNCTION:
bit = DO_NOFUNC;
break;
case CMDBUILTIN:
bit = DO_ALTBLTIN;
break;
}
if (act & bit) {
updatetbl = 0;
cmdp = NULL;
} else if (cmdp->rehash == 0)
goto success;
}
bcmd = find_builtin(name);
if (bcmd && (bcmd->flags & BUILTIN_REGULAR || (
act & DO_ALTPATH ? !(act & DO_ALTBLTIN) : builtinloc <= 0
)))
goto builtin_success;
prev = -1; 
if (cmdp && cmdp->rehash) { 
if (cmdp->cmdtype == CMDBUILTIN)
prev = builtinloc;
else
prev = cmdp->param.index;
}
e = ENOENT;
idx = -1;
loop:
while ((fullname = padvance(&path, name)) != NULL) {
stunalloc(fullname);
idx++;
if (pathopt) {
if (prefix(pathopt, "builtin")) {
if (bcmd)
goto builtin_success;
continue;
} else if (!(act & DO_NOFUNC) &&
prefix(pathopt, "func")) {
} else {
continue;
}
}
if (fullname[0] == '/' && idx <= prev) {
if (idx < prev)
continue;
TRACE(("searchexec \"%s\": no change\n", name));
goto success;
}
while (stat64(fullname, &statb) < 0) {
#ifdef SYSV
if (errno == EINTR)
continue;
#endif
if (errno != ENOENT && errno != ENOTDIR)
e = errno;
goto loop;
}
e = EACCES; 
if (!S_ISREG(statb.st_mode))
continue;
if (pathopt) { 
stalloc(strlen(fullname) + 1);
readcmdfile(fullname);
if ((cmdp = cmdlookup(name, 0)) == NULL ||
cmdp->cmdtype != CMDFUNCTION)
sh_error("%s not defined in %s", name,
fullname);
stunalloc(fullname);
goto success;
}
#ifdef notdef
if (statb.st_uid == geteuid()) {
if ((statb.st_mode & 0100) == 0)
goto loop;
} else if (statb.st_gid == getegid()) {
if ((statb.st_mode & 010) == 0)
goto loop;
} else {
if ((statb.st_mode & 01) == 0)
goto loop;
}
#endif
TRACE(("searchexec \"%s\" returns \"%s\"\n", name, fullname));
if (!updatetbl) {
entry->cmdtype = CMDNORMAL;
entry->u.index = idx;
return;
}
INTOFF;
cmdp = cmdlookup(name, 1);
cmdp->cmdtype = CMDNORMAL;
cmdp->param.index = idx;
INTON;
goto success;
}
if (cmdp && updatetbl)
delete_cmd_entry();
if (act & DO_ERR)
sh_warnx("%s: %s", name, errmsg(e, E_EXEC));
entry->cmdtype = CMDUNKNOWN;
return;
builtin_success:
if (!updatetbl) {
entry->cmdtype = CMDBUILTIN;
entry->u.cmd = bcmd;
return;
}
INTOFF;
cmdp = cmdlookup(name, 1);
cmdp->cmdtype = CMDBUILTIN;
cmdp->param.cmd = bcmd;
INTON;
success:
cmdp->rehash = 0;
entry->cmdtype = cmdp->cmdtype;
entry->u = cmdp->param;
}
struct builtincmd *
find_builtin(const char *name)
{
struct builtincmd *bp;
bp = bsearch(
&name, builtincmd, NUMBUILTINS, sizeof(struct builtincmd),
pstrcmp
);
return bp;
}
void
hashcd(void)
{
struct tblentry **pp;
struct tblentry *cmdp;
for (pp = cmdtable ; pp < &cmdtable[CMDTABLESIZE] ; pp++) {
for (cmdp = *pp ; cmdp ; cmdp = cmdp->next) {
if (cmdp->cmdtype == CMDNORMAL || (
cmdp->cmdtype == CMDBUILTIN &&
!(cmdp->param.cmd->flags & BUILTIN_REGULAR) &&
builtinloc > 0
))
cmdp->rehash = 1;
}
}
}
void
changepath(const char *newval)
{
const char *old, *new;
int idx;
int firstchange;
int bltin;
old = pathval();
new = newval;
firstchange = 9999; 
idx = 0;
bltin = -1;
for (;;) {
if (*old != *new) {
firstchange = idx;
if ((*old == '\0' && *new == ':')
|| (*old == ':' && *new == '\0'))
firstchange++;
old = new; 
}
if (*new == '\0')
break;
if (*new == '%' && bltin < 0 && prefix(new + 1, "builtin"))
bltin = idx;
if (*new == ':') {
idx++;
}
new++, old++;
}
if (builtinloc < 0 && bltin >= 0)
builtinloc = bltin; 
if (builtinloc >= 0 && bltin < 0)
firstchange = 0;
clearcmdentry(firstchange);
builtinloc = bltin;
}
STATIC void
clearcmdentry(int firstchange)
{
struct tblentry **tblp;
struct tblentry **pp;
struct tblentry *cmdp;
INTOFF;
for (tblp = cmdtable ; tblp < &cmdtable[CMDTABLESIZE] ; tblp++) {
pp = tblp;
while ((cmdp = *pp) != NULL) {
if ((cmdp->cmdtype == CMDNORMAL &&
cmdp->param.index >= firstchange)
|| (cmdp->cmdtype == CMDBUILTIN &&
builtinloc >= firstchange)) {
*pp = cmdp->next;
ckfree(cmdp);
} else {
pp = &cmdp->next;
}
}
}
INTON;
}
struct tblentry **lastcmdentry;
STATIC struct tblentry *
cmdlookup(const char *name, int add)
{
unsigned int hashval;
const char *p;
struct tblentry *cmdp;
struct tblentry **pp;
p = name;
hashval = (unsigned char)*p << 4;
while (*p)
hashval += (unsigned char)*p++;
hashval &= 0x7FFF;
pp = &cmdtable[hashval % CMDTABLESIZE];
for (cmdp = *pp ; cmdp ; cmdp = cmdp->next) {
if (equal(cmdp->cmdname, name))
break;
pp = &cmdp->next;
}
if (add && cmdp == NULL) {
cmdp = *pp = ckmalloc(sizeof (struct tblentry) - ARB
+ strlen(name) + 1);
cmdp->next = NULL;
cmdp->cmdtype = CMDUNKNOWN;
strcpy(cmdp->cmdname, name);
}
lastcmdentry = pp;
return cmdp;
}
STATIC void
delete_cmd_entry(void)
{
struct tblentry *cmdp;
INTOFF;
cmdp = *lastcmdentry;
*lastcmdentry = cmdp->next;
if (cmdp->cmdtype == CMDFUNCTION)
freefunc(cmdp->param.func);
ckfree(cmdp);
INTON;
}
#ifdef notdef
void
getcmdentry(char *name, struct cmdentry *entry)
{
struct tblentry *cmdp = cmdlookup(name, 0);
if (cmdp) {
entry->u = cmdp->param;
entry->cmdtype = cmdp->cmdtype;
} else {
entry->cmdtype = CMDUNKNOWN;
entry->u.index = 0;
}
}
#endif
STATIC void
addcmdentry(char *name, struct cmdentry *entry)
{
struct tblentry *cmdp;
cmdp = cmdlookup(name, 1);
if (cmdp->cmdtype == CMDFUNCTION) {
freefunc(cmdp->param.func);
}
cmdp->cmdtype = entry->cmdtype;
cmdp->param = entry->u;
cmdp->rehash = 0;
}
void
defun(union node *func)
{
struct cmdentry entry;
INTOFF;
entry.cmdtype = CMDFUNCTION;
entry.u.func = copyfunc(func);
addcmdentry(func->ndefun.text, &entry);
INTON;
}
void
unsetfunc(const char *name)
{
struct tblentry *cmdp;
if ((cmdp = cmdlookup(name, 0)) != NULL &&
cmdp->cmdtype == CMDFUNCTION)
delete_cmd_entry();
}
int
typecmd(int argc, char **argv)
{
int i;
int err = 0;
for (i = 1; i < argc; i++) {
err |= describe_command(out1, argv[i], 1);
}
return err;
}
STATIC int
describe_command(out, command, verbose)
struct output *out;
char *command;
int verbose;
{
struct cmdentry entry;
struct tblentry *cmdp;
const struct alias *ap;
const char *path = pathval();
if (verbose) {
outstr(command, out);
}
if (findkwd(command)) {
outstr(verbose ? " is a shell keyword" : command, out);
goto out;
}
if ((ap = lookupalias(command, 0)) != NULL) {
if (verbose) {
outfmt(out, " is an alias for %s", ap->val);
} else {
outstr("alias ", out);
printalias(ap);
return 0;
}
goto out;
}
if ((cmdp = cmdlookup(command, 0)) != NULL) {
entry.cmdtype = cmdp->cmdtype;
entry.u = cmdp->param;
} else {
find_command(command, &entry, DO_ABS, path);
}
switch (entry.cmdtype) {
case CMDNORMAL: {
int j = entry.u.index;
char *p;
if (j == -1) {
p = command;
} else {
do {
p = padvance(&path, command);
stunalloc(p);
} while (--j >= 0);
}
if (verbose) {
outfmt(
out, " is%s %s",
cmdp ? " a tracked alias for" : nullstr, p
);
} else {
outstr(p, out);
}
break;
}
case CMDFUNCTION:
if (verbose) {
outstr(" is a shell function", out);
} else {
outstr(command, out);
}
break;
case CMDBUILTIN:
if (verbose) {
outfmt(
out, " is a %sshell builtin",
entry.u.cmd->flags & BUILTIN_SPECIAL ?
"special " : nullstr
);
} else {
outstr(command, out);
}
break;
default:
if (verbose) {
outstr(": not found\n", out);
}
return 127;
}
out:
outc('\n', out);
return 0;
}
int
commandcmd(argc, argv)
int argc;
char **argv;
{
char *cmd;
int c;
enum {
VERIFY_BRIEF = 1,
VERIFY_VERBOSE = 2,
} verify = 0;
while ((c = nextopt("pvV")) != '\0')
if (c == 'V')
verify |= VERIFY_VERBOSE;
else if (c == 'v')
verify |= VERIFY_BRIEF;
#ifdef DEBUG
else if (c != 'p')
abort();
#endif
cmd = *argptr;
if (verify && cmd)
return describe_command(out1, cmd, verify - VERIFY_BRIEF);
return 0;
}
#include <sys/types.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <dirent.h>
#include <unistd.h>
#ifdef HAVE_GETPWNAM
#include <pwd.h>
#endif
#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <limits.h>
#include <string.h>
#include <fnmatch.h>
#ifdef HAVE_GLOB
#include <glob.h>
#endif
#include <ctype.h>
#define RMESCAPE_ALLOC 0x1 
#define RMESCAPE_GLOB 0x2 
#define RMESCAPE_GROW 0x8 
#define RMESCAPE_HEAP 0x10 
#define QUOTES_ESC (EXP_FULL | EXP_CASE | EXP_QPAT)
#define QUOTES_KEEPNUL EXP_TILDE
struct ifsregion {
struct ifsregion *next; 
int begoff; 
int endoff; 
int nulonly; 
};
static char *expdest;
static struct nodelist *argbackq;
static struct ifsregion ifsfirst;
static struct ifsregion *ifslastp;
static struct arglist exparg;
STATIC void argstr(char *, int);
STATIC char *exptilde(char *, char *, int);
STATIC void expbackq(union node *, int);
STATIC const char *subevalvar(char *, char *, int, int, int, int, int);
STATIC char *evalvar(char *, int);
STATIC size_t strtodest(const char *, const char *, int);
STATIC void memtodest(const char *, size_t, const char *, int);
STATIC ssize_t varvalue(char *, int, int);
STATIC void expandmeta(struct strlist *, int);
#ifdef HAVE_GLOB
STATIC void addglob(const glob_t *);
#else
STATIC void expmeta(char *, char *);
STATIC struct strlist *expsort(struct strlist *);
STATIC struct strlist *msort(struct strlist *, int);
#endif
STATIC void addfname(char *);
STATIC int patmatch(char *, const char *);
#ifndef HAVE_FNMATCH
STATIC int pmatch(const char *, const char *);
#else
#define pmatch(a, b) !fnmatch((a), (b), 0)
#endif
STATIC int cvtnum(intmax_t);
STATIC size_t esclen(const char *, const char *);
STATIC char *scanleft(char *, char *, char *, char *, int, int);
STATIC char *scanright(char *, char *, char *, char *, int, int);
STATIC void varunset(const char *, const char *, const char *, int)
__attribute__((__noreturn__));
STATIC inline char *
preglob(const char *pattern, int flag) {
flag |= RMESCAPE_GLOB;
return _rmescapes((char *)pattern, flag);
}
STATIC size_t
esclen(const char *start, const char *p) {
size_t esc = 0;
while (p > start && *--p == (char)CTLESC) {
esc++;
}
return esc;
}
static inline const char *getpwhome(const char *name)
{
#ifdef HAVE_GETPWNAM
struct passwd *pw = getpwnam(name);
return pw ? pw->pw_dir : 0;
#else
return 0;
#endif
}
void
expandarg(union node *arg, struct arglist *arglist, int flag)
{
struct strlist *sp;
char *p;
argbackq = arg->narg.backquote;
STARTSTACKSTR(expdest);
argstr(arg->narg.text, flag);
p = _STPUTC('\0', expdest);
expdest = p - 1;
if (arglist == NULL) {
goto out;
}
p = grabstackstr(p);
exparg.lastp = &exparg.list;
if (flag & EXP_FULL) {
ifsbreakup(p, &exparg);
*exparg.lastp = NULL;
exparg.lastp = &exparg.list;
expandmeta(exparg.list, flag);
} else {
sp = (struct strlist *)stalloc(sizeof (struct strlist));
sp->text = p;
*exparg.lastp = sp;
exparg.lastp = &sp->next;
}
*exparg.lastp = NULL;
if (exparg.list) {
*arglist->lastp = exparg.list;
arglist->lastp = exparg.lastp;
}
out:
ifsfree();
}
STATIC void
argstr(char *p, int flag)
{
static const char spclchars[] = {
'=',
':',
CTLQUOTEMARK,
CTLENDVAR,
CTLESC,
CTLVAR,
CTLBACKQ,
CTLENDARI,
0
};
const char *reject = spclchars;
int c;
int breakall = (flag & (EXP_WORD | EXP_QUOTED)) == EXP_WORD;
int inquotes;
size_t length;
int startloc;
if (!(flag & EXP_VARTILDE)) {
reject += 2;
} else if (flag & EXP_VARTILDE2) {
reject++;
}
inquotes = 0;
length = 0;
if (flag & EXP_TILDE) {
char *q;
flag &= ~EXP_TILDE;
tilde:
q = p;
if (*q == '~')
p = exptilde(p, q, flag);
}
start:
startloc = expdest - (char *)stackblock();
for (;;) {
length += strcspn(p + length, reject);
c = (signed char)p[length];
if (c && (!(c & 0x80) || c == CTLENDARI)) {
length++;
}
if (length > 0) {
int newloc;
expdest = stnputs(p, length, expdest);
newloc = expdest - (char *)stackblock();
if (breakall && !inquotes && newloc > startloc) {
recordregion(startloc, newloc, 0);
}
startloc = newloc;
}
p += length + 1;
length = 0;
switch (c) {
case '\0':
goto breakloop;
case '=':
if (flag & EXP_VARTILDE2) {
p--;
continue;
}
flag |= EXP_VARTILDE2;
reject++;
case ':':
if (*--p == '~') {
goto tilde;
}
continue;
}
switch (c) {
case CTLENDVAR: 
goto breakloop;
case CTLQUOTEMARK:
inquotes ^= EXP_QUOTED;
if (inquotes && !memcmp(p, dolatstr + 1,
DOLATSTRLEN - 1)) {
p = evalvar(p + 1, flag | inquotes) + 1;
goto start;
}
addquote:
if (flag & QUOTES_ESC) {
p--;
length++;
startloc++;
}
break;
case CTLESC:
startloc++;
length++;
if (((flag | inquotes) & (EXP_QPAT | EXP_QUOTED)) ==
EXP_QPAT && *p != '\\')
break;
goto addquote;
case CTLVAR:
p = evalvar(p, flag | inquotes);
goto start;
case CTLBACKQ:
expbackq(argbackq->n, flag | inquotes);
argbackq = argbackq->next;
goto start;
case CTLENDARI:
p--;
expari(flag | inquotes);
goto start;
}
}
breakloop:
;
}
STATIC char *
exptilde(char *startp, char *p, int flag)
{
signed char c;
char *name;
const char *home;
int quotes = flag & QUOTES_ESC;
name = p + 1;
while ((c = *++p) != '\0') {
switch(c) {
case CTLESC:
return (startp);
case CTLQUOTEMARK:
return (startp);
case ':':
if (flag & EXP_VARTILDE)
goto done;
break;
case '/':
case CTLENDVAR:
goto done;
}
}
done:
*p = '\0';
if (*name == '\0') {
home = lookupvar(homestr);
} else {
home = getpwhome(name);
}
if (!home || !*home)
goto lose;
*p = c;
strtodest(home, SQSYNTAX, quotes);
return (p);
lose:
*p = c;
return (startp);
}
void 
removerecordregions(int endoff)
{
if (ifslastp == NULL)
return;
if (ifsfirst.endoff > endoff) {
while (ifsfirst.next != NULL) {
struct ifsregion *ifsp;
INTOFF;
ifsp = ifsfirst.next->next;
ckfree(ifsfirst.next);
ifsfirst.next = ifsp;
INTON;
}
if (ifsfirst.begoff > endoff)
ifslastp = NULL;
else {
ifslastp = &ifsfirst;
ifsfirst.endoff = endoff;
}
return;
}
ifslastp = &ifsfirst;
while (ifslastp->next && ifslastp->next->begoff < endoff)
ifslastp=ifslastp->next;
while (ifslastp->next != NULL) {
struct ifsregion *ifsp;
INTOFF;
ifsp = ifslastp->next->next;
ckfree(ifslastp->next);
ifslastp->next = ifsp;
INTON;
}
if (ifslastp->endoff > endoff)
ifslastp->endoff = endoff;
}
void
expari(int flag)
{
struct stackmark sm;
char *p, *start;
int begoff;
int len;
intmax_t result;
start = stackblock();
p = expdest;
pushstackmark(&sm, p - start);
*--p = '\0';
p--;
do {
int esc;
while (*p != (char)CTLARI) {
p--;
#ifdef DEBUG
if (p < start) {
sh_error("missing CTLARI (shouldn't happen)");
}
#endif
}
esc = esclen(start, p);
if (!(esc % 2)) {
break;
}
p -= esc + 1;
} while (1);
begoff = p - start;
removerecordregions(begoff);
expdest = p;
if (likely(flag & QUOTES_ESC))
rmescapes(p + 1);
result = arith(p + 1);
popstackmark(&sm);
len = cvtnum(result);
if (likely(!(flag & EXP_QUOTED)))
recordregion(begoff, begoff + len, 0);
}
STATIC void
expbackq(union node *cmd, int flag)
{
struct backcmd in;
int i;
char buf[128];
char *p;
char *dest;
int startloc;
char const *syntax = flag & EXP_QUOTED ? DQSYNTAX : BASESYNTAX;
struct stackmark smark;
INTOFF;
startloc = expdest - (char *)stackblock();
pushstackmark(&smark, startloc);
evalbackcmd(cmd, (struct backcmd *) &in);
popstackmark(&smark);
p = in.buf;
i = in.nleft;
if (i == 0)
goto read;
for (;;) {
memtodest(p, i, syntax, flag & QUOTES_ESC);
read:
if (in.fd < 0)
break;
do {
i = read(in.fd, buf, sizeof buf);
} while (i < 0 && errno == EINTR);
TRACE(("expbackq: read returns %d\n", i));
if (i <= 0)
break;
p = buf;
}
if (in.buf)
ckfree(in.buf);
if (in.fd >= 0) {
close(in.fd);
back_exitstatus = waitforjob(in.jp);
}
INTON;
dest = expdest;
for (; dest > (char *)stackblock() && dest[-1] == '\n';)
STUNPUTC(dest);
expdest = dest;
if (!(flag & EXP_QUOTED))
recordregion(startloc, dest - (char *)stackblock(), 0);
TRACE(("evalbackq: size=%d: \"%.*s\"\n",
(dest - (char *)stackblock()) - startloc,
(dest - (char *)stackblock()) - startloc,
stackblock() + startloc));
}
STATIC char *
scanleft(
char *startp, char *rmesc, char *rmescend, char *str, int quotes,
int zero
) {
char *loc;
char *loc2;
char c;
loc = startp;
loc2 = rmesc;
do {
int match;
const char *s = loc2;
c = *loc2;
if (zero) {
*loc2 = '\0';
s = rmesc;
}
match = pmatch(str, s);
*loc2 = c;
if (match)
return loc;
if (quotes && *loc == (char)CTLESC)
loc++;
loc++;
loc2++;
} while (c);
return 0;
}
STATIC char *
scanright(
char *startp, char *rmesc, char *rmescend, char *str, int quotes,
int zero
) {
int esc = 0;
char *loc;
char *loc2;
for (loc = str - 1, loc2 = rmescend; loc >= startp; loc2--) {
int match;
char c = *loc2;
const char *s = loc2;
if (zero) {
*loc2 = '\0';
s = rmesc;
}
match = pmatch(str, s);
*loc2 = c;
if (match)
return loc;
loc--;
if (quotes) {
if (--esc < 0) {
esc = esclen(startp, loc);
}
if (esc % 2) {
esc--;
loc--;
}
}
}
return 0;
}
STATIC const char *
subevalvar(char *p, char *str, int strloc, int subtype, int startloc, int varflags, int flag)
{
int quotes = flag & QUOTES_ESC;
char *startp;
char *loc;
struct nodelist *saveargbackq = argbackq;
int amount;
char *rmesc, *rmescend;
int zero;
char *(*scan)(char *, char *, char *, char *, int , int);
argstr(p, EXP_TILDE | (subtype != VSASSIGN && subtype != VSQUESTION ?
(flag & EXP_QUOTED ? EXP_QPAT : EXP_CASE) : 0));
STPUTC('\0', expdest);
argbackq = saveargbackq;
startp = stackblock() + startloc;
switch (subtype) {
case VSASSIGN:
setvar(str, startp, 0);
amount = startp - expdest;
STADJUST(amount, expdest);
return startp;
case VSQUESTION:
varunset(p, str, startp, varflags);
}
subtype -= VSTRIMRIGHT;
#ifdef DEBUG
if (subtype < 0 || subtype > 3)
abort();
#endif
rmesc = startp;
rmescend = stackblock() + strloc;
if (quotes) {
rmesc = _rmescapes(startp, RMESCAPE_ALLOC | RMESCAPE_GROW);
if (rmesc != startp) {
rmescend = expdest;
startp = stackblock() + startloc;
}
}
rmescend--;
str = stackblock() + strloc;
preglob(str, 0);
zero = subtype >> 1;
scan = (subtype & 1) ^ zero ? scanleft : scanright;
loc = scan(startp, rmesc, rmescend, str, quotes, zero);
if (loc) {
if (zero) {
memmove(startp, loc, str - loc);
loc = startp + (str - loc) - 1;
}
*loc = '\0';
amount = loc - expdest;
STADJUST(amount, expdest);
}
return loc;
}
STATIC char *
evalvar(char *p, int flag)
{
int subtype;
int varflags;
char *var;
int patloc;
int c;
int startloc;
ssize_t varlen;
int easy;
int quoted;
varflags = *p++;
subtype = varflags & VSTYPE;
if (!subtype)
sh_error("Bad substitution");
quoted = flag & EXP_QUOTED;
var = p;
easy = (!quoted || (*var == '@' && shellparam.nparam));
startloc = expdest - (char *)stackblock();
p = strchr(p, '=') + 1;
again:
varlen = varvalue(var, varflags, flag);
if (varflags & VSNUL)
varlen--;
if (subtype == VSPLUS) {
varlen = -1 - varlen;
goto vsplus;
}
if (subtype == VSMINUS) {
vsplus:
if (varlen < 0) {
argstr(p, flag | EXP_TILDE | EXP_WORD);
goto end;
}
if (easy)
goto record;
goto end;
}
if (subtype == VSASSIGN || subtype == VSQUESTION) {
if (varlen < 0) {
if (subevalvar(p, var, 0, subtype, startloc,
varflags, flag & ~QUOTES_ESC)) {
varflags &= ~VSNUL;
removerecordregions(startloc);
goto again;
}
goto end;
}
if (easy)
goto record;
goto end;
}
if (varlen < 0 && uflag)
varunset(p, var, 0, 0);
if (subtype == VSLENGTH) {
cvtnum(varlen > 0 ? varlen : 0);
goto record;
}
if (subtype == VSNORMAL) {
if (!easy)
goto end;
record:
recordregion(startloc, expdest - (char *)stackblock(), quoted);
goto end;
}
#ifdef DEBUG
switch (subtype) {
case VSTRIMLEFT:
case VSTRIMLEFTMAX:
case VSTRIMRIGHT:
case VSTRIMRIGHTMAX:
break;
default:
abort();
}
#endif
if (varlen >= 0) {
STPUTC('\0', expdest);
patloc = expdest - (char *)stackblock();
if (subevalvar(p, NULL, patloc, subtype,
startloc, varflags, flag) == 0) {
int amount = expdest - (
(char *)stackblock() + patloc - 1
);
STADJUST(-amount, expdest);
}
removerecordregions(startloc);
goto record;
}
end:
if (subtype != VSNORMAL) { 
int nesting = 1;
for (;;) {
if ((c = (signed char)*p++) == CTLESC)
p++;
else if (c == CTLBACKQ) {
if (varlen >= 0)
argbackq = argbackq->next;
} else if (c == CTLVAR) {
if ((*p++ & VSTYPE) != VSNORMAL)
nesting++;
} else if (c == CTLENDVAR) {
if (--nesting == 0)
break;
}
}
}
return p;
}
STATIC void
memtodest(const char *p, size_t len, const char *syntax, int quotes) {
char *q;
if (unlikely(!len))
return;
q = makestrspace(len * 2, expdest);
do {
int c = (signed char)*p++;
if (c) {
if ((quotes & QUOTES_ESC) &&
((syntax[c] == CCTL) ||
(((quotes & EXP_FULL) || syntax != BASESYNTAX) &&
syntax[c] == CBACK)))
USTPUTC(CTLESC, q);
} else if (!(quotes & QUOTES_KEEPNUL))
continue;
USTPUTC(c, q);
} while (--len);
expdest = q;
}
STATIC size_t
strtodest(p, syntax, quotes)
const char *p;
const char *syntax;
int quotes;
{
size_t len = strlen(p);
memtodest(p, len, syntax, quotes);
return len;
}
STATIC ssize_t
varvalue(char *name, int varflags, int flags)
{
int num;
char *p;
int i;
int sep;
char sepc;
char **ap;
char const *syntax;
int quoted = flags & EXP_QUOTED;
int subtype = varflags & VSTYPE;
int discard = subtype == VSPLUS || subtype == VSLENGTH;
int quotes = (discard ? 0 : (flags & QUOTES_ESC)) | QUOTES_KEEPNUL;
ssize_t len = 0;
sep = quoted ? ((flags & EXP_FULL) << CHAR_BIT) : 0;
syntax = quoted ? DQSYNTAX : BASESYNTAX;
switch (*name) {
case '$':
num = rootpid;
goto numvar;
case '?':
num = exitstatus;
goto numvar;
case '#':
num = shellparam.nparam;
goto numvar;
case '!':
num = backgndpid;
if (num == 0)
return -1;
numvar:
len = cvtnum(num);
break;
case '-':
p = makestrspace(NOPTS, expdest);
for (i = NOPTS - 1; i >= 0; i--) {
if (optlist[i]) {
USTPUTC(optletters[i], p);
len++;
}
}
expdest = p;
break;
case '@':
if (sep)
goto param;
case '*':
sep = ifsset() ? ifsval()[0] : ' ';
param:
if (!(ap = shellparam.p))
return -1;
sepc = sep;
while ((p = *ap++)) {
len += strtodest(p, syntax, quotes);
if (*ap && sep) {
len++;
memtodest(&sepc, 1, syntax, quotes);
}
}
break;
case '0':
case '1':
case '2':
case '3':
case '4':
case '5':
case '6':
case '7':
case '8':
case '9':
num = atoi(name);
if (num < 0 || num > shellparam.nparam)
return -1;
p = num ? shellparam.p[num - 1] : arg0;
goto value;
default:
p = lookupvar(name);
value:
if (!p)
return -1;
len = strtodest(p, syntax, quotes);
break;
}
if (discard)
STADJUST(-len, expdest);
return len;
}
void
recordregion(int start, int end, int nulonly)
{
struct ifsregion *ifsp;
if (ifslastp == NULL) {
ifsp = &ifsfirst;
} else {
INTOFF;
ifsp = (struct ifsregion *)ckmalloc(sizeof (struct ifsregion));
ifsp->next = NULL;
ifslastp->next = ifsp;
INTON;
}
ifslastp = ifsp;
ifslastp->begoff = start;
ifslastp->endoff = end;
ifslastp->nulonly = nulonly;
}
void
ifsbreakup(char *string, struct arglist *arglist)
{
struct ifsregion *ifsp;
struct strlist *sp;
char *start;
char *p;
char *q;
const char *ifs, *realifs;
int ifsspc;
int nulonly;
start = string;
if (ifslastp != NULL) {
ifsspc = 0;
nulonly = 0;
realifs = ifsset() ? ifsval() : defifs;
ifsp = &ifsfirst;
do {
p = string + ifsp->begoff;
nulonly = ifsp->nulonly;
ifs = nulonly ? nullstr : realifs;
ifsspc = 0;
while (p < string + ifsp->endoff) {
q = p;
if (*p == (char)CTLESC)
p++;
if (strchr(ifs, *p)) {
if (!nulonly)
ifsspc = (strchr(defifs, *p) != NULL);
if (q == start && ifsspc) {
p++;
start = p;
continue;
}
*q = '\0';
sp = (struct strlist *)stalloc(sizeof *sp);
sp->text = start;
*arglist->lastp = sp;
arglist->lastp = &sp->next;
p++;
if (!nulonly) {
for (;;) {
if (p >= string + ifsp->endoff) {
break;
}
q = p;
if (*p == (char)CTLESC)
p++;
if (strchr(ifs, *p) == NULL ) {
p = q;
break;
} else if (strchr(defifs, *p) == NULL) {
if (ifsspc) {
p++;
ifsspc = 0;
} else {
p = q;
break;
}
} else
p++;
}
}
start = p;
} else
p++;
}
} while ((ifsp = ifsp->next) != NULL);
if (nulonly)
goto add;
}
if (!*start)
return;
add:
sp = (struct strlist *)stalloc(sizeof *sp);
sp->text = start;
*arglist->lastp = sp;
arglist->lastp = &sp->next;
}
void ifsfree(void)
{
struct ifsregion *p = ifsfirst.next;
if (!p)
goto out;
INTOFF;
do {
struct ifsregion *ifsp;
ifsp = p->next;
ckfree(p);
p = ifsp;
} while (p);
ifsfirst.next = NULL;
INTON;
out:
ifslastp = NULL;
}
#ifdef HAVE_GLOB
STATIC void
expandmeta(str, flag)
struct strlist *str;
int flag;
{
while (str) {
const char *p;
glob_t pglob;
int i;
if (fflag)
goto nometa;
INTOFF;
p = preglob(str->text, RMESCAPE_ALLOC | RMESCAPE_HEAP);
i = glob(p, GLOB_NOMAGIC, 0, &pglob);
if (p != str->text)
ckfree(p);
switch (i) {
case 0:
if (!(pglob.gl_flags & GLOB_MAGCHAR))
goto nometa2;
addglob(&pglob);
globfree(&pglob);
INTON;
break;
case GLOB_NOMATCH:
nometa2:
globfree(&pglob);
INTON;
nometa:
*exparg.lastp = str;
rmescapes(str->text);
exparg.lastp = &str->next;
break;
default: 
sh_error("Out of space");
}
str = str->next;
}
}
STATIC void
addglob(pglob)
const glob_t *pglob;
{
char **p = pglob->gl_pathv;
do {
addfname(*p);
} while (*++p);
}
#else 
STATIC char *expdir;
STATIC void
expandmeta(struct strlist *str, int flag)
{
static const char metachars[] = {
'*', '?', '[', 0
};
while (str) {
struct strlist **savelastp;
struct strlist *sp;
char *p;
if (fflag)
goto nometa;
if (!strpbrk(str->text, metachars))
goto nometa;
savelastp = exparg.lastp;
INTOFF;
p = preglob(str->text, RMESCAPE_ALLOC | RMESCAPE_HEAP);
{
int i = strlen(str->text);
expdir = ckmalloc(i < 2048 ? 2048 : i); 
}
expmeta(expdir, p);
ckfree(expdir);
if (p != str->text)
ckfree(p);
INTON;
if (exparg.lastp == savelastp) {
nometa:
*exparg.lastp = str;
rmescapes(str->text);
exparg.lastp = &str->next;
} else {
*exparg.lastp = NULL;
*savelastp = sp = expsort(*savelastp);
while (sp->next != NULL)
sp = sp->next;
exparg.lastp = &sp->next;
}
str = str->next;
}
}
STATIC void
expmeta(char *enddir, char *name)
{
char *p;
const char *cp;
char *start;
char *endname;
int metaflag;
struct stat64 statb;
DIR *dirp;
struct dirent *dp;
int atend;
int matchdot;
int esc;
metaflag = 0;
start = name;
for (p = name; esc = 0, *p; p += esc + 1) {
if (*p == '*' || *p == '?')
metaflag = 1;
else if (*p == '[') {
char *q = p + 1;
if (*q == '!')
q++;
for (;;) {
if (*q == '\\')
q++;
if (*q == '/' || *q == '\0')
break;
if (*++q == ']') {
metaflag = 1;
break;
}
}
} else {
if (*p == '\\')
esc++;
if (p[esc] == '/') {
if (metaflag)
break;
start = p + esc + 1;
}
}
}
if (metaflag == 0) { 
if (enddir != expdir)
metaflag++;
p = name;
do {
if (*p == '\\')
p++;
*enddir++ = *p;
} while (*p++);
if (metaflag == 0 || lstat64(expdir, &statb) >= 0)
addfname(expdir);
return;
}
endname = p;
if (name < start) {
p = name;
do {
if (*p == '\\')
p++;
*enddir++ = *p++;
} while (p < start);
}
if (enddir == expdir) {
cp = ".";
} else if (enddir == expdir + 1 && *expdir == '/') {
cp = "/";
} else {
cp = expdir;
enddir[-1] = '\0';
}
if ((dirp = opendir(cp)) == NULL)
return;
if (enddir != expdir)
enddir[-1] = '/';
if (*endname == 0) {
atend = 1;
} else {
atend = 0;
*endname = '\0';
endname += esc + 1;
}
matchdot = 0;
p = start;
if (*p == '\\')
p++;
if (*p == '.')
matchdot++;
while (! int_pending() && (dp = readdir(dirp)) != NULL) {
if (dp->d_name[0] == '.' && ! matchdot)
continue;
if (pmatch(start, dp->d_name)) {
if (atend) {
scopy(dp->d_name, enddir);
addfname(expdir);
} else {
for (p = enddir, cp = dp->d_name;
(*p++ = *cp++) != '\0';)
continue;
p[-1] = '/';
expmeta(p, endname);
}
}
}
closedir(dirp);
if (! atend)
endname[-esc - 1] = esc ? '\\' : '/';
}
#endif 
STATIC void
addfname(char *name)
{
struct strlist *sp;
sp = (struct strlist *)stalloc(sizeof *sp);
sp->text = sstrdup(name);
*exparg.lastp = sp;
exparg.lastp = &sp->next;
}
#ifndef HAVE_GLOB
STATIC struct strlist *
expsort(struct strlist *str)
{
int len;
struct strlist *sp;
len = 0;
for (sp = str ; sp ; sp = sp->next)
len++;
return msort(str, len);
}
STATIC struct strlist *
msort(struct strlist *list, int len)
{
struct strlist *p, *q = NULL;
struct strlist **lpp;
int half;
int n;
if (len <= 1)
return list;
half = len >> 1;
p = list;
for (n = half ; --n >= 0 ; ) {
q = p;
p = p->next;
}
q->next = NULL; 
q = msort(list, half); 
p = msort(p, len - half); 
lpp = &list;
for (;;) {
if (strcmp(p->text, q->text) < 0) {
*lpp = p;
lpp = &p->next;
if ((p = *lpp) == NULL) {
*lpp = q;
break;
}
} else {
*lpp = q;
lpp = &q->next;
if ((q = *lpp) == NULL) {
*lpp = p;
break;
}
}
}
return list;
}
#endif
STATIC inline int
patmatch(char *pattern, const char *string)
{
return pmatch(preglob(pattern, 0), string);
}
#ifndef HAVE_FNMATCH
STATIC int ccmatch(const char *p, int chr, const char **r)
{
static const struct class {
char name[10];
int (*fn)(int);
} classes[] = {
{ .name = ":alnum:]", .fn = isalnum },
{ .name = ":cntrl:]", .fn = iscntrl },
{ .name = ":lower:]", .fn = islower },
{ .name = ":space:]", .fn = isspace },
{ .name = ":alpha:]", .fn = isalpha },
{ .name = ":digit:]", .fn = isdigit },
{ .name = ":print:]", .fn = isprint },
{ .name = ":upper:]", .fn = isupper },
{ .name = ":blank:]", .fn = isblank },
{ .name = ":graph:]", .fn = isgraph },
{ .name = ":punct:]", .fn = ispunct },
{ .name = ":xdigit:]", .fn = isxdigit },
};
const struct class *class, *end;
end = classes + sizeof(classes) / sizeof(classes[0]);
for (class = classes; class < end; class++) {
const char *q;
q = prefix(p, class->name);
if (!q)
continue;
*r = q;
return class->fn(chr);
}
*r = 0;
return 0;
}
STATIC int
pmatch(const char *pattern, const char *string)
{
const char *p, *q;
char c;
p = pattern;
q = string;
for (;;) {
switch (c = *p++) {
case '\0':
goto breakloop;
case '\\':
if (*p) {
c = *p++;
}
goto dft;
case '?':
if (*q++ == '\0')
return 0;
break;
case '*':
c = *p;
while (c == '*')
c = *++p;
if (c != '\\' && c != '?' && c != '*' && c != '[') {
while (*q != c) {
if (*q == '\0')
return 0;
q++;
}
}
do {
if (pmatch(p, q))
return 1;
} while (*q++ != '\0');
return 0;
case '[': {
const char *startp;
int invert, found;
char chr;
startp = p;
invert = 0;
if (*p == '!') {
invert++;
p++;
}
found = 0;
chr = *q++;
if (chr == '\0')
return 0;
c = *p++;
do {
if (!c) {
p = startp;
c = *p;
goto dft;
}
if (c == '[') {
const char *r;
found |= !!ccmatch(p, chr, &r);
if (r) {
p = r;
continue;
}
} else if (c == '\\')
c = *p++;
if (*p == '-' && p[1] != ']') {
p++;
if (*p == '\\')
p++;
if (chr >= c && chr <= *p)
found = 1;
p++;
} else {
if (chr == c)
found = 1;
}
} while ((c = *p++) != ']');
if (found == invert)
return 0;
break;
}
dft: default:
if (*q++ != c)
return 0;
break;
}
}
breakloop:
if (*q != '\0')
return 0;
return 1;
}
#endif
char *
_rmescapes(char *str, int flag)
{
char *p, *q, *r;
unsigned inquotes;
int notescaped;
int globbing;
p = strpbrk(str, qchars);
if (!p) {
return str;
}
q = p;
r = str;
if (flag & RMESCAPE_ALLOC) {
size_t len = p - str;
size_t fulllen = len + strlen(p) + 1;
if (flag & RMESCAPE_GROW) {
int strloc = str - (char *)stackblock();
r = makestrspace(fulllen, expdest);
str = (char *)stackblock() + strloc;
p = str + len;
} else if (flag & RMESCAPE_HEAP) {
r = ckmalloc(fulllen);
} else {
r = stalloc(fulllen);
}
q = r;
if (len > 0) {
q = mempcpy(q, str, len);
}
}
inquotes = 0;
globbing = flag & RMESCAPE_GLOB;
notescaped = globbing;
while (*p) {
if (*p == (char)CTLQUOTEMARK) {
inquotes = ~inquotes;
p++;
notescaped = globbing;
continue;
}
if (*p == (char)CTLESC) {
p++;
if (notescaped)
*q++ = '\\';
} else if (*p == '\\' && !inquotes) {
notescaped = 0;
goto copy;
}
notescaped = globbing;
copy:
*q++ = *p++;
}
*q = '\0';
if (flag & RMESCAPE_GROW) {
expdest = r;
STADJUST(q - r + 1, expdest);
}
return r;
}
int
casematch(union node *pattern, char *val)
{
struct stackmark smark;
int result;
setstackmark(&smark);
argbackq = pattern->narg.backquote;
STARTSTACKSTR(expdest);
argstr(pattern->narg.text, EXP_TILDE | EXP_CASE);
STACKSTRNUL(expdest);
ifsfree();
result = patmatch(stackblock(), val);
popstackmark(&smark);
return result;
}
STATIC int
cvtnum(intmax_t num)
{
int len = max_int_length(sizeof(num));
expdest = makestrspace(len, expdest);
len = fmtstr(expdest, len, "%" PRIdMAX, num);
STADJUST(len, expdest);
return len;
}
STATIC void
varunset(const char *end, const char *var, const char *umsg, int varflags)
{
const char *msg;
const char *tail;
tail = nullstr;
msg = "parameter not set";
if (umsg) {
if (*end == (char)CTLENDVAR) {
if (varflags & VSNUL)
tail = " or null";
} else
msg = umsg;
}
sh_error("%.*s: %s%s", end - var - 1, var, msg, tail);
}
#ifdef mkinit
INCLUDE "expand.h"
RESET {
ifsfree();
}
#endif
#include <sys/param.h>
#ifdef HAVE_PATHS_H
#include <paths.h>
#endif
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#ifndef SMALL
#define MAXHISTLOOPS 4 
#define DEFEDITOR "ed" 
History *hist; 
EditLine *el; 
int displayhist;
static FILE *el_in, *el_out;
STATIC const char *fc_replace(const char *, char *, char *);
#ifdef DEBUG
extern FILE *tracefile;
#endif
void
histedit(void)
{
FILE *el_err;
#define editing (Eflag || Vflag)
if (iflag) {
if (!hist) {
INTOFF;
hist = history_init();
INTON;
if (hist != NULL)
sethistsize(histsizeval());
else
out2str("sh: can't initialize history\n");
}
if (editing && !el && isatty(0)) { 
INTOFF;
if (el_in == NULL)
el_in = fdopen(0, "r");
if (el_out == NULL)
el_out = fdopen(2, "w");
if (el_in == NULL || el_out == NULL)
goto bad;
el_err = el_out;
#if DEBUG
if (tracefile)
el_err = tracefile;
#endif
el = el_init(arg0, el_in, el_out, el_err);
if (el != NULL) {
if (hist)
el_set(el, EL_HIST, history, hist);
el_set(el, EL_PROMPT, getprompt);
} else {
bad:
out2str("sh: can't initialize editing\n");
}
INTON;
} else if (!editing && el) {
INTOFF;
el_end(el);
el = NULL;
INTON;
}
if (el) {
if (Vflag)
el_set(el, EL_EDITOR, "vi");
else if (Eflag)
el_set(el, EL_EDITOR, "emacs");
el_source(el, NULL);
}
} else {
INTOFF;
if (el) { 
el_end(el);
el = NULL;
}
if (hist) {
history_end(hist);
hist = NULL;
}
INTON;
}
}
void
sethistsize(const char *hs)
{
int histsize;
HistEvent he;
if (hist != NULL) {
if (hs == NULL || *hs == '\0' ||
(histsize = atoi(hs)) < 0)
histsize = 100;
history(hist, &he, H_SETSIZE, histsize);
}
}
void
setterm(const char *term)
{
if (el != NULL && term != NULL)
if (el_set(el, EL_TERMINAL, term) != 0) {
outfmt(out2, "sh: Can't set terminal type %s\n", term);
outfmt(out2, "sh: Using dumb terminal settings.\n");
}
}
int
histcmd(int argc, char **argv)
{
int ch;
const char *editor = NULL;
HistEvent he;
int lflg = 0, nflg = 0, rflg = 0, sflg = 0;
int i, retval;
const char *firststr, *laststr;
int first, last, direction;
char *pat = NULL, *repl; 
static int active = 0;
struct jmploc jmploc;
struct jmploc *volatile savehandler;
char editfile[MAXPATHLEN + 1];
FILE *efp;
#ifdef __GNUC__
(void) &editor;
(void) &lflg;
(void) &nflg;
(void) &rflg;
(void) &sflg;
(void) &firststr;
(void) &laststr;
(void) &pat;
(void) &repl;
(void) &efp;
(void) &argc;
(void) &argv;
#endif
if (hist == NULL)
sh_error("history not active");
if (argc == 1)
sh_error("missing history argument");
#ifdef __GLIBC__
optind = 0;
#else
optreset = 1; optind = 1; 
#endif
while (not_fcnumber(argv[optind]) &&
(ch = getopt(argc, argv, ":e:lnrs")) != -1)
switch ((char)ch) {
case 'e':
editor = optionarg;
break;
case 'l':
lflg = 1;
break;
case 'n':
nflg = 1;
break;
case 'r':
rflg = 1;
break;
case 's':
sflg = 1;
break;
case ':':
sh_error("option -%c expects argument", optopt);
case '?':
default:
sh_error("unknown option: -%c", optopt);
}
argc -= optind, argv += optind;
if (lflg == 0 || editor || sflg) {
lflg = 0; 
editfile[0] = '\0';
if (setjmp(jmploc.loc)) {
active = 0;
if (*editfile)
unlink(editfile);
handler = savehandler;
longjmp(handler->loc, 1);
}
savehandler = handler;
handler = &jmploc;
if (++active > MAXHISTLOOPS) {
active = 0;
displayhist = 0;
sh_error("called recursively too many times");
}
if (sflg == 0) {
if (editor == NULL &&
(editor = bltinlookup("FCEDIT")) == NULL &&
(editor = bltinlookup("EDITOR")) == NULL)
editor = DEFEDITOR;
if (editor[0] == '-' && editor[1] == '\0') {
sflg = 1; 
editor = NULL;
}
}
}
if (lflg == 0 && argc > 0 &&
((repl = strchr(argv[0], '=')) != NULL)) {
pat = argv[0];
*repl++ = '\0';
argc--, argv++;
}
switch (argc) {
case 0:
firststr = lflg ? "-16" : "-1";
laststr = "-1";
break;
case 1:
firststr = argv[0];
laststr = lflg ? "-1" : argv[0];
break;
case 2:
firststr = argv[0];
laststr = argv[1];
break;
default:
sh_error("too many args");
}
first = str_to_event(firststr, 0);
last = str_to_event(laststr, 1);
if (rflg) {
i = last;
last = first;
first = i;
}
direction = first < last ? H_PREV : H_NEXT;
if (editor) {
int fd;
INTOFF; 
sprintf(editfile, "%s_shXXXXXX", _PATH_TMP);
if ((fd = mkstemp(editfile)) < 0)
sh_error("can't create temporary file %s", editfile);
if ((efp = fdopen(fd, "w")) == NULL) {
close(fd);
sh_error("can't allocate stdio buffer for temp");
}
}
history(hist, &he, H_FIRST);
retval = history(hist, &he, H_NEXT_EVENT, first);
for (;retval != -1; retval = history(hist, &he, direction)) {
if (lflg) {
if (!nflg)
out1fmt("%5d ", he.num);
out1str(he.str);
} else {
const char *s = pat ?
fc_replace(he.str, pat, repl) : he.str;
if (sflg) {
if (displayhist) {
out2str(s);
}
evalstring(strcpy(stalloc(strlen(s) + 1), s),
0);
if (displayhist && hist) {
history(hist, &he, H_ENTER, s);
}
} else
fputs(s, efp);
}
if (he.num == last)
break;
}
if (editor) {
char *editcmd;
fclose(efp);
editcmd = stalloc(strlen(editor) + strlen(editfile) + 2);
sprintf(editcmd, "%s %s", editor, editfile);
evalstring(editcmd, 0);
INTON;
readcmdfile(editfile); 
unlink(editfile);
}
if (lflg == 0 && active > 0)
--active;
if (displayhist)
displayhist = 0;
return 0;
}
STATIC const char *
fc_replace(const char *s, char *p, char *r)
{
char *dest;
int plen = strlen(p);
STARTSTACKSTR(dest);
while (*s) {
if (*s == *p && strncmp(s, p, plen) == 0) {
while (*r)
STPUTC(*r++, dest);
s += plen;
*p = '\0'; 
} else
STPUTC(*s++, dest);
}
STACKSTRNUL(dest);
dest = grabstackstr(dest);
return (dest);
}
int
not_fcnumber(char *s)
{
if (s == NULL)
return 0;
if (*s == '-')
s++;
return (!is_number(s));
}
int
str_to_event(const char *str, int last)
{
HistEvent he;
const char *s = str;
int relative = 0;
int i, retval;
retval = history(hist, &he, H_FIRST);
switch (*s) {
case '-':
relative = 1;
case '+':
s++;
}
if (is_number(s)) {
i = atoi(s);
if (relative) {
while (retval != -1 && i--) {
retval = history(hist, &he, H_NEXT);
}
if (retval == -1)
retval = history(hist, &he, H_LAST);
} else {
retval = history(hist, &he, H_NEXT_EVENT, i);
if (retval == -1) {
retval = history(hist, &he,
last ? H_FIRST : H_LAST);
}
}
if (retval == -1)
sh_error("history number %s not found (internal error)",
str);
} else {
retval = history(hist, &he, H_PREV_STR, str);
if (retval == -1)
sh_error("history pattern not found: %s", str);
}
return (he.num);
}
#endif
#include <stdio.h> 
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#ifndef SMALL
#endif
#ifdef HETIO
#endif
#define EOF_NLEFT -99 
#define IBUFSIZ (BUFSIZ + 1)
MKINIT
struct strpush {
struct strpush *prev; 
char *prevstring;
int prevnleft;
struct alias *ap; 
char *string; 
};
MKINIT
struct parsefile {
struct parsefile *prev; 
int linno; 
int fd; 
int nleft; 
int lleft; 
char *nextc; 
char *buf; 
struct strpush *strpush; 
struct strpush basestrpush; 
};
int plinno = 1; 
int parsenleft; 
MKINIT int parselleft; 
char *parsenextc; 
MKINIT struct parsefile basepf; 
MKINIT char basebuf[IBUFSIZ]; 
struct parsefile *parsefile = &basepf; 
int whichprompt; 
#ifndef SMALL
EditLine *el; 
#endif
STATIC void pushfile(void);
static int preadfd(void);
static void setinputfd(int fd, int push);
#ifdef mkinit
INCLUDE <stdio.h>
INCLUDE "input.h"
INCLUDE "error.h"
INIT {
basepf.nextc = basepf.buf = basebuf;
}
RESET {
parselleft = parsenleft = 0; 
popallfiles();
}
#endif
int
pgetc(void)
{
return pgetc_macro();
}
int
pgetc2()
{
int c;
do {
c = pgetc_macro();
} while (c == PEOA);
return c;
}
static int
preadfd(void)
{
int nr;
char *buf = parsefile->buf;
parsenextc = buf;
retry:
#ifndef SMALL
if (parsefile->fd == 0 && el) {
static const char *rl_cp;
static int el_len;
if (rl_cp == NULL)
rl_cp = el_gets(el, &el_len);
if (rl_cp == NULL)
nr = 0;
else {
nr = el_len;
if (nr > IBUFSIZ - 1)
nr = IBUFSIZ - 1;
memcpy(buf, rl_cp, nr);
if (nr != el_len) {
el_len -= nr;
rl_cp += nr;
} else
rl_cp = 0;
}
} else
#endif
#ifdef HETIO
nr = hetio_read_input(parsefile->fd);
if (nr == -255)
#endif
nr = read(parsefile->fd, buf, IBUFSIZ - 1);
if (nr < 0) {
if (errno == EINTR)
goto retry;
if (parsefile->fd == 0 && errno == EWOULDBLOCK) {
int flags = fcntl(0, F_GETFL, 0);
if (flags >= 0 && flags & O_NONBLOCK) {
flags &=~ O_NONBLOCK;
if (fcntl(0, F_SETFL, flags) >= 0) {
out2str("sh: turning off NDELAY mode\n");
goto retry;
}
}
}
}
return nr;
}
int
preadbuffer(void)
{
char *q;
int more;
#ifndef SMALL
int something;
#endif
char savec;
while (unlikely(parsefile->strpush)) {
if (
parsenleft == -1 && parsefile->strpush->ap &&
parsenextc[-1] != ' ' && parsenextc[-1] != '\t'
) {
return PEOA;
}
popstring();
if (--parsenleft >= 0)
return (signed char)*parsenextc++;
}
if (unlikely(parsenleft == EOF_NLEFT || parsefile->buf == NULL))
return PEOF;
flushout(&output);
#ifdef FLUSHERR
flushout(&errout);
#endif
more = parselleft;
if (more <= 0) {
again:
if ((more = preadfd()) <= 0) {
parselleft = parsenleft = EOF_NLEFT;
return PEOF;
}
}
q = parsenextc;
#ifndef SMALL
something = 0;
#endif
for (;;) {
int c;
more--;
c = *q;
if (!c)
memmove(q, q + 1, more);
else {
q++;
if (c == '\n') {
parsenleft = q - parsenextc - 1;
break;
}
#ifndef SMALL
switch (c) {
default:
something = 1;
case '\t':
case ' ':
break;
}
#endif
}
if (more <= 0) {
parsenleft = q - parsenextc - 1;
if (parsenleft < 0)
goto again;
break;
}
}
parselleft = more;
savec = *q;
*q = '\0';
#ifndef SMALL
if (parsefile->fd == 0 && hist && something) {
HistEvent he;
INTOFF;
history(hist, &he, whichprompt == 1? H_ENTER : H_APPEND,
parsenextc);
INTON;
}
#endif
if (vflag) {
out2str(parsenextc);
#ifdef FLUSHERR
flushout(out2);
#endif
}
*q = savec;
return (signed char)*parsenextc++;
}
void
pungetc(void)
{
parsenleft++;
parsenextc--;
}
void
pushstring(char *s, void *ap)
{
struct strpush *sp;
size_t len;
len = strlen(s);
INTOFF;
if (parsefile->strpush) {
sp = ckmalloc(sizeof (struct strpush));
sp->prev = parsefile->strpush;
parsefile->strpush = sp;
} else
sp = parsefile->strpush = &(parsefile->basestrpush);
sp->prevstring = parsenextc;
sp->prevnleft = parsenleft;
sp->ap = (struct alias *)ap;
if (ap) {
((struct alias *)ap)->flag |= ALIASINUSE;
sp->string = s;
}
parsenextc = s;
parsenleft = len;
INTON;
}
void
popstring(void)
{
struct strpush *sp = parsefile->strpush;
INTOFF;
if (sp->ap) {
if (parsenextc[-1] == ' ' || parsenextc[-1] == '\t') {
checkkwd |= CHKALIAS;
}
if (sp->string != sp->ap->val) {
ckfree(sp->string);
}
sp->ap->flag &= ~ALIASINUSE;
if (sp->ap->flag & ALIASDEAD) {
unalias(sp->ap->name);
}
}
parsenextc = sp->prevstring;
parsenleft = sp->prevnleft;
parsefile->strpush = sp->prev;
if (sp != &(parsefile->basestrpush))
ckfree(sp);
INTON;
}
int
setinputfile(const char *fname, int flags)
{
int fd;
INTOFF;
if ((fd = open(fname, O_RDONLY)) < 0) {
if (flags & INPUT_NOFILE_OK)
goto out;
exitstatus = 127;
exerror(EXERROR, "Can't open %s", fname);
}
if (fd < 10)
fd = savefd(fd, fd);
setinputfd(fd, flags & INPUT_PUSH_FILE);
out:
INTON;
return fd;
}
static void
setinputfd(int fd, int push)
{
if (push) {
pushfile();
parsefile->buf = 0;
}
parsefile->fd = fd;
if (parsefile->buf == NULL)
parsefile->buf = ckmalloc(IBUFSIZ);
parselleft = parsenleft = 0;
plinno = 1;
}
void
setinputstring(char *string)
{
INTOFF;
pushfile();
parsenextc = string;
parsenleft = strlen(string);
parsefile->buf = NULL;
plinno = 1;
INTON;
}
STATIC void
pushfile(void)
{
struct parsefile *pf;
parsefile->nleft = parsenleft;
parsefile->lleft = parselleft;
parsefile->nextc = parsenextc;
parsefile->linno = plinno;
pf = (struct parsefile *)ckmalloc(sizeof (struct parsefile));
pf->prev = parsefile;
pf->fd = -1;
pf->strpush = NULL;
pf->basestrpush.prev = NULL;
parsefile = pf;
}
void
popfile(void)
{
struct parsefile *pf = parsefile;
INTOFF;
if (pf->fd >= 0)
close(pf->fd);
if (pf->buf)
ckfree(pf->buf);
while (pf->strpush)
popstring();
parsefile = pf->prev;
ckfree(pf);
parsenleft = parsefile->nleft;
parselleft = parsefile->lleft;
parsenextc = parsefile->nextc;
plinno = parsefile->linno;
INTON;
}
void
popallfiles(void)
{
while (parsefile != &basepf)
popfile();
}
void
closescript(void)
{
popallfiles();
if (parsefile->fd > 0) {
close(parsefile->fd);
parsefile->fd = 0;
}
}
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
#include <stdlib.h>
#ifdef HAVE_PATHS_H
#include <paths.h>
#endif
#include <sys/types.h>
#include <sys/param.h>
#ifdef BSD
#include <sys/wait.h>
#include <sys/time.h>
#include <sys/resource.h>
#endif
#include <sys/ioctl.h>
#if JOBS
#include <termios.h>
#endif
#define CUR_DELETE 2
#define CUR_RUNNING 1
#define CUR_STOPPED 0
#define DOWAIT_NORMAL 0
#define DOWAIT_BLOCK 1
#define DOWAIT_WAITCMD 2
static struct job *jobtab;
static unsigned njobs;
pid_t backgndpid;
#if JOBS
static int initialpgrp;
static int ttyfd = -1;
#endif
static struct job *curjob;
static int jobless;
STATIC void set_curjob(struct job *, unsigned);
STATIC int jobno(const struct job *);
STATIC int sprint_status(char *, int, int);
STATIC void freejob(struct job *);
STATIC struct job *getjob(const char *, int);
STATIC struct job *growjobtab(void);
STATIC void forkchild(struct job *, union node *, int);
STATIC void forkparent(struct job *, union node *, int, pid_t);
STATIC int dowait(int, struct job *);
#ifdef SYSV
STATIC int onsigchild(void);
#endif
STATIC int waitproc(int, int *);
STATIC char *commandtext(union node *);
STATIC void cmdtxt(union node *);
STATIC void cmdlist(union node *, int);
STATIC void cmdputs(const char *);
STATIC void showpipe(struct job *, struct output *);
STATIC int getstatus(struct job *);
#if JOBS
static int restartjob(struct job *, int);
static void xtcsetpgrp(int, pid_t);
#endif
STATIC void
set_curjob(struct job *jp, unsigned mode)
{
struct job *jp1;
struct job **jpp, **curp;
jpp = curp = &curjob;
do {
jp1 = *jpp;
if (jp1 == jp)
break;
jpp = &jp1->prev_job;
} while (1);
*jpp = jp1->prev_job;
jpp = curp;
switch (mode) {
default:
#ifdef DEBUG
abort();
#endif
case CUR_DELETE:
break;
case CUR_RUNNING:
do {
jp1 = *jpp;
if (!JOBS || !jp1 || jp1->state != JOBSTOPPED)
break;
jpp = &jp1->prev_job;
} while (1);
#if JOBS
case CUR_STOPPED:
#endif
jp->prev_job = *jpp;
*jpp = jp;
break;
}
}
#if JOBS
int jobctl;
void
setjobctl(int on)
{
int fd;
int pgrp;
if (on == jobctl || rootshell == 0)
return;
if (on) {
int ofd;
ofd = fd = open(_PATH_TTY, O_RDWR);
if (fd < 0) {
fd += 3;
while (!isatty(fd))
if (--fd < 0)
goto out;
}
fd = savefd(fd, ofd);
do { 
if ((pgrp = tcgetpgrp(fd)) < 0) {
out:
sh_warnx("can't access tty; job control turned off");
mflag = on = 0;
goto close;
}
if (pgrp == getpgrp())
break;
killpg(0, SIGTTIN);
} while (1);
initialpgrp = pgrp;
setsignal(SIGTSTP);
setsignal(SIGTTOU);
setsignal(SIGTTIN);
pgrp = rootpid;
setpgid(0, pgrp);
xtcsetpgrp(fd, pgrp);
} else {
fd = ttyfd;
pgrp = initialpgrp;
xtcsetpgrp(fd, pgrp);
setpgid(0, pgrp);
setsignal(SIGTSTP);
setsignal(SIGTTOU);
setsignal(SIGTTIN);
close:
close(fd);
fd = -1;
}
ttyfd = fd;
jobctl = on;
}
#endif
int
killcmd(argc, argv)
int argc;
char **argv;
{
extern const char * const signal_names[];
int signo = -1;
int list = 0;
int i;
pid_t pid;
struct job *jp;
if (argc <= 1) {
usage:
sh_error(
"Usage: kill [-s sigspec | -signum | -sigspec] [pid | job]... or\n"
"kill -l [exitstatus]"
);
}
if (**++argv == '-') {
signo = decode_signal(*argv + 1, 1);
if (signo < 0) {
int c;
while ((c = nextopt("ls:")) != '\0')
switch (c) {
default:
#ifdef DEBUG
abort();
#endif
case 'l':
list = 1;
break;
case 's':
signo = decode_signal(optionarg, 1);
if (signo < 0) {
sh_error(
"invalid signal number or name: %s",
optionarg
);
}
break;
}
argv = argptr;
} else
argv++;
}
if (!list && signo < 0)
signo = SIGTERM;
if ((signo < 0 || !*argv) ^ list) {
goto usage;
}
if (list) {
struct output *out;
out = out1;
if (!*argv) {
outstr("0\n", out);
for (i = 1; i < NSIG; i++) {
outfmt(out, snlfmt, signal_names[i]);
}
return 0;
}
signo = number(*argv);
if (signo > 128)
signo -= 128;
if (0 < signo && signo < NSIG)
outfmt(out, snlfmt, signal_names[signo]);
else
sh_error("invalid signal number or exit status: %s",
*argv);
return 0;
}
i = 0;
do {
if (**argv == '%') {
jp = getjob(*argv, 0);
pid = -jp->ps[0].pid;
} else
pid = **argv == '-' ?
-number(*argv + 1) : number(*argv);
if (kill(pid, signo) != 0) {
sh_warnx("%s\n", strerror(errno));
i = 1;
}
} while (*++argv);
return i;
}
STATIC int
jobno(const struct job *jp)
{
return jp - jobtab + 1;
}
#if JOBS
int
fgcmd(int argc, char **argv)
{
struct job *jp;
struct output *out;
int mode;
int retval;
mode = (**argv == 'f') ? FORK_FG : FORK_BG;
nextopt(nullstr);
argv = argptr;
out = out1;
do {
jp = getjob(*argv, 1);
if (mode == FORK_BG) {
set_curjob(jp, CUR_RUNNING);
outfmt(out, "[%d] ", jobno(jp));
}
outstr(jp->ps->cmd, out);
showpipe(jp, out);
retval = restartjob(jp, mode);
} while (*argv && *++argv);
return retval;
}
int bgcmd(int argc, char **argv)
#ifdef HAVE_ALIAS_ATTRIBUTE
__attribute__((__alias__("fgcmd")));
#else
{
return fgcmd(argc, argv);
}
#endif
STATIC int
restartjob(struct job *jp, int mode)
{
struct procstat *ps;
int i;
int status;
pid_t pgid;
INTOFF;
if (jp->state == JOBDONE)
goto out;
jp->state = JOBRUNNING;
pgid = jp->ps->pid;
if (mode == FORK_FG)
xtcsetpgrp(ttyfd, pgid);
killpg(pgid, SIGCONT);
ps = jp->ps;
i = jp->nprocs;
do {
if (WIFSTOPPED(ps->status)) {
ps->status = -1;
}
} while (ps++, --i);
out:
status = (mode == FORK_FG) ? waitforjob(jp) : 0;
INTON;
return status;
}
#endif
STATIC int
sprint_status(char *s, int status, int sigonly)
{
int col;
int st;
col = 0;
st = WEXITSTATUS(status);
if (!WIFEXITED(status)) {
#if JOBS
st = WSTOPSIG(status);
if (!WIFSTOPPED(status))
#endif
st = WTERMSIG(status);
if (sigonly) {
if (st == SIGINT || st == SIGPIPE)
goto out;
#if JOBS
if (WIFSTOPPED(status))
goto out;
#endif
}
col = fmtstr(s, 32, "%s", strsignal(st));
#ifdef WCOREDUMP
if (WCOREDUMP(status)) {
col += fmtstr(s + col, 16, " (core dumped)");
}
#endif
} else if (!sigonly) {
if (st)
col = fmtstr(s, 16, "Done(%d)", st);
else
col = fmtstr(s, 16, "Done");
}
out:
return col;
}
static void
showjob(struct output *out, struct job *jp, int mode)
{
struct procstat *ps;
struct procstat *psend;
int col;
int indent;
char s[80];
ps = jp->ps;
if (mode & SHOW_PGID) {
outfmt(out, "%d\n", ps->pid);
return;
}
col = fmtstr(s, 16, "[%d] ", jobno(jp));
indent = col;
if (jp == curjob)
s[col - 2] = '+';
else if (curjob && jp == curjob->prev_job)
s[col - 2] = '-';
if (mode & SHOW_PID)
col += fmtstr(s + col, 16, "%d ", ps->pid);
psend = ps + jp->nprocs;
if (jp->state == JOBRUNNING) {
scopy("Running", s + col);
col += strlen("Running");
} else {
int status = psend[-1].status;
#if JOBS
if (jp->state == JOBSTOPPED)
status = jp->stopstatus;
#endif
col += sprint_status(s + col, status, 0);
}
goto start;
do {
col = fmtstr(s, 48, " |\n%*c%d ", indent, ' ', ps->pid) - 3;
start:
outfmt(
out, "%s%*c%s",
s, 33 - col >= 0 ? 33 - col : 0, ' ', ps->cmd
);
if (!(mode & SHOW_PID)) {
showpipe(jp, out);
break;
}
if (++ps == psend) {
outcslow('\n', out);
break;
}
} while (1);
jp->changed = 0;
if (jp->state == JOBDONE) {
TRACE(("showjob: freeing job %d\n", jobno(jp)));
freejob(jp);
}
}
int
jobscmd(int argc, char **argv)
{
int mode, m;
struct output *out;
mode = 0;
while ((m = nextopt("lp")))
if (m == 'l')
mode = SHOW_PID;
else
mode = SHOW_PGID;
out = out1;
argv = argptr;
if (*argv)
do
showjob(out, getjob(*argv,0), mode);
while (*++argv);
else
showjobs(out, mode);
return 0;
}
void
showjobs(struct output *out, int mode)
{
struct job *jp;
TRACE(("showjobs(%x) called\n", mode));
while (dowait(DOWAIT_NORMAL, NULL) > 0)
continue;
for (jp = curjob; jp; jp = jp->prev_job) {
if (!(mode & SHOW_CHANGED) || jp->changed)
showjob(out, jp, mode);
}
}
STATIC void
freejob(struct job *jp)
{
struct procstat *ps;
int i;
INTOFF;
for (i = jp->nprocs, ps = jp->ps ; --i >= 0 ; ps++) {
if (ps->cmd != nullstr)
ckfree(ps->cmd);
}
if (jp->ps != &jp->ps0)
ckfree(jp->ps);
jp->used = 0;
set_curjob(jp, CUR_DELETE);
INTON;
}
int
waitcmd(int argc, char **argv)
{
struct job *job;
int retval;
struct job *jp;
nextopt(nullstr);
retval = 0;
argv = argptr;
if (!*argv) {
for (;;) {
jp = curjob;
while (1) {
if (!jp) {
goto out;
}
if (jp->state == JOBRUNNING)
break;
jp->waited = 1;
jp = jp->prev_job;
}
if (dowait(DOWAIT_WAITCMD, 0) <= 0)
goto sigout;
}
}
retval = 127;
do {
if (**argv != '%') {
pid_t pid = number(*argv);
job = curjob;
goto start;
do {
if (job->ps[job->nprocs - 1].pid == pid)
break;
job = job->prev_job;
start:
if (!job)
goto repeat;
} while (1);
} else
job = getjob(*argv, 0);
while (job->state == JOBRUNNING)
if (dowait(DOWAIT_WAITCMD, 0) <= 0)
goto sigout;
job->waited = 1;
retval = getstatus(job);
repeat:
;
} while (*++argv);
out:
return retval;
sigout:
retval = 128 + pendingsigs;
goto out;
}
STATIC struct job *
getjob(const char *name, int getctl)
{
struct job *jp;
struct job *found;
const char *err_msg = "No such job: %s";
unsigned num;
int c;
const char *p;
char *(*match)(const char *, const char *);
jp = curjob;
p = name;
if (!p)
goto currentjob;
if (*p != '%')
goto err;
c = *++p;
if (!c)
goto currentjob;
if (!p[1]) {
if (c == '+' || c == '%') {
currentjob:
err_msg = "No current job";
goto check;
} else if (c == '-') {
if (jp)
jp = jp->prev_job;
err_msg = "No previous job";
check:
if (!jp)
goto err;
goto gotit;
}
}
if (is_number(p)) {
num = atoi(p);
if (num < njobs) {
jp = jobtab + num - 1;
if (jp->used)
goto gotit;
goto err;
}
}
match = prefix;
if (*p == '?') {
match = strstr;
p++;
}
found = 0;
while (1) {
if (!jp)
goto err;
if (match(jp->ps[0].cmd, p)) {
if (found)
goto err;
found = jp;
err_msg = "%s: ambiguous";
}
jp = jp->prev_job;
}
gotit:
#if JOBS
err_msg = "job %s not created under job control";
if (getctl && jp->jobctl == 0)
goto err;
#endif
return jp;
err:
sh_error(err_msg, name);
}
struct job *
makejob(union node *node, int nprocs)
{
int i;
struct job *jp;
for (i = njobs, jp = jobtab ; ; jp++) {
if (--i < 0) {
jp = growjobtab();
break;
}
if (jp->used == 0)
break;
if (jp->state != JOBDONE || !jp->waited)
continue;
if (jobctl)
continue;
freejob(jp);
break;
}
memset(jp, 0, sizeof(*jp));
#if JOBS
if (jobctl)
jp->jobctl = 1;
#endif
jp->prev_job = curjob;
curjob = jp;
jp->used = 1;
jp->ps = &jp->ps0;
if (nprocs > 1) {
jp->ps = ckmalloc(nprocs * sizeof (struct procstat));
}
TRACE(("makejob(0x%lx, %d) returns %%%d\n", (long)node, nprocs,
jobno(jp)));
return jp;
}
STATIC struct job *
growjobtab(void)
{
size_t len;
ptrdiff_t offset;
struct job *jp, *jq;
len = njobs * sizeof(*jp);
jq = jobtab;
jp = ckrealloc(jq, len + 4 * sizeof(*jp));
offset = (char *)jp - (char *)jq;
if (offset) {
size_t l = len;
jq = (struct job *)((char *)jq + l);
while (l) {
l -= sizeof(*jp);
jq--;
#define joff(p) ((struct job *)((char *)(p) + l))
#define jmove(p) (p) = (void *)((char *)(p) + offset)
if (likely(joff(jp)->ps == &jq->ps0))
jmove(joff(jp)->ps);
if (joff(jp)->prev_job)
jmove(joff(jp)->prev_job);
}
if (curjob)
jmove(curjob);
#undef joff
#undef jmove
}
njobs += 4;
jobtab = jp;
jp = (struct job *)((char *)jp + len);
jq = jp + 3;
do {
jq->used = 0;
} while (--jq >= jp);
return jp;
}
STATIC inline void
forkchild(struct job *jp, union node *n, int mode)
{
int oldlvl;
TRACE(("Child shell %d\n", getpid()));
oldlvl = shlvl;
shlvl++;
closescript();
clear_traps();
#if JOBS
jobctl = 0;
if (mode != FORK_NOJOB && jp->jobctl && !oldlvl) {
pid_t pgrp;
if (jp->nprocs == 0)
pgrp = getpid();
else
pgrp = jp->ps[0].pid;
(void)setpgid(0, pgrp);
if (mode == FORK_FG)
xtcsetpgrp(ttyfd, pgrp);
setsignal(SIGTSTP);
setsignal(SIGTTOU);
} else
#endif
if (mode == FORK_BG) {
ignoresig(SIGINT);
ignoresig(SIGQUIT);
if (jp->nprocs == 0) {
close(0);
if (open(_PATH_DEVNULL, O_RDONLY) != 0)
sh_error("Can't open %s", _PATH_DEVNULL);
}
}
if (!oldlvl && iflag) {
setsignal(SIGINT);
setsignal(SIGQUIT);
setsignal(SIGTERM);
}
for (jp = curjob; jp; jp = jp->prev_job)
freejob(jp);
jobless = 0;
}
STATIC inline void
forkparent(struct job *jp, union node *n, int mode, pid_t pid)
{
TRACE(("In parent shell: child = %d\n", pid));
if (!jp) {
while (jobless && dowait(DOWAIT_NORMAL, 0) > 0);
jobless++;
return;
}
#if JOBS
if (mode != FORK_NOJOB && jp->jobctl) {
int pgrp;
if (jp->nprocs == 0)
pgrp = pid;
else
pgrp = jp->ps[0].pid;
(void)setpgid(pid, pgrp);
}
#endif
if (mode == FORK_BG) {
backgndpid = pid; 
set_curjob(jp, CUR_RUNNING);
}
if (jp) {
struct procstat *ps = &jp->ps[jp->nprocs++];
ps->pid = pid;
ps->status = -1;
ps->cmd = nullstr;
if (jobctl && n)
ps->cmd = commandtext(n);
}
}
int
forkshell(struct job *jp, union node *n, int mode)
{
int pid;
TRACE(("forkshell(%%%d, %p, %d) called\n", jobno(jp), n, mode));
pid = fork();
if (pid < 0) {
TRACE(("Fork failed, errno=%d", errno));
if (jp)
freejob(jp);
sh_error("Cannot fork");
}
if (pid == 0)
forkchild(jp, n, mode);
else
forkparent(jp, n, mode, pid);
return pid;
}
int
waitforjob(struct job *jp)
{
int st;
TRACE(("waitforjob(%%%d) called\n", jobno(jp)));
while (jp->state == JOBRUNNING) {
dowait(DOWAIT_BLOCK, jp);
}
st = getstatus(jp);
#if JOBS
if (jp->jobctl) {
xtcsetpgrp(ttyfd, rootpid);
if (jp->sigint)
raise(SIGINT);
}
#endif
if (! JOBS || jp->state == JOBDONE)
freejob(jp);
return st;
}
STATIC int
dowait(int block, struct job *job)
{
int pid;
int status;
struct job *jp;
struct job *thisjob = NULL;
int state;
INTOFF;
TRACE(("dowait(%d) called\n", block));
pid = waitproc(block, &status);
TRACE(("wait returns pid %d, status=%d\n", pid, status));
if (pid <= 0)
goto out;
for (jp = curjob; jp; jp = jp->prev_job) {
struct procstat *sp;
struct procstat *spend;
if (jp->state == JOBDONE)
continue;
state = JOBDONE;
spend = jp->ps + jp->nprocs;
sp = jp->ps;
do {
if (sp->pid == pid) {
TRACE(("Job %d: changing status of proc %d from 0x%x to 0x%x\n", jobno(jp), pid, sp->status, status));
sp->status = status;
thisjob = jp;
}
if (sp->status == -1)
state = JOBRUNNING;
#if JOBS
if (state == JOBRUNNING)
continue;
if (WIFSTOPPED(sp->status)) {
jp->stopstatus = sp->status;
state = JOBSTOPPED;
}
#endif
} while (++sp < spend);
if (thisjob)
goto gotjob;
}
if (!JOBS || !WIFSTOPPED(status))
jobless--;
goto out;
gotjob:
if (state != JOBRUNNING) {
thisjob->changed = 1;
if (thisjob->state != state) {
TRACE(("Job %d: changing state from %d to %d\n", jobno(thisjob), thisjob->state, state));
thisjob->state = state;
#if JOBS
if (state == JOBSTOPPED) {
set_curjob(thisjob, CUR_STOPPED);
}
#endif
}
}
out:
INTON;
if (thisjob && thisjob == job) {
char s[48 + 1];
int len;
len = sprint_status(s, status, 1);
if (len) {
s[len] = '\n';
s[len + 1] = 0;
outstr(s, out2);
}
}
return pid;
}
#ifdef SYSV
STATIC int gotsigchild;
STATIC int onsigchild() {
gotsigchild = 1;
}
#endif
STATIC int
waitproc(int block, int *status)
{
sigset_t mask, oldmask;
int flags = block == DOWAIT_BLOCK ? 0 : WNOHANG;
int err;
#if JOBS
if (jobctl)
flags |= WUNTRACED;
#endif
do {
gotsigchld = 0;
err = wait3(status, flags, NULL);
if (err || !block)
break;
block = 0;
sigfillset(&mask);
sigprocmask(SIG_SETMASK, &mask, &oldmask);
while (!gotsigchld && !pendingsigs)
sigsuspend(&oldmask);
sigclearmask();
} while (gotsigchld);
return err;
}
int job_warning;
int
stoppedjobs(void)
{
struct job *jp;
int retval;
retval = 0;
if (job_warning)
goto out;
jp = curjob;
if (jp && jp->state == JOBSTOPPED) {
out2str("You have stopped jobs.\n");
job_warning = 2;
retval++;
}
out:
return retval;
}
STATIC char *cmdnextc;
STATIC char *
commandtext(union node *n)
{
char *name;
STARTSTACKSTR(cmdnextc);
cmdtxt(n);
name = stackblock();
TRACE(("commandtext: name %p, end %p\n", name, cmdnextc));
return savestr(name);
}
STATIC void
cmdtxt(union node *n)
{
union node *np;
struct nodelist *lp;
const char *p;
char s[2];
if (!n)
return;
switch (n->type) {
default:
#if DEBUG
abort();
#endif
case NPIPE:
lp = n->npipe.cmdlist;
for (;;) {
cmdtxt(lp->n);
lp = lp->next;
if (!lp)
break;
cmdputs(" | ");
}
break;
case NSEMI:
p = "; ";
goto binop;
case NAND:
p = " && ";
goto binop;
case NOR:
p = " || ";
binop:
cmdtxt(n->nbinary.ch1);
cmdputs(p);
n = n->nbinary.ch2;
goto donode;
case NREDIR:
case NBACKGND:
n = n->nredir.n;
goto donode;
case NNOT:
cmdputs("!");
n = n->nnot.com;
donode:
cmdtxt(n);
break;
case NIF:
cmdputs("if ");
cmdtxt(n->nif.test);
cmdputs("; then ");
if (n->nif.elsepart) {
cmdtxt(n->nif.ifpart);
cmdputs("; else ");
n = n->nif.elsepart;
} else {
n = n->nif.ifpart;
}
p = "; fi";
goto dotail;
case NSUBSHELL:
cmdputs("(");
n = n->nredir.n;
p = ")";
goto dotail;
case NWHILE:
p = "while ";
goto until;
case NUNTIL:
p = "until ";
until:
cmdputs(p);
cmdtxt(n->nbinary.ch1);
n = n->nbinary.ch2;
p = "; done";
dodo:
cmdputs("; do ");
dotail:
cmdtxt(n);
goto dotail2;
case NFOR:
cmdputs("for ");
cmdputs(n->nfor.var);
cmdputs(" in ");
cmdlist(n->nfor.args, 1);
n = n->nfor.body;
p = "; done";
goto dodo;
case NDEFUN:
cmdputs(n->ndefun.text);
p = "() { ... }";
goto dotail2;
case NCMD:
cmdlist(n->ncmd.args, 1);
cmdlist(n->ncmd.redirect, 0);
break;
case NARG:
p = n->narg.text;
dotail2:
cmdputs(p);
break;
case NHERE:
case NXHERE:
p = "<<...";
goto dotail2;
case NCASE:
cmdputs("case ");
cmdputs(n->ncase.expr->narg.text);
cmdputs(" in ");
for (np = n->ncase.cases; np; np = np->nclist.next) {
cmdtxt(np->nclist.pattern);
cmdputs(") ");
cmdtxt(np->nclist.body);
cmdputs(";; ");
}
p = "esac";
goto dotail2;
case NTO:
p = ">";
goto redir;
case NCLOBBER:
p = ">|";
goto redir;
case NAPPEND:
p = ">>";
goto redir;
case NTOFD:
p = ">&";
goto redir;
case NFROM:
p = "<";
goto redir;
case NFROMFD:
p = "<&";
goto redir;
case NFROMTO:
p = "<>";
redir:
s[0] = n->nfile.fd + '0';
s[1] = '\0';
cmdputs(s);
cmdputs(p);
if (n->type == NTOFD || n->type == NFROMFD) {
s[0] = n->ndup.dupfd + '0';
p = s;
goto dotail2;
} else {
n = n->nfile.fname;
goto donode;
}
}
}
STATIC void
cmdlist(union node *np, int sep)
{
for (; np; np = np->narg.next) {
if (!sep)
cmdputs(spcstr);
cmdtxt(np);
if (sep && np->narg.next)
cmdputs(spcstr);
}
}
STATIC void
cmdputs(const char *s)
{
const char *p, *str;
char cc[2] = " ";
char *nextc;
signed char c;
int subtype = 0;
int quoted = 0;
static const char vstype[VSTYPE + 1][4] = {
"", "}", "-", "+", "?", "=",
"%", "%%", "#", "##",
};
nextc = makestrspace((strlen(s) + 1) * 8, cmdnextc);
p = s;
while ((c = *p++) != 0) {
str = 0;
switch (c) {
case CTLESC:
c = *p++;
break;
case CTLVAR:
subtype = *p++;
if ((subtype & VSTYPE) == VSLENGTH)
str = "${#";
else
str = "${";
goto dostr;
case CTLENDVAR:
str = "\"}" + !(quoted & 1);
quoted >>= 1;
subtype = 0;
goto dostr;
case CTLBACKQ:
str = "$(...)";
goto dostr;
case CTLARI:
str = "$((";
goto dostr;
case CTLENDARI:
str = "))";
goto dostr;
case CTLQUOTEMARK:
quoted ^= 1;
c = '"';
break;
case '=':
if (subtype == 0)
break;
if ((subtype & VSTYPE) != VSNORMAL)
quoted <<= 1;
str = vstype[subtype & VSTYPE];
if (subtype & VSNUL)
c = ':';
else
goto checkstr;
break;
case '\'':
case '\\':
case '"':
case '$':
cc[0] = c;
str = cc;
c = '\\';
break;
default:
break;
}
USTPUTC(c, nextc);
checkstr:
if (!str)
continue;
dostr:
while ((c = *str++)) {
USTPUTC(c, nextc);
}
}
if (quoted & 1) {
USTPUTC('"', nextc);
}
*nextc = 0;
cmdnextc = nextc;
}
STATIC void
showpipe(struct job *jp, struct output *out)
{
struct procstat *sp;
struct procstat *spend;
spend = jp->ps + jp->nprocs;
for (sp = jp->ps + 1; sp < spend; sp++)
outfmt(out, " | %s", sp->cmd);
outcslow('\n', out);
flushall();
}
#if JOBS
STATIC void
xtcsetpgrp(int fd, pid_t pgrp)
{
if (tcsetpgrp(fd, pgrp))
sh_error("Cannot set tty process group (%s)", strerror(errno));
}
#endif
STATIC int
getstatus(struct job *job) {
int status;
int retval;
status = job->ps[job->nprocs - 1].status;
retval = WEXITSTATUS(status);
if (!WIFEXITED(status)) {
#if JOBS
retval = WSTOPSIG(status);
if (!WIFSTOPPED(status))
#endif
{
retval = WTERMSIG(status);
#if JOBS
if (retval == SIGINT)
job->sigint = 1;
#endif
}
retval += 128;
}
TRACE(("getstatus: job %d, nproc %d, status %x, retval %x\n",
jobno(job), job->nprocs, status, retval));
return retval;
}
#include <sys/types.h>
#include <sys/stat.h>
#include <stdlib.h>
#define MAXMBOXES 10
static time_t mailtime[MAXMBOXES];
static int changed;
void
chkmail(void)
{
const char *mpath;
char *p;
char *q;
time_t *mtp;
struct stackmark smark;
struct stat64 statb;
setstackmark(&smark);
mpath = mpathset() ? mpathval() : mailval();
for (mtp = mailtime; mtp < mailtime + MAXMBOXES; mtp++) {
p = padvance(&mpath, nullstr);
if (p == NULL)
break;
if (*p == '\0')
continue;
for (q = p ; *q ; q++);
#ifdef DEBUG
if (q[-1] != '/')
abort();
#endif
q[-1] = '\0'; 
if (stat64(p, &statb) < 0) {
*mtp = 0;
continue;
}
if (!changed && statb.st_mtime != *mtp) {
outfmt(
&errout, snlfmt,
pathopt ? pathopt : "you have mail"
);
}
*mtp = statb.st_mtime;
}
changed = 0;
popstackmark(&smark);
}
void
changemail(const char *val)
{
changed++;
}
#include <stdio.h>
#include <signal.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#ifdef HETIO
#endif
#define PROFILE 0
int rootpid;
int shlvl;
#ifdef __GLIBC__
int *dash_errno;
#endif
#if PROFILE
short profile_buf[16384];
extern int etext();
#endif
STATIC void read_profile(const char *);
STATIC char *find_dot_file(char *);
static int cmdloop(int);
int main(int, char **);
int
main(int argc, char **argv)
{
char *shinit;
volatile int state;
struct jmploc jmploc;
struct stackmark smark;
int login;
#ifdef __GLIBC__
dash_errno = __errno_location();
#endif
#if PROFILE
monitor(4, etext, profile_buf, sizeof profile_buf, 50);
#endif
state = 0;
if (unlikely(setjmp(jmploc.loc))) {
int e;
int s;
reset();
e = exception;
s = state;
if (e == EXEXIT || s == 0 || iflag == 0 || shlvl)
exitshell();
if (e == EXINT
#if ATTY
&& (! attyset() || equal(termval(), "emacs"))
#endif
) {
out2c('\n');
#ifdef FLUSHERR
flushout(out2);
#endif
}
popstackmark(&smark);
FORCEINTON; 
if (s == 1)
goto state1;
else if (s == 2)
goto state2;
else if (s == 3)
goto state3;
else
goto state4;
}
handler = &jmploc;
#ifdef DEBUG
opentrace();
trputs("Shell args: "); trargs(argv);
#endif
rootpid = getpid();
init();
setstackmark(&smark);
login = procargs(argc, argv);
if (login) {
state = 1;
read_profile("/etc/profile");
state1:
state = 2;
read_profile("$HOME/.profile");
}
state2:
state = 3;
if (
#ifndef linux
getuid() == geteuid() && getgid() == getegid() &&
#endif
iflag
) {
if ((shinit = lookupvar("ENV")) != NULL && *shinit != '\0') {
read_profile(shinit);
}
}
popstackmark(&smark);
state3:
state = 4;
if (minusc)
evalstring(minusc, sflag ? 0 : EV_EXIT);
if (sflag || minusc == NULL) {
state4: 
cmdloop(1);
}
#if PROFILE
monitor(0);
#endif
#if GPROF
{
extern void _mcleanup(void);
_mcleanup();
}
#endif
exitshell();
}
static int
cmdloop(int top)
{
union node *n;
struct stackmark smark;
int inter;
int status = 0;
int numeof = 0;
TRACE(("cmdloop(%d) called\n", top));
#ifdef HETIO
if(iflag && top)
hetio_init();
#endif
for (;;) {
int skip;
setstackmark(&smark);
if (jobctl)
showjobs(out2, SHOW_CHANGED);
inter = 0;
if (iflag && top) {
inter++;
chkmail();
}
n = parsecmd(inter);
if (n == NEOF) {
if (!top || numeof >= 50)
break;
if (!stoppedjobs()) {
if (!Iflag)
break;
out2str("\nUse \"exit\" to leave shell.\n");
}
numeof++;
} else if (nflag == 0) {
job_warning = (job_warning == 2) ? 1 : 0;
numeof = 0;
evaltree(n, 0);
status = exitstatus;
}
popstackmark(&smark);
skip = evalskip;
if (skip) {
evalskip &= ~SKIPFUNC;
break;
}
}
return status;
}
STATIC void
read_profile(const char *name)
{
name = expandstr(name);
if (setinputfile(name, INPUT_PUSH_FILE | INPUT_NOFILE_OK) < 0)
return;
cmdloop(0);
popfile();
}
void
readcmdfile(char *name)
{
setinputfile(name, INPUT_PUSH_FILE);
cmdloop(0);
popfile();
}
STATIC char *
find_dot_file(char *basename)
{
char *fullname;
const char *path = pathval();
struct stat statb;
if (strchr(basename, '/'))
return basename;
while ((fullname = padvance(&path, basename)) != NULL) {
if ((stat(fullname, &statb) == 0) && S_ISREG(statb.st_mode)) {
return fullname;
}
stunalloc(fullname);
}
sh_error("%s: not found", basename);
}
int
dotcmd(int argc, char **argv)
{
int status = 0;
if (argc >= 2) { 
char *fullname;
fullname = find_dot_file(argv[1]);
setinputfile(fullname, INPUT_PUSH_FILE);
commandname = fullname;
status = cmdloop(0);
popfile();
}
return status;
}
int
exitcmd(int argc, char **argv)
{
if (stoppedjobs())
return 0;
if (argc > 1)
exitstatus = number(argv[1]);
exraise(EXEXIT);
}
#include <stdlib.h>
#include <unistd.h>
pointer
ckmalloc(size_t nbytes)
{
pointer p;
p = malloc(nbytes);
if (p == NULL)
sh_error("Out of space");
return p;
}
pointer
ckrealloc(pointer p, size_t nbytes)
{
p = realloc(p, nbytes);
if (p == NULL)
sh_error("Out of space");
return p;
}
char *
savestr(const char *s)
{
char *p = strdup(s);
if (!p)
sh_error("Out of space");
return p;
}
#define MINSIZE SHELL_ALIGN(504)
struct stack_block {
struct stack_block *prev;
char space[MINSIZE];
};
struct stack_block stackbase;
struct stack_block *stackp = &stackbase;
char *stacknxt = stackbase.space;
size_t stacknleft = MINSIZE;
char *sstrend = stackbase.space + MINSIZE;
pointer
stalloc(size_t nbytes)
{
char *p;
size_t aligned;
aligned = SHELL_ALIGN(nbytes);
if (aligned > stacknleft) {
size_t len;
size_t blocksize;
struct stack_block *sp;
blocksize = aligned;
if (blocksize < MINSIZE)
blocksize = MINSIZE;
len = sizeof(struct stack_block) - MINSIZE + blocksize;
if (len < blocksize)
sh_error("Out of space");
INTOFF;
sp = ckmalloc(len);
sp->prev = stackp;
stacknxt = sp->space;
stacknleft = blocksize;
sstrend = stacknxt + blocksize;
stackp = sp;
INTON;
}
p = stacknxt;
stacknxt += aligned;
stacknleft -= aligned;
return p;
}
void
stunalloc(pointer p)
{
#ifdef DEBUG
if (!p || (stacknxt < (char *)p) || ((char *)p < stackp->space)) {
write(2, "stunalloc\n", 10);
abort();
}
#endif
stacknleft += stacknxt - (char *)p;
stacknxt = p;
}
void pushstackmark(struct stackmark *mark, size_t len)
{
mark->stackp = stackp;
mark->stacknxt = stacknxt;
mark->stacknleft = stacknleft;
grabstackblock(len);
}
void setstackmark(struct stackmark *mark)
{
pushstackmark(mark, stacknxt == stackp->space && stackp != &stackbase);
}
void
popstackmark(struct stackmark *mark)
{
struct stack_block *sp;
INTOFF;
while (stackp != mark->stackp) {
sp = stackp;
stackp = sp->prev;
ckfree(sp);
}
stacknxt = mark->stacknxt;
stacknleft = mark->stacknleft;
sstrend = mark->stacknxt + mark->stacknleft;
INTON;
}
void
growstackblock(void)
{
size_t newlen;
newlen = stacknleft * 2;
if (newlen < stacknleft)
sh_error("Out of space");
if (newlen < 128)
newlen += 128;
if (stacknxt == stackp->space && stackp != &stackbase) {
struct stack_block *sp;
struct stack_block *prevstackp;
size_t grosslen;
INTOFF;
sp = stackp;
prevstackp = sp->prev;
grosslen = newlen + sizeof(struct stack_block) - MINSIZE;
sp = ckrealloc((pointer)sp, grosslen);
sp->prev = prevstackp;
stackp = sp;
stacknxt = sp->space;
stacknleft = newlen;
sstrend = sp->space + newlen;
INTON;
} else {
char *oldspace = stacknxt;
int oldlen = stacknleft;
char *p = stalloc(newlen);
stacknxt = memcpy(p, oldspace, oldlen);
stacknleft += newlen;
}
}
void *
growstackstr(void)
{
size_t len = stackblocksize();
growstackblock();
return stackblock() + len;
}
char *
makestrspace(size_t newlen, char *p)
{
size_t len = p - stacknxt;
size_t size;
for (;;) {
size_t nleft;
size = stackblocksize();
nleft = size - len;
if (nleft >= newlen)
break;
growstackblock();
}
return stackblock() + len;
}
char *
stnputs(const char *s, size_t n, char *p)
{
p = makestrspace(n, p);
p = mempcpy(p, s, n);
return p;
}
char *
stputs(const char *s, char *p)
{
return stnputs(s, strlen(s), p);
}
#include <sys/types.h> 
#include <sys/param.h> 
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <unistd.h>
#include <stdlib.h>
#include <ctype.h>
#include <inttypes.h>
#undef rflag
static void
readcmd_handle_line(char *s, char **ap)
{
struct arglist arglist;
struct strlist *sl;
char *backup;
char *line;
line = stackblock();
s = grabstackstr(s);
backup = sstrdup(line);
arglist.lastp = &arglist.list;
ifsbreakup(s, &arglist);
*arglist.lastp = NULL;
ifsfree();
sl = arglist.list;
do {
if (!sl) {
do {
setvar(*ap, nullstr, 0);
} while (*++ap);
return;
}
if (!ap[1] && sl->next) {
size_t offset;
char *remainder;
offset = sl->text - s;
remainder = backup + offset;
rmescapes(remainder);
setvar(*ap, remainder, 0);
return;
}
rmescapes(sl->text);
setvar(*ap, sl->text, 0);
sl = sl->next;
} while (*++ap);
}
int
readcmd(int argc, char **argv)
{
char **ap;
char c;
int rflag;
char *prompt;
char *p;
int startloc;
int newloc;
int status;
int i;
rflag = 0;
prompt = NULL;
while ((i = nextopt("p:r")) != '\0') {
if (i == 'p')
prompt = optionarg;
else
rflag = 1;
}
if (prompt && isatty(0)) {
out2str(prompt);
#ifdef FLUSHERR
flushall();
#endif
}
if (*(ap = argptr) == NULL)
sh_error("arg count");
status = 0;
STARTSTACKSTR(p);
goto start;
for (;;) {
switch (read(0, &c, 1)) {
case 1:
break;
default:
if (errno == EINTR && !pendingsigs)
continue;
case 0:
status = 1;
goto out;
}
if (c == '\0')
continue;
if (newloc >= startloc) {
if (c == '\n')
goto resetbs;
goto put;
}
if (!rflag && c == '\\') {
newloc = p - (char *)stackblock();
continue;
}
if (c == '\n')
break;
put:
CHECKSTRSPACE(2, p);
if (strchr(qchars, c))
USTPUTC(CTLESC, p);
USTPUTC(c, p);
if (newloc >= startloc) {
resetbs:
recordregion(startloc, newloc, 0);
start:
startloc = p - (char *)stackblock();
newloc = startloc - 1;
}
}
out:
recordregion(startloc, p - (char *)stackblock(), 0);
STACKSTRNUL(p);
readcmd_handle_line(p + 1, ap);
return status;
}
int
umaskcmd(int argc, char **argv)
{
char *ap;
int mask;
int i;
int symbolic_mode = 0;
while ((i = nextopt("S")) != '\0') {
symbolic_mode = 1;
}
INTOFF;
mask = umask(0);
umask(mask);
INTON;
if ((ap = *argptr) == NULL) {
if (symbolic_mode) {
char buf[18];
int j;
mask = ~mask;
ap = buf;
for (i = 0; i < 3; i++) {
*ap++ = "ugo"[i];
*ap++ = '=';
for (j = 0; j < 3; j++)
if (mask & (1 << (8 - (3*i + j))))
*ap++ = "rwx"[j];
*ap++ = ',';
}
ap[-1] = '\0';
out1fmt("%s\n", buf);
} else {
out1fmt("%.4o\n", mask);
}
} else {
int new_mask;
if (isdigit((unsigned char) *ap)) {
new_mask = 0;
do {
if (*ap >= '8' || *ap < '0')
sh_error(illnum, *argptr);
new_mask = (new_mask << 3) + (*ap - '0');
} while (*++ap != '\0');
} else {
int positions, new_val;
char op;
mask = ~mask;
new_mask = mask;
positions = 0;
while (*ap) {
while (*ap && strchr("augo", *ap))
switch (*ap++) {
case 'a': positions |= 0111; break;
case 'u': positions |= 0100; break;
case 'g': positions |= 0010; break;
case 'o': positions |= 0001; break;
}
if (!positions)
positions = 0111; 
if (!strchr("=+-", op = *ap))
break;
ap++;
new_val = 0;
while (*ap && strchr("rwxugoXs", *ap))
switch (*ap++) {
case 'r': new_val |= 04; break;
case 'w': new_val |= 02; break;
case 'x': new_val |= 01; break;
case 'u': new_val |= mask >> 6;
break;
case 'g': new_val |= mask >> 3;
break;
case 'o': new_val |= mask >> 0;
break;
case 'X': if (mask & 0111)
new_val |= 01;
break;
case 's': 
break;
}
new_val = (new_val & 07) * positions;
switch (op) {
case '-':
new_mask &= ~new_val;
break;
case '=':
new_mask = new_val
| (new_mask & ~(positions * 07));
break;
case '+':
new_mask |= new_val;
}
if (*ap == ',') {
positions = 0;
ap++;
} else if (!strchr("=+-", *ap))
break;
}
if (*ap) {
sh_error("Illegal mode: %s", *argptr);
return 1;
}
new_mask = ~new_mask;
}
umask(new_mask);
}
return 0;
}
#ifdef HAVE_GETRLIMIT
struct limits {
const char *name;
int cmd;
int factor; 
char option;
};
static const struct limits limits[] = {
#ifdef RLIMIT_CPU
{ "time(seconds)", RLIMIT_CPU, 1, 't' },
#endif
#ifdef RLIMIT_FSIZE
{ "file(blocks)", RLIMIT_FSIZE, 512, 'f' },
#endif
#ifdef RLIMIT_DATA
{ "data(kbytes)", RLIMIT_DATA, 1024, 'd' },
#endif
#ifdef RLIMIT_STACK
{ "stack(kbytes)", RLIMIT_STACK, 1024, 's' },
#endif
#ifdef RLIMIT_CORE
{ "coredump(blocks)", RLIMIT_CORE, 512, 'c' },
#endif
#ifdef RLIMIT_RSS
{ "memory(kbytes)", RLIMIT_RSS, 1024, 'm' },
#endif
#ifdef RLIMIT_MEMLOCK
{ "locked memory(kbytes)", RLIMIT_MEMLOCK, 1024, 'l' },
#endif
#ifdef RLIMIT_NPROC
{ "process", RLIMIT_NPROC, 1, 'p' },
#endif
#ifdef RLIMIT_NOFILE
{ "nofiles", RLIMIT_NOFILE, 1, 'n' },
#endif
#ifdef RLIMIT_AS
{ "vmemory(kbytes)", RLIMIT_AS, 1024, 'v' },
#endif
#ifdef RLIMIT_LOCKS
{ "locks", RLIMIT_LOCKS, 1, 'w' },
#endif
{ (char *) 0, 0, 0, '\0' }
};
enum limtype { SOFT = 0x1, HARD = 0x2 };
static void printlim(enum limtype how, const struct rlimit *limit,
const struct limits *l)
{
rlim_t val;
val = limit->rlim_max;
if (how & SOFT)
val = limit->rlim_cur;
if (val == RLIM_INFINITY)
out1fmt("unlimited\n");
else {
val /= l->factor;
out1fmt("%" PRIdMAX "\n", (intmax_t) val);
}
}
int
ulimitcmd(int argc, char **argv)
{
int c;
rlim_t val = 0;
enum limtype how = SOFT | HARD;
const struct limits *l;
int set, all = 0;
int optc, what;
struct rlimit limit;
what = 'f';
while ((optc = nextopt("HSa"
#ifdef RLIMIT_CPU
"t"
#endif
#ifdef RLIMIT_FSIZE
"f"
#endif
#ifdef RLIMIT_DATA
"d"
#endif
#ifdef RLIMIT_STACK
"s"
#endif
#ifdef RLIMIT_CORE
"c"
#endif
#ifdef RLIMIT_RSS
"m"
#endif
#ifdef RLIMIT_MEMLOCK
"l"
#endif
#ifdef RLIMIT_NPROC
"p"
#endif
#ifdef RLIMIT_NOFILE
"n"
#endif
#ifdef RLIMIT_AS
"v"
#endif
#ifdef RLIMIT_LOCKS
"w"
#endif
)) != '\0')
switch (optc) {
case 'H':
how = HARD;
break;
case 'S':
how = SOFT;
break;
case 'a':
all = 1;
break;
default:
what = optc;
}
for (l = limits; l->option != what; l++)
;
set = *argptr ? 1 : 0;
if (set) {
char *p = *argptr;
if (all || argptr[1])
sh_error("too many arguments");
if (strcmp(p, "unlimited") == 0)
val = RLIM_INFINITY;
else {
val = (rlim_t) 0;
while ((c = *p++) >= '0' && c <= '9')
{
val = (val * 10) + (long)(c - '0');
if (val < (rlim_t) 0)
break;
}
if (c)
sh_error("bad number");
val *= l->factor;
}
}
if (all) {
for (l = limits; l->name; l++) {
getrlimit(l->cmd, &limit);
out1fmt("%-20s ", l->name);
printlim(how, &limit, l);
}
return 0;
}
getrlimit(l->cmd, &limit);
if (set) {
if (how & HARD)
limit.rlim_max = val;
if (how & SOFT)
limit.rlim_cur = val;
if (setrlimit(l->cmd, &limit) < 0)
sh_error("error setting limit (%s)", strerror(errno));
} else {
printlim(how, &limit, l);
}
return 0;
}
#endif
#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <inttypes.h>
#include <stdlib.h>
char nullstr[1]; 
const char spcstr[] = " ";
const char snlfmt[] = "%s\n";
const char dolatstr[] = { CTLQUOTEMARK, CTLVAR, VSNORMAL, '@', '=',
CTLQUOTEMARK, '\0' };
const char qchars[] = { CTLESC, CTLQUOTEMARK, 0 };
const char illnum[] = "Illegal number: %s";
const char homestr[] = "HOME";
#if 0
void
scopyn(const char *from, char *to, int size)
{
while (--size > 0) {
if ((*to++ = *from++) == '\0')
return;
}
*to = '\0';
}
#endif
char *
prefix(const char *string, const char *pfx)
{
while (*pfx) {
if (*pfx++ != *string++)
return 0;
}
return (char *) string;
}
void badnum(const char *s)
{
sh_error(illnum, s);
}
intmax_t atomax(const char *s, int base)
{
char *p;
intmax_t r;
errno = 0;
r = strtoimax(s, &p, base);
if (errno != 0)
badnum(s);
if (p == s && base)
badnum(s);
while (isspace((unsigned char)*p))
p++;
if (*p)
badnum(s);
return r;
}
intmax_t atomax10(const char *s)
{
return atomax(s, 10);
}
int
number(const char *s)
{
intmax_t n = atomax10(s);
if (n < 0 || n > INT_MAX)
badnum(s);
return n;
}
int
is_number(const char *p)
{
do {
if (! is_digit(*p))
return 0;
} while (*++p != '\0');
return 1;
}
char *
single_quote(const char *s) {
char *p;
STARTSTACKSTR(p);
do {
char *q;
size_t len;
len = strchrnul(s, '\'') - s;
q = p = makestrspace(len + 3, p);
*q++ = '\'';
q = mempcpy(q, s, len);
*q++ = '\'';
s += len;
STADJUST(q - p, p);
len = strspn(s, "'");
if (!len)
break;
q = p = makestrspace(len + 3, p);
*q++ = '"';
q = mempcpy(q, s, len);
*q++ = '"';
s += len;
STADJUST(q - p, p);
} while (*s);
USTPUTC(0, p);
return stackblock();
}
char *
sstrdup(const char *p)
{
size_t len = strlen(p) + 1;
return memcpy(stalloc(len), p, len);
}
int
pstrcmp(const void *a, const void *b)
{
return strcmp(*(const char *const *) a, *(const char *const *) b);
}
const char *const *
findstring(const char *s, const char *const *array, size_t nmemb)
{
return bsearch(&s, array, nmemb, sizeof(const char *), pstrcmp);
}
#include <signal.h>
#include <unistd.h>
#include <stdlib.h>
#define DEFINE_OPTIONS
#undef DEFINE_OPTIONS
#ifndef SMALL
#endif
char *arg0; 
struct shparam shellparam; 
char **argptr; 
char *optionarg; 
char *optptr; 
char *minusc; 
static const char *const optnames[NOPTS] = {
"errexit",
"noglob",
"ignoreeof",
"interactive",
"monitor",
"noexec",
"stdin",
"xtrace",
"verbose",
"vi",
"emacs",
"noclobber",
"allexport",
"notify",
"nounset",
"nolog",
"debug",
};
const char optletters[NOPTS] = {
'e',
'f',
'I',
'i',
'm',
'n',
's',
'x',
'v',
'V',
'E',
'C',
'a',
'b',
'u',
0,
0,
};
char optlist[NOPTS];
static int options(int);
STATIC void minus_o(char *, int);
STATIC void setoption(int, int);
STATIC int getopts(char *, char *, char **);
int
procargs(int argc, char **argv)
{
int i;
const char *xminusc;
char **xargv;
int login;
xargv = argv;
login = xargv[0] && xargv[0][0] == '-';
arg0 = xargv[0];
if (argc > 0)
xargv++;
for (i = 0; i < NOPTS; i++)
optlist[i] = 2;
argptr = xargv;
login |= options(1);
xargv = argptr;
xminusc = minusc;
if (*xargv == NULL) {
if (xminusc)
sh_error("-c requires an argument");
sflag = 1;
}
if (iflag == 2 && sflag == 1 && isatty(0) && isatty(1))
iflag = 1;
if (mflag == 2)
mflag = iflag;
for (i = 0; i < NOPTS; i++)
if (optlist[i] == 2)
optlist[i] = 0;
#if DEBUG == 2
debug = 1;
#endif
if (xminusc) {
minusc = *xargv++;
if (*xargv)
goto setarg0;
} else if (!sflag) {
setinputfile(*xargv, 0);
setarg0:
arg0 = *xargv++;
commandname = arg0;
}
shellparam.p = xargv;
shellparam.optind = 1;
shellparam.optoff = -1;
while (*xargv) {
shellparam.nparam++;
xargv++;
}
optschanged();
return login;
}
void
optschanged(void)
{
#ifdef DEBUG
opentrace();
#endif
setinteractive(iflag);
#ifndef SMALL
histedit();
#endif
setjobctl(mflag);
}
STATIC int
options(int cmdline)
{
char *p;
int val;
int c;
int login = 0;
if (cmdline)
minusc = NULL;
while ((p = *argptr) != NULL) {
argptr++;
if ((c = *p++) == '-') {
val = 1;
if (p[0] == '\0' || (p[0] == '-' && p[1] == '\0')) {
if (!cmdline) {
if (p[0] == '\0')
xflag = vflag = 0;
else if (*argptr == NULL)
setparam(argptr);
}
break; 
}
} else if (c == '+') {
val = 0;
} else {
argptr--;
break;
}
while ((c = *p++) != '\0') {
if (c == 'c' && cmdline) {
minusc = p; 
} else if (c == 'l' && cmdline) {
login = 1;
} else if (c == 'o') {
minus_o(*argptr, val);
if (*argptr)
argptr++;
} else {
setoption(c, val);
}
}
}
return login;
}
STATIC void
minus_o(char *name, int val)
{
int i;
if (name == NULL) {
if (val) {
out1str("Current option settings\n");
for (i = 0; i < NOPTS; i++)
out1fmt("%-16s%s\n", optnames[i],
optlist[i] ? "on" : "off");
} else {
for (i = 0; i < NOPTS; i++)
out1fmt("set %s %s\n",
optlist[i] ? "-o" : "+o",
optnames[i]);
}
} else {
for (i = 0; i < NOPTS; i++)
if (equal(name, optnames[i])) {
optlist[i] = val;
return;
}
sh_error("Illegal option -o %s", name);
}
}
STATIC void
setoption(int flag, int val)
{
int i;
for (i = 0; i < NOPTS; i++)
if (optletters[i] == flag) {
optlist[i] = val;
if (val) {
if (flag == 'V')
Eflag = 0;
else if (flag == 'E')
Vflag = 0;
}
return;
}
sh_error("Illegal option -%c", flag);
}
void
setparam(char **argv)
{
char **newparam;
char **ap;
int nparam;
for (nparam = 0 ; argv[nparam] ; nparam++);
ap = newparam = ckmalloc((nparam + 1) * sizeof *ap);
while (*argv) {
*ap++ = savestr(*argv++);
}
*ap = NULL;
freeparam(&shellparam);
shellparam.malloc = 1;
shellparam.nparam = nparam;
shellparam.p = newparam;
shellparam.optind = 1;
shellparam.optoff = -1;
}
void
freeparam(volatile struct shparam *param)
{
char **ap;
if (param->malloc) {
for (ap = param->p ; *ap ; ap++)
ckfree(*ap);
ckfree(param->p);
}
}
int
shiftcmd(int argc, char **argv)
{
int n;
char **ap1, **ap2;
n = 1;
if (argc > 1)
n = number(argv[1]);
if (n > shellparam.nparam)
sh_error("can't shift that many");
INTOFF;
shellparam.nparam -= n;
for (ap1 = shellparam.p ; --n >= 0 ; ap1++) {
if (shellparam.malloc)
ckfree(*ap1);
}
ap2 = shellparam.p;
while ((*ap2++ = *ap1++) != NULL);
shellparam.optind = 1;
shellparam.optoff = -1;
INTON;
return 0;
}
int
setcmd(int argc, char **argv)
{
if (argc == 1)
return showvars(nullstr, 0, VUNSET);
INTOFF;
options(0);
optschanged();
if (*argptr != NULL) {
setparam(argptr);
}
INTON;
return 0;
}
void
getoptsreset(value)
const char *value;
{
shellparam.optind = number(value) ?: 1;
shellparam.optoff = -1;
}
int
getoptscmd(int argc, char **argv)
{
char **optbase;
if (argc < 3)
sh_error("Usage: getopts optstring var [arg]");
else if (argc == 3) {
optbase = shellparam.p;
if ((unsigned)shellparam.optind > shellparam.nparam + 1) {
shellparam.optind = 1;
shellparam.optoff = -1;
}
}
else {
optbase = &argv[3];
if ((unsigned)shellparam.optind > argc - 2) {
shellparam.optind = 1;
shellparam.optoff = -1;
}
}
return getopts(argv[1], argv[2], optbase);
}
STATIC int
getopts(char *optstr, char *optvar, char **optfirst)
{
char *p, *q;
char c = '?';
int done = 0;
char s[2];
char **optnext;
int ind = shellparam.optind;
int off = shellparam.optoff;
shellparam.optind = -1;
optnext = optfirst + ind - 1;
if (ind <= 1 || off < 0 || strlen(optnext[-1]) < off)
p = NULL;
else
p = optnext[-1] + off;
if (p == NULL || *p == '\0') {
p = *optnext;
if (p == NULL || *p != '-' || *++p == '\0') {
atend:
p = NULL;
done = 1;
goto out;
}
optnext++;
if (p[0] == '-' && p[1] == '\0') 
goto atend;
}
c = *p++;
for (q = optstr; *q != c; ) {
if (*q == '\0') {
if (optstr[0] == ':') {
s[0] = c;
s[1] = '\0';
setvar("OPTARG", s, 0);
} else {
outfmt(&errout, "Illegal option -%c\n", c);
(void) unsetvar("OPTARG");
}
c = '?';
goto out;
}
if (*++q == ':')
q++;
}
if (*++q == ':') {
if (*p == '\0' && (p = *optnext) == NULL) {
if (optstr[0] == ':') {
s[0] = c;
s[1] = '\0';
setvar("OPTARG", s, 0);
c = ':';
} else {
outfmt(&errout, "No arg for -%c option\n", c);
(void) unsetvar("OPTARG");
c = '?';
}
goto out;
}
if (p == *optnext)
optnext++;
setvar("OPTARG", p, 0);
p = NULL;
} else
setvar("OPTARG", nullstr, 0);
out:
ind = optnext - optfirst + 1;
setvarint("OPTIND", ind, VNOFUNC);
s[0] = c;
s[1] = '\0';
setvar(optvar, s, 0);
shellparam.optoff = p ? p - *(optnext - 1) : -1;
shellparam.optind = ind;
return done;
}
int
nextopt(const char *optstring)
{
char *p;
const char *q;
char c;
if ((p = optptr) == NULL || *p == '\0') {
p = *argptr;
if (p == NULL || *p != '-' || *++p == '\0')
return '\0';
argptr++;
if (p[0] == '-' && p[1] == '\0') 
return '\0';
}
c = *p++;
for (q = optstring ; *q != c ; ) {
if (*q == '\0')
sh_error("Illegal option -%c", c);
if (*++q == ':')
q++;
}
if (*++q == ':') {
if (*p == '\0' && (p = *argptr++) == NULL)
sh_error("No arg for -%c option", c);
optionarg = p;
p = NULL;
}
optptr = p;
return c;
}
#if HAVE_ALLOCA_H
#include <alloca.h>
#endif
#include <stdlib.h>
#ifndef SMALL
#endif
#define FAKEEOFMARK (char *)1
struct heredoc {
struct heredoc *next; 
union node *here; 
char *eofmark; 
int striptabs; 
};
struct heredoc *heredoclist; 
int doprompt; 
int needprompt; 
int lasttoken; 
int tokpushback; 
char *wordtext; 
int checkkwd;
struct nodelist *backquotelist;
union node *redirnode;
struct heredoc *heredoc;
int quoteflag; 
STATIC union node *list(int);
STATIC union node *andor(void);
STATIC union node *pipeline(void);
STATIC union node *command(void);
STATIC union node *simplecmd(void);
STATIC union node *makename(void);
STATIC void parsefname(void);
STATIC void parseheredoc(void);
STATIC int peektoken(void);
STATIC int readtoken(void);
STATIC int xxreadtoken(void);
STATIC int readtoken1(int, char const *, char *, int);
STATIC void synexpect(int) __attribute__((__noreturn__));
STATIC void synerror(const char *) __attribute__((__noreturn__));
STATIC void setprompt(int);
static inline int
isassignment(const char *p)
{
const char *q = endofname(p);
if (p == q)
return 0;
return *q == '=';
}
static inline int realeofmark(const char *eofmark)
{
return eofmark && eofmark != FAKEEOFMARK;
}
union node *
parsecmd(int interact)
{
int t;
tokpushback = 0;
doprompt = interact;
if (doprompt)
setprompt(doprompt);
needprompt = 0;
t = readtoken();
if (t == TEOF)
return NEOF;
if (t == TNL)
return NULL;
tokpushback++;
return list(1);
}
STATIC union node *
list(int nlflag)
{
union node *n1, *n2, *n3;
int tok;
checkkwd = CHKNL | CHKKWD | CHKALIAS;
if (nlflag == 2 && tokendlist[peektoken()])
return NULL;
n1 = NULL;
for (;;) {
n2 = andor();
tok = readtoken();
if (tok == TBACKGND) {
if (n2->type == NPIPE) {
n2->npipe.backgnd = 1;
} else {
if (n2->type != NREDIR) {
n3 = stalloc(sizeof(struct nredir));
n3->nredir.n = n2;
n3->nredir.redirect = NULL;
n2 = n3;
}
n2->type = NBACKGND;
}
}
if (n1 == NULL) {
n1 = n2;
}
else {
n3 = (union node *)stalloc(sizeof (struct nbinary));
n3->type = NSEMI;
n3->nbinary.ch1 = n1;
n3->nbinary.ch2 = n2;
n1 = n3;
}
switch (tok) {
case TBACKGND:
case TSEMI:
tok = readtoken();
case TNL:
if (tok == TNL) {
parseheredoc();
if (nlflag == 1)
return n1;
} else {
tokpushback++;
}
checkkwd = CHKNL | CHKKWD | CHKALIAS;
if (tokendlist[peektoken()])
return n1;
break;
case TEOF:
if (heredoclist)
parseheredoc();
else
pungetc(); 
tokpushback++;
return n1;
default:
if (nlflag == 1)
synexpect(-1);
tokpushback++;
return n1;
}
}
}
STATIC union node *
andor(void)
{
union node *n1, *n2, *n3;
int t;
n1 = pipeline();
for (;;) {
if ((t = readtoken()) == TAND) {
t = NAND;
} else if (t == TOR) {
t = NOR;
} else {
tokpushback++;
return n1;
}
checkkwd = CHKNL | CHKKWD | CHKALIAS;
n2 = pipeline();
n3 = (union node *)stalloc(sizeof (struct nbinary));
n3->type = t;
n3->nbinary.ch1 = n1;
n3->nbinary.ch2 = n2;
n1 = n3;
}
}
STATIC union node *
pipeline(void)
{
union node *n1, *n2, *pipenode;
struct nodelist *lp, *prev;
int negate;
negate = 0;
TRACE(("pipeline: entered\n"));
if (readtoken() == TNOT) {
negate = !negate;
checkkwd = CHKKWD | CHKALIAS;
} else
tokpushback++;
n1 = command();
if (readtoken() == TPIPE) {
pipenode = (union node *)stalloc(sizeof (struct npipe));
pipenode->type = NPIPE;
pipenode->npipe.backgnd = 0;
lp = (struct nodelist *)stalloc(sizeof (struct nodelist));
pipenode->npipe.cmdlist = lp;
lp->n = n1;
do {
prev = lp;
lp = (struct nodelist *)stalloc(sizeof (struct nodelist));
checkkwd = CHKNL | CHKKWD | CHKALIAS;
lp->n = command();
prev->next = lp;
} while (readtoken() == TPIPE);
lp->next = NULL;
n1 = pipenode;
}
tokpushback++;
if (negate) {
n2 = (union node *)stalloc(sizeof (struct nnot));
n2->type = NNOT;
n2->nnot.com = n1;
return n2;
} else
return n1;
}
STATIC union node *
command(void)
{
union node *n1, *n2;
union node *ap, **app;
union node *cp, **cpp;
union node *redir, **rpp;
union node **rpp2;
int t;
int savelinno;
redir = NULL;
rpp2 = &redir;
savelinno = plinno;
switch (readtoken()) {
default:
synexpect(-1);
case TIF:
n1 = (union node *)stalloc(sizeof (struct nif));
n1->type = NIF;
n1->nif.test = list(0);
if (readtoken() != TTHEN)
synexpect(TTHEN);
n1->nif.ifpart = list(0);
n2 = n1;
while (readtoken() == TELIF) {
n2->nif.elsepart = (union node *)stalloc(sizeof (struct nif));
n2 = n2->nif.elsepart;
n2->type = NIF;
n2->nif.test = list(0);
if (readtoken() != TTHEN)
synexpect(TTHEN);
n2->nif.ifpart = list(0);
}
if (lasttoken == TELSE)
n2->nif.elsepart = list(0);
else {
n2->nif.elsepart = NULL;
tokpushback++;
}
t = TFI;
break;
case TWHILE:
case TUNTIL: {
int got;
n1 = (union node *)stalloc(sizeof (struct nbinary));
n1->type = (lasttoken == TWHILE)? NWHILE : NUNTIL;
n1->nbinary.ch1 = list(0);
if ((got=readtoken()) != TDO) {
TRACE(("expecting DO got %s %s\n", tokname[got], got == TWORD ? wordtext : ""));
synexpect(TDO);
}
n1->nbinary.ch2 = list(0);
t = TDONE;
break;
}
case TFOR:
if (readtoken() != TWORD || quoteflag || ! goodname(wordtext))
synerror("Bad for loop variable");
n1 = (union node *)stalloc(sizeof (struct nfor));
n1->type = NFOR;
n1->nfor.linno = savelinno;
n1->nfor.var = wordtext;
checkkwd = CHKNL | CHKKWD | CHKALIAS;
if (readtoken() == TIN) {
app = &ap;
while (readtoken() == TWORD) {
n2 = (union node *)stalloc(sizeof (struct narg));
n2->type = NARG;
n2->narg.text = wordtext;
n2->narg.backquote = backquotelist;
*app = n2;
app = &n2->narg.next;
}
*app = NULL;
n1->nfor.args = ap;
if (lasttoken != TNL && lasttoken != TSEMI)
synexpect(-1);
} else {
n2 = (union node *)stalloc(sizeof (struct narg));
n2->type = NARG;
n2->narg.text = (char *)dolatstr;
n2->narg.backquote = NULL;
n2->narg.next = NULL;
n1->nfor.args = n2;
if (lasttoken != TSEMI)
tokpushback++;
}
checkkwd = CHKNL | CHKKWD | CHKALIAS;
if (readtoken() != TDO)
synexpect(TDO);
n1->nfor.body = list(0);
t = TDONE;
break;
case TCASE:
n1 = (union node *)stalloc(sizeof (struct ncase));
n1->type = NCASE;
n1->ncase.linno = savelinno;
if (readtoken() != TWORD)
synexpect(TWORD);
n1->ncase.expr = n2 = (union node *)stalloc(sizeof (struct narg));
n2->type = NARG;
n2->narg.text = wordtext;
n2->narg.backquote = backquotelist;
n2->narg.next = NULL;
checkkwd = CHKNL | CHKKWD | CHKALIAS;
if (readtoken() != TIN)
synexpect(TIN);
cpp = &n1->ncase.cases;
next_case:
checkkwd = CHKNL | CHKKWD;
t = readtoken();
while(t != TESAC) {
if (lasttoken == TLP)
readtoken();
*cpp = cp = (union node *)stalloc(sizeof (struct nclist));
cp->type = NCLIST;
app = &cp->nclist.pattern;
for (;;) {
*app = ap = (union node *)stalloc(sizeof (struct narg));
ap->type = NARG;
ap->narg.text = wordtext;
ap->narg.backquote = backquotelist;
if (readtoken() != TPIPE)
break;
app = &ap->narg.next;
readtoken();
}
ap->narg.next = NULL;
if (lasttoken != TRP)
synexpect(TRP);
cp->nclist.body = list(2);
cpp = &cp->nclist.next;
checkkwd = CHKNL | CHKKWD;
if ((t = readtoken()) != TESAC) {
if (t != TENDCASE)
synexpect(TENDCASE);
else
goto next_case;
}
}
*cpp = NULL;
goto redir;
case TLP:
n1 = (union node *)stalloc(sizeof (struct nredir));
n1->type = NSUBSHELL;
n1->nredir.linno = savelinno;
n1->nredir.n = list(0);
n1->nredir.redirect = NULL;
t = TRP;
break;
case TBEGIN:
n1 = list(0);
t = TEND;
break;
case TWORD:
case TREDIR:
tokpushback++;
return simplecmd();
}
if (readtoken() != t)
synexpect(t);
redir:
checkkwd = CHKKWD | CHKALIAS;
rpp = rpp2;
while (readtoken() == TREDIR) {
*rpp = n2 = redirnode;
rpp = &n2->nfile.next;
parsefname();
}
tokpushback++;
*rpp = NULL;
if (redir) {
if (n1->type != NSUBSHELL) {
n2 = (union node *)stalloc(sizeof (struct nredir));
n2->type = NREDIR;
n2->nredir.linno = savelinno;
n2->nredir.n = n1;
n1 = n2;
}
n1->nredir.redirect = redir;
}
return n1;
}
STATIC union node *
simplecmd(void) {
union node *args, **app;
union node *n = NULL;
union node *vars, **vpp;
union node **rpp, *redir;
int savecheckkwd;
int savelinno;
args = NULL;
app = &args;
vars = NULL;
vpp = &vars;
redir = NULL;
rpp = &redir;
savecheckkwd = CHKALIAS;
savelinno = plinno;
for (;;) {
checkkwd = savecheckkwd;
switch (readtoken()) {
case TWORD:
n = (union node *)stalloc(sizeof (struct narg));
n->type = NARG;
n->narg.text = wordtext;
n->narg.backquote = backquotelist;
if (savecheckkwd && isassignment(wordtext)) {
*vpp = n;
vpp = &n->narg.next;
} else {
*app = n;
app = &n->narg.next;
savecheckkwd = 0;
}
break;
case TREDIR:
*rpp = n = redirnode;
rpp = &n->nfile.next;
parsefname(); 
break;
case TLP:
if (
args && app == &args->narg.next &&
!vars && !redir
) {
struct builtincmd *bcmd;
const char *name;
if (readtoken() != TRP)
synexpect(TRP);
name = n->narg.text;
if (
!goodname(name) || (
(bcmd = find_builtin(name)) &&
bcmd->flags & BUILTIN_SPECIAL
)
)
synerror("Bad function name");
n->type = NDEFUN;
checkkwd = CHKNL | CHKKWD | CHKALIAS;
n->ndefun.text = n->narg.text;
n->ndefun.linno = plinno;
n->ndefun.body = command();
return n;
}
default:
tokpushback++;
goto out;
}
}
out:
*app = NULL;
*vpp = NULL;
*rpp = NULL;
n = (union node *)stalloc(sizeof (struct ncmd));
n->type = NCMD;
n->ncmd.linno = savelinno;
n->ncmd.args = args;
n->ncmd.assign = vars;
n->ncmd.redirect = redir;
return n;
}
STATIC union node *
makename(void)
{
union node *n;
n = (union node *)stalloc(sizeof (struct narg));
n->type = NARG;
n->narg.next = NULL;
n->narg.text = wordtext;
n->narg.backquote = backquotelist;
return n;
}
void fixredir(union node *n, const char *text, int err)
{
TRACE(("Fix redir %s %d\n", text, err));
if (!err)
n->ndup.vname = NULL;
if (is_digit(text[0]) && text[1] == '\0')
n->ndup.dupfd = digit_val(text[0]);
else if (text[0] == '-' && text[1] == '\0')
n->ndup.dupfd = -1;
else {
if (err)
synerror("Bad fd number");
else
n->ndup.vname = makename();
}
}
STATIC void
parsefname(void)
{
union node *n = redirnode;
if (n->type == NHERE)
checkkwd = CHKEOFMARK;
if (readtoken() != TWORD)
synexpect(-1);
if (n->type == NHERE) {
struct heredoc *here = heredoc;
struct heredoc *p;
if (quoteflag == 0)
n->type = NXHERE;
TRACE(("Here document %d\n", n->type));
rmescapes(wordtext);
here->eofmark = wordtext;
here->next = NULL;
if (heredoclist == NULL)
heredoclist = here;
else {
for (p = heredoclist ; p->next ; p = p->next);
p->next = here;
}
} else if (n->type == NTOFD || n->type == NFROMFD) {
fixredir(n, wordtext, 0);
} else {
n->nfile.fname = makename();
}
}
STATIC void
parseheredoc(void)
{
struct heredoc *here;
union node *n;
here = heredoclist;
heredoclist = 0;
while (here) {
if (needprompt) {
setprompt(2);
}
readtoken1(pgetc(), here->here->type == NHERE? SQSYNTAX : DQSYNTAX,
here->eofmark, here->striptabs);
n = (union node *)stalloc(sizeof (struct narg));
n->narg.type = NARG;
n->narg.next = NULL;
n->narg.text = wordtext;
n->narg.backquote = backquotelist;
here->here->nhere.doc = n;
here = here->next;
}
}
STATIC int
peektoken(void)
{
int t;
t = readtoken();
tokpushback++;
return (t);
}
STATIC int
readtoken(void)
{
int t;
int kwd = checkkwd;
#ifdef DEBUG
int alreadyseen = tokpushback;
#endif
top:
t = xxreadtoken();
if (kwd & CHKNL) {
while (t == TNL) {
parseheredoc();
t = xxreadtoken();
}
}
if (t != TWORD || quoteflag) {
goto out;
}
if (kwd & CHKKWD) {
const char *const *pp;
if ((pp = findkwd(wordtext))) {
lasttoken = t = pp - parsekwd + KWDOFFSET;
TRACE(("keyword %s recognized\n", tokname[t]));
goto out;
}
}
if (checkkwd & CHKALIAS) {
struct alias *ap;
if ((ap = lookupalias(wordtext, 1)) != NULL) {
if (*ap->val) {
pushstring(ap->val, ap);
}
goto top;
}
}
out:
checkkwd = 0;
#ifdef DEBUG
if (!alreadyseen)
TRACE(("token %s %s\n", tokname[t], t == TWORD ? wordtext : ""));
else
TRACE(("reread token %s %s\n", tokname[t], t == TWORD ? wordtext : ""));
#endif
return (t);
}
#define RETURN(token) return lasttoken = token
STATIC int
xxreadtoken(void)
{
int c;
if (tokpushback) {
tokpushback = 0;
return lasttoken;
}
if (needprompt) {
setprompt(2);
}
for (;;) { 
c = pgetc_macro();
switch (c) {
case ' ': case '\t':
case PEOA:
continue;
case '#':
while ((c = pgetc()) != '\n' && c != PEOF);
pungetc();
continue;
case '\\':
if (pgetc() == '\n') {
plinno++;
if (doprompt)
setprompt(2);
continue;
}
pungetc();
goto breakloop;
case '\n':
plinno++;
needprompt = doprompt;
RETURN(TNL);
case PEOF:
RETURN(TEOF);
case '&':
if (pgetc() == '&')
RETURN(TAND);
pungetc();
RETURN(TBACKGND);
case '|':
if (pgetc() == '|')
RETURN(TOR);
pungetc();
RETURN(TPIPE);
case ';':
if (pgetc() == ';')
RETURN(TENDCASE);
pungetc();
RETURN(TSEMI);
case '(':
RETURN(TLP);
case ')':
RETURN(TRP);
default:
goto breakloop;
}
}
breakloop:
return readtoken1(c, BASESYNTAX, (char *)NULL, 0);
#undef RETURN
}
#define CHECKEND() {goto checkend; checkend_return:;}
#define PARSEREDIR() {goto parseredir; parseredir_return:;}
#define PARSESUB() {goto parsesub; parsesub_return:;}
#define PARSEBACKQOLD() {oldstyle = 1; goto parsebackq; parsebackq_oldreturn:;}
#define PARSEBACKQNEW() {oldstyle = 0; goto parsebackq; parsebackq_newreturn:;}
#define PARSEARITH() {goto parsearith; parsearith_return:;}
STATIC int
readtoken1(int firstc, char const *syntax, char *eofmark, int striptabs)
{
int c = firstc;
char *out;
int len;
struct nodelist *bqlist;
int quotef;
int dblquote;
int varnest; 
int arinest; 
int parenlevel; 
int dqvarnest; 
int oldstyle;
char const *uninitialized_var(prevsyntax);
dblquote = 0;
if (syntax == DQSYNTAX)
dblquote = 1;
quotef = 0;
bqlist = NULL;
varnest = 0;
arinest = 0;
parenlevel = 0;
dqvarnest = 0;
STARTSTACKSTR(out);
loop: { 
#if ATTY
if (c == '\034' && doprompt
&& attyset() && ! equal(termval(), "emacs")) {
attyline();
if (syntax == BASESYNTAX)
return readtoken();
c = pgetc();
goto loop;
}
#endif
CHECKEND(); 
for (;;) { 
CHECKSTRSPACE(4, out); 
switch(syntax[c]) {
case CNL: 
if (syntax == BASESYNTAX)
goto endword; 
USTPUTC(c, out);
plinno++;
if (doprompt)
setprompt(2);
c = pgetc();
goto loop; 
case CWORD:
USTPUTC(c, out);
break;
case CCTL:
if (eofmark == NULL || dblquote)
USTPUTC(CTLESC, out);
USTPUTC(c, out);
break;
case CBACK:
c = pgetc2();
if (c == PEOF) {
USTPUTC(CTLESC, out);
USTPUTC('\\', out);
pungetc();
} else if (c == '\n') {
plinno++;
if (doprompt)
setprompt(2);
} else {
if (
dblquote &&
c != '\\' && c != '`' &&
c != '$' && (
c != '"' ||
eofmark != NULL
)
) {
USTPUTC('\\', out);
}
USTPUTC(CTLESC, out);
USTPUTC(c, out);
quotef++;
}
break;
case CSQUOTE:
syntax = SQSYNTAX;
quotemark:
if (eofmark == NULL) {
USTPUTC(CTLQUOTEMARK, out);
}
break;
case CDQUOTE:
syntax = DQSYNTAX;
dblquote = 1;
goto quotemark;
case CENDQUOTE:
if (eofmark && !varnest)
USTPUTC(c, out);
else {
if (dqvarnest == 0) {
syntax = BASESYNTAX;
dblquote = 0;
}
quotef++;
goto quotemark;
}
break;
case CVAR: 
PARSESUB(); 
break;
case CENDVAR: 
if (varnest > 0) {
varnest--;
if (dqvarnest > 0) {
dqvarnest--;
}
USTPUTC(CTLENDVAR, out);
} else {
USTPUTC(c, out);
}
break;
case CLP: 
parenlevel++;
USTPUTC(c, out);
break;
case CRP: 
if (parenlevel > 0) {
USTPUTC(c, out);
--parenlevel;
} else {
if (pgetc() == ')') {
USTPUTC(CTLENDARI, out);
if (!--arinest)
syntax = prevsyntax;
} else {
pungetc();
USTPUTC(')', out);
}
}
break;
case CBQUOTE: 
PARSEBACKQOLD();
break;
case CEOS:
goto endword; 
case CIGN:
break;
default:
if (varnest == 0)
goto endword; 
if (c != PEOA) {
USTPUTC(c, out);
}
}
c = pgetc_macro();
}
}
endword:
if (syntax == ARISYNTAX)
synerror("Missing '))'");
if (syntax != BASESYNTAX && eofmark == NULL)
synerror("Unterminated quoted string");
if (varnest != 0) {
synerror("Missing '}'");
}
USTPUTC('\0', out);
len = out - (char *)stackblock();
out = stackblock();
if (eofmark == NULL) {
if ((c == '>' || c == '<')
&& quotef == 0
&& len <= 2
&& (*out == '\0' || is_digit(*out))) {
PARSEREDIR();
return lasttoken = TREDIR;
} else {
pungetc();
}
}
quoteflag = quotef;
backquotelist = bqlist;
grabstackblock(len);
wordtext = out;
return lasttoken = TWORD;
checkend: {
if (realeofmark(eofmark)) {
int markloc;
char *p;
if (c == PEOA) {
c = pgetc2();
}
if (striptabs) {
while (c == '\t') {
c = pgetc2();
}
}
markloc = out - (char *)stackblock();
for (p = eofmark; STPUTC(c, out), *p; p++) {
if (c != *p)
goto more_heredoc;
c = pgetc2();
}
if (c == '\n' || c == PEOF) {
c = PEOF;
plinno++;
needprompt = doprompt;
} else {
int len;
more_heredoc:
p = (char *)stackblock() + markloc + 1;
len = out - p;
if (len) {
len -= c < 0;
c = p[-1];
if (len) {
char *str;
str = alloca(len + 1);
*(char *)mempcpy(str, p, len) = 0;
pushstring(str, NULL);
}
}
}
STADJUST((char *)stackblock() + markloc - out, out);
}
goto checkend_return;
}
parseredir: {
char fd = *out;
union node *np;
np = (union node *)stalloc(sizeof (struct nfile));
if (c == '>') {
np->nfile.fd = 1;
c = pgetc();
if (c == '>')
np->type = NAPPEND;
else if (c == '|')
np->type = NCLOBBER;
else if (c == '&')
np->type = NTOFD;
else {
np->type = NTO;
pungetc();
}
} else { 
np->nfile.fd = 0;
switch (c = pgetc()) {
case '<':
if (sizeof (struct nfile) != sizeof (struct nhere)) {
np = (union node *)stalloc(sizeof (struct nhere));
np->nfile.fd = 0;
}
np->type = NHERE;
heredoc = (struct heredoc *)stalloc(sizeof (struct heredoc));
heredoc->here = np;
if ((c = pgetc()) == '-') {
heredoc->striptabs = 1;
} else {
heredoc->striptabs = 0;
pungetc();
}
break;
case '&':
np->type = NFROMFD;
break;
case '>':
np->type = NFROMTO;
break;
default:
np->type = NFROM;
pungetc();
break;
}
}
if (fd != '\0')
np->nfile.fd = digit_val(fd);
redirnode = np;
goto parseredir_return;
}
parsesub: {
int subtype;
int typeloc;
char *p;
static const char types[] = "}-+?=";
c = pgetc();
if (
(checkkwd & CHKEOFMARK) ||
c <= PEOA ||
(c != '(' && c != '{' && !is_name(c) && !is_special(c))
) {
USTPUTC('$', out);
pungetc();
} else if (c == '(') { 
if (pgetc() == '(') {
PARSEARITH();
} else {
pungetc();
PARSEBACKQNEW();
}
} else {
USTPUTC(CTLVAR, out);
typeloc = out - (char *)stackblock();
STADJUST(1, out);
subtype = VSNORMAL;
if (likely(c == '{')) {
c = pgetc();
subtype = 0;
}
varname:
if (is_name(c)) {
do {
STPUTC(c, out);
c = pgetc();
} while (is_in_name(c));
} else if (is_digit(c)) {
do {
STPUTC(c, out);
c = pgetc();
} while (is_digit(c));
}
else if (is_special(c)) {
int cc = c;
c = pgetc();
if (!subtype && cc == '#') {
subtype = VSLENGTH;
if (c == '_' || isalnum(c))
goto varname;
cc = c;
c = pgetc();
if (cc == '}' || c != '}') {
pungetc();
subtype = 0;
c = cc;
cc = '#';
}
}
USTPUTC(cc, out);
}
else
goto badsub;
if (subtype == 0) {
switch (c) {
case ':':
subtype = VSNUL;
c = pgetc();
default:
p = strchr(types, c);
if (p == NULL)
break;
subtype |= p - types + VSNORMAL;
break;
case '%':
case '#':
{
int cc = c;
subtype = c == '#' ? VSTRIMLEFT :
VSTRIMRIGHT;
c = pgetc();
if (c == cc)
subtype++;
else
pungetc();
break;
}
}
} else {
badsub:
pungetc();
}
*((char *)stackblock() + typeloc) = subtype;
if (subtype != VSNORMAL) {
varnest++;
if (dblquote)
dqvarnest++;
}
STPUTC('=', out);
}
goto parsesub_return;
}
parsebackq: {
struct nodelist **nlpp;
union node *n;
char *str;
size_t savelen;
int uninitialized_var(saveprompt);
str = NULL;
savelen = out - (char *)stackblock();
if (savelen > 0) {
str = alloca(savelen);
memcpy(str, stackblock(), savelen);
}
if (oldstyle) {
char *pout;
int pc;
size_t psavelen;
char *pstr;
STARTSTACKSTR(pout);
for (;;) {
if (needprompt) {
setprompt(2);
}
switch (pc = pgetc()) {
case '`':
goto done;
case '\\':
if ((pc = pgetc()) == '\n') {
plinno++;
if (doprompt)
setprompt(2);
continue;
}
if (pc != '\\' && pc != '`' && pc != '$'
&& (!dblquote || pc != '"'))
STPUTC('\\', pout);
if (pc > PEOA) {
break;
}
case PEOF:
case PEOA:
synerror("EOF in backquote substitution");
case '\n':
plinno++;
needprompt = doprompt;
break;
default:
break;
}
STPUTC(pc, pout);
}
done:
STPUTC('\0', pout);
psavelen = pout - (char *)stackblock();
if (psavelen > 0) {
pstr = grabstackstr(pout);
setinputstring(pstr);
}
}
nlpp = &bqlist;
while (*nlpp)
nlpp = &(*nlpp)->next;
*nlpp = (struct nodelist *)stalloc(sizeof (struct nodelist));
(*nlpp)->next = NULL;
if (oldstyle) {
saveprompt = doprompt;
doprompt = 0;
}
n = list(2);
if (oldstyle)
doprompt = saveprompt;
else {
if (readtoken() != TRP)
synexpect(TRP);
}
(*nlpp)->n = n;
if (oldstyle) {
popfile();
tokpushback = 0;
}
while (stackblocksize() <= savelen)
growstackblock();
STARTSTACKSTR(out);
if (str) {
memcpy(out, str, savelen);
STADJUST(savelen, out);
}
USTPUTC(CTLBACKQ, out);
if (oldstyle)
goto parsebackq_oldreturn;
else
goto parsebackq_newreturn;
}
parsearith: {
if (++arinest == 1) {
prevsyntax = syntax;
syntax = ARISYNTAX;
}
USTPUTC(CTLARI, out);
goto parsearith_return;
}
} 
#ifdef mkinit
INCLUDE "parser.h"
RESET {
tokpushback = 0;
checkkwd = 0;
}
#endif
char *
endofname(const char *name)
{
char *p;
p = (char *) name;
if (! is_name(*p))
return p;
while (*++p) {
if (! is_in_name(*p))
break;
}
return p;
}
STATIC void
synexpect(int token)
{
char msg[64];
if (token >= 0) {
fmtstr(msg, 64, "%s unexpected (expecting %s)",
tokname[lasttoken], tokname[token]);
} else {
fmtstr(msg, 64, "%s unexpected", tokname[lasttoken]);
}
synerror(msg);
}
STATIC void
synerror(const char *msg)
{
errlinno = plinno;
sh_error("Syntax error: %s", msg);
}
STATIC void
setprompt(int which)
{
struct stackmark smark;
int show;
needprompt = 0;
whichprompt = which;
#ifdef SMALL
show = 1;
#else
show = !el;
#endif
if (show) {
pushstackmark(&smark, stackblocksize());
out2str(getprompt(NULL));
popstackmark(&smark);
}
}
const char *
expandstr(const char *ps)
{
union node n;
int saveprompt;
setinputstring((char *)ps);
saveprompt = doprompt;
doprompt = 0;
readtoken1(pgetc(), DQSYNTAX, FAKEEOFMARK, 0);
doprompt = saveprompt;
popfile();
n.narg.type = NARG;
n.narg.next = NULL;
n.narg.text = wordtext;
n.narg.backquote = backquotelist;
expandarg(&n, NULL, EXP_QUOTED);
return stackblock();
}
const char *
getprompt(void *unused)
{
const char *prompt;
switch (whichprompt) {
default:
#ifdef DEBUG
return "<internal prompt error>";
#endif
case 0:
return nullstr;
case 1:
prompt = ps1val();
break;
case 2:
prompt = ps2val();
break;
}
return expandstr(prompt);
}
const char *const *
findkwd(const char *s)
{
return findstring(
s, parsekwd, sizeof(parsekwd) / sizeof(const char *)
);
}
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/param.h> 
#include <signal.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#define REALLY_CLOSED -3 
#define EMPTY -2 
#define CLOSED -1 
#ifndef PIPE_BUF
# define PIPESIZE 4096 
#else
# define PIPESIZE PIPE_BUF
#endif
MKINIT
struct redirtab {
struct redirtab *next;
int renamed[10];
};
MKINIT struct redirtab *redirlist;
STATIC int openredirect(union node *);
#ifdef notyet
STATIC void dupredirect(union node *, int, char[10]);
#else
STATIC void dupredirect(union node *, int);
#endif
STATIC int openhere(union node *);
void
redirect(union node *redir, int flags)
{
union node *n;
struct redirtab *sv;
int i;
int fd;
int newfd;
int *p;
#if notyet
char memory[10]; 
for (i = 10 ; --i >= 0 ; )
memory[i] = 0;
memory[1] = flags & REDIR_BACKQ;
#endif
if (!redir)
return;
sv = NULL;
INTOFF;
if (likely(flags & REDIR_PUSH))
sv = redirlist;
n = redir;
do {
newfd = openredirect(n);
if (newfd < -1)
continue;
fd = n->nfile.fd;
if (sv) {
p = &sv->renamed[fd];
i = *p;
if (likely(i == EMPTY)) {
i = CLOSED;
if (fd != newfd) {
i = savefd(fd, fd);
fd = -1;
}
}
if (i == newfd)
i = REALLY_CLOSED;
*p = i;
}
if (fd == newfd)
continue;
#ifdef notyet
dupredirect(n, newfd, memory);
#else
dupredirect(n, newfd);
#endif
} while ((n = n->nfile.next));
INTON;
#ifdef notyet
if (memory[1])
out1 = &memout;
if (memory[2])
out2 = &memout;
#endif
if (flags & REDIR_SAVEFD2 && sv->renamed[2] >= 0)
preverrout.fd = sv->renamed[2];
}
STATIC int
openredirect(union node *redir)
{
struct stat64 sb;
char *fname;
int f;
switch (redir->nfile.type) {
case NFROM:
fname = redir->nfile.expfname;
if ((f = open64(fname, O_RDONLY)) < 0)
goto eopen;
break;
case NFROMTO:
fname = redir->nfile.expfname;
if ((f = open64(fname, O_RDWR|O_CREAT, 0666)) < 0)
goto ecreate;
break;
case NTO:
if (Cflag) {
fname = redir->nfile.expfname;
if (stat64(fname, &sb) < 0) {
if ((f = open64(fname, O_WRONLY|O_CREAT|O_EXCL, 0666)) < 0)
goto ecreate;
} else if (!S_ISREG(sb.st_mode)) {
if ((f = open64(fname, O_WRONLY, 0666)) < 0)
goto ecreate;
if (fstat64(f, &sb) < 0 && S_ISREG(sb.st_mode)) {
close(f);
errno = EEXIST;
goto ecreate;
}
} else {
errno = EEXIST;
goto ecreate;
}
break;
}
case NCLOBBER:
fname = redir->nfile.expfname;
if ((f = open64(fname, O_WRONLY|O_CREAT|O_TRUNC, 0666)) < 0)
goto ecreate;
break;
case NAPPEND:
fname = redir->nfile.expfname;
if ((f = open64(fname, O_WRONLY|O_CREAT|O_APPEND, 0666)) < 0)
goto ecreate;
break;
case NTOFD:
case NFROMFD:
f = redir->ndup.dupfd;
if (f == redir->nfile.fd)
f = -2;
break;
default:
#ifdef DEBUG
abort();
#endif
case NHERE:
case NXHERE:
f = openhere(redir);
break;
}
return f;
ecreate:
sh_error("cannot create %s: %s", fname, errmsg(errno, E_CREAT));
eopen:
sh_error("cannot open %s: %s", fname, errmsg(errno, E_OPEN));
}
STATIC void
#ifdef notyet
dupredirect(redir, f, memory)
#else
dupredirect(redir, f)
#endif
union node *redir;
int f;
#ifdef notyet
char memory[10];
#endif
{
int fd = redir->nfile.fd;
int err = 0;
#ifdef notyet
memory[fd] = 0;
#endif
if (redir->nfile.type == NTOFD || redir->nfile.type == NFROMFD) {
if (f >= 0) {
#ifdef notyet
if (memory[f])
memory[fd] = 1;
else
#endif
if (dup2(f, fd) < 0) {
err = errno;
goto err;
}
return;
}
f = fd;
} else if (dup2(f, fd) < 0)
err = errno;
close(f);
if (err < 0)
goto err;
return;
err:
sh_error("%d: %s", f, strerror(err));
}
STATIC int
openhere(union node *redir)
{
char *p;
int pip[2];
size_t len = 0;
if (pipe(pip) < 0)
sh_error("Pipe call failed");
p = redir->nhere.doc->narg.text;
if (redir->type == NXHERE) {
expandarg(redir->nhere.doc, NULL, EXP_QUOTED);
p = stackblock();
}
len = strlen(p);
if (len <= PIPESIZE) {
xwrite(pip[1], p, len);
goto out;
}
if (forkshell((struct job *)NULL, (union node *)NULL, FORK_NOJOB) == 0) {
close(pip[0]);
signal(SIGINT, SIG_IGN);
signal(SIGQUIT, SIG_IGN);
signal(SIGHUP, SIG_IGN);
#ifdef SIGTSTP
signal(SIGTSTP, SIG_IGN);
#endif
signal(SIGPIPE, SIG_DFL);
xwrite(pip[1], p, len);
_exit(0);
}
out:
close(pip[1]);
return pip[0];
}
void
popredir(int drop)
{
struct redirtab *rp;
int i;
INTOFF;
rp = redirlist;
for (i = 0 ; i < 10 ; i++) {
switch (rp->renamed[i]) {
case CLOSED:
if (!drop)
close(i);
break;
case EMPTY:
case REALLY_CLOSED:
break;
default:
if (!drop)
dup2(rp->renamed[i], i);
close(rp->renamed[i]);
break;
}
}
redirlist = rp->next;
ckfree(rp);
INTON;
}
#ifdef mkinit
INCLUDE "redir.h"
RESET {
unwindredir(0);
}
#endif
int
savefd(int from, int ofd)
{
int newfd;
int err;
newfd = fcntl(from, F_DUPFD, 10);
err = newfd < 0 ? errno : 0;
if (err != EBADF) {
close(ofd);
if (err)
sh_error("%d: %s", from, strerror(err));
else
fcntl(newfd, F_SETFD, FD_CLOEXEC);
}
return newfd;
}
int
redirectsafe(union node *redir, int flags)
{
int err;
volatile int saveint;
struct jmploc *volatile savehandler = handler;
struct jmploc jmploc;
SAVEINT(saveint);
if (!(err = setjmp(jmploc.loc) * 2)) {
handler = &jmploc;
redirect(redir, flags);
}
handler = savehandler;
if (err && exception != EXERROR)
longjmp(handler->loc, 1);
RESTOREINT(saveint);
return err;
}
void unwindredir(struct redirtab *stop)
{
while (redirlist != stop)
popredir(0);
}
struct redirtab *pushredir(union node *redir)
{
struct redirtab *sv;
struct redirtab *q;
int i;
q = redirlist;
if (!redir)
goto out;
sv = ckmalloc(sizeof (struct redirtab));
sv->next = q;
redirlist = sv;
for (i = 0; i < 10; i++)
sv->renamed[i] = EMPTY;
out:
return q;
}
#include <stdio.h>
#include <stdarg.h>
#ifdef DEBUG
static void shtree(union node *, int, char *, FILE*);
static void shcmd(union node *, FILE *);
static void sharg(union node *, FILE *);
static void indent(int, char *, FILE *);
static void trstring(char *);
void
showtree(union node *n)
{
trputs("showtree called\n");
shtree(n, 1, NULL, stdout);
}
static void
shtree(union node *n, int ind, char *pfx, FILE *fp)
{
struct nodelist *lp;
const char *s;
if (n == NULL)
return;
indent(ind, pfx, fp);
switch(n->type) {
case NSEMI:
s = "; ";
goto binop;
case NAND:
s = " && ";
goto binop;
case NOR:
s = " || ";
binop:
shtree(n->nbinary.ch1, ind, NULL, fp);
fputs(s, fp);
shtree(n->nbinary.ch2, ind, NULL, fp);
break;
case NCMD:
shcmd(n, fp);
if (ind >= 0)
putc('\n', fp);
break;
case NPIPE:
for (lp = n->npipe.cmdlist ; lp ; lp = lp->next) {
shcmd(lp->n, fp);
if (lp->next)
fputs(" | ", fp);
}
if (n->npipe.backgnd)
fputs(" &", fp);
if (ind >= 0)
putc('\n', fp);
break;
default:
fprintf(fp, "<node type %d>", n->type);
if (ind >= 0)
putc('\n', fp);
break;
}
}
static void
shcmd(union node *cmd, FILE *fp)
{
union node *np;
int first;
const char *s;
int dftfd;
first = 1;
for (np = cmd->ncmd.args ; np ; np = np->narg.next) {
if (! first)
putchar(' ');
sharg(np, fp);
first = 0;
}
for (np = cmd->ncmd.redirect ; np ; np = np->nfile.next) {
if (! first)
putchar(' ');
switch (np->nfile.type) {
case NTO: s = ">"; dftfd = 1; break;
case NCLOBBER: s = ">|"; dftfd = 1; break;
case NAPPEND: s = ">>"; dftfd = 1; break;
case NTOFD: s = ">&"; dftfd = 1; break;
case NFROM: s = "<"; dftfd = 0; break;
case NFROMFD: s = "<&"; dftfd = 0; break;
case NFROMTO: s = "<>"; dftfd = 0; break;
default: s = "*error*"; dftfd = 0; break;
}
if (np->nfile.fd != dftfd)
fprintf(fp, "%d", np->nfile.fd);
fputs(s, fp);
if (np->nfile.type == NTOFD || np->nfile.type == NFROMFD) {
fprintf(fp, "%d", np->ndup.dupfd);
} else {
sharg(np->nfile.fname, fp);
}
first = 0;
}
}
static void
sharg(union node *arg, FILE *fp)
{
char *p;
struct nodelist *bqlist;
int subtype;
if (arg->type != NARG) {
printf("<node type %d>\n", arg->type);
abort();
}
bqlist = arg->narg.backquote;
for (p = arg->narg.text ; *p ; p++) {
switch ((signed char)*p) {
case CTLESC:
putc(*++p, fp);
break;
case CTLVAR:
putc('$', fp);
putc('{', fp);
subtype = *++p;
if (subtype == VSLENGTH)
putc('#', fp);
while (*p != '=')
putc(*p++, fp);
if (subtype & VSNUL)
putc(':', fp);
switch (subtype & VSTYPE) {
case VSNORMAL:
putc('}', fp);
break;
case VSMINUS:
putc('-', fp);
break;
case VSPLUS:
putc('+', fp);
break;
case VSQUESTION:
putc('?', fp);
break;
case VSASSIGN:
putc('=', fp);
break;
case VSTRIMLEFT:
putc('#', fp);
break;
case VSTRIMLEFTMAX:
putc('#', fp);
putc('#', fp);
break;
case VSTRIMRIGHT:
putc('%', fp);
break;
case VSTRIMRIGHTMAX:
putc('%', fp);
putc('%', fp);
break;
case VSLENGTH:
break;
default:
printf("<subtype %d>", subtype);
}
break;
case CTLENDVAR:
putc('}', fp);
break;
case CTLBACKQ:
putc('$', fp);
putc('(', fp);
shtree(bqlist->n, -1, NULL, fp);
putc(')', fp);
break;
default:
putc(*p, fp);
break;
}
}
}
static void
indent(int amount, char *pfx, FILE *fp)
{
int i;
for (i = 0 ; i < amount ; i++) {
if (pfx && i == amount - 1)
fputs(pfx, fp);
putc('\t', fp);
}
}
FILE *tracefile;
void
trputc(int c)
{
if (debug != 1)
return;
putc(c, tracefile);
}
void
trace(const char *fmt, ...)
{
va_list va;
if (debug != 1)
return;
va_start(va, fmt);
(void) vfprintf(tracefile, fmt, va);
va_end(va);
}
void
tracev(const char *fmt, va_list va)
{
if (debug != 1)
return;
(void) vfprintf(tracefile, fmt, va);
}
void
trputs(const char *s)
{
if (debug != 1)
return;
fputs(s, tracefile);
}
static void
trstring(char *s)
{
char *p;
char c;
if (debug != 1)
return;
putc('"', tracefile);
for (p = s ; *p ; p++) {
switch ((signed char)*p) {
case '\n': c = 'n'; goto backslash;
case '\t': c = 't'; goto backslash;
case '\r': c = 'r'; goto backslash;
case '"': c = '"'; goto backslash;
case '\\': c = '\\'; goto backslash;
case CTLESC: c = 'e'; goto backslash;
case CTLVAR: c = 'v'; goto backslash;
case CTLBACKQ: c = 'q'; goto backslash;
backslash: putc('\\', tracefile);
putc(c, tracefile);
break;
default:
if (*p >= ' ' && *p <= '~')
putc(*p, tracefile);
else {
putc('\\', tracefile);
putc(*p >> 6 & 03, tracefile);
putc(*p >> 3 & 07, tracefile);
putc(*p & 07, tracefile);
}
break;
}
}
putc('"', tracefile);
}
void
trargs(char **ap)
{
if (debug != 1)
return;
while (*ap) {
trstring(*ap++);
if (*ap)
putc(' ', tracefile);
else
putc('\n', tracefile);
}
}
void
opentrace(void)
{
char s[100];
#ifdef O_APPEND
int flags;
#endif
if (debug != 1) {
if (tracefile)
fflush(tracefile);
return;
}
#ifdef not_this_way
{
char *p;
if ((p = getenv(homestr)) == NULL) {
if (geteuid() == 0)
p = "/";
else
p = "/tmp";
}
scopy(p, s);
strcat(s, "/trace");
}
#else
scopy("./trace", s);
#endif 
if (tracefile) {
#ifndef __KLIBC__
if (!freopen(s, "a", tracefile)) {
#else
if (!(!fclose(tracefile) && (tracefile = fopen(s, "a")))) {
#endif 
fprintf(stderr, "Can't re-open %s\n", s);
debug = 0;
return;
}
} else {
if ((tracefile = fopen(s, "a")) == NULL) {
fprintf(stderr, "Can't open %s\n", s);
debug = 0;
return;
}
}
#ifdef O_APPEND
if ((flags = fcntl(fileno(tracefile), F_GETFL, 0)) >= 0)
fcntl(fileno(tracefile), F_SETFL, flags | O_APPEND);
#endif
#ifndef __KLIBC__
setlinebuf(tracefile);
#endif 
fputs("\nTracing started.\n", tracefile);
}
#endif 
#include <signal.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#ifdef HETIO
#endif
#define S_DFL 1 
#define S_CATCH 2 
#define S_IGN 3 
#define S_HARD_IGN 4 
#define S_RESET 5 
static char *trap[NSIG];
int trapcnt;
char sigmode[NSIG - 1];
static char gotsig[NSIG - 1];
volatile sig_atomic_t pendingsigs;
int gotsigchld;
extern const char * const signal_names[];
#ifdef mkinit
INCLUDE "trap.h"
INIT {
sigmode[SIGCHLD - 1] = S_DFL;
setsignal(SIGCHLD);
}
#endif
int
trapcmd(int argc, char **argv)
{
char *action;
char **ap;
int signo;
nextopt(nullstr);
ap = argptr;
if (!*ap) {
for (signo = 0 ; signo < NSIG ; signo++) {
if (trap[signo] != NULL) {
out1fmt(
"trap -- %s %s\n",
single_quote(trap[signo]),
signal_names[signo]
);
}
}
return 0;
}
if (!ap[1])
action = NULL;
else
action = *ap++;
while (*ap) {
if ((signo = decode_signal(*ap, 0)) < 0) {
outfmt(out2, "trap: %s: bad trap\n", *ap);
return 1;
}
INTOFF;
if (action) {
if (action[0] == '-' && action[1] == '\0')
action = NULL;
else {
if (*action)
trapcnt++;
action = savestr(action);
}
}
if (trap[signo]) {
if (*trap[signo])
trapcnt--;
ckfree(trap[signo]);
}
trap[signo] = action;
if (signo != 0)
setsignal(signo);
INTON;
ap++;
}
return 0;
}
void
clear_traps(void)
{
char **tp;
INTOFF;
for (tp = trap ; tp < &trap[NSIG] ; tp++) {
if (*tp && **tp) { 
ckfree(*tp);
*tp = NULL;
if (tp != &trap[0])
setsignal(tp - trap);
}
}
trapcnt = 0;
INTON;
}
void
setsignal(int signo)
{
int action;
char *t, tsig;
struct sigaction act;
if ((t = trap[signo]) == NULL)
action = S_DFL;
else if (*t != '\0')
action = S_CATCH;
else
action = S_IGN;
if (rootshell && action == S_DFL) {
switch (signo) {
case SIGINT:
if (iflag || minusc || sflag == 0)
action = S_CATCH;
break;
case SIGQUIT:
#ifdef DEBUG
if (debug)
break;
#endif
case SIGTERM:
if (iflag)
action = S_IGN;
break;
#if JOBS
case SIGTSTP:
case SIGTTOU:
if (mflag)
action = S_IGN;
break;
#endif
}
}
if (signo == SIGCHLD)
action = S_CATCH;
t = &sigmode[signo - 1];
tsig = *t;
if (tsig == 0) {
if (sigaction(signo, 0, &act) == -1) {
return;
}
if (act.sa_handler == SIG_IGN) {
if (mflag && (signo == SIGTSTP ||
signo == SIGTTIN || signo == SIGTTOU)) {
tsig = S_IGN; 
} else
tsig = S_HARD_IGN;
} else {
tsig = S_RESET; 
}
}
if (tsig == S_HARD_IGN || tsig == action)
return;
switch (action) {
case S_CATCH:
act.sa_handler = onsig;
break;
case S_IGN:
act.sa_handler = SIG_IGN;
break;
default:
act.sa_handler = SIG_DFL;
}
*t = action;
act.sa_flags = 0;
sigfillset(&act.sa_mask);
sigaction(signo, &act, 0);
}
void
ignoresig(int signo)
{
if (sigmode[signo - 1] != S_IGN && sigmode[signo - 1] != S_HARD_IGN) {
signal(signo, SIG_IGN);
}
sigmode[signo - 1] = S_HARD_IGN;
}
void
onsig(int signo)
{
if (signo == SIGCHLD) {
gotsigchld = 1;
if (!trap[SIGCHLD])
return;
}
gotsig[signo - 1] = 1;
pendingsigs = signo;
if (signo == SIGINT && !trap[SIGINT]) {
if (!suppressint)
onint();
intpending = 1;
}
}
void dotrap(void)
{
char *p;
char *q;
int i;
int savestatus;
savestatus = exitstatus;
pendingsigs = 0;
barrier();
for (i = 0, q = gotsig; i < NSIG - 1; i++, q++) {
if (!*q)
continue;
*q = 0;
p = trap[i + 1];
if (!p)
continue;
evalstring(p, 0);
exitstatus = savestatus;
if (evalskip)
break;
}
}
void
setinteractive(int on)
{
static int is_interactive;
if (++on == is_interactive)
return;
is_interactive = on;
setsignal(SIGINT);
setsignal(SIGQUIT);
setsignal(SIGTERM);
}
void
exitshell(void)
{
struct jmploc loc;
char *p;
volatile int status;
#ifdef HETIO
hetio_reset_term();
#endif
status = exitstatus;
TRACE(("pid %d, exitshell(%d)\n", getpid(), status));
if (setjmp(loc.loc)) {
if (exception == EXEXIT)
status = exitstatus;
goto out;
}
handler = &loc;
if ((p = trap[0])) {
trap[0] = NULL;
evalskip = 0;
evalstring(p, 0);
}
out:
if (likely(!setjmp(loc.loc)))
setjobctl(0);
flushall();
_exit(status);
}
int decode_signal(const char *string, int minsig)
{
int signo;
if (is_number(string)) {
signo = atoi(string);
if (signo >= NSIG) {
return -1;
}
return signo;
}
for (signo = minsig; signo < NSIG; signo++) {
if (signal_names[signo] && !strcasecmp(string, signal_names[signo])) {
return signo;
}
}
return -1;
}
#include <sys/types.h> 
#include <sys/param.h> 
#include <sys/ioctl.h>
#include <stdio.h> 
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#ifdef USE_GLIBC_STDIO
#include <fcntl.h>
#endif
#include <limits.h>
#define OUTBUFSIZ BUFSIZ
#define MEM_OUT -3 
#ifdef USE_GLIBC_STDIO
struct output output = {
stream: 0, nextc: 0, end: 0, buf: 0, bufsize: 0, fd: 1, flags: 0
};
struct output errout = {
stream: 0, nextc: 0, end: 0, buf: 0, bufsize: 0, fd: 2, flags: 0
}
#ifdef notyet
struct output memout = {
stream: 0, nextc: 0, end: 0, buf: 0, bufsize: 0, fd: MEM_OUT, flags: 0
};
#endif
#else
struct output output = {
nextc: 0, end: 0, buf: 0, bufsize: OUTBUFSIZ, fd: 1, flags: 0
};
struct output errout = {
nextc: 0, end: 0, buf: 0, bufsize: 0, fd: 2, flags: 0
};
struct output preverrout;
#ifdef notyet
struct output memout = {
nextc: 0, end: 0, buf: 0, bufsize: 0, fd: MEM_OUT, flags: 0
};
#endif
#endif
struct output *out1 = &output;
struct output *out2 = &errout;
#ifndef USE_GLIBC_STDIO
static void __outstr(const char *, size_t, struct output *);
#endif
static int xvsnprintf(char *, size_t, const char *, va_list);
#ifdef mkinit
INCLUDE "output.h"
INCLUDE "memalloc.h"
INIT {
#ifdef USE_GLIBC_STDIO
initstreams();
#endif
}
RESET {
#ifdef notyet
out1 = &output;
out2 = &errout;
#ifdef USE_GLIBC_STDIO
if (memout.stream != NULL)
__closememout();
#endif
if (memout.buf != NULL) {
ckfree(memout.buf);
memout.buf = NULL;
}
#endif
}
#endif
#ifndef USE_GLIBC_STDIO
static void
__outstr(const char *p, size_t len, struct output *dest)
{
size_t bufsize;
size_t offset;
size_t nleft;
nleft = dest->end - dest->nextc;
if (nleft >= len) {
buffered:
dest->nextc = mempcpy(dest->nextc, p, len);
return;
}
bufsize = dest->bufsize;
if (!bufsize) {
;
} else if (dest->buf == NULL) {
if (dest->fd == MEM_OUT && len > bufsize) {
bufsize = len;
}
offset = 0;
goto alloc;
} else if (dest->fd == MEM_OUT) {
offset = bufsize;
if (bufsize >= len) {
bufsize <<= 1;
} else {
bufsize += len;
}
if (bufsize < offset)
goto err;
alloc:
INTOFF;
dest->buf = ckrealloc(dest->buf, bufsize);
dest->bufsize = bufsize;
dest->end = dest->buf + bufsize;
dest->nextc = dest->buf + offset;
INTON;
} else {
flushout(dest);
}
nleft = dest->end - dest->nextc;
if (nleft > len)
goto buffered;
if ((xwrite(dest->fd, p, len))) {
err:
dest->flags |= OUTPUT_ERR;
}
}
#endif
void
outstr(const char *p, struct output *file)
{
#ifdef USE_GLIBC_STDIO
INTOFF;
fputs(p, file->stream);
INTON;
#else
size_t len;
len = strlen(p);
__outstr(p, len, file);
#endif
}
#ifndef USE_GLIBC_STDIO
void
outcslow(int c, struct output *dest)
{
char buf = c;
__outstr(&buf, 1, dest);
}
#endif
void
flushall(void)
{
flushout(&output);
#ifdef FLUSHERR
flushout(&errout);
#endif
}
void
flushout(struct output *dest)
{
#ifdef USE_GLIBC_STDIO
INTOFF;
fflush(dest->stream);
INTON;
#else
size_t len;
len = dest->nextc - dest->buf;
if (!len || dest->fd < 0)
return;
dest->nextc = dest->buf;
if ((xwrite(dest->fd, dest->buf, len)))
dest->flags |= OUTPUT_ERR;
#endif
}
void
outfmt(struct output *file, const char *fmt, ...)
{
va_list ap;
va_start(ap, fmt);
doformat(file, fmt, ap);
va_end(ap);
}
void
out1fmt(const char *fmt, ...)
{
va_list ap;
va_start(ap, fmt);
doformat(out1, fmt, ap);
va_end(ap);
}
int
fmtstr(char *outbuf, size_t length, const char *fmt, ...)
{
va_list ap;
int ret;
va_start(ap, fmt);
ret = xvsnprintf(outbuf, length, fmt, ap);
va_end(ap);
return ret;
}
#ifndef USE_GLIBC_STDIO
void
doformat(struct output *dest, const char *f, va_list ap)
{
struct stackmark smark;
char *s;
int len, ret;
size_t size;
va_list ap2;
va_copy(ap2, ap);
size = dest->end - dest->nextc;
len = xvsnprintf(dest->nextc, size, f, ap2);
va_end(ap2);
if (len < 0) {
dest->flags |= OUTPUT_ERR;
return;
}
if (len < size) {
dest->nextc += len;
return;
}
setstackmark(&smark);
s = stalloc((len >= stackblocksize() ? len : stackblocksize()) + 1);
ret = xvsnprintf(s, len + 1, f, ap);
if (ret == len)
__outstr(s, len, dest);
else
dest->flags |= OUTPUT_ERR;
popstackmark(&smark);
}
#endif
int
xwrite(int fd, const void *p, size_t n)
{
const char *buf = p;
while (n) {
ssize_t i;
size_t m;
m = n;
if (m > SSIZE_MAX)
m = SSIZE_MAX;
do {
i = write(fd, buf, m);
} while (i < 0 && errno == EINTR);
if (i < 0)
return -1;
buf += i;
n -= i;
}
return 0;
}
#ifdef notyet
#ifdef USE_GLIBC_STDIO
void initstreams() {
output.stream = stdout;
errout.stream = stderr;
}
void
openmemout(void) {
INTOFF;
memout.stream = open_memstream(&memout.buf, &memout.bufsize);
INTON;
}
int
__closememout(void) {
int error;
error = fclose(memout.stream);
memout.stream = NULL;
return error;
}
#endif
#endif
#ifdef __hpux
static int
xvsnprintf(char *outbuf, size_t length, const char *fmt, va_list ap)
{
int ret;
char* dummy = NULL;
char* dummy_new = NULL;
size_t dummy_len = 8;
va_list ap_mine;
if (length > 0) {
INTOFF;
va_copy(ap_mine, ap);
errno = 0;
ret = vsnprintf(outbuf, length, fmt, ap_mine);
va_end(ap_mine);
INTON;
} else {
ret = -1;
errno = 0;
}
if (ret < 0 && errno == 0) {
do {
dummy_len *= 2;
dummy_new = realloc(dummy, dummy_len);
if (!dummy_new) {
ret = -1;
errno = ENOMEM;
break;
}
dummy = dummy_new;
INTOFF;
va_copy(ap_mine, ap);
errno = 0;
ret = vsnprintf(dummy, dummy_len, fmt, ap_mine);
va_end(ap_mine);
INTON;
} while (ret < 0 && errno == 0);
if (ret >= 0 && length) {
memcpy(outbuf, dummy, length);
}
if (dummy) free(dummy);
}
return ret;
}
#else
static int
xvsnprintf(char *outbuf, size_t length, const char *fmt, va_list ap)
{
int ret;
#ifdef __sun
char dummy[1];
if (length == 0) {
outbuf = dummy;
length = sizeof(dummy);
}
#endif
INTOFF;
ret = vsnprintf(outbuf, length, fmt, ap);
INTON;
return ret;
}
#endif
#include <sys/types.h>
#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static int conv_escape_str(char *);
static char *conv_escape(char *, int *);
static int getchr(void);
static double getdouble(void);
static intmax_t getintmax(void);
static uintmax_t getuintmax(void);
static char *getstr(void);
static char *mklong(const char *, const char *);
static void check_conversion(const char *, const char *);
static int rval;
static char **gargv;
#define isodigit(c) ((c) >= '0' && (c) <= '7')
#define octtobin(c) ((c) - '0')
#define PF(f, func) { \
switch ((char *)param - (char *)array) { \
default: \
(void)blt_printf(f, array[0], array[1], func); \
break; \
case sizeof(*param): \
(void)blt_printf(f, array[0], func); \
break; \
case 0: \
(void)blt_printf(f, func); \
break; \
} \
}
int printfcmd(int argc, char *argv[])
{
char *fmt;
char *format;
int ch;
rval = 0;
nextopt(nullstr);
argv = argptr;
format = *argv;
if (!format) {
warnx("usage: printf format [arg ...]");
goto err;
}
gargv = ++argv;
#define SKIP1 "#-+ 0"
#define SKIP2 "*0123456789"
do {
for (fmt = format; (ch = *fmt++) ;) {
char *start;
char nextch;
int array[2];
int *param;
if (ch == '\\') {
int c_ch;
fmt = conv_escape(fmt, &c_ch);
ch = c_ch;
goto pc;
}
if (ch != '%' || (*fmt == '%' && (++fmt || 1))) {
pc:
blt_putchar(ch);
continue;
}
start = fmt - 1;
param = array;
fmt += strspn(fmt, SKIP1);
if (*fmt == '*')
*param++ = getintmax();
fmt += strspn(fmt, SKIP2);
if (*fmt == '.')
++fmt;
if (*fmt == '*')
*param++ = getintmax();
fmt += strspn(fmt, SKIP2);
ch = *fmt;
if (!ch) {
warnx("missing format character");
goto err;
}
nextch = fmt[1];
fmt[1] = 0;
switch (ch) {
case 'b': {
int done = conv_escape_str(getstr());
char *p = stackblock();
*fmt = 's';
PF(start, p);
if (done)
goto out;
*fmt = 'b';
break;
}
case 'c': {
int p = getchr();
PF(start, p);
break;
}
case 's': {
char *p = getstr();
PF(start, p);
break;
}
case 'd':
case 'i': {
intmax_t p = getintmax();
char *f = mklong(start, fmt);
PF(f, p);
break;
}
case 'o':
case 'u':
case 'x':
case 'X': {
uintmax_t p = getuintmax();
char *f = mklong(start, fmt);
PF(f, p);
break;
}
case 'e':
case 'E':
case 'f':
case 'g':
case 'G': {
double p = getdouble();
PF(start, p);
break;
}
default:
warnx("%s: invalid directive", start);
goto err;
}
*++fmt = nextch;
}
} while (gargv != argv && *gargv);
out:
return rval;
err:
return 1;
}
static int
conv_escape_str(char *str)
{
int ch;
char *cp;
STARTSTACKSTR(cp);
do {
int c;
ch = *str++;
if (ch != '\\')
continue;
ch = *str++;
if (ch == 'c') {
ch = 0x100;
continue;
}
if (ch == '0') {
unsigned char i;
i = 3;
ch = 0;
do {
unsigned k = octtobin(*str);
if (k > 7)
break;
str++;
ch <<= 3;
ch += k;
} while (--i);
continue;
}
str = conv_escape(str - 1, &c);
ch = c;
} while (STPUTC(ch, cp), (char)ch);
return ch;
}
static char *
conv_escape(char *str, int *conv_ch)
{
int value;
int ch;
ch = *str;
switch (ch) {
default:
case 0:
value = '\\';
goto out;
case '0': case '1': case '2': case '3':
case '4': case '5': case '6': case '7':
ch = 3;
value = 0;
do {
value <<= 3;
value += octtobin(*str++);
} while (isodigit(*str) && --ch);
goto out;
case '\\': value = '\\'; break; 
case 'a': value = '\a'; break; 
case 'b': value = '\b'; break; 
case 'f': value = '\f'; break; 
case 'n': value = '\n'; break; 
case 'r': value = '\r'; break; 
case 't': value = '\t'; break; 
case 'v': value = '\v'; break; 
}
str++;
out:
*conv_ch = value;
return str;
}
static char *
mklong(const char *str, const char *ch)
{
char *copy;
size_t len;
size_t pridmax_len = strlen(PRIdMAX);
len = ch - str + pridmax_len;
STARTSTACKSTR(copy);
copy = makestrspace(len + 1, copy);
memcpy(copy, str, len - pridmax_len);
memcpy(copy + len - pridmax_len, PRIdMAX, pridmax_len - 1);
copy[len - 1] = *ch;
copy[len] = '\0';
return (copy); 
}
static int
getchr(void)
{
int val = 0;
if (*gargv)
val = **gargv++;
return val;
}
static char *
getstr(void)
{
char *val = nullstr;
if (*gargv)
val = *gargv++;
return val;
}
static intmax_t
getintmax(void)
{
intmax_t val = 0;
char *cp, *ep;
cp = *gargv;
if (cp == NULL)
goto out;
gargv++;
val = (unsigned char) cp[1];
if (*cp == '\"' || *cp == '\'')
goto out;
errno = 0;
val = strtoimax(cp, &ep, 0);
check_conversion(cp, ep);
out:
return val;
}
static uintmax_t
getuintmax(void)
{
uintmax_t val = 0;
char *cp, *ep;
cp = *gargv;
if (cp == NULL)
goto out;
gargv++;
val = (unsigned char) cp[1];
if (*cp == '\"' || *cp == '\'')
goto out;
errno = 0;
val = strtoumax(cp, &ep, 0);
check_conversion(cp, ep);
out:
return val;
}
static double
getdouble(void)
{
double val;
char *cp, *ep;
cp = *gargv;
if (cp == NULL)
return 0;
gargv++;
if (*cp == '\"' || *cp == '\'')
return (unsigned char) cp[1];
errno = 0;
val = strtod(cp, &ep);
check_conversion(cp, ep);
return val;
}
static void
check_conversion(const char *s, const char *ep)
{
if (*ep) {
if (ep == s)
warnx("%s: expected numeric value", s);
else
warnx("%s: not completely converted", s);
rval = 1;
} else if (errno == ERANGE) {
warnx("%s: %s", s, strerror(ERANGE));
rval = 1;
}
}
int
echocmd(int argc, char **argv)
{
int nonl = 0;
struct output *outs = out1;
if (!*++argv)
goto end;
if (equal(*argv, "-n")) {
nonl = ~nonl;
if (!*++argv)
goto end;
}
do {
int c;
nonl += conv_escape_str(*argv);
outstr(stackblock(), outs);
if (nonl > 0)
break;
c = ' ';
if (!*++argv) {
end:
if (nonl) {
break;
}
c = '\n';
}
outc(c, outs);
} while (*argv);
return 0;
}
#ifndef HAVE_ISALPHA
#define isalnum _isalnum
#define iscntrl _iscntrl
#define islower _islower
#define isspace _isspace
#define isalpha _isalpha
#define isdigit _isdigit
#define isprint _isprint
#define isupper _isupper
#define isblank _isblank
#define isgraph _isgraph
#define ispunct _ispunct
#define isxdigit _isxdigit
#include <ctype.h>
#undef isalnum
#undef iscntrl
#undef islower
#undef isspace
#undef isalpha
#undef isdigit
#undef isprint
#undef isupper
#undef isblank
#undef isgraph
#undef ispunct
#undef isxdigit
#endif
#include <signal.h>
#include <string.h>
#ifndef HAVE_MEMPCPY
void *mempcpy(void *dest, const void *src, size_t n)
{
return memcpy(dest, src, n) + n;
}
#endif
#ifndef HAVE_STPCPY
char *stpcpy(char *dest, const char *src)
{
size_t len = strlen(src);
dest[len] = 0;
return mempcpy(dest, src, len);
}
#endif
#ifndef HAVE_STRCHRNUL
char *strchrnul(const char *s, int c)
{
char *p = strchr(s, c);
if (!p)
p = (char *)s + strlen(s);
return p;
}
#endif
#ifndef HAVE_STRSIGNAL
char *strsignal(int sig)
{
static char buf[19];
#if HAVE_DECL_SYS_SIGLIST
if ((unsigned)sig < NSIG && sys_siglist[sig])
return (char *)sys_siglist[sig];
#endif
fmtstr(buf, sizeof(buf), "Signal %d", sig); 
return buf;
}
#endif
#ifndef HAVE_BSEARCH
void *bsearch(const void *key, const void *base, size_t nmemb,
size_t size, int (*cmp)(const void *, const void *))
{
while (nmemb) {
size_t mididx = nmemb / 2;
const void *midobj = base + mididx * size;
int diff = cmp(key, midobj);
if (diff == 0)
return (void *)midobj;
if (diff > 0) {
base = midobj + size;
nmemb -= mididx + 1;
} else
nmemb = mididx;
}
return 0;
}
#endif
#ifndef HAVE_SYSCONF
long sysconf(int name)
{
sh_error("no sysconf for: %d", name);
}
#endif
#ifndef HAVE_ISALPHA
int isalnum(int c) {
return _isalnum(c);
}
int iscntrl(int c) {
return _iscntrl(c);
}
int islower(int c) {
return _islower(c);
}
int isspace(int c) {
return _isspace(c);
}
int isalpha(int c) {
return _isalpha(c);
}
int isdigit(int c) {
return _isdigit(c);
}
int isprint(int c) {
return _isprint(c);
}
int isupper(int c) {
return _isupper(c);
}
#if HAVE_DECL_ISBLANK
int isblank(int c) {
return _isblank(c);
}
#endif
int isgraph(int c) {
return _isgraph(c);
}
int ispunct(int c) {
return _ispunct(c);
}
int isxdigit(int c) {
return _isxdigit(c);
}
#endif
#if !HAVE_DECL_ISBLANK
int isblank(int c) {
return c == ' ' || c == '\t';
}
#endif
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdarg.h>
enum token {
EOI,
FILRD,
FILWR,
FILEX,
FILEXIST,
FILREG,
FILDIR,
FILCDEV,
FILBDEV,
FILFIFO,
FILSOCK,
FILSYM,
FILGZ,
FILTT,
FILSUID,
FILSGID,
FILSTCK,
FILNT,
FILOT,
FILEQ,
FILUID,
FILGID,
STREZ,
STRNZ,
STREQ,
STRNE,
STRLT,
STRGT,
INTEQ,
INTNE,
INTGE,
INTGT,
INTLE,
INTLT,
UNOT,
BAND,
BOR,
LPAREN,
RPAREN,
OPERAND
};
enum token_types {
UNOP,
BINOP,
BUNOP,
BBINOP,
PAREN
};
static struct t_op {
const char *op_text;
short op_num, op_type;
} const ops [] = {
{"-r", FILRD, UNOP},
{"-w", FILWR, UNOP},
{"-x", FILEX, UNOP},
{"-e", FILEXIST,UNOP},
{"-f", FILREG, UNOP},
{"-d", FILDIR, UNOP},
{"-c", FILCDEV,UNOP},
{"-b", FILBDEV,UNOP},
{"-p", FILFIFO,UNOP},
{"-u", FILSUID,UNOP},
{"-g", FILSGID,UNOP},
{"-k", FILSTCK,UNOP},
{"-s", FILGZ, UNOP},
{"-t", FILTT, UNOP},
{"-z", STREZ, UNOP},
{"-n", STRNZ, UNOP},
{"-h", FILSYM, UNOP}, 
{"-O", FILUID, UNOP},
{"-G", FILGID, UNOP},
{"-L", FILSYM, UNOP},
{"-S", FILSOCK,UNOP},
{"=", STREQ, BINOP},
{"!=", STRNE, BINOP},
{"<", STRLT, BINOP},
{">", STRGT, BINOP},
{"-eq", INTEQ, BINOP},
{"-ne", INTNE, BINOP},
{"-ge", INTGE, BINOP},
{"-gt", INTGT, BINOP},
{"-le", INTLE, BINOP},
{"-lt", INTLT, BINOP},
{"-nt", FILNT, BINOP},
{"-ot", FILOT, BINOP},
{"-ef", FILEQ, BINOP},
{"!", UNOT, BUNOP},
{"-a", BAND, BBINOP},
{"-o", BOR, BBINOP},
{"(", LPAREN, PAREN},
{")", RPAREN, PAREN},
{0, 0, 0}
};
static char **t_wp;
static struct t_op const *t_wp_op;
static void syntax(const char *, const char *);
static int oexpr(enum token);
static int aexpr(enum token);
static int nexpr(enum token);
static int test_primary(enum token);
static int test_binop(void);
static int filstat(char *, enum token);
static enum token t_lex(char **);
static int isoperand(char **);
static int newerf(const char *, const char *);
static int olderf(const char *, const char *);
static int equalf(const char *, const char *);
#ifdef HAVE_FACCESSAT
static int test_file_access(const char *, int);
#else
static int test_st_mode(const struct stat64 *, int);
static int bash_group_member(gid_t);
#endif
static inline intmax_t getn(const char *s)
{
return atomax10(s);
}
static const struct t_op *getop(const char *s)
{
const struct t_op *op;
for (op = ops; op->op_text; op++) {
if (strcmp(s, op->op_text) == 0)
return op;
}
return NULL;
}
int
testcmd(int argc, char **argv)
{
const struct t_op *op;
enum token n;
int res;
if (*argv[0] == '[') {
if (*argv[--argc] != ']')
error("missing ]");
argv[argc] = NULL;
}
argv++;
argc--;
if (argc < 1)
return 1;
switch (argc) {
case 3:
op = getop(argv[1]);
if (op && op->op_type == BINOP) {
n = OPERAND;
goto eval;
}
case 4:
if (!strcmp(argv[0], "(") && !strcmp(argv[argc - 1], ")")) {
argv[--argc] = NULL;
argv++;
argc--;
}
}
n = t_lex(argv);
eval:
t_wp = argv;
res = !oexpr(n);
argv = t_wp;
if (argv[0] != NULL && argv[1] != NULL)
syntax(argv[0], "unexpected operator");
return res;
}
static void
syntax(const char *op, const char *msg)
{
if (op && *op)
error("%s: %s", op, msg);
else
error("%s", msg);
}
static int
oexpr(enum token n)
{
int res = 0;
for (;;) {
res |= aexpr(n);
n = t_lex(t_wp + 1);
if (n != BOR)
break;
n = t_lex(t_wp += 2);
}
return res;
}
static int
aexpr(enum token n)
{
int res = 1;
for (;;) {
if (!nexpr(n))
res = 0;
n = t_lex(t_wp + 1);
if (n != BAND)
break;
n = t_lex(t_wp += 2);
}
return res;
}
static int
nexpr(enum token n)
{
if (n == UNOT)
return !nexpr(t_lex(++t_wp));
return test_primary(n);
}
static int
test_primary(enum token n)
{
enum token nn;
int res;
if (n == EOI)
return 0; 
if (n == LPAREN) {
if ((nn = t_lex(++t_wp)) == RPAREN)
return 0; 
res = oexpr(nn);
if (t_lex(++t_wp) != RPAREN)
syntax(NULL, "closing paren expected");
return res;
}
if (t_wp_op && t_wp_op->op_type == UNOP) {
if (*++t_wp == NULL)
syntax(t_wp_op->op_text, "argument expected");
switch (n) {
case STREZ:
return strlen(*t_wp) == 0;
case STRNZ:
return strlen(*t_wp) != 0;
case FILTT:
return isatty(getn(*t_wp));
#ifdef HAVE_FACCESSAT
case FILRD:
return test_file_access(*t_wp, R_OK);
case FILWR:
return test_file_access(*t_wp, W_OK);
case FILEX:
return test_file_access(*t_wp, X_OK);
#endif
default:
return filstat(*t_wp, n);
}
}
if (t_lex(t_wp + 1), t_wp_op && t_wp_op->op_type == BINOP) {
return test_binop();
}
return strlen(*t_wp) > 0;
}
static int
test_binop(void)
{
const char *opnd1, *opnd2;
struct t_op const *op;
opnd1 = *t_wp;
(void) t_lex(++t_wp);
op = t_wp_op;
if ((opnd2 = *++t_wp) == (char *)0)
syntax(op->op_text, "argument expected");
switch (op->op_num) {
default:
#ifdef DEBUG
abort();
#endif
case STREQ:
return strcmp(opnd1, opnd2) == 0;
case STRNE:
return strcmp(opnd1, opnd2) != 0;
case STRLT:
return strcmp(opnd1, opnd2) < 0;
case STRGT:
return strcmp(opnd1, opnd2) > 0;
case INTEQ:
return getn(opnd1) == getn(opnd2);
case INTNE:
return getn(opnd1) != getn(opnd2);
case INTGE:
return getn(opnd1) >= getn(opnd2);
case INTGT:
return getn(opnd1) > getn(opnd2);
case INTLE:
return getn(opnd1) <= getn(opnd2);
case INTLT:
return getn(opnd1) < getn(opnd2);
case FILNT:
return newerf (opnd1, opnd2);
case FILOT:
return olderf (opnd1, opnd2);
case FILEQ:
return equalf (opnd1, opnd2);
}
}
static int
filstat(char *nm, enum token mode)
{
struct stat64 s;
if (mode == FILSYM ? lstat64(nm, &s) : stat64(nm, &s))
return 0;
switch (mode) {
#ifndef HAVE_FACCESSAT
case FILRD:
return test_st_mode(&s, R_OK);
case FILWR:
return test_st_mode(&s, W_OK);
case FILEX:
return test_st_mode(&s, X_OK);
#endif
case FILEXIST:
return 1;
case FILREG:
return S_ISREG(s.st_mode);
case FILDIR:
return S_ISDIR(s.st_mode);
case FILCDEV:
return S_ISCHR(s.st_mode);
case FILBDEV:
return S_ISBLK(s.st_mode);
case FILFIFO:
return S_ISFIFO(s.st_mode);
case FILSOCK:
return S_ISSOCK(s.st_mode);
case FILSYM:
return S_ISLNK(s.st_mode);
case FILSUID:
return (s.st_mode & S_ISUID) != 0;
case FILSGID:
return (s.st_mode & S_ISGID) != 0;
case FILSTCK:
return (s.st_mode & S_ISVTX) != 0;
case FILGZ:
return !!s.st_size;
case FILUID:
return s.st_uid == geteuid();
case FILGID:
return s.st_gid == getegid();
default:
return 1;
}
}
static enum token t_lex(char **tp)
{
struct t_op const *op;
char *s = *tp;
if (s == 0) {
t_wp_op = (struct t_op *)0;
return EOI;
}
op = getop(s);
if (op && !(op->op_type == UNOP && isoperand(tp)) &&
!(op->op_num == LPAREN && !tp[1])) {
t_wp_op = op;
return op->op_num;
}
t_wp_op = (struct t_op *)0;
return OPERAND;
}
static int isoperand(char **tp)
{
struct t_op const *op;
char *s;
if (!(s = tp[1]))
return 1;
if (!tp[2])
return 0;
op = getop(s);
return op && op->op_type == BINOP;
}
static int
newerf (const char *f1, const char *f2)
{
struct stat b1, b2;
return (stat (f1, &b1) == 0 &&
stat (f2, &b2) == 0 &&
b1.st_mtime > b2.st_mtime);
}
static int
olderf (const char *f1, const char *f2)
{
struct stat b1, b2;
return (stat (f1, &b1) == 0 &&
stat (f2, &b2) == 0 &&
b1.st_mtime < b2.st_mtime);
}
static int
equalf (const char *f1, const char *f2)
{
struct stat b1, b2;
return (stat (f1, &b1) == 0 &&
stat (f2, &b2) == 0 &&
b1.st_dev == b2.st_dev &&
b1.st_ino == b2.st_ino);
}
#ifdef HAVE_FACCESSAT
static int test_file_access(const char *path, int mode)
{
return !faccessat(AT_FDCWD, path, mode, AT_EACCESS);
}
#else 
static int
test_st_mode(const struct stat64 *st, int mode)
{
int euid = geteuid();
if (euid == 0) {
if (mode != X_OK)
return 1;
mode = S_IXUSR | S_IXGRP | S_IXOTH;
} else if (st->st_uid == euid)
mode <<= 6;
else if (bash_group_member(st->st_gid))
mode <<= 3;
return st->st_mode & mode;
}
static int
bash_group_member(gid_t gid)
{
register int i;
gid_t *group_array;
int ngroups;
if (gid == getgid() || gid == getegid())
return (1);
ngroups = getgroups(0, NULL);
group_array = stalloc(ngroups * sizeof(gid_t));
if ((getgroups(ngroups, group_array)) != ngroups)
return (0);
for (i = 0; i < ngroups; i++)
if (gid == group_array[i])
return (1);
return (0);
}
#endif 
#include <sys/times.h>
#include <unistd.h>
#ifdef USE_GLIBC_STDIO
#include <stdio.h>
#else
#endif
int timescmd(int argc, char** argv) {
struct tms buf;
long int clk_tck = sysconf(_SC_CLK_TCK);
times(&buf);
blt_printf("%dm%fs %dm%fs\n%dm%fs %dm%fs\n",
(int) (buf.tms_utime / clk_tck / 60),
((double) buf.tms_utime) / clk_tck,
(int) (buf.tms_stime / clk_tck / 60),
((double) buf.tms_stime) / clk_tck,
(int) (buf.tms_cutime / clk_tck / 60),
((double) buf.tms_cutime) / clk_tck,
(int) (buf.tms_cstime / clk_tck / 60),
((double) buf.tms_cstime) / clk_tck);
return 0;
}
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#ifdef HAVE_PATHS_H
#include <paths.h>
#endif
#ifndef SMALL
#endif
#define VTABSIZE 521
struct localvar_list {
struct localvar_list *next;
struct localvar *lv;
};
MKINIT struct localvar_list *localvar_stack;
const char defpathvar[] =
"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin";
#ifdef IFS_BROKEN
const char defifsvar[] = "IFS= \t\n";
#else
const char defifs[] = " \t\n";
#endif
int lineno;
char linenovar[sizeof("LINENO=")+sizeof(int)*CHAR_BIT/3+1] = "LINENO=";
struct var varinit[] = {
#if ATTY
{ 0, VSTRFIXED|VTEXTFIXED|VUNSET, "ATTY\0", 0 },
#endif
#ifdef IFS_BROKEN
{ 0, VSTRFIXED|VTEXTFIXED, defifsvar, 0 },
#else
{ 0, VSTRFIXED|VTEXTFIXED|VUNSET, "IFS\0", 0 },
#endif
{ 0, VSTRFIXED|VTEXTFIXED|VUNSET, "MAIL\0", changemail },
{ 0, VSTRFIXED|VTEXTFIXED|VUNSET, "MAILPATH\0", changemail },
{ 0, VSTRFIXED|VTEXTFIXED, defpathvar, changepath },
{ 0, VSTRFIXED|VTEXTFIXED, "PS1=$ ", 0 },
{ 0, VSTRFIXED|VTEXTFIXED, "PS2=> ", 0 },
{ 0, VSTRFIXED|VTEXTFIXED, "PS4=+ ", 0 },
{ 0, VSTRFIXED|VTEXTFIXED, "OPTIND=1", getoptsreset },
{ 0, VSTRFIXED|VTEXTFIXED, linenovar, 0 },
#ifndef SMALL
{ 0, VSTRFIXED|VTEXTFIXED|VUNSET, "TERM\0", 0 },
{ 0, VSTRFIXED|VTEXTFIXED|VUNSET, "HISTSIZE\0", sethistsize },
#endif
};
STATIC struct var *vartab[VTABSIZE];
STATIC struct var **hashvar(const char *);
STATIC int vpcmp(const void *, const void *);
STATIC struct var **findvar(struct var **, const char *);
#ifdef mkinit
INCLUDE <unistd.h>
INCLUDE <sys/types.h>
INCLUDE <sys/stat.h>
INCLUDE "cd.h"
INCLUDE "output.h"
INCLUDE "var.h"
MKINIT char **environ;
INIT {
char **envp;
static char ppid[32] = "PPID=";
const char *p;
struct stat st1, st2;
initvar();
for (envp = environ ; *envp ; envp++) {
if (strchr(*envp, '=')) {
setvareq(*envp, VEXPORT|VTEXTFIXED);
}
}
fmtstr(ppid + 5, sizeof(ppid) - 5, "%ld", (long) getppid());
setvareq(ppid, VTEXTFIXED);
p = lookupvar("PWD");
if (p)
if (*p != '/' || stat(p, &st1) || stat(".", &st2) ||
st1.st_dev != st2.st_dev || st1.st_ino != st2.st_ino)
p = 0;
setpwd(p, 0);
}
RESET {
unwindlocalvars(0);
}
#endif
void
initvar(void)
{
struct var *vp;
struct var *end;
struct var **vpp;
vp = varinit;
end = vp + sizeof(varinit) / sizeof(varinit[0]);
do {
vpp = hashvar(vp->text);
vp->next = *vpp;
*vpp = vp;
} while (++vp < end);
if (!geteuid())
vps1.text = "PS1=# ";
}
struct var *setvar(const char *name, const char *val, int flags)
{
char *p, *q;
size_t namelen;
char *nameeq;
size_t vallen;
struct var *vp;
q = endofname(name);
p = strchrnul(q, '=');
namelen = p - name;
if (!namelen || p != q)
sh_error("%.*s: bad variable name", namelen, name);
vallen = 0;
if (val == NULL) {
flags |= VUNSET;
} else {
vallen = strlen(val);
}
INTOFF;
p = mempcpy(nameeq = ckmalloc(namelen + vallen + 2), name, namelen);
if (val) {
*p++ = '=';
p = mempcpy(p, val, vallen);
}
*p = '\0';
vp = setvareq(nameeq, flags | VNOSAVE);
INTON;
return vp;
}
intmax_t setvarint(const char *name, intmax_t val, int flags)
{
int len = max_int_length(sizeof(val));
char buf[len];
fmtstr(buf, len, "%" PRIdMAX, val);
setvar(name, buf, flags);
return val;
}
struct var *setvareq(char *s, int flags)
{
struct var *vp, **vpp;
vpp = hashvar(s);
flags |= (VEXPORT & (((unsigned) (1 - aflag)) - 1));
vpp = findvar(vpp, s);
vp = *vpp;
if (vp) {
if (vp->flags & VREADONLY) {
const char *n;
if (flags & VNOSAVE)
free(s);
n = vp->text;
sh_error("%.*s: is read only", strchrnul(n, '=') - n,
n);
}
if (flags & VNOSET)
goto out;
if (vp->func && (flags & VNOFUNC) == 0)
(*vp->func)(strchrnul(s, '=') + 1);
if ((vp->flags & (VTEXTFIXED|VSTACK)) == 0)
ckfree(vp->text);
if (((flags & (VEXPORT|VREADONLY|VSTRFIXED|VUNSET)) |
(vp->flags & VSTRFIXED)) == VUNSET) {
*vpp = vp->next;
ckfree(vp);
out_free:
if ((flags & (VTEXTFIXED|VSTACK|VNOSAVE)) == VNOSAVE)
ckfree(s);
goto out;
}
flags |= vp->flags & ~(VTEXTFIXED|VSTACK|VNOSAVE|VUNSET);
} else {
if (flags & VNOSET)
goto out;
if ((flags & (VEXPORT|VREADONLY|VSTRFIXED|VUNSET)) == VUNSET)
goto out_free;
vp = ckmalloc(sizeof (*vp));
vp->next = *vpp;
vp->func = NULL;
*vpp = vp;
}
if (!(flags & (VTEXTFIXED|VSTACK|VNOSAVE)))
s = savestr(s);
vp->text = s;
vp->flags = flags;
out:
return vp;
}
void
listsetvar(struct strlist *list, int flags)
{
struct strlist *lp;
lp = list;
if (!lp)
return;
INTOFF;
do {
setvareq(lp->text, flags);
} while ((lp = lp->next));
INTON;
}
char *
lookupvar(const char *name)
{
struct var *v;
if ((v = *findvar(hashvar(name), name)) && !(v->flags & VUNSET)) {
if (v == &vlineno && v->text == linenovar) {
fmtstr(linenovar+7, sizeof(linenovar)-7, "%d", lineno);
}
return strchrnul(v->text, '=') + 1;
}
return NULL;
}
intmax_t lookupvarint(const char *name)
{
return atomax(lookupvar(name) ?: nullstr, 0);
}
char **
listvars(int on, int off, char ***end)
{
struct var **vpp;
struct var *vp;
char **ep;
int mask;
STARTSTACKSTR(ep);
vpp = vartab;
mask = on | off;
do {
for (vp = *vpp ; vp ; vp = vp->next)
if ((vp->flags & mask) == on) {
if (ep == stackstrend())
ep = growstackstr();
*ep++ = (char *) vp->text;
}
} while (++vpp < vartab + VTABSIZE);
if (ep == stackstrend())
ep = growstackstr();
if (end)
*end = ep;
*ep++ = NULL;
return grabstackstr(ep);
}
int
showvars(const char *prefix, int on, int off)
{
const char *sep;
char **ep, **epend;
ep = listvars(on, off, &epend);
qsort(ep, epend - ep, sizeof(char *), vpcmp);
sep = *prefix ? spcstr : prefix;
for (; ep < epend; ep++) {
const char *p;
const char *q;
p = strchrnul(*ep, '=');
q = nullstr;
if (*p)
q = single_quote(++p);
out1fmt("%s%s%.*s%s\n", prefix, sep, (int)(p - *ep), *ep, q);
}
return 0;
}
int
exportcmd(int argc, char **argv)
{
struct var *vp;
char *name;
const char *p;
char **aptr;
int flag = argv[0][0] == 'r'? VREADONLY : VEXPORT;
int notp;
notp = nextopt("p") - 'p';
if (notp && ((name = *(aptr = argptr)))) {
do {
if ((p = strchr(name, '=')) != NULL) {
p++;
} else {
if ((vp = *findvar(hashvar(name), name))) {
vp->flags |= flag;
continue;
}
}
setvar(name, p, flag);
} while ((name = *++aptr) != NULL);
} else {
showvars(argv[0], flag, 0);
}
return 0;
}
int
localcmd(int argc, char **argv)
{
char *name;
if (!localvar_stack)
sh_error("not in a function");
argv = argptr;
while ((name = *argv++) != NULL) {
mklocal(name);
}
return 0;
}
void mklocal(char *name)
{
struct localvar *lvp;
struct var **vpp;
struct var *vp;
INTOFF;
lvp = ckmalloc(sizeof (struct localvar));
if (name[0] == '-' && name[1] == '\0') {
char *p;
p = ckmalloc(sizeof(optlist));
lvp->text = memcpy(p, optlist, sizeof(optlist));
vp = NULL;
} else {
char *eq;
vpp = hashvar(name);
vp = *findvar(vpp, name);
eq = strchr(name, '=');
if (vp == NULL) {
if (eq)
vp = setvareq(name, VSTRFIXED);
else
vp = setvar(name, NULL, VSTRFIXED);
lvp->flags = VUNSET;
} else {
lvp->text = vp->text;
lvp->flags = vp->flags;
vp->flags |= VSTRFIXED|VTEXTFIXED;
if (eq)
setvareq(name, 0);
}
}
lvp->vp = vp;
lvp->next = localvar_stack->lv;
localvar_stack->lv = lvp;
INTON;
}
void
poplocalvars(int keep)
{
struct localvar_list *ll;
struct localvar *lvp, *next;
struct var *vp;
INTOFF;
ll = localvar_stack;
localvar_stack = ll->next;
next = ll->lv;
ckfree(ll);
while ((lvp = next) != NULL) {
next = lvp->next;
vp = lvp->vp;
TRACE(("poplocalvar %s", vp ? vp->text : "-"));
if (keep) {
int bits = VSTRFIXED;
if (lvp->flags != VUNSET) {
if (vp->text == lvp->text)
bits |= VTEXTFIXED;
else if (!(lvp->flags & (VTEXTFIXED|VSTACK)))
ckfree(lvp->text);
}
vp->flags &= ~bits;
vp->flags |= (lvp->flags & bits);
if ((vp->flags &
(VEXPORT|VREADONLY|VSTRFIXED|VUNSET)) == VUNSET)
unsetvar(vp->text);
} else if (vp == NULL) { 
memcpy(optlist, lvp->text, sizeof(optlist));
ckfree(lvp->text);
optschanged();
} else if (lvp->flags == VUNSET) {
vp->flags &= ~(VSTRFIXED|VREADONLY);
unsetvar(vp->text);
} else {
if (vp->func)
(*vp->func)(strchrnul(lvp->text, '=') + 1);
if ((vp->flags & (VTEXTFIXED|VSTACK)) == 0)
ckfree(vp->text);
vp->flags = lvp->flags;
vp->text = lvp->text;
}
ckfree(lvp);
}
INTON;
}
struct localvar_list *pushlocalvars(void)
{
struct localvar_list *ll;
INTOFF;
ll = ckmalloc(sizeof(*ll));
ll->lv = NULL;
ll->next = localvar_stack;
localvar_stack = ll;
INTON;
return ll->next;
}
void unwindlocalvars(struct localvar_list *stop)
{
while (localvar_stack != stop)
poplocalvars(0);
}
int
unsetcmd(int argc, char **argv)
{
char **ap;
int i;
int flag = 0;
while ((i = nextopt("vf")) != '\0') {
flag = i;
}
for (ap = argptr; *ap ; ap++) {
if (flag != 'f') {
unsetvar(*ap);
continue;
}
if (flag != 'v')
unsetfunc(*ap);
}
return 0;
}
void unsetvar(const char *s)
{
setvar(s, 0, 0);
}
STATIC struct var **
hashvar(const char *p)
{
unsigned int hashval;
hashval = ((unsigned char) *p) << 4;
while (*p && *p != '=')
hashval += (unsigned char) *p++;
return &vartab[hashval % VTABSIZE];
}
int
varcmp(const char *p, const char *q)
{
int c, d;
while ((c = *p) == (d = *q)) {
if (!c || c == '=')
goto out;
p++;
q++;
}
if (c == '=')
c = 0;
if (d == '=')
d = 0;
out:
return c - d;
}
STATIC int
vpcmp(const void *a, const void *b)
{
return varcmp(*(const char **)a, *(const char **)b);
}
STATIC struct var **
findvar(struct var **vpp, const char *name)
{
for (; *vpp; vpp = &(*vpp)->next) {
if (varequal((*vpp)->text, name)) {
break;
}
}
return vpp;
}
#include <signal.h>
const char *const signal_names[] = {
[0] = "EXIT",
#ifdef SIGHUP
[SIGHUP] = "HUP",
#endif
#ifdef SIGINT
[SIGINT] = "INT",
#endif
#ifdef SIGQUIT
[SIGQUIT] = "QUIT",
#endif
#ifdef SIGILL
[SIGILL] = "ILL",
#endif
#ifdef SIGTRAP
[SIGTRAP] = "TRAP",
#endif
#ifdef SIGABRT
[SIGABRT] = "ABRT",
#endif
#ifdef SIGBUS
[SIGBUS] = "BUS",
#endif
#ifdef SIGFPE
[SIGFPE] = "FPE",
#endif
#ifdef SIGKILL
[SIGKILL] = "KILL",
#endif
#ifdef SIGUSR1
[SIGUSR1] = "USR1",
#endif
#ifdef SIGSEGV
[SIGSEGV] = "SEGV",
#endif
#ifdef SIGUSR2
[SIGUSR2] = "USR2",
#endif
#ifdef SIGPIPE
[SIGPIPE] = "PIPE",
#endif
#ifdef SIGALRM
[SIGALRM] = "ALRM",
#endif
#ifdef SIGTERM
[SIGTERM] = "TERM",
#endif
#ifdef SIGCHLD
[SIGCHLD] = "CHLD",
#endif
#ifdef SIGCONT
[SIGCONT] = "CONT",
#endif
#ifdef SIGSTOP
[SIGSTOP] = "STOP",
#endif
#ifdef SIGTSTP
[SIGTSTP] = "TSTP",
#endif
#ifdef SIGTTIN
[SIGTTIN] = "TTIN",
#endif
#ifdef SIGTTOU
[SIGTTOU] = "TTOU",
#endif
#ifdef SIGURG
[SIGURG] = "URG",
#endif
#ifdef SIGXCPU
[SIGXCPU] = "XCPU",
#endif
#ifdef SIGXFSZ
[SIGXFSZ] = "XFSZ",
#endif
#ifdef SIGVTALRM
[SIGVTALRM] = "VTALRM",
#endif
#ifdef SIGPROF
[SIGPROF] = "PROF",
#endif
#ifdef SIGWINCH
[SIGWINCH] = "WINCH",
#endif
#ifdef SIGIO
[SIGIO] = "IO",
#endif
#ifdef SIGPWR
[SIGPWR] = "PWR",
#endif
#ifdef SIGSYS
[SIGSYS] = "SYS",
#endif
[NSIG] = (char *)0x0
};
#include <stdlib.h>
#include <unistd.h>
#ifdef HAVE_ALLOCA_H
#include <alloca.h>
#endif
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
static size_t strchrcount(const char* str, char c)
{
size_t count = 0;
char* ptr = NULL;
for (ptr = strchr(str,c);
ptr;
count++, ptr = strchr(ptr+1,c));
return count;
}
static char* copyquoted(char* dst, const char* src)
{
for (; *src; *(dst++) = *(src++))
{
if (*src == '\'')
{
*dst++ = '\'';
*dst++ = '\\';
*dst++ = '\'';
}
}
return dst;
}
static int setquoted(const char* var, int argc, char** argv)
{
size_t needed = argc; 
int i = 0;
char* str = NULL;
char* pos = NULL;
for (i = 0; i < argc; i++)
{
needed += 2 
+ strlen(argv[i]) 
+ 3 * strchrcount(argv[i], '\''); 
}
#ifdef HAVE_ALLOCA_H
pos = str = alloca(needed);
#else
pos = str = ckmalloc(needed);
#endif
for (i = 0; i < argc; i++)
{
*pos++ = '\'';
pos = copyquoted(pos, argv[i]);
*pos++ = '\'';
if (i < argc - 1)
{
*pos++ = ' ';
}
}
*pos = '\0';
setvar(var, str, 0);
#ifndef HAVE_ALLOCA_H
ckfree(str);
#endif
return 0;
}
int mk_quotecmd(int argc, char** argv)
{
return setquoted("result", argc - 1, argv + 1);
}
int mk_quote_spacecmd(int argc, char** argv)
{
size_t needed = argc - 1; 
int i = 0;
int j = 0;
char* str = NULL;
char* pos = NULL;
for (i = 1; i < argc; i++)
{
needed += strlen(argv[1]) + strchrcount(argv[1], ' ');
}
#ifdef HAVE_ALLOCA_H
pos = str = alloca(needed);
#else
pos = str = ckmalloc(needed);
#endif
for (i = 1; i < argc; i++)
{
for(j = 0; argv[i][j]; j++)
{
if (argv[i][j] == ' ')
*pos++ = '\\';
*pos++ = argv[i][j];
}
if (i < argc - 1)
{
*pos++ = ' ';
}
}
*pos = '\0';
setvar("result", str, 0);
#ifndef HAVE_ALLOCA_H
ckfree(str);
#endif
return 0;
}
int mk_push_varscmd(int argc, char** argv)
{
int i = 0;
for (i = 1; i < argc; i++)
{
mklocal(argv[i]);
if (!strchr(argv[i], '='))
{
setvar(argv[i], "", 0);
}
}
return 0;
}
static void shiftn(int n)
{
char** ap1 = NULL;
char** ap2 = NULL;
if (n > shellparam.nparam)
sh_error("can't shift that many");
INTOFF;
shellparam.nparam -= n;
for (ap1 = shellparam.p ; --n >= 0 ; ap1++) {
if (shellparam.malloc)
ckfree(*ap1);
}
ap2 = shellparam.p;
while ((*ap2++ = *ap1++) != NULL);
shellparam.optind = 1;
shellparam.optoff = -1;
INTON;
}
int mk_parse_paramscmd(int argc, char** argv)
{
int i = 0;
int j = 0;
for (i = 0; i < shellparam.nparam; i++)
{
if (!strcmp(shellparam.p[i], "--"))
{
i++;
break;
}
else if (*shellparam.p[i] == '@' && 
!strcmp(shellparam.p[i] + strlen(shellparam.p[i]) - 2, "={"))
{
for (j = i+1; j < shellparam.nparam; j++)
{
if (!strcmp(shellparam.p[j], "}"))
{
shellparam.p[i][strlen(shellparam.p[i]) - 2] = '\0';
setquoted(shellparam.p[i] + 1, j - i - 1, shellparam.p + i + 1);
shellparam.p[i][strlen(shellparam.p[i]) - 2] = '=';
i = j;
break;
}
}
if (j == shellparam.nparam)
{
sh_error("missing closing }");
}
}
else if (strchr(shellparam.p[i], '='))
{
setvareq(shellparam.p[i], 0);
}
else
{
break;
}
}
shiftn(i);
}
int bgcmd(int, char **);
int fgcmd(int, char **);
int breakcmd(int, char **);
int cdcmd(int, char **);
int commandcmd(int, char **);
int dotcmd(int, char **);
int echocmd(int, char **);
int evalcmd(int, char **);
int execcmd(int, char **);
int exitcmd(int, char **);
int exportcmd(int, char **);
int falsecmd(int, char **);
int getoptscmd(int, char **);
int hashcmd(int, char **);
int jobscmd(int, char **);
int localcmd(int, char **);
int printfcmd(int, char **);
int pwdcmd(int, char **);
int readcmd(int, char **);
int returncmd(int, char **);
int setcmd(int, char **);
int shiftcmd(int, char **);
int timescmd(int, char **);
int trapcmd(int, char **);
int truecmd(int, char **);
int typecmd(int, char **);
int umaskcmd(int, char **);
int unaliascmd(int, char **);
int unsetcmd(int, char **);
int waitcmd(int, char **);
int aliascmd(int, char **);
int ulimitcmd(int, char **);
int testcmd(int, char **);
int killcmd(int, char **);
int mk_quotecmd(int, char **);
int mk_quote_spacecmd(int, char **);
int mk_push_varscmd(int, char **);
int mk_parse_paramscmd(int, char **);
const struct builtincmd builtincmd[] = {
{ ".", dotcmd, 3 },
{ ":", truecmd, 3 },
{ "[", testcmd, 0 },
{ "_mk_push_vars", mk_push_varscmd, 7 },
{ "alias", aliascmd, 6 },
{ "bg", bgcmd, 2 },
{ "break", breakcmd, 3 },
{ "cd", cdcmd, 2 },
{ "chdir", cdcmd, 0 },
{ "command", commandcmd, 2 },
{ "continue", breakcmd, 3 },
{ "echo", echocmd, 0 },
{ "eval", NULL, 3 },
{ "exec", execcmd, 3 },
{ "exit", exitcmd, 3 },
{ "export", exportcmd, 7 },
{ "false", falsecmd, 2 },
{ "fg", fgcmd, 2 },
{ "getopts", getoptscmd, 2 },
{ "hash", hashcmd, 0 },
{ "jobs", jobscmd, 2 },
{ "kill", killcmd, 2 },
{ "local", localcmd, 7 },
{ "mk_parse_params", mk_parse_paramscmd, 0 },
{ "mk_quote", mk_quotecmd, 0 },
{ "mk_quote_list", mk_quotecmd, 0 },
{ "mk_quote_space", mk_quote_spacecmd, 0 },
{ "mk_quote_space_list", mk_quote_spacecmd, 0 },
{ "printf", printfcmd, 0 },
{ "pwd", pwdcmd, 0 },
{ "read", readcmd, 2 },
{ "readonly", exportcmd, 7 },
{ "return", returncmd, 3 },
{ "set", setcmd, 3 },
{ "shift", shiftcmd, 3 },
{ "test", testcmd, 0 },
{ "times", timescmd, 3 },
{ "trap", trapcmd, 3 },
{ "true", truecmd, 2 },
{ "type", typecmd, 0 },
{ "ulimit", ulimitcmd, 0 },
{ "umask", umaskcmd, 2 },
{ "unalias", unaliascmd, 2 },
{ "unset", unsetcmd, 3 },
{ "wait", waitcmd, 2 },
};
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#undef ATABSIZE
#define ATABSIZE 39
#undef ARITH_MAX_PREC
#define ARITH_MAX_PREC 8
#undef CD_PHYSICAL
#define CD_PHYSICAL 1
#undef CD_PRINT
#define CD_PRINT 2
#undef CMDTABLESIZE
#define CMDTABLESIZE 31 
#undef ARB
#define ARB 1 
#undef RMESCAPE_ALLOC
#define RMESCAPE_ALLOC 0x1 
#undef RMESCAPE_GLOB
#define RMESCAPE_GLOB 0x2 
#undef RMESCAPE_GROW
#define RMESCAPE_GROW 0x8 
#undef RMESCAPE_HEAP
#define RMESCAPE_HEAP 0x10 
#undef QUOTES_ESC
#define QUOTES_ESC (EXP_FULL | EXP_CASE | EXP_QPAT)
#undef QUOTES_KEEPNUL
#define QUOTES_KEEPNUL EXP_TILDE
#undef MAXHISTLOOPS
#define MAXHISTLOOPS 4 
#undef DEFEDITOR
#define DEFEDITOR "ed" 
#undef editing
#define editing (Eflag || Vflag)
#undef EOF_NLEFT
#define EOF_NLEFT -99 
#undef IBUFSIZ
#define IBUFSIZ (BUFSIZ + 1)
#undef CUR_DELETE
#define CUR_DELETE 2
#undef CUR_RUNNING
#define CUR_RUNNING 1
#undef CUR_STOPPED
#define CUR_STOPPED 0
#undef DOWAIT_NORMAL
#define DOWAIT_NORMAL 0
#undef DOWAIT_BLOCK
#define DOWAIT_BLOCK 1
#undef DOWAIT_WAITCMD
#define DOWAIT_WAITCMD 2
#undef MAXMBOXES
#define MAXMBOXES 10
#undef PROFILE
#define PROFILE 0
#undef MINSIZE
#define MINSIZE SHELL_ALIGN(504)
#undef DEFINE_OPTIONS
#define DEFINE_OPTIONS
#undef FAKEEOFMARK
#define FAKEEOFMARK (char *)1
#undef REALLY_CLOSED
#define REALLY_CLOSED -3 
#undef EMPTY
#define EMPTY -2 
#undef CLOSED
#define CLOSED -1 
#undef S_DFL
#define S_DFL 1 
#undef S_CATCH
#define S_CATCH 2 
#undef S_IGN
#define S_IGN 3 
#undef S_HARD_IGN
#define S_HARD_IGN 4 
#undef S_RESET
#define S_RESET 5 
#undef OUTBUFSIZ
#define OUTBUFSIZ BUFSIZ
#undef MEM_OUT
#define MEM_OUT -3 
#undef SKIP1
#define SKIP1 "#-+ 0"
#undef SKIP2
#define SKIP2 "*0123456789"
#undef isalnum
#define isalnum _isalnum
#undef iscntrl
#define iscntrl _iscntrl
#undef islower
#define islower _islower
#undef isspace
#define isspace _isspace
#undef isalpha
#define isalpha _isalpha
#undef isdigit
#define isdigit _isdigit
#undef isprint
#define isprint _isprint
#undef isupper
#define isupper _isupper
#undef isblank
#define isblank _isblank
#undef isgraph
#define isgraph _isgraph
#undef ispunct
#define ispunct _ispunct
#undef isxdigit
#define isxdigit _isxdigit
#undef VTABSIZE
#define VTABSIZE 521
extern int loopnest; 
#ifndef SMOOSH
struct strpush {
struct strpush *prev; 
char *prevstring;
int prevnleft;
struct alias *ap; 
char *string; 
};
#endif
#ifndef SMOOSH
struct parsefile {
struct parsefile *prev; 
int linno; 
int fd; 
int nleft; 
int lleft; 
char *nextc; 
char *buf; 
struct strpush *strpush; 
struct strpush basestrpush; 
};
#endif
extern int parselleft; 
extern struct parsefile basepf; 
extern char basebuf[IBUFSIZ]; 
#ifndef SMOOSH
struct redirtab {
struct redirtab *next;
int renamed[10];
};
#endif
extern struct redirtab *redirlist;
extern struct localvar_list *localvar_stack;
extern char **environ;
void
init() {
{
basepf.nextc = basepf.buf = basebuf;
}
{
sigmode[SIGCHLD - 1] = S_DFL;
setsignal(SIGCHLD);
}
{
#ifdef USE_GLIBC_STDIO
initstreams();
#endif
}
{
char **envp;
static char ppid[32] = "PPID=";
const char *p;
struct stat st1, st2;
initvar();
for (envp = environ ; *envp ; envp++) {
if (strchr(*envp, '=')) {
setvareq(*envp, VEXPORT|VTEXTFIXED);
}
}
fmtstr(ppid + 5, sizeof(ppid) - 5, "%ld", (long) getppid());
setvareq(ppid, VTEXTFIXED);
p = lookupvar("PWD");
if (p)
if (*p != '/' || stat(p, &st1) || stat(".", &st2) ||
st1.st_dev != st2.st_dev || st1.st_ino != st2.st_ino)
p = 0;
setpwd(p, 0);
}
}
void
reset() {
{
evalskip = 0;
loopnest = 0;
}
{
ifsfree();
}
{
parselleft = parsenleft = 0; 
popallfiles();
}
{
tokpushback = 0;
checkkwd = 0;
}
{
unwindredir(0);
}
{
#ifdef notyet
out1 = &output;
out2 = &errout;
#ifdef USE_GLIBC_STDIO
if (memout.stream != NULL)
__closememout();
#endif
if (memout.buf != NULL) {
ckfree(memout.buf);
memout.buf = NULL;
}
#endif
}
{
unwindlocalvars(0);
}
}
#include <stdlib.h>
int funcblocksize; 
int funcstringsize; 
pointer funcblock; 
char *funcstring; 
static const short nodesize[26] = {
SHELL_ALIGN(sizeof (struct ncmd)),
SHELL_ALIGN(sizeof (struct npipe)),
SHELL_ALIGN(sizeof (struct nredir)),
SHELL_ALIGN(sizeof (struct nredir)),
SHELL_ALIGN(sizeof (struct nredir)),
SHELL_ALIGN(sizeof (struct nbinary)),
SHELL_ALIGN(sizeof (struct nbinary)),
SHELL_ALIGN(sizeof (struct nbinary)),
SHELL_ALIGN(sizeof (struct nif)),
SHELL_ALIGN(sizeof (struct nbinary)),
SHELL_ALIGN(sizeof (struct nbinary)),
SHELL_ALIGN(sizeof (struct nfor)),
SHELL_ALIGN(sizeof (struct ncase)),
SHELL_ALIGN(sizeof (struct nclist)),
SHELL_ALIGN(sizeof (struct ndefun)),
SHELL_ALIGN(sizeof (struct narg)),
SHELL_ALIGN(sizeof (struct nfile)),
SHELL_ALIGN(sizeof (struct nfile)),
SHELL_ALIGN(sizeof (struct nfile)),
SHELL_ALIGN(sizeof (struct nfile)),
SHELL_ALIGN(sizeof (struct nfile)),
SHELL_ALIGN(sizeof (struct ndup)),
SHELL_ALIGN(sizeof (struct ndup)),
SHELL_ALIGN(sizeof (struct nhere)),
SHELL_ALIGN(sizeof (struct nhere)),
SHELL_ALIGN(sizeof (struct nnot)),
};
STATIC void calcsize(union node *);
STATIC void sizenodelist(struct nodelist *);
STATIC union node *copynode(union node *);
STATIC struct nodelist *copynodelist(struct nodelist *);
STATIC char *nodesavestr(char *);
struct funcnode *
copyfunc(union node *n)
{
struct funcnode *f;
size_t blocksize;
funcblocksize = offsetof(struct funcnode, n);
funcstringsize = 0;
calcsize(n);
blocksize = funcblocksize;
f = ckmalloc(blocksize + funcstringsize);
funcblock = (char *) f + offsetof(struct funcnode, n);
funcstring = (char *) f + blocksize;
copynode(n);
f->count = 0;
return f;
}
STATIC void
calcsize(n)
union node *n;
{
if (n == NULL)
return;
funcblocksize += nodesize[n->type];
switch (n->type) {
case NCMD:
calcsize(n->ncmd.redirect);
calcsize(n->ncmd.args);
calcsize(n->ncmd.assign);
break;
case NPIPE:
sizenodelist(n->npipe.cmdlist);
break;
case NREDIR:
case NBACKGND:
case NSUBSHELL:
calcsize(n->nredir.redirect);
calcsize(n->nredir.n);
break;
case NAND:
case NOR:
case NSEMI:
case NWHILE:
case NUNTIL:
calcsize(n->nbinary.ch2);
calcsize(n->nbinary.ch1);
break;
case NIF:
calcsize(n->nif.elsepart);
calcsize(n->nif.ifpart);
calcsize(n->nif.test);
break;
case NFOR:
funcstringsize += strlen(n->nfor.var) + 1;
calcsize(n->nfor.body);
calcsize(n->nfor.args);
break;
case NCASE:
calcsize(n->ncase.cases);
calcsize(n->ncase.expr);
break;
case NCLIST:
calcsize(n->nclist.body);
calcsize(n->nclist.pattern);
calcsize(n->nclist.next);
break;
case NDEFUN:
calcsize(n->ndefun.body);
funcstringsize += strlen(n->ndefun.text) + 1;
break;
case NARG:
sizenodelist(n->narg.backquote);
funcstringsize += strlen(n->narg.text) + 1;
calcsize(n->narg.next);
break;
case NTO:
case NCLOBBER:
case NFROM:
case NFROMTO:
case NAPPEND:
calcsize(n->nfile.fname);
calcsize(n->nfile.next);
break;
case NTOFD:
case NFROMFD:
calcsize(n->ndup.vname);
calcsize(n->ndup.next);
break;
case NHERE:
case NXHERE:
calcsize(n->nhere.doc);
calcsize(n->nhere.next);
break;
case NNOT:
calcsize(n->nnot.com);
break;
};
}
STATIC void
sizenodelist(lp)
struct nodelist *lp;
{
while (lp) {
funcblocksize += SHELL_ALIGN(sizeof(struct nodelist));
calcsize(lp->n);
lp = lp->next;
}
}
STATIC union node *
copynode(n)
union node *n;
{
union node *new;
if (n == NULL)
return NULL;
new = funcblock;
funcblock = (char *) funcblock + nodesize[n->type];
switch (n->type) {
case NCMD:
new->ncmd.redirect = copynode(n->ncmd.redirect);
new->ncmd.args = copynode(n->ncmd.args);
new->ncmd.assign = copynode(n->ncmd.assign);
new->ncmd.linno = n->ncmd.linno;
break;
case NPIPE:
new->npipe.cmdlist = copynodelist(n->npipe.cmdlist);
new->npipe.backgnd = n->npipe.backgnd;
break;
case NREDIR:
case NBACKGND:
case NSUBSHELL:
new->nredir.redirect = copynode(n->nredir.redirect);
new->nredir.n = copynode(n->nredir.n);
new->nredir.linno = n->nredir.linno;
break;
case NAND:
case NOR:
case NSEMI:
case NWHILE:
case NUNTIL:
new->nbinary.ch2 = copynode(n->nbinary.ch2);
new->nbinary.ch1 = copynode(n->nbinary.ch1);
break;
case NIF:
new->nif.elsepart = copynode(n->nif.elsepart);
new->nif.ifpart = copynode(n->nif.ifpart);
new->nif.test = copynode(n->nif.test);
break;
case NFOR:
new->nfor.var = nodesavestr(n->nfor.var);
new->nfor.body = copynode(n->nfor.body);
new->nfor.args = copynode(n->nfor.args);
new->nfor.linno = n->nfor.linno;
break;
case NCASE:
new->ncase.cases = copynode(n->ncase.cases);
new->ncase.expr = copynode(n->ncase.expr);
new->ncase.linno = n->ncase.linno;
break;
case NCLIST:
new->nclist.body = copynode(n->nclist.body);
new->nclist.pattern = copynode(n->nclist.pattern);
new->nclist.next = copynode(n->nclist.next);
break;
case NDEFUN:
new->ndefun.body = copynode(n->ndefun.body);
new->ndefun.text = nodesavestr(n->ndefun.text);
new->ndefun.linno = n->ndefun.linno;
break;
case NARG:
new->narg.backquote = copynodelist(n->narg.backquote);
new->narg.text = nodesavestr(n->narg.text);
new->narg.next = copynode(n->narg.next);
break;
case NTO:
case NCLOBBER:
case NFROM:
case NFROMTO:
case NAPPEND:
new->nfile.fname = copynode(n->nfile.fname);
new->nfile.fd = n->nfile.fd;
new->nfile.next = copynode(n->nfile.next);
break;
case NTOFD:
case NFROMFD:
new->ndup.vname = copynode(n->ndup.vname);
new->ndup.dupfd = n->ndup.dupfd;
new->ndup.fd = n->ndup.fd;
new->ndup.next = copynode(n->ndup.next);
break;
case NHERE:
case NXHERE:
new->nhere.doc = copynode(n->nhere.doc);
new->nhere.fd = n->nhere.fd;
new->nhere.next = copynode(n->nhere.next);
break;
case NNOT:
new->nnot.com = copynode(n->nnot.com);
break;
};
new->type = n->type;
return new;
}
STATIC struct nodelist *
copynodelist(lp)
struct nodelist *lp;
{
struct nodelist *start;
struct nodelist **lpp;
lpp = &start;
while (lp) {
*lpp = funcblock;
funcblock = (char *) funcblock +
SHELL_ALIGN(sizeof(struct nodelist));
(*lpp)->n = copynode(lp->n);
lp = lp->next;
lpp = &(*lpp)->next;
}
*lpp = NULL;
return start;
}
STATIC char *
nodesavestr(s)
char *s;
{
char *rtn = funcstring;
funcstring = stpcpy(funcstring, s) + 1;
return rtn;
}
void
freefunc(struct funcnode *f)
{
if (f && --f->count < 0)
ckfree(f);
}
const char basesyntax[] = {
CEOS, CSPCL, CWORD, CCTL,
CCTL, CCTL, CCTL, CCTL,
CCTL, CCTL, CCTL, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CSPCL,
CNL, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CSPCL, CWORD,
CDQUOTE, CWORD, CVAR, CWORD,
CSPCL, CSQUOTE, CSPCL, CSPCL,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CSPCL, CSPCL, CWORD,
CSPCL, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CBACK, CWORD,
CWORD, CWORD, CBQUOTE, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CSPCL, CENDVAR,
CWORD, CWORD
};
const char dqsyntax[] = {
CEOS, CIGN, CWORD, CCTL,
CCTL, CCTL, CCTL, CCTL,
CCTL, CCTL, CCTL, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CNL, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CCTL,
CENDQUOTE,CWORD, CVAR, CWORD,
CWORD, CWORD, CWORD, CWORD,
CCTL, CWORD, CWORD, CCTL,
CWORD, CCTL, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CCTL, CWORD, CWORD, CCTL,
CWORD, CCTL, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CCTL, CBACK, CCTL,
CWORD, CWORD, CBQUOTE, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CENDVAR,
CCTL, CWORD
};
const char sqsyntax[] = {
CEOS, CIGN, CWORD, CCTL,
CCTL, CCTL, CCTL, CCTL,
CCTL, CCTL, CCTL, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CNL, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CCTL,
CWORD, CWORD, CWORD, CWORD,
CWORD, CENDQUOTE,CWORD, CWORD,
CCTL, CWORD, CWORD, CCTL,
CWORD, CCTL, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CCTL, CWORD, CWORD, CCTL,
CWORD, CCTL, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CCTL, CCTL, CCTL,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CCTL, CWORD
};
const char arisyntax[] = {
CEOS, CIGN, CWORD, CCTL,
CCTL, CCTL, CCTL, CCTL,
CCTL, CCTL, CCTL, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CNL, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CVAR, CWORD,
CWORD, CWORD, CLP, CRP,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CBACK, CWORD,
CWORD, CWORD, CBQUOTE, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CWORD,
CWORD, CWORD, CWORD, CENDVAR,
CWORD, CWORD
};
const char is_type[] = {
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, 0,
0, 0, 0, ISSPECL,
0, ISSPECL, ISSPECL, 0,
0, 0, 0, 0,
ISSPECL, 0, 0, ISSPECL,
0, 0, ISDIGIT, ISDIGIT,
ISDIGIT, ISDIGIT, ISDIGIT, ISDIGIT,
ISDIGIT, ISDIGIT, ISDIGIT, ISDIGIT,
0, 0, 0, 0,
0, ISSPECL, ISSPECL, ISUPPER,
ISUPPER, ISUPPER, ISUPPER, ISUPPER,
ISUPPER, ISUPPER, ISUPPER, ISUPPER,
ISUPPER, ISUPPER, ISUPPER, ISUPPER,
ISUPPER, ISUPPER, ISUPPER, ISUPPER,
ISUPPER, ISUPPER, ISUPPER, ISUPPER,
ISUPPER, ISUPPER, ISUPPER, ISUPPER,
ISUPPER, 0, 0, 0,
0, ISUNDER, 0, ISLOWER,
ISLOWER, ISLOWER, ISLOWER, ISLOWER,
ISLOWER, ISLOWER, ISLOWER, ISLOWER,
ISLOWER, ISLOWER, ISLOWER, ISLOWER,
ISLOWER, ISLOWER, ISLOWER, ISLOWER,
ISLOWER, ISLOWER, ISLOWER, ISLOWER,
ISLOWER, ISLOWER, ISLOWER, ISLOWER,
ISLOWER, 0, 0, 0,
0, 0
};
