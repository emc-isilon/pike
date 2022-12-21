import os

SAMBA_VERSION = os.environ.get("SAMBA_VERSION") or None
SAMBA_VERSION_INFO = (
    tuple(int(sv) for sv in SAMBA_VERSION.split(".")) if SAMBA_VERSION else None
)


def samba_version(greater=None, lesser=None):
    """Use with pytest.mark.skipif"""
    if SAMBA_VERSION is None:
        return SAMBA_VERSION
    if greater is not None:
        if SAMBA_VERSION_INFO < greater:
            return False
    if lesser is not None:
        if SAMBA_VERSION_INFO > lesser:
            return False
    return SAMBA_VERSION_INFO
