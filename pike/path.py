"""
pike.path - Path-like interface for working with a Tree object
"""

from pathlib import PureWindowsPath

from . import model
from . import ntstatus
from . import smb2


class PikePath(PureWindowsPath):
    def __new__(cls, channel, tree, *path_components):
        p = PureWindowsPath.__new__(PikePath, *path_components)
        p._channel = channel
        p._tree = tree
        return p

    def _from_parsed_parts(self, *args, **kwargs):
        """
        Override _from_parsed_parts to carry _channel and _tree when extending.

        This is a classmethod in the parent, but we'll override it as an
        instance method, because it's not called in the class context and we
        need to carry instance variables.
        """
        if not isinstance(self, PikePath):
            raise NotImplementedError(
                "Cannot extend from non-instance: {!r}".format(self)
            )
        new_path = super(PikePath, self)._from_parsed_parts(*args, **kwargs)
        # carry the channel and tree when joining paths
        new_path._channel = self._channel
        new_path._tree = self._tree
        return new_path

    @classmethod
    def cwd(cls):
        raise NotImplementedError("No concept of cwd for {!r}".format(cls))

    @classmethod
    def home(cls):
        raise NotImplementedError("No concept of home for {!r}".format(cls))

    def stat(
        self,
        file_information_class=smb2.FILE_BASIC_INFORMATION,
        info_type=smb2.SMB2_0_INFO_FILE,
        options=0,
    ):
        with self._channel.create(
            self._tree,
            str(self),
            access=smb2.FILE_READ_ATTRIBUTES,
            disposition=smb2.FILE_OPEN,
            options=options,
        ).result() as handle:
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
            with self._channel.create(
                self._tree,
                str(self),
                access=0,
                disposition=smb2.FILE_OPEN,
                options=options,
            ).result() as handle:
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

    def iterdir(self):
        with self._channel.create(
            self._tree,
            str(self),
            access=smb2.GENERIC_READ,
            disposition=smb2.FILE_OPEN,
            options=smb2.FILE_DIRECTORY_FILE,
        ).result() as handle:
            for item in self._channel.enum_directory(
                handle, file_information_class=smb2.FILE_NAMES_INFORMATION
            ):
                if item.file_name in (".", ".."):
                    continue
                yield self / item.file_name

    def mkdir(self, mode=None, parents=False, exist_ok=False):
        if mode is not None:
            warnings.warn("`mode` argument is not handled at this time", stacklevel=2)
        try:
            with self._channel.create(
                self._tree,
                str(self),
                access=smb2.GENERIC_WRITE,
                disposition=smb2.FILE_CREATE,
                options=smb2.FILE_DIRECTORY_FILE,
            ).result() as handle:
                return
        except model.ResponseError as re:
            if re.response.status == ntstatus.STATUS_OBJECT_NAME_COLLISION and exist_ok:
                return
            if not parents or self.parent == self:
                raise
            self.parent.mkdir(parents=True, exist_ok=True)
            self.mkdir(mode, parents=False, exist_ok=exist_ok)
