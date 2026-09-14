import unittest
from dataclasses import replace

from phantomx.executor_authority import ExecutorAuthorityError, ExecutorAuthorityEvidence, observe_executor_authority, verify_executor_authority
from phantomx.hashing import keccak256_hex
from phantomx.polygon_rpc import RPCProvider

EXECUTOR = "0x" + "aa" * 20
OWNER = "0x" + "bb" * 20
OTHER = "0x" + "cc" * 20
CODE = b"\x60\x01\x60\x00\x55"
CODE_HASH = keccak256_hex(CODE)


class ExecutorAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.evidence = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=OWNER,
            observed_block=1000,
            runtime_code_hash=CODE_HASH,
        )

    def test_valid_authority_matches_exact_executor_and_sender(self):
        verify_executor_authority(
            self.evidence,
            chain_id=137,
            executor=EXECUTOR,
            sender=OWNER,
            minimum_observed_block=999,
        )

    def test_owner_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ExecutorAuthorityError, "owner"):
            verify_executor_authority(self.evidence, chain_id=137, executor=EXECUTOR, sender=OTHER)

    def test_executor_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ExecutorAuthorityError, "executor"):
            verify_executor_authority(self.evidence, chain_id=137, executor=OTHER, sender=OWNER)

    def test_chain_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ExecutorAuthorityError, "chain"):
            verify_executor_authority(self.evidence, chain_id=1, executor=EXECUTOR, sender=OWNER)

    def test_stale_observation_is_rejected(self):
        with self.assertRaisesRegex(ExecutorAuthorityError, "predates"):
            verify_executor_authority(self.evidence, chain_id=137, executor=EXECUTOR, sender=OWNER, minimum_observed_block=1001)

    def test_evidence_hash_is_deterministic_and_bound(self):
        same = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR.upper().replace("0X", "0x"),
            owner=OWNER,
            observed_block=1000,
            runtime_code_hash=CODE_HASH.upper().replace("0X", "0x"),
        )
        self.assertEqual(same.evidence_hash, self.evidence.evidence_hash)
        with self.assertRaisesRegex(ExecutorAuthorityError, "evidence hash mismatch"):
            ExecutorAuthorityEvidence(
                schema_version=1,
                chain_id=137,
                executor=EXECUTOR,
                owner=OWNER,
                observed_block=1000,
                runtime_code_hash=CODE_HASH,
                evidence_hash="0x" + "99" * 32,
            )

    def test_observer_binds_owner_and_code_to_one_block(self):
        block = "0x3e8"
        def transport(method, *params):
            if method == "eth_chainId":
                return {"result": "0x89"}
            if method == "eth_blockNumber":
                return {"result": block}
            if method == "eth_call":
                self.assertEqual(params[0], {"to": EXECUTOR, "data": "0x8da5cb5b"})
                self.assertEqual(params[1], block)
                return {"result": "0x" + "00" * 12 + OWNER[2:]}
            if method == "eth_getCode":
                self.assertEqual(params[0], EXECUTOR)
                self.assertEqual(params[1], block)
                return {"result": "0x" + CODE.hex()}
            raise AssertionError(method)
        observed = observe_executor_authority(RPCProvider("authority", transport), EXECUTOR)
        self.assertEqual(observed.chain_id, 137)
        self.assertEqual(observed.executor, EXECUTOR)
        self.assertEqual(observed.owner, OWNER)
        self.assertEqual(observed.observed_block, 1000)
        self.assertEqual(observed.runtime_code_hash, CODE_HASH)

    def test_observer_rejects_wrong_chain(self):
        def transport(method, *params):
            self.assertEqual(method, "eth_chainId")
            return {"result": "0x1"}
        with self.assertRaisesRegex(ExecutorAuthorityError, "unexpected chain"):
            observe_executor_authority(RPCProvider("wrong", transport), EXECUTOR)

    def test_observer_rejects_noncanonical_owner_word(self):
        def transport(method, *params):
            if method == "eth_chainId":
                return {"result": "0x89"}
            if method == "eth_blockNumber":
                return {"result": "0x3e8"}
            if method == "eth_call":
                return {"result": "0x1234"}
            raise AssertionError(method)
        with self.assertRaisesRegex(ExecutorAuthorityError, "canonical ABI"):
            observe_executor_authority(RPCProvider("bad-owner", transport), EXECUTOR)

    def test_observer_rejects_empty_runtime_code(self):
        def transport(method, *params):
            if method == "eth_chainId":
                return {"result": "0x89"}
            if method == "eth_blockNumber":
                return {"result": "0x3e8"}
            if method == "eth_call":
                return {"result": "0x" + "00" * 12 + OWNER[2:]}
            if method == "eth_getCode":
                return {"result": "0x"}
            raise AssertionError(method)
        with self.assertRaisesRegex(ExecutorAuthorityError, "runtime code"):
            observe_executor_authority(RPCProvider("empty-code", transport), EXECUTOR)

    def test_runtime_code_hash_is_bytes_hash_not_text_hash(self):
        text_hash = keccak256_hex(("0x" + CODE.hex()).encode())
        self.assertNotEqual(self.evidence.runtime_code_hash, text_hash)
        self.assertEqual(self.evidence.runtime_code_hash, CODE_HASH)


if __name__ == "__main__":
    unittest.main(verbosity=2)