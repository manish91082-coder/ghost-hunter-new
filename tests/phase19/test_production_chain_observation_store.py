import tempfile
import unittest
from pathlib import Path

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.production_chain_observation import QuorumChainObservation
from phantomx.production_chain_observation_store import (
    ProductionChainObservationStoreError,
    persist_quorum_chain_observation,
    require_quorum_chain_observation,
)
from phantomx.sqlite_execution_store import SQLiteExecutionStore

TX = "0x" + "11" * 32
INTENT = "0x" + "22" * 32


def make_observation(state=ChainObservationState.INCLUDED, names=("a", "b"), block=100):
    decision = ObservationDecision(state, TX, None, "test evidence")
    return QuorumChainObservation(
        schema_version=1,
        chain_id=137,
        tx_hash=TX,
        decision=decision,
        common_observed_block=block,
        attesting_provider_names=tuple(names),
    )


class ProductionChainObservationStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SQLiteExecutionStore(Path(self.tmp.name) / "execution.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_persist_records_quorum_attesters_and_hash(self):
        obs = make_observation()
        row = persist_quorum_chain_observation(store=self.store, intent_hash=INTENT, observation=obs)
        self.assertEqual(row.attesting_provider_names, ("a", "b"))
        self.assertEqual(row.evidence_hash, obs.evidence_hash)

    def test_persist_is_idempotent_for_exact_evidence(self):
        obs = make_observation()
        first = persist_quorum_chain_observation(store=self.store, intent_hash=INTENT, observation=obs)
        second = persist_quorum_chain_observation(store=self.store, intent_hash=INTENT, observation=obs)
        self.assertEqual(first.sequence, second.sequence)

    def test_wrong_intent_hash_is_rejected(self):
        with self.assertRaises(ProductionChainObservationStoreError):
            persist_quorum_chain_observation(store=self.store, intent_hash="0x1234", observation=make_observation())

    def test_wrong_chain_is_rejected(self):
        bad = QuorumChainObservation(1, 1, TX, ObservationDecision(ChainObservationState.INCLUDED, TX, None, "test"), 100, ("a",))
        with self.assertRaises(ProductionChainObservationStoreError):
            persist_quorum_chain_observation(store=self.store, intent_hash=INTENT, observation=bad)

    def test_exact_fresh_reuse_is_accepted(self):
        obs = make_observation(block=100)
        persist_quorum_chain_observation(store=self.store, intent_hash=INTENT, observation=obs)
        row = require_quorum_chain_observation(
            store=self.store, intent_hash=INTENT, observation=obs,
            current_observed_block=105, maximum_age_blocks=5,
            minimum_attesting_providers=2,
        )
        self.assertEqual(row.common_observed_block, 100)

    def test_stale_reuse_is_rejected(self):
        obs = make_observation(block=100)
        persist_quorum_chain_observation(store=self.store, intent_hash=INTENT, observation=obs)
        with self.assertRaises(ProductionChainObservationStoreError):
            require_quorum_chain_observation(
                store=self.store, intent_hash=INTENT, observation=obs,
                current_observed_block=106, maximum_age_blocks=5,
            )

    def test_future_reuse_is_rejected(self):
        obs = make_observation(block=100)
        persist_quorum_chain_observation(store=self.store, intent_hash=INTENT, observation=obs)
        with self.assertRaises(ProductionChainObservationStoreError):
            require_quorum_chain_observation(
                store=self.store, intent_hash=INTENT, observation=obs,
                current_observed_block=99, maximum_age_blocks=5,
            )

    def test_attester_policy_is_enforced(self):
        obs = make_observation(names=("a",), block=100)
        persist_quorum_chain_observation(store=self.store, intent_hash=INTENT, observation=obs)
        with self.assertRaises(ProductionChainObservationStoreError):
            require_quorum_chain_observation(
                store=self.store, intent_hash=INTENT, observation=obs,
                current_observed_block=100, maximum_age_blocks=5,
                minimum_attesting_providers=2,
            )

    def test_tampered_evidence_is_not_found(self):
        obs = make_observation()
        persist_quorum_chain_observation(store=self.store, intent_hash=INTENT, observation=obs)
        tampered = make_observation(names=("a", "c"), block=100)
        with self.assertRaises(ProductionChainObservationStoreError):
            require_quorum_chain_observation(
                store=self.store, intent_hash=INTENT, observation=tampered,
                current_observed_block=100, maximum_age_blocks=5,
            )


if __name__ == "__main__":
    unittest.main()
