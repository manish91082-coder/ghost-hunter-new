import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.execution_observation import (
    persist_quorum_chain_observation,
)
from phantomx.production_chain_observation import QuorumChainObservation
from phantomx.production_chain_observation_store import (
    PersistedQuorumChainObservation,
    ProductionChainObservationStoreError,
)
from phantomx.sqlite_execution_store import SQLiteExecutionStore

TX = "0x" + "11" * 32
INTENT = "0x" + "22" * 32


class QuorumExecutionObservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SQLiteExecutionStore(Path(self.tmp.name) / "execution.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def _quorum(self, state=ChainObservationState.INCLUDED, replacement=None):
        decision = ObservationDecision(state, TX, replacement, "quorum evidence")
        return QuorumChainObservation(
            schema_version=1,
            chain_id=137,
            tx_hash=TX,
            decision=decision,
            common_observed_block=100,
            attesting_provider_names=("a", "b"),
        )

    def _observation(self, state=ChainObservationState.INCLUDED, replacement=None):
        return ObservationDecision(state, TX, replacement, "full chain evidence")

    @patch("phantomx.execution_observation.persist_chain_observation")
    @patch("phantomx.execution_observation.require_quorum_chain_observation")
    def test_requires_quorum_admission_before_lifecycle_persistence(self, require, persist):
        quorum = self._quorum()
        observation = self._observation()
        admitted = PersistedQuorumChainObservation(
            sequence=7,
            intent_hash=INTENT,
            tx_hash=TX,
            state=ChainObservationState.INCLUDED,
            chain_id=137,
            common_observed_block=100,
            attesting_provider_names=("a", "b"),
            evidence_hash=quorum.evidence_hash,
        )
        require.return_value = admitted
        persist.return_value = object()

        result = persist_quorum_chain_observation(
            store=self.store,
            intent=object(),
            quorum_observation=quorum,
            observation=observation,
            tx_nonce=7,
            current_observed_block=105,
            maximum_age_blocks=5,
            minimum_attesting_providers=2,
            block_hash="0x" + "33" * 32,
            block_number=999,
            canonical_block_hash="0x" + "33" * 32,
        )

        self.assertIs(result, persist.return_value)
        require.assert_called_once()
        persist.assert_called_once()
        self.assertEqual(require.call_args.kwargs["minimum_attesting_providers"], 2)
        self.assertEqual(persist.call_args.kwargs["tx_nonce"], 7)

    def test_single_provider_evidence_can_be_refused_by_admission_policy(self):
        quorum = self._quorum()
        quorum = QuorumChainObservation(
            schema_version=1,
            chain_id=137,
            tx_hash=TX,
            decision=quorum.decision,
            common_observed_block=100,
            attesting_provider_names=("a",),
        )
        from phantomx.production_chain_observation_store import persist_quorum_chain_observation as persist_quorum
        persist_quorum(store=self.store, intent_hash=INTENT, observation=quorum)
        with self.assertRaises(ProductionChainObservationStoreError):
            from phantomx.production_chain_observation_store import require_quorum_chain_observation
            require_quorum_chain_observation(
                store=self.store,
                intent_hash=INTENT,
                observation=quorum,
                current_observed_block=100,
                maximum_age_blocks=5,
                minimum_attesting_providers=2,
            )

    @patch("phantomx.execution_observation.require_quorum_chain_observation")
    def test_mismatched_state_is_blocked_before_admission(self, require):
        quorum = self._quorum(ChainObservationState.INCLUDED)
        with self.assertRaises(ValueError):
            persist_quorum_chain_observation(
                store=self.store,
                intent=object(),
                quorum_observation=quorum,
                observation=self._observation(ChainObservationState.REVERTED),
                tx_nonce=7,
                current_observed_block=100,
                maximum_age_blocks=5,
            )
        require.assert_not_called()

    @patch("phantomx.execution_observation.require_quorum_chain_observation")
    def test_replacement_binding_is_blocked_before_admission(self, require):
        quorum = self._quorum(ChainObservationState.REPLACED, replacement="0x" + "44" * 32)
        with self.assertRaises(ValueError):
            persist_quorum_chain_observation(
                store=self.store,
                intent=object(),
                quorum_observation=quorum,
                observation=self._observation(ChainObservationState.REPLACED, replacement="0x" + "55" * 32),
                tx_nonce=7,
                current_observed_block=100,
                maximum_age_blocks=5,
            )
        require.assert_not_called()


if __name__ == "__main__":
    unittest.main()
