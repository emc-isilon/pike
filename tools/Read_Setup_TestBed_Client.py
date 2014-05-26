import os;
import sys;

def CreateFile(size, name):
  try:
    fname = name;
    print fname;
    fh = open("../output/"+fname, 'w')
    filesize = long(size)
    print "Creating a file of %d Bytes with name as %s in output directory\n"%(filesize, fname);
    print "filesize is %d bytes\n"%filesize

    if size<128:
      for i in range(size):
        fh.write("x")
    else:
      chunk=(filesize/128);
      print "Creating a file of %d Bytes with name as %s in output directory\n"%(filesize, fname);
      for i in range(chunk):
        #while (os.path.getsize(fname) < filesize):
        fh.write ("900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface")
  finally:
    fh.close()

CreateFile(0,"EmptyFile") #for Empty file
CreateFile(512,"512BytesFile") #for 500Bytes file
CreateFile(51200,"50KBFile") #for 50KB file
CreateFile(131072,"128KBFile") #for 128KB file
CreateFile(1048576,"1MBFile") #for 1MB file
CreateFile(10485760,"10MBFile") #for 10MB file
CreateFile(1073741824,"1GBFile") #for 1GB file

# Code to create sparse file
# Does not account for size < 1
#
def Sparse(file, size):
  try:
    f = open("../output/"+file, "wb")
    f.seek(size-1)
    f.write(b'\x00')

  finally:
    f.close()

Sparse("Sparse", 51200)

