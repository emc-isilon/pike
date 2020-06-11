#
# Copyright (c) 2013, EMC Corporation
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Module Name:
#
#        changenotify.py
#
# Abstract:
#
#        Change Notify tests
#
# Authors: Masen Furer <masen.furer@emc.com>
#

import pike.model
import pike.ntstatus
import pike.smb2
import pike.test

class ChangeNotifyTest(pike.test.PikeTest):
    def test_change_notify_file_name(self):
        filename = "change_notify.txt"
        chan, tree = self.tree_connect()

        # connect to the root of the share
        root = chan.create(tree,
                           '',
                           access=pike.smb2.GENERIC_READ,
                           options=pike.smb2.FILE_DIRECTORY_FILE,
                           share=pike.smb2.FILE_SHARE_READ).result()

        # build a change notify request
        smb_req = chan.request(obj=root)
        notify_req = pike.smb2.ChangeNotifyRequest(smb_req)
        notify_req.file_id = root.file_id
        notify_req.completion_filter = pike.smb2.SMB2_NOTIFY_CHANGE_FILE_NAME
        # send the request async
        futures = chan.connection.submit(smb_req.parent)

        # create a file on the share to trigger the notification
        file = chan.create(tree,
                           filename,
                           access=pike.smb2.FILE_READ_DATA | pike.smb2.FILE_WRITE_DATA | pike.smb2.DELETE,
                           share=pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE,
                           options=pike.smb2.FILE_DELETE_ON_CLOSE,
                           disposition=pike.smb2.FILE_SUPERSEDE).result()
       
        chan.close(file)
        
        # collect the change notify response
        result = futures[0].result()[0]

        # expect one notification, for the file add
        self.assertEqual(len(result.notifications), 1)
        self.assertEqual(result.notifications[0].filename, filename)
        self.assertEqual(result.notifications[0].action, pike.smb2.SMB2_ACTION_ADDED)
        
        chan.close(root)

    def test_change_notify_cancel(self):
        chan, tree = self.tree_connect()

        root = chan.create(tree,
                           '',
                           access=pike.smb2.GENERIC_READ,
                           options=pike.smb2.FILE_DIRECTORY_FILE,
                           share=pike.smb2.FILE_SHARE_READ).result()
        cn_future = chan.change_notify(root)
        # close the handle for the outstanding notify
        chan.close(root)

        smb2_resp = cn_future.result()
        # [MS-SMB2] 3.3.5.10 - The Server MUST send an SMB2 CHANGE_NOTIFY Response with
        # STATUS_NOTIFY_CLEANUP status code for all pending CHANGE_NOTIFY requests
        # associated with the FileId that is closed.
        self.assertEqual(smb2_resp.status, pike.ntstatus.STATUS_NOTIFY_CLEANUP)
        notify_resp = smb2_resp[0]
        # The response should contain no FileNotifyInformation structs
        self.assertEqual(len(notify_resp), 0)
