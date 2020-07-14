import six
if six.PY2:
    import array
    oldarray = array.array
    # monkey-patch tobytes for python 2.7
    class newarray(oldarray):
        def tobytes(self, *args, **kwargs):
            return self.tostring(*args, **kwargs)

        def __getslice__(self, *args, **kwargs):
            return type(self)(self.typecode, super(newarray, self).__getslice__(*args, **kwargs))

        def __add__(self, *args, **kwargs):
            return type(self)(self.typecode, super(newarray, self).__add__(*args, **kwargs))

    array.array = newarray

__all__ = [
        'auth',
        'core',
        'crypto',
        'digest',
        'kerberos',
        'model',
        'netbios',
        'ntlm'
        'nttime',
        'ntstatus',
        'smb2',
        'test',
        'transport',
]
# __version__ is defined by setuptools_scm using git tag
# https://github.com/pypa/setuptools_scm/