# buildwheel

build pike-smb2 manylinux wheel (including for python2.7)

```
docker build -t pike-buildwheel buildwheel
docker run -it -v /tmp/wheelhouse:/src/pike/wheelhouse pike-buildwheel
```
