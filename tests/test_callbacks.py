#
# Copyright (c) 2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#

import pike.core as core
import pike.model as model
import pike.smb2 as smb2
import pike.test


class TestClientCallbacks(pike.test.PikeTest):
    def test_pre_serialize(self):
        callback_future = model.Future()
        def cb(frame):
            with callback_future:
                self.assertTrue(isinstance(frame, core.Frame))
                self.assertTrue(isinstance(frame[0], smb2.Smb2))
                self.assertTrue(isinstance(frame[0][0], smb2.NegotiateRequest))
                self.assertFalse(hasattr(frame, "buf"))
                callback_future.complete(True)
        self.default_client.register_callback(model.EV_REQ_PRE_SERIALIZE, cb)
        conn = self.default_client.connect(self.server, self.port)
        conn.negotiate()
        self.assertTrue(callback_future.result(timeout=2))

    def test_post_serialize(self):
        callback_future = model.Future()
        def cb(frame):
            with callback_future:
                self.assertTrue(isinstance(frame, core.Frame))
                self.assertTrue(isinstance(frame[0], smb2.Smb2))
                self.assertTrue(isinstance(frame[0][0], smb2.NegotiateRequest))
                self.assertTrue(hasattr(frame, "buf"))
                self.assertEqual(frame.len + 4, len(frame.buf))
                callback_future.complete(True)
        self.default_client.register_callback(model.EV_REQ_POST_SERIALIZE, cb)
        conn = self.default_client.connect(self.server, self.port)
        conn.negotiate()
        self.assertTrue(callback_future.result(timeout=2))

    def test_pre_post_send(self):
        pre_callback_future = model.Future()
        post_callback_future = model.Future()
        expected_bytes = []
        def pre_cb(data):
            with pre_callback_future:
                expected_bytes.insert(0, len(data))
                self.assertGreater(expected_bytes[0], 16)
                pre_callback_future.complete(True)
        def post_cb(bytes_written):
            with post_callback_future:
                self.assertEqual(expected_bytes.pop(), bytes_written)
                if not expected_bytes:
                    post_callback_future.complete(True)
        self.default_client.register_callback(model.EV_REQ_PRE_SEND, pre_cb)
        self.default_client.register_callback(model.EV_REQ_POST_SEND, post_cb)
        conn = self.default_client.connect(self.server, self.port)
        conn.negotiate()
        self.assertTrue(pre_callback_future.result(timeout=2))
        self.assertTrue(post_callback_future.result(timeout=2))

    def test_pre_deserialize(self):
        callback_future = model.Future()
        def cb(data):
            with callback_future:
                self.assertGreater(len(data), 4)
                callback_future.complete(True)
        self.default_client.register_callback(model.EV_RES_PRE_DESERIALIZE, cb)
        conn = self.default_client.connect(self.server, self.port)
        conn.negotiate()
        self.assertTrue(callback_future.result(timeout=2))

    def test_post_deserialize(self):
        callback_future = model.Future()
        def cb(frame):
            with callback_future:
                self.assertTrue(isinstance(frame, core.Frame))
                self.assertTrue(isinstance(frame[0], smb2.Smb2))
                self.assertTrue(isinstance(frame[0][0], smb2.NegotiateResponse))
                self.assertTrue(hasattr(frame, "buf"))
                self.assertEqual(frame.len + 4, len(frame.buf))
                callback_future.complete(True)
        self.default_client.register_callback(model.EV_RES_POST_DESERIALIZE, cb)
        conn = self.default_client.connect(self.server, self.port)
        conn.negotiate()
        self.assertTrue(callback_future.result(timeout=2))

    def test_pre_post_recv(self):
        pre_callback_future = model.Future()
        post_callback_future = model.Future()
        expected_bytes = []
        expected_rounds = [1,2]
        def pre_cb(read_bytes):
            with pre_callback_future:
                expected_bytes.insert(0, read_bytes)
                self.assertGreater(read_bytes, 3)
                pre_callback_future.complete(True)
        def post_cb(data):
            with post_callback_future:
                self.assertEqual(expected_bytes.pop(), len(data))
                expected_rounds.pop()
                if not expected_rounds:
                    post_callback_future.complete(True)
        self.default_client.register_callback(model.EV_RES_PRE_RECV, pre_cb)
        self.default_client.register_callback(model.EV_RES_POST_RECV, post_cb)
        conn = self.default_client.connect(self.server, self.port)
        conn.negotiate()
        self.assertTrue(pre_callback_future.result(timeout=2))
        self.assertTrue(post_callback_future.result(timeout=2))


