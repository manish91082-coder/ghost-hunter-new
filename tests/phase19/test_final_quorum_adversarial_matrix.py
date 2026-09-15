import ast
import unittest
from dataclasses import replace

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.durable_nonce import NonceStatus
from phantomx.durable_recovery import DurableRecoveryError, persist_quorum_recovery_observation
from phantomx.economics import CostBreakdown
from phantomx.execution import ExecutionState
from phantomx.execution_observation import persist_quorum_chain_observation
from phantomx.execution_reconciliation import ExecutionReconciliationError, reconcile_quorum_included_execution
from phantomx.production_chain_observation import QuorumChainObservation
from phantomx.production_chain_observation_store import ProductionChainObservationStoreError, persist_quorum_chain_observation as persist_quorum_evidence, require_quorum_chain_observation
from phantomx.settlement import ReceiptRecord
from phantomx.sqlite_execution_store import SQLiteExecutionStore
from phantomx.execution_submission import submit_prepared_execution
from tests.phase19.test_execution_submission import ExecutionSubmissionTests, FakeRelay

OLD_BLOCK = "0x" + "11" * 32
BAD_BLOCK = "0x" + "22" * 32
REPLACEMENT = "0x" + "33" * 32
OTHER_TX = "0x" + "44" * 32


class FinalQuorumAdversarialMatrixTests(unittest.TestCase):
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

    def _obs(self, state, *, replacement=None, tx_hash=None):
        return ObservationDecision(state, tx_hash or self.tx_hash, replacement, f"final {state.value.lower()} evidence")

    def _quorum(self, obs, *, block=100, providers=("provider-a", "provider-b")):
        return QuorumChainObservation(1, 137, obs.tx_hash, obs, block, providers)

    def _admit(self, quorum):
        return persist_quorum_evidence(store=self.store, intent_hash=self.intent.intent_hash(), observation=quorum)

    def test_pending_and_reverted_are_quorum_gated(self):
        pending = self._obs(ChainObservationState.PENDING)
        pending_q = self._quorum(pending)
        self._admit(pending_q)
        pending_result = persist_quorum_chain_observation(
            store=self.store, intent=self.intent, quorum_observation=pending_q, observation=pending,
            tx_nonce=self.intent.nonce, pending_nonce=self.intent.nonce + 1,
            current_observed_block=105, maximum_age_blocks=5, minimum_attesting_providers=2,
        )
        self.assertEqual(pending_result.transaction_state, ExecutionState.PENDING)

        self.fixture.tearDown()
        self.fixture = ExecutionSubmissionTests(); self.fixture.setUp(); self.addCleanup(self.fixture.tearDown)
        self.store = self.fixture.store; self.prepared = self.fixture._prepare()
        submit_prepared_execution(store=self.store, prepared=self.prepared, relay=FakeRelay(), now=self.fixture.now, submission_authority=self.prepared.authority)
        self.intent = self.prepared.assembly.intent; self.tx_hash = self.prepared.signed_transaction.transaction_hash
        reverted = self._obs(ChainObservationState.REVERTED)
        reverted_q = self._quorum(reverted)
        self._admit(reverted_q)
        reverted_result = persist_quorum_chain_observation(
            store=self.store, intent=self.intent, quorum_observation=reverted_q, observation=reverted,
            tx_nonce=self.intent.nonce, pending_nonce=self.intent.nonce + 1,
            current_observed_block=105, maximum_age_blocks=5, minimum_attesting_providers=2,
            block_hash=OLD_BLOCK, block_number=100, canonical_block_hash=OLD_BLOCK,
        )
        self.assertEqual(reverted_result.transaction_state, ExecutionState.PROFIT_FAILED)

    def test_tampered_future_stale_and_single_provider_evidence_is_blocked(self):
        obs = self._obs(ChainObservationState.INCLUDED)
        for quorum, message in (
            (self._quorum(obs, block=106), "future-dated"),
            (self._quorum(obs, block=99), "stale"),
        ):
            self._admit(quorum)
            with self.assertRaisesRegex(ProductionChainObservationStoreError, message):
                require_quorum_chain_observation(store=self.store, intent_hash=self.intent.intent_hash(), observation=quorum, current_observed_block=105, maximum_age_blocks=5, minimum_attesting_providers=2)
        single = self._quorum(obs, providers=("provider-a",))
        self._admit(single)
        with self.assertRaisesRegex(ProductionChainObservationStoreError, "below policy"):
            require_quorum_chain_observation(store=self.store, intent_hash=self.intent.intent_hash(), observation=single, current_observed_block=105, maximum_age_blocks=5, minimum_attesting_providers=2)
        tampered = replace(obs, evidence_reason="tampered")
        tampered_q = self._quorum(tampered)
        with self.assertRaises(ProductionChainObservationStoreError):
            require_quorum_chain_observation(store=self.store, intent_hash=self.intent.intent_hash(), observation=tampered_q, current_observed_block=105, maximum_age_blocks=5, minimum_attesting_providers=2)

    def test_settlement_requires_canonical_block_and_rejects_conflict(self):
        obs = self._obs(ChainObservationState.INCLUDED)
        quorum = self._quorum(obs)
        self._admit(quorum)
        persist_quorum_chain_observation(
            store=self.store, intent=self.intent, quorum_observation=quorum, observation=obs,
            tx_nonce=self.intent.nonce, pending_nonce=self.intent.nonce + 1,
            current_observed_block=105, maximum_age_blocks=5, minimum_attesting_providers=2,
            block_hash=OLD_BLOCK, block_number=6000, canonical_block_hash=OLD_BLOCK,
        )
        common = dict(
            store=self.store, intent=self.intent, quorum_observation=quorum, observation=obs,
            current_observed_block=105, maximum_age_blocks=5, minimum_attesting_providers=2,
            receipt=ReceiptRecord(self.tx_hash, 1, 21_000, 100, 6000), block_hash=OLD_BLOCK,
            final_settlement="101.00", flash_repayment="100.00", costs=CostBreakdown(gas="0.01", relay="0.01"),
        )
        with self.assertRaisesRegex(ExecutionReconciliationError, "not canonical"):
            reconcile_quorum_included_execution(**common, canonical_block_hash=BAD_BLOCK)
        good = reconcile_quorum_included_execution(**common, canonical_block_hash=OLD_BLOCK)
        same = reconcile_quorum_included_execution(**common, canonical_block_hash=OLD_BLOCK)
        self.assertEqual(good.settlement_record.record_hash, same.settlement_record.record_hash)
        with self.assertRaises(ExecutionReconciliationError):
            reconcile_quorum_included_execution(**dict(common, canonical_block_hash=OLD_BLOCK, final_settlement="101.01"))

    def test_recovery_drop_replacement_reorg_require_quorum(self):
        drop = self._obs(ChainObservationState.DROPPED)
        single = self._quorum(drop, providers=("provider-a",))
        self._admit(single)
        with self.assertRaisesRegex(DurableRecoveryError, "fresh quorum evidence"):
            persist_quorum_recovery_observation(
                store=self.store, intent=self.intent, quorum_observation=single, observation=drop,
                tx_nonce=self.intent.nonce, current_observed_block=105, maximum_age_blocks=5,
                minimum_attesting_providers=2, pending_nonce=self.intent.nonce + 1,
            )
        fresh = self._quorum(drop)
        self._admit(fresh)
        result = persist_quorum_recovery_observation(
            store=self.store, intent=self.intent, quorum_observation=fresh, observation=drop,
            tx_nonce=self.intent.nonce, current_observed_block=105, maximum_age_blocks=5,
            minimum_attesting_providers=2, pending_nonce=self.intent.nonce + 1,
        )
        self.assertEqual(result.nonce_state, NonceStatus.DROPPED)

    def test_quorum_evidence_survives_restart(self):
        obs = self._obs(ChainObservationState.PENDING)
        quorum = self._quorum(obs)
        self._admit(quorum)
        restarted = SQLiteExecutionStore(self.store.path)
        admitted = require_quorum_chain_observation(
            store=restarted, intent_hash=self.intent.intent_hash(), observation=quorum,
            current_observed_block=105, maximum_age_blocks=5, minimum_attesting_providers=2,
        )
        self.assertEqual(admitted.evidence_hash, quorum.evidence_hash)

    def test_low_level_mutation_primitives_have_only_intended_callers(self):
        root = __import__("pathlib").Path(__file__).resolve().parents[2] / "phantomx"
        callers = {"persist_recovery_observation": [], "reconcile_included_execution": []}
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else None
                    if name in callers:
                        callers[name].append(path.name)
        self.assertEqual(callers["persist_recovery_observation"], ["durable_recovery.py"])
        self.assertEqual(callers["reconcile_included_execution"], ["execution_reconciliation.py"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
