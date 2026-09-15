import unittest
from dataclasses import replace

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.durable_nonce import NonceStatus
from phantomx.durable_recovery import DurableRecoveryError, persist_recovery_observation
from phantomx.execution import ExecutionState
from phantomx.execution_observation import persist_chain_observation
from phantomx.execution_submission import submit_prepared_execution

from tests.phase19.test_execution_submission import ExecutionSubmissionTests, FakeRelay


class DurableRecoveryTests(unittest.TestCase):
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
        self.tx_hash = self.prepared.signed_transaction.transaction_hash
        self.intent = self.prepared.assembly.intent
        self.nonce = self.intent.nonce

    def _observation(self, state, *, replacement=None, tx_hash=None):
        return ObservationDecision(
            state=state,
            tx_hash=tx_hash or self.tx_hash,
            replacement_tx_hash=replacement,
            evidence_reason=f"test {state.value.lower()} evidence",
        )

    def test_drop_is_durably_terminal_and_eligible_for_replacement_review(self):
        result = persist_recovery_observation(
            store=self.store,
            intent=self.intent,
            observation=self._observation(ChainObservationState.DROPPED),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
        )
        self.assertEqual(result.action.value, "ELIGIBLE_FOR_REPLACEMENT_REVIEW")
        self.assertEqual(result.transaction_state, ExecutionState.DROPPED)
        self.assertEqual(result.nonce_state, NonceStatus.DROPPED)
        self.assertEqual(self.store.get_transaction(self.prepared.transaction_record.record_hash()).state, ExecutionState.DROPPED)
        self.assertEqual(self.store.get_nonce(self.intent.sender, self.nonce).status, NonceStatus.DROPPED)

    def test_drop_without_nonce_advancement_is_rejected(self):
        with self.assertRaises(DurableRecoveryError):
            persist_recovery_observation(
                store=self.store,
                intent=self.intent,
                observation=self._observation(ChainObservationState.DROPPED),
                tx_nonce=self.nonce,
                pending_nonce=self.nonce,
            )

    def test_explicit_replacement_is_durably_recorded_without_submitting_it(self):
        replacement_hash = "0x" + "ab" * 32
        result = persist_recovery_observation(
            store=self.store,
            intent=self.intent,
            observation=self._observation(ChainObservationState.REPLACED, replacement=replacement_hash),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
        )
        self.assertEqual(result.action.value, "REVIEW_REPLACEMENT")
        self.assertEqual(result.transaction_state, ExecutionState.REPLACED)
        self.assertEqual(result.nonce_state, NonceStatus.REPLACED)
        self.assertEqual(self.store.get_transaction(self.prepared.transaction_record.record_hash()).state, ExecutionState.REPLACED)
        self.assertEqual(self.store.get_nonce(self.intent.sender, self.nonce).status, NonceStatus.REPLACED)

    def test_recovery_binds_replacement_record_to_observed_transaction_hash(self):
        replacement_hash = "0x" + "bb" * 32
        replacement_record = replace(
            self.prepared.transaction_record,
            tx_hash=replacement_hash,
            state=ExecutionState.PRIVATE_SUBMITTED,
            replacement_of=self.prepared.transaction_record.tx_hash,
        )
        payload = replacement_record.canonical()
        with self.store._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO transaction_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    replacement_record.record_hash(),
                    payload["intent_hash"],
                    payload["authorization_hash"],
                    payload["reservation_id"],
                    payload["chain_id"],
                    payload["sender"],
                    payload["executor"],
                    payload["nonce"],
                    payload["calldata_hash"],
                    payload["gas_limit"],
                    payload["max_fee_per_gas"],
                    payload["max_priority_fee_per_gas"],
                    payload["tx_hash"],
                    payload["state"],
                    payload["replacement_of"],
                ),
            )
            db.execute("COMMIT")

        result = persist_recovery_observation(
            store=self.store,
            intent=self.intent,
            observation=self._observation(
                ChainObservationState.REPLACED,
                tx_hash=replacement_hash,
                replacement="0x" + "cc" * 32,
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
        )
        self.assertEqual(result.transaction_record_hash, replacement_record.record_hash())
        self.assertEqual(self.store.get_transaction(self.prepared.transaction_record.record_hash()).state, ExecutionState.SIGNED if False else ExecutionState.PRIVATE_SUBMITTED)
        self.assertEqual(self.store.get_transaction(replacement_record.record_hash()).state, ExecutionState.REPLACED)

    def test_reorg_moves_included_record_to_reorged_and_reobservation_can_recover(self):
        persist_chain_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                state=ChainObservationState.INCLUDED,
                tx_hash=self.tx_hash,
                replacement_tx_hash=None,
                evidence_reason="canonical successful receipt",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
            block_hash="0x" + "11" * 32,
            block_number=7000,
            canonical_block_hash="0x" + "11" * 32,
        )
        reorged = persist_recovery_observation(
            store=self.store,
            intent=self.intent,
            observation=self._observation(ChainObservationState.REORGED),
            tx_nonce=self.nonce,
            block_hash="0x" + "11" * 32,
            block_number=7000,
            canonical_block_hash="0x" + "22" * 32,
        )
        self.assertEqual(reorged.transaction_state, ExecutionState.REORGED)
        self.assertEqual(reorged.nonce_state, NonceStatus.REORGED)
        pending = persist_chain_observation(
            store=self.store,
            intent=self.intent,
            observation=ObservationDecision(
                state=ChainObservationState.PENDING,
                tx_hash=self.tx_hash,
                replacement_tx_hash=None,
                evidence_reason="reobserved pending after reorg",
            ),
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 0,
        )
        self.assertEqual(pending.transaction_state, ExecutionState.PENDING)
        self.assertEqual(pending.nonce_state, NonceStatus.SUBMITTED)

    def test_reorg_requires_changed_canonical_identity(self):
        with self.assertRaises(DurableRecoveryError):
            persist_recovery_observation(
                store=self.store,
                intent=self.intent,
                observation=self._observation(ChainObservationState.REORGED),
                tx_nonce=self.nonce,
                block_hash="0x" + "11" * 32,
                block_number=7000,
                canonical_block_hash="0x" + "11" * 32,
            )

    def test_duplicate_recovery_evidence_is_idempotent(self):
        observation = self._observation(ChainObservationState.DROPPED)
        kwargs = dict(
            store=self.store,
            intent=self.intent,
            observation=observation,
            tx_nonce=self.nonce,
            pending_nonce=self.nonce + 1,
        )
        first = persist_recovery_observation(**kwargs)
        second = persist_recovery_observation(**kwargs)
        self.assertEqual(first.sequence, second.sequence)
        self.assertEqual(first.evidence_hash, second.evidence_hash)


if __name__ == "__main__":
    unittest.main(verbosity=2)
