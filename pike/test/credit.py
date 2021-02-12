#
# Copyright (c) 2017-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        credit.py
#
# Abstract:
#
#        credit tracking test cases
#
# Authors: Masen Furer <masen.furer@dell.com>
#

from __future__ import division
from __future__ import print_function
from builtins import map
from builtins import object
from builtins import range

import array
import random
import sys

import pike.model
import pike.smb2
import pike.test

# common size constants
size_64k = 2 ** 16
size_128k = 2 ** 17
size_192k = size_64k + size_128k
size_512k = 2 ** 19
size_960k = size_192k * 5
size_1m = 2 ** 20
size_2m = 2 ** 21
size_4m = 2 ** 22
size_8m = 2 ** 23

share_all = (
    pike.smb2.FILE_SHARE_READ | pike.smb2.FILE_SHARE_WRITE | pike.smb2.FILE_SHARE_DELETE
)
lease_rh = pike.smb2.SMB2_LEASE_READ_CACHING | pike.smb2.SMB2_LEASE_HANDLE_CACHING


# debugging callback functions which are registered if debug logging is enabled
def post_serialize_credit_assessment(nb):
    smb_res = nb[0]
    print(
        "{0} ({1}) ___ Charge: {2} / Request: {3} / Total: {4}".format(
            smb_res.command,
            smb_res.message_id,
            smb_res.credit_charge,
            smb_res.credit_request,
            nb.conn.credits,
        )
    )


def post_deserialize_credit_assessment(nb):
    smb_res = nb[0]
    print(
        "{0} ({1}) ___ Charge: {2} / Response: {3} / Total: {4}".format(
            smb_res.command,
            smb_res.message_id,
            smb_res.credit_charge,
            smb_res.credit_response,
            nb.conn.credits + smb_res.credit_response - smb_res.credit_charge,
        )
    )


def post_serialize_credit_assert(exp_credit_charge, future):
    def cb(nb):
        with future:
            if nb[0].credit_charge != exp_credit_charge:
                raise AssertionError(
                    "Expected credit_charge {0}. Actual {1}".format(
                        exp_credit_charge, nb[0].credit_charge
                    )
                )
            future.complete(True)

    return cb


