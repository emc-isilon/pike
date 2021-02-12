"""
pike.path - Path-like interface for working with a Tree object
"""

import datetime
import io
import os
from pathlib import PureWindowsPath, _WindowsFlavour

from . import model
from . import ntstatus
from . import nttime
from . import smb2


MAX_SYMLINK_RECURSE = 10


class _PikeFlavour(_WindowsFlavour):
    def casefold(self, s):
        if isinstance(s, model.Tree):
            s = os.fspath(s)
        return s.lower()

    def casefold_parts(self, parts):
        return [
            p.lower()
            for p in [
                os.fspath(rp) if isinstance(rp, model.Tree) else rp for rp in parts
            ]
        ]


_pike_flavour = _PikeFlavour()


class PikePath(PureWindowsPath):
    _flavour = _pike_flavour

    @classmethod
    def _parse_args(cls, args):
        """
        Override _parse_args to ensure a Tree is returned as drv
        """
        drv, root, parts = super(PikePath, cls)._parse_args(args)
        if args:
            if isinstance(args[0], model.Tree):
                drv = args[0]
            if isinstance(args[0], cls):
                drv = args[0]._drv
        return drv, root, parts

    @property
    def _channel(self):
        return self._drv.session.first_channel()

    @property
    def _tree(self):
        return self._drv

    @property
    def _path(self):
        if self._drv or self._root:
            return self._flavour.join(self._parts[1:])
        return str(self)

    def join_from_root(self, path):
        """
        Return a new PikePath by joining `path` to the root of this PikePath.

        Used to rehome an existing absolute path for use by this PikePath's Tree.
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

    def glob(self, pattern):
        raise NotImplementedError("glob() is not supported")

    def group(self):
        raise NotImplementedError("group() is not supported")

    def is_dir(self):
        return self.exists(options=smb2.FILE_DIRECTORY_FILE)

    def is_file(self):
        return self.exists(options=smb2.FILE_NON_DIRECTORY_FILE)

    def is_symlink(self):
        return self.exists(options=smb2.FILE_OPEN_REPARSE_POINT)

    def is_mount(self):
        return True  # all paths are on SMB mount

    def is_socket(self):
        return False

    def is_fifo(self):
        return False  # might be supported some day

    def is_block_device(self):
        return False

    def is_char_device(self):
        return False

    def glob(self, pattern):
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
        for item in self.glob("*"):
            yield item

    def link_to(self, target):
        raise NotImplementedError("hardlinks are not supported over SMB")

    def mkdir(self, mode=None, parents=False, exist_ok=False):
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
        Open a file-like with immediate IO via pike
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
        """
        with self.open("rb") as f:
            return f.read()

    def read_text(self, encoding=None, errors=None):
        """
        Return the decoded contents of the pointed-to file as a string.
        """
        with self.open("r") as f:
            return f.read()

    def readlink(self):
        with self._create_follow(
            access=smb2.READ_ATTRIBUTES,
            disposition=smb2.FILE_OPEN,
            options=smb2.FILE_NON_DIRECTORY_FILE | smb2.FILE_OPEN_REPARSE_POINT,
        ) as handle:
            # XXX: not making additional tree connects here, so absolute links
            # will only work across the same share
            return self.join_from_root(handle.get_symlink()[0].substitute_name)

    def rename(self, target, replace=True):
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

    def rename(self, target):
        return self.rename(target, replace=True)

    def resolve(self, strict=True):
        with self._create_follow(access=0, disposition=smb2.FILE_OPEN) as handle:
            return self.join_from_root(handle.create_request.name)

    def rglob(self, pattern):
        raise NotImplementedError("rglob is not supported by {!r}".format(type(self)))

    def rmdir(self, missing_ok=False):
        self.unlink(missing_ok=missing_ok, options=smb2.FILE_DIRECTORY_FILE)

    def samefile(self, otherpath):
        my_id = self.stat(file_information_class=smb2.FILE_INTERNAL_INFORMATION)
        if my_id == 0:
            raise NotImplementedError("remote filesystem does not return unique file index")
        if not isinstance(otherpath, type(self)):
            otherpath = self.join_from_root(otherpath)
        other_id = otherpath.stat(file_information_class=smb2.FILE_INTERNAL_INFORMATION)
        return my_id == other_id

    def symlink_to(self, target, target_is_directory=False):
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

    def touch(self, mode, exist_ok=True):
        disposition = smb2.FILE_OPEN_IF if exist_ok else smb2.FILE_CREATE
        with self._create_follow(
            access=smb2.GENERIC_WRITE,
            disposition=disposition,
            options=smb2.FILE_NON_DIRECTORY_FILE,
        ) as handle:
            with self.set_file_info(smb2.FileBasicInformation) as file_info:
                file_info.change_time = nttime.NtTime(datetime.datetime.now())

    def unlink(self, missing_ok=False, options=smb2.FILE_NON_DIRECTORY_FILE):
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
        """
        with self.open("wb") as f:
            return f.write(data)

    def write_text(self, data, encoding=None, errors=None):
        """
        Open the file pointed to in text mode, write data to it, and close the file
        """
        with self.open("w") as f:
            return f.write(data)
