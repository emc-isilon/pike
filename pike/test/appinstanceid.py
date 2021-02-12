#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        appinstanceid.py
#
# Abstract:
#
#        App instance ID tests
#
# Authors: Arlene Berry (arlene.berry@emc.com)
#

from builtins import map
import pike.model
import pike.smb2
import pike.test
import pike.ntstatus
import random
import array


@pike.test.RequireDialect(pike.smb2.DIALECT_SMB3_0)
@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_PERSISTENT_HANDLES)
@pike.test.RequireShareCapabilities(pike.smb2.SMB2_SHARE_CAP_CONTINUOUS_AVAILABILITY)
class AppInstanceIdTest(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(AppInstanceIdTest, self).__init__(*args, **kwargs)
        self.share_all = (
            pike.smb2.FILE_SHARE_READ
            | pike.smb2.FILE_SHARE_WRITE
            | pike.smb2.FILE_SHARE_DELETE
        )
        self.lease1 = array.array("B", map(random.randint, [0] * 16, [255] * 16))
        self.app_instance_id1 = array.array(
            "B", map(random.randint, [0] * 16, [255] * 16)
        )
        self.r = pike.smb2.SMB2_LEASE_READ_CACHING
        self.rw = self.r | pike.smb2.SMB2_LEASE_WRITE_CACHING
        self.rh = self.r | pike.smb2.SMB2_LEASE_HANDLE_CACHING
        self.rwh = self.rw | self.rh

    # Perform create with AppInstanceId
    def test_appinstanceid(self):
        chan, tree = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(
            tree,
            "appinstanceid.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=self.share_all,
            disposition=pike.smb2.FILE_OPEN_IF,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rwh,
            durable=0,
            persistent=True,
            app_instance_id=self.app_instance_id1,
        ).result()

        self.assertEqual(handle1.durable_flags, pike.smb2.SMB2_DHANDLE_FLAG_PERSISTENT)
        self.assertEqual(handle1.lease.lease_state, self.rwh)

        chan.close(handle1)

    # Invalidate disconnected persistent handle via AppInstanceId
    def test_appinstanceid_persistent_with_disconnect(self):
        chan, tree = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(
            tree,
            "appinstanceid.txt",
            share=self.share_all,
            disposition=pike.smb2.FILE_OPEN_IF,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rwh,
            durable=0,
            persistent=True,
            app_instance_id=self.app_instance_id1,
        ).result()

        self.assertEqual(handle1.durable_flags, pike.smb2.SMB2_DHANDLE_FLAG_PERSISTENT)
        self.assertEqual(handle1.lease.lease_state, self.rwh)

        # Close the connection
        chan.connection.close()

        chan2, tree2 = self.tree_connect(client=pike.model.Client())

        # Request reconnect
        handle2 = chan2.create(
            tree,
            "appinstanceid.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=self.share_all,
            disposition=pike.smb2.FILE_OPEN_IF,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rwh,
            durable=0,
            persistent=True,
            app_instance_id=self.app_instance_id1,
        ).result()

        self.assertEqual(handle2.durable_flags, pike.smb2.SMB2_DHANDLE_FLAG_PERSISTENT)
        self.assertEqual(handle2.lease.lease_state, self.rwh)

        chan2.close(handle2)

    # Invalidating a disconnected persistent handle
    # with AppInstanceId fails when reusing the same client GUID
    def test_appinstanceid_reconnect_same_clientguid(self):
        chan, tree = self.tree_connect()

        # Request rwh lease
        handle1 = chan.create(
            tree,
            "appinstanceid.txt",
            share=self.share_all,
            disposition=pike.smb2.FILE_OPEN_IF,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rwh,
            durable=0,
            persistent=True,
            app_instance_id=self.app_instance_id1,
        ).result()

        self.assertEqual(handle1.durable_flags, pike.smb2.SMB2_DHANDLE_FLAG_PERSISTENT)
        self.assertEqual(handle1.lease.lease_state, self.rwh)

        # Close the connection
        chan.connection.close()

        chan2, tree2 = self.tree_connect()

        # Request reconnect
        with self.assert_error(pike.ntstatus.STATUS_FILE_NOT_AVAILABLE):
            handle2 = chan2.create(
                tree,
                "appinstanceid.txt",
                access=pike.smb2.FILE_READ_DATA
                | pike.smb2.FILE_WRITE_DATA
                | pike.smb2.DELETE,
                share=self.share_all,
                disposition=pike.smb2.FILE_OPEN_IF,
                options=pike.smb2.FILE_DELETE_ON_CLOSE,
                oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
                lease_key=self.lease1,
                lease_state=self.rwh,
                durable=0,
                persistent=True,
                app_instance_id=self.app_instance_id1,
            ).result()

        # Close the connection
        chan2.connection.close()

        chan3, tree3 = self.tree_connect(client=pike.model.Client())

        # Request reconnect
        handle3 = chan3.create(
            tree,
            "appinstanceid.txt",
            access=pike.smb2.FILE_READ_DATA
            | pike.smb2.FILE_WRITE_DATA
            | pike.smb2.DELETE,
            share=self.share_all,
            disposition=pike.smb2.FILE_OPEN_IF,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=self.lease1,
            lease_state=self.rwh,
            durable=0,
            persistent=True,
            app_instance_id=self.app_instance_id1,
        ).result()

        self.assertEqual(handle3.durable_flags, pike.smb2.SMB2_DHANDLE_FLAG_PERSISTENT)
        self.assertEqual(handle3.lease.lease_state, self.rwh)

        chan3.close(handle3)
