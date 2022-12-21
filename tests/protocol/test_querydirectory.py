#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        test_querydirectory.py
#
# Abstract:
#
#        Query directory tests
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#
from __future__ import unicode_literals
import uuid

import pytest

import pike.model
import pike.smb2
import pike.test
import pike.ntstatus


@pytest.fixture
def directory_for_query(pike_tmp_path):
    with pike_tmp_path.create(
        access=pike.smb2.GENERIC_READ,
        options=pike.smb2.FILE_DIRECTORY_FILE,
        share=pike.smb2.FILE_SHARE_READ,
    ) as handle:
        yield handle


def test_file_directory_info_special(pike_tree_connect, directory_for_query):
    """
    Enumerate directory at FILE_DIRECTORY_INFORMATION level.

    Test for presence of . and .. entries.
    """

    names = [
        info.file_name
        for info in pike_tree_connect.chan.enum_directory(directory_for_query)
    ]

    assert "." in names
    assert ".." in names


@pytest.fixture
def file_in_directory(pike_tmp_path):
    fid = pike_tmp_path / "hello.txt"
    fid.touch()
    yield fid.name


def test_specific_name(pike_tree_connect, directory_for_query, file_in_directory):
    """
    Querying for a specific filename twice on the same handle succeeds the first time

    ...and fails with STATUS_NO_MORE_FILES the second.
    """
    query1 = pike_tree_connect.chan.query_directory(
        directory_for_query, file_name=file_in_directory
    )
    assert file_in_directory in (info.file_name for info in query1)

    with pike.ntstatus.raises(pike.ntstatus.STATUS_NO_MORE_FILES):
        pike_tree_connect.chan.query_directory(
            directory_for_query, file_name=file_in_directory
        )


@pytest.fixture
def unicode_files_and_dirs(pike_tmp_path):
    files = ["f1", "P̂îk̂ê", "C尺U乇ﾚ", "𐌃Ꝋ𐌍'𐌕 𐌁𐌓𐌄𐌀𐌊 𐌌𐌙", "⣫o⣖k"]
    dirs = ["𝓻𝓮𝓪𝓵𝔂 𝓵𝓲𝓯𝓮 𝓽𝓮𝓼𝓽 𝓬𝓪𝓼𝓮"]
    for fname in files:
        (pike_tmp_path / fname).touch()
    for dname in dirs:
        (pike_tmp_path / dname).mkdir()

    yield files, dirs

    for fname in files:
        (pike_tmp_path / fname).unlink()
    for dname in dirs:
        (pike_tmp_path / dname).rmdir()


def assert_names_in_listing(listing_names, expected_names):
    files, dirs = expected_names
    for fname in files:
        assert fname in listing_names
    for dname in dirs:
        assert dname in listing_names


def test_file_id_both_directory_information(
    pike_tree_connect,
    directory_for_query,
    unicode_files_and_dirs,
):
    result = pike_tree_connect.chan.query_directory(
        directory_for_query,
        file_information_class=pike.smb2.FILE_ID_BOTH_DIR_INFORMATION,
    )
    names = [info.file_name for info in result]
    assert_names_in_listing(names, expected_names=unicode_files_and_dirs)
    valid_file_ids = [info.file_id >= 0 for info in result]
    assert all(valid_file_ids)


def test_restart_scan(
    pike_tree_connect,
    directory_for_query,
    unicode_files_and_dirs,
):
    result = pike_tree_connect.chan.query_directory(directory_for_query)
    names1 = [info.file_name for info in result]
    assert_names_in_listing(names1, expected_names=unicode_files_and_dirs)
    result = pike_tree_connect.chan.query_directory(
        directory_for_query, flags=pike.smb2.SL_RESTART_SCAN, file_name="*"
    )
    names2 = [info.file_name for info in result]
    print(names2)
    assert names1 == names2
