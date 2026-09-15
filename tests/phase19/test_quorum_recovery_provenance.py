import ast
import unittest
from pathlib import Path

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.durable_nonce import NonceStatus
from phantomx.durable_recovery import (
    DurableRecoveryError,
    persist_chain_observation,
    persist_quorum_recovery_observation,
)
from phantomx.execution import ExecutionState
from phantomx.production_chain_observation import QuorumChainObservation
from phantomx.production_chain_observation_store import persist_quorum_chain_observation
from phantomx.execution_submission import submit_prepared_execution

from tests.phase19.test_execution_submission import ExecutionSubmissionTests, FakeRelay


OLD_BLOCK = "0x" + "11" * 32
NEW_BLOCK = "0x" + "22" * 32
REPLACEMENT = "0x" + "33" * 32
OTHER_TX = "0x" + "44" * 32


class QuorumRecoveryProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ExecutionSubmissionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store = self.fixture.store
        self.prepared = self.fixture._prepare()
        submit_prepared_execution(
            store=self.store,
            prepared=self.prepared,
            relay=FakeRelay(),
            now=self.fixture.now,
            submission_authority=self.prepared.authority,
        )
        self.intent = self.prepared.assembly.intent
        self.tx_hash = self.prepared.signed_transaction.transaction_hash
        self.nonce = self.intent.nonce

    def _observation(self, state, *, tx_hash=None, replacement=None, reason=None):
        return ObservationDecision(
            state=state,
            tx_hash=tx_hash or self.tx_hash,
            replacement_tx_hash=replacement,
            evidence_reason=reason or f"quorum {state.value.lower()} evidence",
        )

    def _quorum(self, observation, *, block=100, providers=("provider-a", "provider-b")):
        return QuorumChainObservation(
            schema_version=1,
            chain_id=137,
            tx_hash=observation.tx_hash,
            decision=observation,
            common_observed_block=block,
            attesting_provider_names=providers,
        )

    def _admit(self, quorum):
        return persist_quorum_chain_observation(
            store=self.store,
            intent_hash=self.intent.intent_hash(),
            observation=quorum,
        )

    def _recover(self, observation, quorum, **overrides):
        kwargs = dict(
            store=self.store,
            intent=self.intent,
            quorum_observation=quorum,
            observation=observation,
            tx_nonce=self.nonce,
            current_observed_block=105,
            maximum_age_blocks=5,
            minimum_attesting_providers=2,
        )
        kwargs.update(overrides)
        return persist_quorum_recovery_observation(**kwargs)

    def test_single_provider_drop_is_blocked_before_durable_mutation(self):
        observation = self._observation(ChainObservationState.DROPPED)
        quorum = self._quorum(observation, providers=("provider-a",))
        self._admit(quorum)
        with self.assertRaisesRegex(DurableRecoveryError, "fresh quorum evidence"):
            self._recover(observation, quorum, pending_nonce=self.nonce + 1)
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.PRIVATE_SUBMITTED,
        )
        self.assertEqual(self.store.get_nonce(self.intent.sender, self.nonce).status, NonceStatus.SUBMITTED)

    def test_fresh_two_provider_drop_is_admitted_and_mutates_once(self):
        observation = self._observation(ChainObservationState.DROPPED)
        quorum = self._quorum(observation)
        self._admit(quorum)
        result = self._recover(observation, quorum, pending_nonce=self.nonce + 1)
        self.assertEqual(result.transaction_state, ExecutionState.DROPPED)
        self.assertEqual(result.nonce_state, NonceStatus.DROPPED)

    def test_stale_quorum_blocks_replacement_recovery(self):
        observation = self._observation(ChainObservationState.REPLACED, replacement=REPLACEMENT)
        quorum = self._quorum(observation, block=99)
        self._admit(quorum)
        with self.assertRaisesRegex(DurableRecoveryError, "fresh quorum evidence"):
            self._recover(observation, quorum, pending_nonce=self.nonce + 1)
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.PRIVATE_SUBMITTED,
        )

    def test_future_quorum_blocks_reorg_recovery(self):
        persist_chain_observation(
            store=self.store,
            intent=self.intent,
            observation=self._observation(ChainObservationState.INCLUDED, reason="prior canonical inclusion"),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
            block_hash=OLD_BLOCK,
            block_number=7000,
            canonical_block_hash=OLD_BLOCK,
        )
        observation = self._observation(ChainObservationState.REORGED)
        quorum = self._quorum(observation, block=106)
        self._admit(quorum)
        with self.assertRaisesRegex(DurableRecoveryError, "fresh quorum evidence"):
            self._recover(
                observation,
                quorum,
                block_hash=OLD_BLOCK,
                block_number=7000,
                canonical_block_hash=NEW_BLOCK,
            )
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.INCLUDED,
        )

    def test_replacement_binding_mismatch_is_blocked_before_admission(self):
        admitted = self._observation(ChainObservationState.REPLACED, replacement=REPLACEMENT)
        quorum = self._quorum(admitted)
        self._admit(quorum)
        mismatched = self._observation(ChainObservationState.REPLACED, replacement=OTHER_TX)
        with self.assertRaisesRegex(DurableRecoveryError, "replacement binding mismatch"):
            self._recover(mismatched, quorum, pending_nonce=self.nonce + 1)
        self.assertEqual(
            self.store.get_transaction(self.prepared.transaction_record.record_hash()).state,
            ExecutionState.PRIVATE_SUBMITTED,
        )

    def test_two_provider_reorg_requires_changed_canonical_identity_and_is_admitted(self):
        persist_chain_observation(
            store=self.store,
            intent=self.intent,
            observation=self._observation(ChainObservationState.INCLUDED, reason="prior canonical inclusion"),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
            block_hash=OLD_BLOCK,
            block_number=7000,
            canonical_block_hash=OLD_BLOCK,
        )
        observation = self._observation(ChainObservationState.REORGED)
        quorum = self._quorum(observation)
        self._admit(quorum)
        result = self._recover(
            observation,
            quorum,
            block_hash=OLD_BLOCK,
            block_number=7000,
            canonical_block_hash=NEW_BLOCK,
        )
        self.assertEqual(result.transaction_state, ExecutionState.REORGED)
        self.assertEqual(result.nonce_state, NonceStatus.REORGED)

    def test_production_modules_have_no_direct_quorum_bypass_to_low_level_recovery(self):
        root = Path(__file__).resolve().parents[2] / "phantomx"
        direct_callers = []
        for path in sorted(root.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if isinstance(func, ast.Name) and func.id == "persist_recovery_observation":
                    direct_callers.append(path.name)
                elif isinstance(func, ast.Attribute) and func.attr == "persist_recovery_observation":
                    direct_callers.append(path.name)
        self.assertEqual(direct_callers, ["durable_recovery.py"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