@pike.test.RequireCapabilities(pike.smb2.SMB2_GLOBAL_CAP_LARGE_MTU)
class CreditTest(pike.test.PikeTest):
    def __init__(self, *args, **kwargs):
        super(CreditTest, self).__init__(*args, **kwargs)
        if self.loglevel == pike.test.logging.DEBUG:
            self.default_client.register_callback(
                pike.model.EV_REQ_POST_SERIALIZE, post_serialize_credit_assessment
            )
            self.default_client.register_callback(
                pike.model.EV_RES_POST_DESERIALIZE, post_deserialize_credit_assessment
            )

    # set the default credit request to 1 to make things more predictable
    def setUp(self):
        self.prev_default_credit_request = pike.model.default_credit_request
        pike.model.default_credit_request = 1

    def tearDown(self):
        pike.model.default_credit_request = self.prev_default_credit_request

    def generic_mc_write_mc_read(self, file_size, write_size, read_size):
        """
        perform multiple multi credit write operations requesting multiple
        credits in return
        then perform one large read operation and subsequently close the file
        """
        fname = self.id().rpartition(".")[-1]
        buf = b"\0\1\2\3\4\5\6\7" * 8192
        buflen = len(buf)
        file_chunks = file_size // buflen
        write_chunks = file_size // write_size
        write_buf = buf * (file_chunks // write_chunks)
        write_credits_per_op = write_size // size_64k
        chan, tree = self.tree_connect()
        starting_credits = chan.connection.negotiate_response.parent.credit_response
        self.info("creating {0} ({1} bytes)".format(fname, file_size))

        # get enough initial credits
        with chan.let(credit_request=16):
            fh = chan.create(tree, fname).result()

        self.info(
            "writing {0} chunks of {1} bytes; {2} credits per op".format(
                write_chunks, write_size, write_credits_per_op
            )
        )
        for ix in range(write_chunks):
            credit_assert_future = pike.model.Future()
            with chan.connection.callback(
                pike.model.EV_REQ_POST_SERIALIZE,
                post_serialize_credit_assert(
                    write_credits_per_op, credit_assert_future
                ),
            ):
                result = chan.write(fh, write_size * ix, write_buf)
            self.assertEqual(result, write_size)
            self.assertTrue(credit_assert_future.result())
        chan.close(fh)

        # calculate a reasonable expected number of credits
        # from negotiate, session_setup (x2), tree_connect, create (+16), close
        exp_credits = (
            starting_credits + ((pike.model.default_credit_request - 1) * 4) + 15
        )
        credit_request_per_op = pike.model.default_credit_request
        # from the series of write requests
        if write_credits_per_op > credit_request_per_op:
            credit_request_per_op = write_credits_per_op
        exp_credits += write_chunks * (credit_request_per_op - write_credits_per_op)
        # windows seems to have a credit wall of 128
        if exp_credits > 128:
            exp_credits = 128
        self.info(
            "Expect the server to have granted at least "
            "{0} credits".format(exp_credits)
        )
        self.assertGreaterEqual(chan.connection.credits, exp_credits)

        read_chunks = file_size // read_size
        read_buf = buf * (file_chunks // read_chunks)
        read_credits_per_op = read_size // size_64k
        self.info(
            "reading {0} chunks of {1} bytes; {2} credits per op".format(
                read_chunks, read_size, read_credits_per_op
            )
        )
        fh = chan.create(
            tree,
            fname,
            access=pike.smb2.GENERIC_READ | pike.smb2.DELETE,
            disposition=pike.smb2.FILE_OPEN,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result()
        file_buffer = array.array("B")
        for ix in range(read_chunks):
            credit_assert_future = pike.model.Future()
            with chan.connection.callback(
                pike.model.EV_REQ_POST_SERIALIZE,
                post_serialize_credit_assert(read_credits_per_op, credit_assert_future),
            ):
                result = chan.read(fh, read_size, read_size * ix)
            file_buffer.extend(result)
            self.assertEqual(len(result), read_size)
            self.assertTrue(credit_assert_future.result())
        chan.close(fh)
        self.assertEqual(file_buffer.tobytes(), buf * file_chunks)

    def generic_arbitrary_mc_write_mc_read(self, file_size, write_size, read_size):
        """
        perform multiple multi credit write operations requesting multiple
        credits in return
        then perform one large read operation and subsequently close the file

        this version of the function works with arbitrary sizes
        """
        fname = self.id().rpartition(".")[-1]
        buf = b"\0\1\2\3\4\5\6\7" * 8192
        buflen = len(buf)
        file_chunks, file_remainder = divmod(file_size, buflen)
        file_buf = buf * file_chunks + buf[:file_remainder]

        write_chunks, write_remainder = divmod(file_size, write_size)
        write_credits_per_op, extra_credits = divmod(write_size, size_64k)
        if extra_credits > 0:
            write_credits_per_op += 1

        # if the sizes are not exact multiples, prepare to write an extra chunk
        extra_write = None
        if write_remainder > 0:
            c, extra_credits = divmod(write_remainder, size_64k)
            if extra_credits > 0:
                c += 1
            extra_write = (write_remainder, c)

        chan, tree = self.tree_connect()
        starting_credits = chan.connection.negotiate_response.parent.credit_response
        self.info("creating {0} ({1} bytes)".format(fname, file_size))

        # get enough initial credits
        with chan.let(credit_request=16):
            fh = chan.create(tree, fname).result()

        self.info(
            "writing {0} chunks of {1} bytes; {2} credits per op".format(
                write_chunks, write_size, write_credits_per_op
            )
        )
        ix = None
        # TODO: consolidate chunks to a list of tuples (file_offset, local_buffer_offset, length)
        # this would simplify the loop, instead of having the extra chunk
        # OR abstract the writing, asserting to a helper function (yeah better idea, retains the logic)
        for ix in range(write_chunks):
            credit_assert_future = pike.model.Future()
            with chan.connection.callback(
                pike.model.EV_REQ_POST_SERIALIZE,
                post_serialize_credit_assert(
                    write_credits_per_op, credit_assert_future
                ),
            ):
                result = chan.write(
                    fh,
                    write_size * ix,
                    file_buf[write_size * ix : write_size * (ix + 1)],
                )
            self.assertEqual(result, write_size)
            self.assertTrue(credit_assert_future.result())
        if extra_write is not None:
            if ix is None:
                extra_write_offset = 0
            else:
                extra_write_offset = write_size * (ix + 1)
                ix = None
            self.info(
                "writing extra chunk of {0} bytes @ {1}; {2} credits".format(
                    extra_write[0], extra_write_offset, extra_write[1]
                )
            )
            credit_assert_future = pike.model.Future()
            with chan.connection.callback(
                pike.model.EV_REQ_POST_SERIALIZE,
                post_serialize_credit_assert(extra_write[1], credit_assert_future),
            ):
                result = chan.write(fh, extra_write_offset, file_buf[-extra_write[0] :])
            self.assertEqual(result, extra_write[0])
            self.assertTrue(credit_assert_future.result())
        chan.close(fh)

        # calculate a reasonable expected number of credits
        # from negotiate, session_setup (x2), tree_connect, create (+16), close
        exp_credits = (
            starting_credits + ((pike.model.default_credit_request - 1) * 4) + 15
        )
        credit_request_per_op = pike.model.default_credit_request
        # from the series of write requests
        if write_credits_per_op > credit_request_per_op:
            credit_request_per_op = write_credits_per_op
        exp_credits += write_chunks * (credit_request_per_op - write_credits_per_op)
        # potential extra write request
        if extra_write is not None:
            credit_request_per_op = pike.model.default_credit_request
            if extra_write[1] > credit_request_per_op:
                credit_request_per_op = extra_write[1]
            exp_credits += credit_request_per_op - extra_write[1]
        # windows seems to have a credit wall of 128
        if exp_credits > 128:
            exp_credits = 128
        self.info(
            "Expect the server to have granted at least "
            "{0} credits".format(exp_credits)
        )
        self.assertGreaterEqual(chan.connection.credits, exp_credits)

        read_chunks, read_remainder = divmod(file_size, read_size)
        read_credits_per_op, extra_credits = divmod(read_size, size_64k)
        if extra_credits > 0:
            read_credits_per_op += 1

        # if the sizes are not exact multiples, prepare to read an extra chunk
        extra_read = None
        if read_remainder > 0:
            c, extra_credits = divmod(read_remainder, size_64k)
            if extra_credits > 0:
                c += 1
            extra_read = (read_remainder, c)

        self.info(
            "reading {0} chunks of {1} bytes; {2} credits per op".format(
                read_chunks, read_size, read_credits_per_op
            )
        )
        fh = chan.create(
            tree,
            fname,
            access=pike.smb2.GENERIC_READ | pike.smb2.DELETE,
            disposition=pike.smb2.FILE_OPEN,
            options=pike.smb2.FILE_DELETE_ON_CLOSE,
        ).result()
        read_buffer = array.array("B")
        for ix in range(read_chunks):
            credit_assert_future = pike.model.Future()
            with chan.connection.callback(
                pike.model.EV_REQ_POST_SERIALIZE,
                post_serialize_credit_assert(read_credits_per_op, credit_assert_future),
            ):
                result = chan.read(fh, read_size, read_size * ix)
            read_buffer.extend(result)
            self.assertEqual(len(result), read_size)
            self.assertTrue(credit_assert_future.result())
        if extra_read is not None:
            if ix is None:
                extra_read_offset = 0
            else:
                extra_read_offset = read_size * (ix + 1)
            self.info(
                "reading extra chunk of {0} bytes @ {1}; {2} credits".format(
                    extra_read[0], extra_read_offset, extra_read[1]
                )
            )
            credit_assert_future = pike.model.Future()
            with chan.connection.callback(
                pike.model.EV_REQ_POST_SERIALIZE,
                post_serialize_credit_assert(extra_read[1], credit_assert_future),
            ):
                result = chan.read(fh, extra_read[0], extra_read_offset)
            read_buffer.extend(result)
            self.assertEqual(len(result), extra_read[0])
            self.assertTrue(credit_assert_future.result())

        chan.close(fh)
        self.assertEqual(read_buffer.tobytes(), file_buf)


class PowerOf2CreditTest(CreditTest):
    def test_1_1m_write_1_1m_read(self):
        self.generic_mc_write_mc_read(size_1m, size_1m, size_1m)

    def test_16_512k_write_8_1m_read(self):
        self.generic_mc_write_mc_read(size_8m, size_512k, size_1m)

    def test_8_1m_write_64_128k_read(self):
        self.generic_mc_write_mc_read(size_8m, size_1m, size_128k)

    def test_4_1m_write_64_64k_read(self):
        self.generic_mc_write_mc_read(size_4m, size_1m, size_64k)

    def test_16_64k_write_1_1m_read(self):
        self.generic_mc_write_mc_read(size_1m, size_64k, size_1m)

    def test_16_128k_write_2_1m_read(self):
        self.generic_mc_write_mc_read(size_2m, size_128k, size_1m)

    def test_16_128k_write_4_512k_read(self):
        self.generic_mc_write_mc_read(size_2m, size_128k, size_512k)

    def test_5_192k_write_1_960k_read(self):
        self.generic_mc_write_mc_read(size_960k, size_192k, size_960k)


class EdgeCreditTest(CreditTest):
    def test_sequence_number_wrap(self):
        """
        one client performs requests until the sequence number is > 2048
        then exhausts it's remaining credits with a single large mtu
        multicredit op
        """
        fname = "test_sequence_number_wrap"
        # buf is 64k == 1 credit
        buf = b"\0\1\2\3\4\5\6\7" * 8192
        credits_per_req = 16
        sequence_number_target = 2080

        chan1, tree1 = self.tree_connect()
        starting_credits = chan1.connection.negotiate_response.parent.credit_response
        self.assertEqual(chan1.connection.credits, starting_credits)

        with chan1.let(credit_request=credits_per_req):
            fh1 = chan1.create(tree1, fname).result()
        exp_credits = starting_credits + credits_per_req - 1
        self.assertEqual(chan1.connection.credits, exp_credits)

        # build up the sequence number to the target
        while chan1.connection._next_mid < sequence_number_target:
            smb_req = chan1.write_request(fh1, 0, buf * credits_per_req).parent
            smb_future = chan1.connection.submit(smb_req.parent)[0]
            smb_resp = smb_future.result()
            if smb_future.interim_response:
                # if server granted credits on interim
                self.assertEqual(
                    smb_future.interim_response.credit_response, credits_per_req
                )
                # then server should grant 0 credits on final resp
                self.assertEqual(smb_resp.credit_response, 0)
            else:
                # otherwise, all credits should be granted in final response
                self.assertEqual(smb_resp.credit_response, credits_per_req)
            # if the server is granting our request,
            # then total number of credits should stay the same
            self.assertEqual(chan1.connection.credits, exp_credits)

        # at the end, next mid should be > target
        self.assertGreater(chan1.connection._next_mid, sequence_number_target)


class AsyncCreditTest(CreditTest):
    def test_async_lock(self):
        """
        establish 2 sessions
        session 1 opens file1 with exclusive lock
        session 2 opens file1 with 3 exclusive lock - allowing pending
        wait for all 3 lock requests to pend
        session 1 unlocks file1
        wait for all 3 lock requests to complete
        verify that credits were not double granted
        """
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        chan2_starting_credits = (
            chan2.connection.negotiate_response.parent.credit_response
        )
        fname = "test_async_lock"
        buf = b"\0\1\2\3\4\5\6\7"
        lock1 = (0, 8, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK)
        contend_locks = [
            (0, 2, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK),
            (2, 2, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK),
            (4, 4, pike.smb2.SMB2_LOCKFLAG_EXCLUSIVE_LOCK),
        ]
        credit_req = 3

        fh1 = chan1.create(tree1, fname, share=share_all).result()
        fh2 = chan2.create(tree2, fname, share=share_all).result()
        self.assertEqual(chan2.connection.credits, chan2_starting_credits)
        chan1.lock(fh1, [lock1]).result()

        # send 3 locks, 1 credit charge, 3 credit request
        lock_futures = []
        for l in contend_locks:
            with chan2.let(credit_request=credit_req):
                f = chan2.lock(fh2, [l])
                lock_futures.append(f)
        # wait for the interim responses
        for f in lock_futures:
            f.wait_interim()
            if f.interim_response is not None:
                self.assertEqual(f.interim_response.credit_response, credit_req)

        # at this point, we should have sent 3x 1charge, 3request lock commands
        exp_credits = chan2_starting_credits + len(contend_locks) * (credit_req - 1)
        self.assertEqual(chan2.connection.credits, exp_credits)

        # unlock fh1 locks
        lock1_un = tuple(list(lock1[:2]) + [pike.smb2.SMB2_LOCKFLAG_UN_LOCK])
        chan1.lock(fh1, [lock1_un])

        # these completion responses shouldn't have a carry a 1 credit charge + 0 grant
        for f in lock_futures:
            self.assertEqual(f.result().credit_response, 0)
        self.assertEqual(chan2.connection.credits, exp_credits)
        buf = b"\0\1\2\3\4\5\6\7" * 8192

        # send a request for all of our credits
        chan2.write(fh2, 0, buf * exp_credits)
        self.assertEqual(chan2.connection.credits, exp_credits)

        # send a request for all of our credits + 1 (this should disconnect the client)
        with self.assertRaises(EOFError):
            chan2.write(fh2, 0, buf * (exp_credits + 1))
            self.fail(
                "We should have {0} credits, but an {1} credit request succeeds".format(
                    exp_credits, exp_credits + 1
                )
            )

    def test_async_write(self):
        """
        establish 2 sessions
        session 1 opens file1 with read/handle caching lease
        session 2 opens file1 with no lease
        session 2 sends several large multi-credit writes triggering a lease break on session 1
        session 2 write requests will return STATUS_PENDING (server consumes credits)
        session 2 write requests should complete with STATUS_SUCCESS (server already consumed credit)
        """
        chan1, tree1 = self.tree_connect()
        chan2, tree2 = self.tree_connect()
        chan2_starting_credits = (
            chan2.connection.negotiate_response.parent.credit_response
        )
        fname = "test_async_write"
        lkey = array.array("B", map(random.randint, [0] * 16, [255] * 16))
        # buf is 64k
        buf = b"\0\1\2\3\4\5\6\7" * 8192
        write_request_multiples = [1, 2, 3, 4]
        credit_req = 16

        fh1 = chan1.create(
            tree1,
            fname,
            share=share_all,
            oplock_level=pike.smb2.SMB2_OPLOCK_LEVEL_LEASE,
            lease_key=lkey,
            lease_state=lease_rh,
        ).result()
        fh2 = chan2.create(tree2, fname, share=share_all).result()
        self.assertEqual(chan2.connection.credits, chan2_starting_credits)
        write_futures = []
        for n_credits in write_request_multiples:
            with chan2.let(credit_request=credit_req):
                f = chan2.connection.submit(
                    chan2.write_request(fh2, 0, buf * n_credits).parent.parent
                )[0]
                f.wait_interim()
                if f.interim_response is not None:
                    self.assertEqual(f.interim_response.credit_response, credit_req)
                write_futures.append(f)

        fh1.lease.on_break(lambda s: s)
        for w in write_futures:
            smb_resp = w.result()
            if smb_resp.flags & pike.smb2.SMB2_FLAGS_ASYNC_COMMAND:
                self.assertEqual(smb_resp.credit_response, 0)
            else:
                self.assertEqual(smb_resp.credit_response, credit_req)
        chan2.close(fh2)
        chan1.close(fh1)


class TestCaseGenerator(object):
    header = """#!/usr/bin/env python
import pike.test
import pike.test.credit


class Generated_{name}_{tag}(pike.test.credit.CreditTest):
    """
    footer = """if __name__ == "__main__":
    pike.test.unittest.main()
"""
    template = """
    def test_{name}_{tag}_{ix}(self):
        self.generic_arbitrary_mc_write_mc_read({file_size}, {write_size}, {read_size})"""

    @classmethod
    def generate_multiple_64k_test_cases(
        cls,
        tag,
        n_cases,
        size_range_multiple,
        write_range_multiple,
        read_range_multiple,
    ):
        name = "Mult64k"
        print(cls.header.format(**locals()))
        for ix in range(n_cases):
            file_size = 2 ** 16 * random.randint(*size_range_multiple)
            write_size = 2 ** 16 * random.randint(*write_range_multiple)
            read_size = 2 ** 16 * random.randint(*read_range_multiple)
            print(cls.template.format(**locals()))
        print(cls.footer.format(**locals()))

    @classmethod
    def generate_arbitrary_test_cases(
        cls, tag, n_cases, size_range, write_range, read_range
    ):
        name = "Arb"
        print(cls.header.format(**locals()))
        for ix in range(n_cases):
            file_size = random.randint(*size_range)
            write_size = random.randint(*write_range)
            read_size = random.randint(*read_range)
            print(cls.template.format(**locals()))
        print(cls.footer.format(**locals()))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    if len(sys.argv) > 1 and sys.argv[1].startswith("64"):
        TestCaseGenerator.generate_multiple_64k_test_cases(
            "gen1", 8, (1, 128), (1, 16), (1, 16)
        )
    else:
        TestCaseGenerator.generate_arbitrary_test_cases(
            "iter1", 32, (45 * 1024, 2 ** 23), (2 ** 15, 2 ** 20), (2 ** 15, 2 ** 20)
        )
