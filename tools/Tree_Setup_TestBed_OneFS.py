import os
import subprocess
import sys
import codecs
from subprocess import Popen, PIPE
#u = "राम"
#uni = u.encode('utf-8')
#print "the unicode var is :",uni
def ShareFile(alias,fname):
    try:
        if not os.path.exists (fname):
			print "the name is",fname
			fh = os.makedirs(fname)
			process = Popen(['isi', 'smb', 'shares', 'create', alias, fname], stdout=PIPE)
			stdout, stderr = process.communicate()
    except Exception as e:
        print "The error is :",str(e)

ShareFile('abcd','/ifs/smb_share/abcd')
ShareFile('abcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopq','/ifs/smb_share/abcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopq')
ShareFile('abcdefghijklmnopqrst','/ifs/smb_share/abcdefghijklmnopqrst/abcdefghijklmnopqrst/abcdefghijklmnopqrst')
ShareFile('tc_22','/ifs/smb_share/tc_22')
#ShareFile(uni, u"/ifs/smb_share/राम")
ShareFile('abcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrst',"/ifs/smb_share/abcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrst")


#Limitations :
#1.) Directory no 5 is not getting created & shared since it is in unicode.


