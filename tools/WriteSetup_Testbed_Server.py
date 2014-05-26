import os;
import sys;

def CreateFile(size, name):
  try:
    fname = name;
    print fname;
    fh = open(fname, 'w')
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
        fh.write ("900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface900dface")
  finally:
    fh.close()

#CreateFile(0,"EmptyFile") #for Empty file
#CreateFile(512,"512BytesFile") #for 500Bytes file
#CreateFile(51200,"50KBFile") #for 50KB file
#CreateFile(131072,"128KBFile") #for 128KB file
#CreateFile(1048576,"1MBFile") #for 1MB file
#CreateFile(10485760,"10MBFile") #for 10MB file
#CreateFile(1073741824,"1GBFile") #for 1GB file

CreateFile(512,"TC001_512BytesFile")
CreateFile(1048576,"TC002_1MBFile")
CreateFile(512,"TC003_512BytesFile")
CreateFile(1048576,"TC004_1MBFile")
CreateFile(1048576,"TC005_1MBFile")
CreateFile(512,"TC006_512BytesFile")
CreateFile(1048576,"TC007_1MBFile")
CreateFile(512,"TC008_512BytesFile")
CreateFile(51200,"TC009_50KBFile")
CreateFile(51200,"TC010_50KBFile")
CreateFile(131072,"TC011_128KBFile")
CreateFile(51200,"TC012_50KBFile")
CreateFile(51200,"TC013_50KBFile")
CreateFile(51200,"TC014_50KBFile")
CreateFile(51200,"TC015_50KBFile")
CreateFile(51200,"TC016_50KBFile")
CreateFile(51200,"TC017_50KBFile")
CreateFile(51200,"TC018_50KBFile")
CreateFile(51200,"TC019_50KBFile")
CreateFile(51200,"TC020_50KBFile")
CreateFile(51200,"TC021_50KBFile")
CreateFile(0,"TC022_EmptyFile")
CreateFile(51200,"TC023_50KBFile")
CreateFile(131072,"TC024_128KBFile")
CreateFile(512,"TC25_512BytesFile")
CreateFile(512,"TC26_512BytesFile")
CreateFile(512,"TC27_512BytesFile")
CreateFile(512,"TC28_512BytesFile")
CreateFile(51200,"TC029_50KBFile")
CreateFile(51200,"TC030_50KBFile")
CreateFile(51200,"TC031_50KBFile")
CreateFile(51200,"TC032_50KBFile")
CreateFile(512,"TC033_512BytesFile")
CreateFile(512,"TC034_512BytesFile")
CreateFile(512,"TC035_512BytesFile")
CreateFile(512,"TC036_512BytesFile")
CreateFile(512,"TC037_512BytesFile")
CreateFile(512,"TC037a_512BytesFile")
CreateFile(512,"TC037b_512BytesFile")
CreateFile(512,"TC037c_512BytesFile")
CreateFile(1048576,"TC039_1MBFile")
CreateFile(512,"TC040_512BytesFile")
CreateFile(512,"TC041_512BytesFile")
CreateFile(512,"TC042_512BytesFile")
CreateFile(512,"TC045_512BytesFile")
CreateFile(512,"TC047_512BytesFile")

