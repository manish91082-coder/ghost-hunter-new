import unittest
from dataclasses import replace

from phantomx.executor_authority import ExecutorAuthorityError, ExecutorAuthorityEvidence, observe_executor_authority, observe_executor_authority_quorum, runtime_code_binding_hash, verify_executor_authority
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

    def test_runtime_code_binding_is_stable_across_block_observations(self):
        later = replace(self.evidence, observed_block=2000, evidence_hash="")
        self.assertEqual(runtime_code_binding_hash(self.evidence), runtime_code_binding_hash(later))

    def test_runtime_code_binding_changes_when_code_identity_changes(self):
        changed = replace(self.evidence, runtime_code_hash="0x" + "66" * 32, evidence_hash="")
        self.assertNotEqual(runtime_code_binding_hash(self.evidence), runtime_code_binding_hash(changed))

    def test_runtime_code_binding_changes_when_owner_changes(self):
        changed = replace(self.evidence, owner=OTHER, evidence_hash="")
        self.assertNotEqual(runtime_code_binding_hash(self.evidence), runtime_code_binding_hash(changed))

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
        changed_provenance = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=OWNER,
            observed_block=1000,
            runtime_code_hash=CODE_HASH,
            attesting_provider_names=("rpc-a",),
        )
        self.assertNotEqual(changed_provenance.evidence_hash, self.evidence.evidence_hash)
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

    def test_attesting_provider_names_must_be_unique(self):
        with self.assertRaisesRegex(ExecutorAuthorityError, "unique"):
            ExecutorAuthorityEvidence(
                schema_version=1,
                chain_id=137,
                executor=EXECUTOR,
                owner=OWNER,
                observed_block=1000,
                runtime_code_hash=CODE_HASH,
                attesting_provider_names=("rpc-a", "rpc-a"),
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
        self.assertEqual(observed.attesting_provider_names, ("authority",))

    def test_quorum_observation_uses_one_common_block_and_consensus_owner_and_code(self):
        calls = []

        def make_transport(block: int, owner: str = OWNER, code: bytes = CODE):
            def transport(method, *params):
                calls.append((block, method, params))
                if method == "eth_chainId":
                    return {"result": "0x89"}
                if method == "eth_blockNumber":
                    return {"result": hex(block)}
                if method == "eth_call":
                    self.assertEqual(params[1], "0x3e8")
                    return {"result": "0x" + "00" * 12 + owner[2:]}
                if method == "eth_getCode":
                    self.assertEqual(params[1], "0x3e8")
                    return {"result": "0x" + code.hex()}
                raise AssertionError(method)
            return transport

        observed = observe_executor_authority_quorum(
            [
                RPCProvider("rpc-a", make_transport(1000)),
                RPCProvider("rpc-b", make_transport(1001)),
                RPCProvider("rpc-c", make_transport(1002)),
            ],
            EXECUTOR,
            quorum=2,
        )
        self.assertEqual(observed.observed_block, 1000)
        self.assertEqual(observed.owner, OWNER)
        self.assertEqual(observed.runtime_code_hash, CODE_HASH)
        self.assertEqual(observed.attesting_provider_names, ("rpc-a", "rpc-b", "rpc-c"))
        self.assertEqual(
            {item[1] for item in calls},
            {"eth_call", "eth_chainId", "eth_getCode", "eth_blockNumber"},
        )

    def test_quorum_provenance_contains_only_consensus_attesters(self):
        def make_transport(owner: str):
            def transport(method, *params):
                if method == "eth_chainId":
                    return {"result": "0x89"}
                if method == "eth_blockNumber":
                    return {"result": "0x3e8"}
                if method == "eth_call":
                    return {"result": "0x" + "00" * 12 + owner[2:]}
                if method == "eth_getCode":
                    return {"result": "0x" + CODE.hex()}
                raise AssertionError(method)
            return transport

        observed = observe_executor_authority_quorum(
            [
                RPCProvider("rpc-a", make_transport(OWNER)),
                RPCProvider("rpc-b", make_transport(OWNER)),
                RPCProvider("rpc-c", make_transport(OTHER)),
            ],
            EXECUTOR,
            quorum=2,
        )
        self.assertEqual(observed.attesting_provider_names, ("rpc-a", "rpc-b"))

    def test_quorum_rejects_ambiguous_split_consensus(self):
        def make_transport(owner: str):
            def transport(method, *params):
                if method == "eth_chainId":
                    return {"result": "0x89"}
                if method == "eth_blockNumber":
                    return {"result": "0x3e8"}
                if method == "eth_call":
                    return {"result": "0x" + "00" * 12 + owner[2:]}
                if method == "eth_getCode":
                    return {"result": "0x" + CODE.hex()}
                raise AssertionError(method)
            return transport

        with self.assertRaisesRegex(ExecutorAuthorityError, "ambiguous"):
            observe_executor_authority_quorum(
                [
                    RPCProvider("rpc-a", make_transport(OWNER)),
                    RPCProvider("rpc-b", make_transport(OWNER)),
                    RPCProvider("rpc-c", make_transport(OTHER)),
                    RPCProvider("rpc-d", make_transport(OTHER)),
                ],
                EXECUTOR,
                quorum=2,
            )

    def test_quorum_rejects_insufficient_agreement(self):
        def make_transport(owner: str):
            def transport(method, *params):
                if method == "eth_chainId":
                    return {"result": "0x89"}
                if method == "eth_blockNumber":
                    return {"result": "0x3e8"}
                if method == "eth_call":
                    return {"result": "0x" + "00" * 12 + owner[2:]}
                if method == "eth_getCode":
                    return {"result": "0x" + CODE.hex()}
                raise AssertionError(method)
            return transport

        with self.assertRaisesRegex(ExecutorAuthorityError, "quorum not reached"):
            observe_executor_authority_quorum(
                [
                    RPCProvider("rpc-a", make_transport(OWNER)),
                    RPCProvider("rpc-b", make_transport(OTHER)),
                    RPCProvider("rpc-c", make_transport(OTHER)),
                ],
                EXECUTOR,
                quorum=3,
            )

    def test_quorum_rejects_duplicate_provider_names(self):
        with self.assertRaisesRegex(ExecutorAuthorityError, "unique"):
            observe_executor_authority_quorum(
                [
                    RPCProvider("same", lambda method, *params: {"result": "0x89"}),
                    RPCProvider("same", lambda method, *params: {"result": "0x89"}),
                ],
                EXECUTOR,
                quorum=1,
            )

    def test_quorum_rejects_wrong_chain_provider(self):
        def transport(chain: str):
            def inner(method, *params):
                if method == "eth_chainId":
                    return {"result": chain}
                return {"result": "0x3e8"}
            return inner

        with self.assertRaisesRegex(ExecutorAuthorityError, "unexpected chain"):
            observe_executor_authority_quorum(
                [
                    RPCProvider("polygon", transport("0x89")),
                    RPCProvider("ethereum", transport("0x1")),
                ],
                EXECUTOR,
                quorum=1,
            )

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
