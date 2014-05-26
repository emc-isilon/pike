import os
import subprocess
import sys

def ShareFile(name):
    try:
	    fname = name
	    fh = os.makedirs(fname)
	    print fname
	    cmd = "net share %s=C:\%s /users:30"%(fname, fname)
	    b = subprocess.Popen(cmd)
    except:
	    pass
ShareFile('abcd') # Directory 1
ShareFile('abcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopq') #Directory 2
ShareFile('abcdefghijklmnopqrst') # Directory 3
ShareFile(u'राम') #Directory 4
ShareFile('abcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrstabcdefghijklmnopqrst') # Directory 5
ShareFile('test27abcdefghijklmnopqrst') # Directory 6




#Limitations :
#1.) Directory no 5 is getting created but not getting shared as it has more than 80 characters.
#2.) Unicode Folder i.e Directory 4 is created but it is not getting shared permissions so manually we have to give share permissions.
#3.) Directory 6 :We need to create directory inside directory manually and share it . Parent Directory is getting created and shared but sub directoried need to be created manually and shared. Format (test27abcdefghijklmnopqrst\abcdefghijklmnopqrst\abcdefghijklmnopqrst)
 

