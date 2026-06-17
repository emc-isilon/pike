# Copyright (c) 2024 Dell Inc. or its subsidiaries. All Rights Reserved.

import uuid

import pike.ntstatus
import pike.smb2
import pytest


# for python print support
# import io
# import sys
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="surrogatepass")

PARAMS = [
    ("\ud83d\ude4f", "valid surrogate pairs"),  # 🙏 emoji
    ("\U0001F600", "32-bit character"),  # 😁 emoji
    ("\uD83D", "high surrogate"),  # high surrogate
    ("\uDC00", "low surrogate"),  # low surrogate
    ("\u4F60\u597D", "BMP characters"),  # Chinese "你好"
]


def validate_filename_support(char):
    spclchar = char.encode("utf-16", "surrogatepass").decode(
        "utf-16", "surrogatepass"
    )
    filename = f"test_io_{spclchar}_{uuid.uuid4()}.txt"
    return filename

def extract_filename(file_path):
    # Normalize path separators to support both Windows (\\) and PowerScale (\ued5c)
    # \\share1\\test_io....txt
    # \ued5cifs\ued5ctest_io_....txt
    normalized_path = file_path.replace("\ued5c", "/").replace("\\", "/")
    file_name = normalized_path.rsplit("/", 1)[-1]
    return file_name


@pytest.mark.parametrize("char, description", PARAMS)
def test_surrogate_filename_full_flow(pike_TreeConnect, char, description):
    filename = validate_filename_support(char)
    print("=" * 50 + f"{description}" + "=" * 50)
    try:
        with pike_TreeConnect() as tc:
            # Step 1: Create file with write/read, no delete on close
            print("Step 1: Creating file")
            with tc.chan.create(
                tc.tree,
                filename,
                access=pike.smb2.GENERIC_READ
                | pike.smb2.GENERIC_WRITE
                | pike.smb2.DELETE,
                share=pike.smb2.FILE_SHARE_READ
                | pike.smb2.FILE_SHARE_DELETE,
                disposition=pike.smb2.FILE_CREATE,
            ).result() as fh:
                buf = "test123"
                tc.chan.write(fh, 0, buf)
                read_data = tc.chan.read(fh, len(buf), 0).tobytes().decode()
                assert (
                    read_data == buf
                ), f"Data mismatch: expected {buf}, got {read_data}"
                print("File created successfully:", filename)
                tc.chan.close(fh)

            # Step 2: Query file info (enumerate)
            print("Step 2: Querying file info")
            with tc.chan.create(
                tc.tree,
                filename,
                access=pike.smb2.GENERIC_READ,
                share=pike.smb2.FILE_SHARE_READ,
            ).result() as fh_open:
                file_info = tc.chan.query_file_info(
                    fh_open,
                    pike.smb2.FILE_ALL_INFORMATION,
                    info_type=pike.smb2.SMB2_0_INFO_FILE,
                    first_result_only=True
                )
                file_path = file_info.name_information.file_name
                file_name = extract_filename(file_path)
                assert (
                    file_name == filename
                ), f"Data mismatch: expected {filename}, got {file_name}"
                print("Queried file info successfully:", file_info.name_information.file_name)
                tc.chan.close(fh_open)

            #Step 3: Open file with delete on close
            print("Step 3: Opening file with DELETE_ON_CLOSE")
            with tc.chan.create(
                tc.tree,
                filename,
                access=pike.smb2.GENERIC_READ
                | pike.smb2.DELETE,
                share=pike.smb2.FILE_SHARE_READ
                | pike.smb2.FILE_SHARE_DELETE,
                disposition=pike.smb2.FILE_OPEN,
                options=pike.smb2.FILE_DELETE_ON_CLOSE,
            ).result() as fh_delete:
                print("File opened with DELETE_ON_CLOSE and will be deleted:", filename)
                pass

            # Step 4: Verify file deletion
            print("Step 4: Verifying file deletion")
            try:
                with tc.chan.create(
                    tc.tree,
                    filename,
                    access=pike.smb2.GENERIC_READ,
                    disposition=pike.smb2.FILE_OPEN,
                ).result() as fh_check:
                    pytest.fail(f"File '{filename}' still exists after DELETE_ON_CLOSE.")
            except pike.model.ResponseError as e:
                assert (e.response.status == pike.ntstatus.STATUS_OBJECT_NAME_NOT_FOUND
                ), f"Unexpected error for filename '{filename}': {e}"
                print("File successfully deleted. Test passed:", filename)
    except Exception as e:
        print(f"Failed for file: {filename} with description '{description}': {e}")
        pytest.fail(f"Unexpected error for filename '{filename}' with description '{description}': {e}")