class TestConnectionCallbacks(pike.test.PikeTest):
    def test_pre_serialize(self):
        callback_future = model.Future()
        def cb(frame):
            with callback_future:
                self.assertTrue(isinstance(frame, core.Frame))
                self.assertTrue(isinstance(frame[0], smb2.Smb2))
                self.assertTrue(isinstance(frame[0][0], smb2.NegotiateRequest))
                self.assertFalse(hasattr(frame, "buf"))
                callback_future.complete(True)
        conn = self.default_client.connect(self.server, self.port)
        conn.register_callback(model.EV_REQ_PRE_SERIALIZE, cb)
        conn.negotiate()
        self.assertTrue(callback_future.result(timeout=2))

    def test_post_serialize(self):
        callback_future = model.Future()
        def cb(frame):
            with callback_future:
                self.assertTrue(isinstance(frame, core.Frame))
                self.assertTrue(isinstance(frame[0], smb2.Smb2))
                self.assertTrue(isinstance(frame[0][0], smb2.NegotiateRequest))
                self.assertTrue(hasattr(frame, "buf"))
                self.assertEqual(frame.len + 4, len(frame.buf))
                callback_future.complete(True)
        conn = self.default_client.connect(self.server, self.port)
        conn.register_callback(model.EV_REQ_POST_SERIALIZE, cb)
        conn.negotiate()
        self.assertTrue(callback_future.result(timeout=2))

    def test_pre_post_send(self):
        pre_callback_future = model.Future()
        post_callback_future = model.Future()
        expected_bytes = []
        def pre_cb(data):
            with pre_callback_future:
                expected_bytes.insert(0, len(data))
                self.assertGreater(expected_bytes[0], 16)
                pre_callback_future.complete(True)
        def post_cb(bytes_written):
            with post_callback_future:
                self.assertEqual(expected_bytes.pop(), bytes_written)
                if not expected_bytes:
                    post_callback_future.complete(True)
        conn = self.default_client.connect(self.server, self.port)
        conn.register_callback(model.EV_REQ_PRE_SEND, pre_cb)
        conn.register_callback(model.EV_REQ_POST_SEND, post_cb)
        conn.negotiate()
        self.assertTrue(pre_callback_future.result(timeout=2))
        self.assertTrue(post_callback_future.result(timeout=2))

    def test_pre_deserialize(self):
        callback_future = model.Future()
        def cb(data):
            with callback_future:
                self.assertGreater(len(data), 4)
                callback_future.complete(True)
        conn = self.default_client.connect(self.server, self.port)
        conn.register_callback(model.EV_RES_PRE_DESERIALIZE, cb)
        conn.negotiate()
        self.assertTrue(callback_future.result(timeout=2))

    def test_post_deserialize(self):
        callback_future = model.Future()
        def cb(frame):
            with callback_future:
                self.assertTrue(isinstance(frame, core.Frame))
                self.assertTrue(isinstance(frame[0], smb2.Smb2))
                self.assertTrue(isinstance(frame[0][0], smb2.NegotiateResponse))
                self.assertTrue(hasattr(frame, "buf"))
                self.assertEqual(frame.len + 4, len(frame.buf))
                callback_future.complete(True)
        conn = self.default_client.connect(self.server, self.port)
        conn.register_callback(model.EV_RES_POST_DESERIALIZE, cb)
        conn.negotiate()
        self.assertTrue(callback_future.result(timeout=2))

    def test_pre_post_recv(self):
        pre_callback_future = model.Future()
        post_callback_future = model.Future()
        expected_bytes = []
        expected_rounds = [1,2]
        def pre_cb(read_bytes):
            with pre_callback_future:
                expected_bytes.insert(0, read_bytes)
                self.assertGreater(read_bytes, 3)
                pre_callback_future.complete(True)
        def post_cb(data):
            with post_callback_future:
                self.assertEqual(expected_bytes.pop(), len(data))
                expected_rounds.pop()
                if not expected_rounds:
                    post_callback_future.complete(True)
        conn = self.default_client.connect(self.server, self.port)
        conn.register_callback(model.EV_RES_PRE_RECV, pre_cb)
        conn.register_callback(model.EV_RES_POST_RECV, post_cb)
        conn.negotiate()
        self.assertTrue(pre_callback_future.result(timeout=2))
        self.assertTrue(post_callback_future.result(timeout=2))
