"""
Path-like interface for working with a Tree object
"""
from __future__ import absolute_import

import datetime
import io
import os
import sys

try:
    from pathlib import PureWindowsPath, _WindowsFlavour
except ImportError:
    from pathlib2 import PureWindowsPath, _WindowsFlavour

from . import model
from . import ntstatus
from . import nttime
from . import smb2


MAX_SYMLINK_RECURSE = 10


class _PikeFlavour(_WindowsFlavour):
    """
    Implement pike-specific overrides of WindowsFlavour semantics.

    Handle the fact that ``_drv`` may be a :py:class:`pike.model.Tree` instance.
    """
    def casefold(self, s):
        if isinstance(s, model.Tree):
            s = os.fspath(s)
        return s.lower()

    def casefold_parts(self, parts):
        if sys.version_info < (3,):
            fspath = lambda p: p.__fspath__()
        else:
            fspath = os.fspath
        return [
            p.lower()
            for p in [
                fspath(rp) if isinstance(rp, model.Tree) else rp for rp in parts
            ]
        ]


_pike_flavour = _PikeFlavour()


class PikePath(PureWindowsPath):
    """
    ``Path`` subclass for :py:class:`pike.model.Tree` instances.

    ``PikePath`` should be either directly instantiated by passing a
    :py:class:`~pike.model.Tree` or by performing typical ``Path`` extension
    (truediv) on a :py:class:`~pike.model.Tree` or
    :py:class:`pike.TreeConnect` instance.

    .. code-block:: python
        :caption: example.py

        import pike.path
        import pike.test

        with pike.TreeConnect() as tc:
            pth = pike.path.PikePath(tc.tree)
            assert (tc / "subdir") == (pth / "subdir")
            assert (tc.tree / "subdir") == (pth / "subdir")

    A ``PikePath`` is bound to a specific connection, session, and tree. If the
    underlying transport is no longer valid, then the path operations will not
    work.

    An existing path, valid or invalid, and be "rehomed" to a different
    ``PikePath`` by calling :py:func:`~pike.path.PikePath.join_from_root`,
    returning a new instance with the path part replaced by that of the passed
    argument.

    .. code-block:: python
        :caption: example.py

        import pike
        import pike.path

        with pike.TreeConnect(), pike.TreeConnect() as tc1, tc2:
            tc1_subdir = tc1 / "subdir"
            tc2_subdir = pike.path.PikePath(tc2.tree).join_from_root(tc1_subdir)
            assert tc1_subdir != tc2_subdir

    Unlike ``WindowsPath``, ``PikePath`` will prefer to raise
    :py:class:`pike.model.ResponseError` exceptions instead of ``OSError``.
    """
    _flavour = _pike_flavour

    @classmethod
    def _parse_args(cls, args):
        """
        Override _parse_args to ensure a Tree is returned as drv
        """
        if sys.version_info < (3,):
            # On python 2, explicitly convert future.types.newstr to native unicode type.
            from future.types import newstr

            # ensure that `newstr` instances are passed as real `unicode`
            # to avoid TypeError: can't intern subclass of string
            args = tuple(
                unicode(pc) if isinstance(pc, newstr) else pc for pc in args
            )
        drv, root, parts = super(PikePath, cls)._parse_args(args)
        if args:
            if isinstance(args[0], model.Tree):
                drv = args[0]
            if isinstance(args[0], cls):
                drv = args[0]._drv
        return drv, root, parts

    @property
    def _channel(self):
        """
        :rtype: pike.model.Channel
        :return: Channel bound to the associated tree
        """
        return self._drv.session.first_channel()

    @property
    def drive(self):
        """
        :rtype: pike.model.Tree
        :return: Tree forming the root of the share / path
        """
        return super(PikePath, self).drive

    _tree = drive

    @property
    def _path(self):
        """
        :rtype: str
        :return: SMB path relative to the root
        """
        if self._drv or self._root:
            return self._flavour.join(self._parts[1:])
        return str(self)

    def join_from_root(self, path):
        """
        Rehome an existing absolute path for use by this PikePath's Tree.

        :rtype: PikePath
        :return: a new :py:class:`~pike.path.PikePath` by joining ``path`` to
            the root of this instance.
        """
        if isinstance(path, type(self)) and (path.is_absolute()):
            return self.joinpath(*path._parts[1:])
        else:
            path = type(self)("\\", path)
        return self / path

    @classmethod
    def cwd(cls):
        raise NotImplementedError("No concept of cwd for {!r}".format(cls))

    @classmethod
    def home(cls):
        raise NotImplementedError("No concept of home for {!r}".format(cls))

    def _create_follow(self, *args, **kwargs):
        """
        Call Channel.create with this Tree and path following symlinks.

        Special kwarg, __RC_DEPTH, is used to track the recursion depth and
        will raise OSError if called more than MAX_SYMLINK_RECURSE times.

        Remaining args and kwargs are passed to create directly.
        """
        depth = kwargs.pop("__RC_DEPTH", 0)
        if depth > MAX_SYMLINK_RECURSE:
            raise OSError("Maximum level of symbolic links exceeded")
        try:
            return self._channel.create(self._tree, self._path, *args, **kwargs).result()
        except model.ResponseError as re:
            if re.response.status != ntstatus.STATUS_STOPPED_ON_SYMLINK:
                raise
            kwargs["__RC_DEPTH"] = depth + 1
            return self.join_from_root(re.response[0][0].error_data.substitute_name)._create_follow(*args, **kwargs)

    def stat(
        self,
        file_information_class=smb2.FILE_BASIC_INFORMATION,
        info_type=smb2.SMB2_0_INFO_FILE,
        options=0,
    ):
        """
        Perform SMB2 QUERY_INFO request for the given ``file_information_class``.

        :type file_information_class: smb2.FileInformationClass
        :param file_information_class: the file information class constant
            describing the type of information to retrieve
        :type info_type: smb2.InfoType
        :param info_type: the SMB2 query info type
        :type options: smb2.CreateOptions
        :param options: options passed to CREATE when opening the file
        :return: single file info object corresponding to the
            file_information_class requested
        """
        with self._create_follow(
            access=smb2.FILE_READ_ATTRIBUTES,
            disposition=smb2.FILE_OPEN,
            options=options,
        ) as handle:
            return self._channel.query_file_info(
                handle, file_information_class, info_type, first_result_only=True
            )

    def lstat(
        self,
        file_information_class=smb2.FILE_BASIC_INFORMATION,
        info_type=smb2.SMB2_0_INFO_FILE,
        options=0,
    ):
        """
        Perform SMB2 QUERY_INFO request for the given ``file_information_class``.

        If this path represents a symlink, open the link itself, rather than the
        target. (Intermediate links will not be followed first.)

        :type file_information_class: smb2.FileInformationClass
        :param file_information_class: the file information class constant
            describing the type of information to retrieve
        :type info_type: smb2.InfoType
        :param info_type: the SMB2 query info type
        :type options: smb2.CreateOptions
        :param options: options passed to CREATE when opening the file
        :return: single file info object corresponding to the
            file_information_class requested
        """
        options = options | smb2.FILE_OPEN_REPARSE_POINT
        return self.stat(
            file_information_class=file_information_class,
            info_type=info_type,
            options=options,
        )

    def chmod(self, mode):
        raise NotImplementedError("ACL modification is not supported")

    lchmod = chmod

    def exists(self, options=0):
        """
        :type options: smb2.CreateOptions
        :param options: options passed to CREATE when opening the file
        :return: True if this path exists
        """
        try:
            with self._create_follow(
                access=0,
                disposition=smb2.FILE_OPEN,
                options=options,
            ) as handle:
                return True
        except model.ResponseError as re:
            if re.response.status not in (
                ntstatus.STATUS_OBJECT_NAME_NOT_FOUND,
                ntstatus.STATUS_OBJECT_PATH_NOT_FOUND,
            ):
                raise
        return False

    def expanduser(self):
        raise NotImplementedError("expanduser() is not supported")

    def group(self):
        raise NotImplementedError("group() is not supported")

    def is_dir(self):
        """
        :return: True if this path is a directory
        """
        return self.exists(options=smb2.FILE_DIRECTORY_FILE)

    def is_file(self):
        """
        :return: True if this path is a normal file
        """
        return self.exists(options=smb2.FILE_NON_DIRECTORY_FILE)

    def is_symlink(self):
        """
        :return: True if this path is a reparse point
        """
        return self.exists(options=smb2.FILE_OPEN_REPARSE_POINT)

    def is_mount(self):
        """
        Note: all PikePath instances are considered to be mounts

        :return: True if this path is a mount point
        """
        return True  # all paths are on SMB mount

    def is_socket(self):
        """
        Note: no PikePath instances are considered to be sockets

        :return: True if this path is a socket
        """
        return False

    def is_fifo(self):
        """
        Note: no PikePath instances are considered to be fifo

        :return: True if this path is a pipe
        """
        return False  # might be supported some day

    def is_block_device(self):
        """
        Note: no PikePath instances are considered to be block devices

        :return: True if this path is a block device
        """
        return False

    def is_char_device(self):
        """
        Note: no PikePath instances are considered to be char devices

        :return: True if this path is a char device
        """
        return False

    def glob(self, pattern):
        """
        Iterate over this subtree and yield all existing files matching pattern.

        Files of any kind, including directories, that match the given relative
        pattern will be yielded with the exception of special entries "." and ".."

        The globbing is handled on the server side, so all ``pattern`` values
        must be valid according to [MS-CIFS] 2.2.1.1.3 Wildcards:
        https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cifs/dc92d939-ec45-40c8-96e5-4c4091e4ab43

        The recursive glob "**" is not supported.

        :param pattern: file search pattern
        :rtype: Iterator[:py:class:`~pike.path.PikePath`]
        """
        if "**" in pattern:
            raise ValueError("recursive glob, '**', is not supported by {!r}".format(type(self)))
        with self._create_follow(
            access=smb2.GENERIC_READ,
            disposition=smb2.FILE_OPEN,
            options=smb2.FILE_DIRECTORY_FILE,
        ) as handle:
            for item in handle.enum_directory(file_information_class=smb2.FILE_NAMES_INFORMATION, file_name=pattern):
                if item.file_name in (".", ".."):
                    continue
                yield self / item.file_name

    def iterdir(self):
        """
        Iterate over this subtree and yield all existing files.

        The special entries "." and ".." will not be yielded.

        :rtype: Iterator[:py:class:`~pike.path.PikePath`]
        """

        for item in self.glob("*"):
            yield item

    def link_to(self, target):
        raise NotImplementedError("hardlinks are not supported over SMB")

    def mkdir(self, mode=None, parents=False, exist_ok=False):
        """
        Create a new directory at this given path.

        :param mode: The mode of the created file. NOT SUPPORTED
        :param parents: if True, create all parent directories if they do not exist
        :param exist_ok: if True, don't raise if the directory exists
        """
        if mode is not None:
            warnings.warn("`mode` argument is not handled at this time", stacklevel=2)
        try:
            with self._create_follow(
                access=smb2.GENERIC_WRITE,
                disposition=smb2.FILE_CREATE,
                options=smb2.FILE_DIRECTORY_FILE,
            ) as handle:
                return
        except model.ResponseError as re:
            if re.response.status == ntstatus.STATUS_OBJECT_NAME_COLLISION and exist_ok:
                return
            if not parents or self.parent == self:
                raise
            self.parent.mkdir(parents=True, exist_ok=True)
            self.mkdir(mode, parents=False, exist_ok=exist_ok)

    def open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        """
        Open the file pointed by this path and return a file object, as
        the built-in open() function does.

        Where possible, the semantics are designed to match a local open file.

        Lease/oplock based buffering is not supported at this time. To avoid
        reading stale data, or locally buffering writes, pass ``buffering=0``.
        """
        buffer_class = io.BufferedReader
        access = 0
        disposition = smb2.FILE_OPEN
        mode = mode.lower()
        if "r" in mode or "+" in mode:
            access |= smb2.GENERIC_READ
        if "a" in mode or "w" in mode or "+" in mode:
            access |= smb2.GENERIC_WRITE
            buffer_class = io.BufferedWriter
        if "+" in mode:
            buffer_class = io.BufferedRandom
        if "x" in mode:
            disposition = smb2.FILE_CREATE
        elif "a" in mode:
            disposition = smb2.FILE_OPEN_IF
        elif "w" in mode or "+" in mode:
            disposition = smb2.FILE_SUPERSEDE
        handle = self._create_follow(
            access=access,
            disposition=disposition,
            options=smb2.FILE_NON_DIRECTORY_FILE,
        )
        if "a" in mode:
            handle.seek(0, SEEK_END)
        if "b" in mode and buffering == 0:
            return handle
        if buffering == -1:
            buffer_size = smb2.BYTES_PER_CREDIT
        buffered_io = buffer_class(handle, buffer_size=buffer_size)
        if "b" in mode:
            return buffered_io
        return io.TextIOWrapper(
            buffered_io, encoding=encoding, errors=errors, newline=newline
        )

    def read_bytes(self):
        """
        Return the binary contents of the pointed-to file as a bytes object.

        :rtype: bytes
        """
        with self.open("rb") as f:
            return f.read()

    def read_text(self, encoding=None, errors=None):
        """
        Return the decoded contents of the pointed-to file as a string.

        :rtype: str
        """
        with self.open("r") as f:
            return f.read()

    def readlink(self):
        """
        Return the :py:class:`~pike.path.PikePath` to which the symbolic link points.

        :rtype: PikePath
        """
        with self._create_follow(
            access=smb2.READ_ATTRIBUTES,
            disposition=smb2.FILE_OPEN,
            options=smb2.FILE_NON_DIRECTORY_FILE | smb2.FILE_OPEN_REPARSE_POINT,
        ) as handle:
            # XXX: not making additional tree connects here, so absolute links
            # will only work across the same share
            return self.join_from_root(handle.get_symlink()[0].substitute_name)

    def rename(self, target, replace=True):
        """
        Rename the object at this path to ``target``.

        :param target: new name
        :param replace: if True, pass ``replace_if_exists`` in ``FileRenameInformation``
        :rtype: PikePath
        :return: path pointing to target
        """
        if not isinstance(target, type(self)):
            target = self.join_from_root(target)
        with self._create_follow(
            access=smb2.DELETE,
            disposition=smb2.FILE_OPEN,
        ) as handle:
            with self.set_file_info(smb2.FileRenameInformation) as file_info:
                file_info.replace_if_exists = replace
                file_info.file_name = target._path
            return target

    def replace(self, target):
        """
        Same as rename, but with replace=True
        """
        return self.rename(target, replace=True)

    def resolve(self, strict=True):
        """
        Follow all symbolic links in the path and return the
        :py:class:`~pike.path.PikePath` at the end of the chain.

        Similar to ``readlink``, however this calls relies on handling the
        SymbolicLinkErrorResponse during create, rather than explicitly
        reading the link target via IOCTL_GET_REPARSE_POINT.
        """
        with self._create_follow(access=0, disposition=smb2.FILE_OPEN) as handle:
            return self.join_from_root(handle.create_request.name)

    def rglob(self, pattern):
        raise NotImplementedError("rglob is not supported by {!r}".format(type(self)))

    def rmdir(self, missing_ok=False):
        """
        Remove the directory at this path.

        The directory must be empty.

        :param missing_ok: if True, don't raise if the directory doesn't exist
        """
        self.unlink(missing_ok=missing_ok, options=smb2.FILE_DIRECTORY_FILE)

    def samefile(self, otherpath):
        """
        Determine if this path points to the same file as another path.

        This uses ``FILE_INTERNAL_INFORMATION`` to perform the check. If the
        server doesn't support this info class, NotImplementedError is raised.

        :type otherpath: PikePath
        :param otherpath: the other path to compare to
        :return: True if otherpath points to the same file
        """
        my_id = self.stat(file_information_class=smb2.FILE_INTERNAL_INFORMATION)
        if my_id == 0:
            raise NotImplementedError("remote filesystem does not return unique file index")
        if not isinstance(otherpath, type(self)):
            otherpath = self.join_from_root(otherpath)
        other_id = otherpath.stat(file_information_class=smb2.FILE_INTERNAL_INFORMATION)
        return my_id == other_id

    def symlink_to(self, target, target_is_directory=False):
        """
        Make this path a symlink pointing to the given path.

        Note the order of arguments (self, target) is the reverse of os.symlink's.

        Does not work for absolute links.

        :type target: PikePath
        :param target: The link's target
        :param target_is_directory: must be True if the target is a directory
        """
        if not isinstance(target, type(self)):
            target = self.join_from_root(target)
        options = smb2.FILE_DIRECTORY_FILE if target_is_directory else 0
        with self._create_follow(
            access=smb2.GENERIC_WRITE,
            attributes=smb2.FILE_ATTRIBUTE_REPARSE_POINT,
            disposition=smb2.FILE_SUPERSEDE,
            options=options | smb2.FILE_OPEN_REPARSE_POINT,
        ) as handle:
            handle.set_symlink(target._path, flags=smb2.SYMLINK_FLAG_RELATIVE)

    def touch(self, mode=None, exist_ok=True):
        """
        Create a new file or update modification time at this given path.

        :param mode: The mode of the created file. NOT SUPPORTED
        :param exist_ok: if True, don't raise if the file exists
        """
        if mode is not None:
            warnings.warn("`mode` argument is not handled at this time", stacklevel=2)
        disposition = smb2.FILE_OPEN_IF if exist_ok else smb2.FILE_CREATE
        with self._create_follow(
            access=smb2.GENERIC_WRITE,
            disposition=disposition,
            options=smb2.FILE_NON_DIRECTORY_FILE,
        ) as handle:
            with self.set_file_info(smb2.FileBasicInformation) as file_info:
                file_info.change_time = nttime.NtTime(datetime.datetime.now())

    def unlink(self, missing_ok=False, options=smb2.FILE_NON_DIRECTORY_FILE):
        """
        Remove the file at this path.

        :param missing_ok: if True, don't raise if the file doesn't exist
        :param options: options passed to CREATE when opening the file
        """
        try:
            with self._create_follow(
                access=smb2.DELETE,
                disposition=smb2.FILE_OPEN,
                options=options | smb2.FILE_DELETE_ON_CLOSE,
            ) as handle:
                pass
        except model.ResponseError as re:
            if (
                re.response.status
                in (
                    ntstatus.STATUS_OBJECT_NAME_NOT_FOUND,
                    ntstatus.STATUS_OBJECT_PATH_NOT_FOUND,
                )
                and missing_ok
            ):
                return
            elif re.response.status == ntstatus.STATUS_STOPPED_ON_SYMLINK:
                return self.unlink(
                    missing_ok=missing_ok,
                    options=options | smb2.FILE_OPEN_REPARSE_POINT,
                )
            raise

    def write_bytes(self, data):
        """
        Open the file pointed to in bytes mode, write data to it, and close the file.

        :type data: bytes
        :param data: bytes to write to the file
        :rtype: int
        :return: number of bytes written
        """
        with self.open("wb") as f:
            return f.write(data)

    def write_text(self, data, encoding=None, errors=None):
        """
        Open the file pointed to in text mode, write data to it, and close the file.

        :type data: str
        :param data: unicode string to write to the file
        :rtype: int
        :return: number of bytes written
        """
        with self.open("w") as f:
            return f.write(data)
