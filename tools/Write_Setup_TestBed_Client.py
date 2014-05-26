import os;
import sys;

def CreateFile(size, name):
  try:
    fname = name;
    print fname;
    fh = open("../output/"+fname, 'w')
    filesize = long(size)
    print "Creating a file of %d Bytes with name as %s in present directory\n"%(filesize, fname);
    print "filesize is %d bytes\n"%filesize

    if size<128:
      for i in range(size):
        fh.write("x")
    else:
      chunk=(filesize/128);
      print "Creating a file of %d Bytes with name as %s in present directory\n"%(filesize, fname);
      for i in range(chunk):
        #while (os.path.getsize(fname) < filesize):
        fh.write ("write mewrite mewrite mewrite mewrite mewrite mewrite mewrite mewrite mewrite mewrite mewrite mewrite mewrite mewrite mewrite me")
  finally:
    fh.close()

CreateFile(1024,"WriteInputFile") #common file for write
CreateFile(0,"WriteInputFileEmpty") #for Empty file
CreateFile(512,"WriteInputFile512B") #for 500Bytes file
CreateFile(1048576,"WriteInputFile1MB") #for 1MB file
CreateFile(5242880,"WriteInputFile5MB") #for 5MB file
CreateFile(10485760,"WriteInputFile10MB") #for 10MB file

