import tempfile
import unittest
from pathlib import Path

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.durable_nonce import NonceStatus
from phantomx.durable_recovery import persist_recovery_observation
from phantomx.execution import ExecutionState
from phantomx.execution_submission import submit_prepared_execution
from phantomx.replacement_coordinator import ReplacementCoordinatorError, prepare_replacement_execution
from phantomx.replacement_policy import ReplacementFeePolicy
from phantomx.sqlite_execution_store import SQLiteExecutionStore

from tests.phase19.test_execution_submission import ExecutionSubmissionTests, FakeRelay


class ReplacementCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ExecutionSubmissionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store = self.fixture.store
        self.prepared = self.fixture._prepare()
        self.policy = ReplacementFeePolicy(
            min_bump_bps=11000,
            max_fee_multiplier_bps=12500,
            max_absolute_fee_per_gas=150,
            max_priority_fee_per_gas=50,
        )
        self.dropped = persist_recovery_observation(
            store=self.store,
            intent=self.prepared.assembly.intent,
            observation=ObservationDecision(
                state=ChainObservationState.DROPPED,
                tx_hash=self.prepared.signed_transaction.transaction_hash,
                replacement_tx_hash=None,
                evidence_reason="pending nonce advanced beyond submitted nonce",
            ),
            tx_nonce=self.prepared.assembly.intent.nonce,
            pending_nonce=self.prepared.assembly.intent.nonce + 1,
        )

    def _replacement(self, **overrides):
        values = dict(
            store=self.store,
            source_record_hash=self.prepared.transaction_record.record_hash(),
            simulation=self.prepared.assembly.simulation,
            economic_proof=self.prepared.assembly.economic_proof,
            replacement_policy=self.policy,
            executor=self.prepared.assembly.intent.executor,
            sender=self.prepared.assembly.intent.sender,
            executor_authority=self.prepared.authority,
            deadline=self.prepared.assembly.intent.deadline,
            first_on_quickswap=True,
            amount_out_min_first=100,
            amount_out_min_second=95,
            minimum_surplus=1,
            aave_pool="0x" + "11" * 20,
            quickswap_router="0x" + "22" * 20,
            uniswap_v3_router="0x" + "33" * 20,
            gas_limit=300_000,
            max_fee_per_gas=115,
            max_priority_fee_per_gas=35,
            policy=self.fixture.policy,
            signer=self.fixture_signer,
            now=self.fixture.now,
            current_block_number=5001,
        )
        values.update(overrides)
        return prepare_replacement_execution(**values)

    @property
    def fixture_signer(self):
        return self.fixture._prepare.__self__._ExecutionSubmissionTests__dict__.get("signer", None) if False else _Signer(self.fixture.PRIVATE_KEY if hasattr(self.fixture, "PRIVATE_KEY") else "0x" + "01" * 32)

    def test_drop_state_is_consumed_into_new_signed_replacement(self):
        replacement = self._replacement()
        self.assertEqual(replacement.source.state, ExecutionState.DROPPED)
        self.assertNotEqual(replacement.signed_transaction.transaction_hash, self.prepared.signed_transaction.transaction_hash)
        self.assertEqual(replacement.assembly.intent.nonce, self.prepared.assembly.intent.nonce)
        self.assertEqual(replacement.transaction_record.replacement_of, self.prepared.signed_transaction.transaction_hash)
        self.assertEqual(self.store.get_transaction(self.prepared.transaction_record.record_hash()).state, ExecutionState.DROPPED)
        self.assertEqual(self.store.get_transaction(replacement.transaction_record.record_hash()).state, ExecutionState.SIGNED)
        nonce = self.store.get_nonce(self.prepared.assembly.intent.sender, self.prepared.assembly.intent.nonce)
        self.assertEqual(nonce.status, NonceStatus.SIGNED)
        self.assertEqual(nonce.tx_hash, replacement.signed_transaction.transaction_hash)
        self.assertEqual(nonce.replacement_of, self.prepared.signed_transaction.transaction_hash)

    def test_replacement_can_be_submitted_through_existing_private_boundary(self):
        replacement = self._replacement()
        submitted = submit_prepared_execution(
            store=self.store,
            prepared=replacement,
            relay=FakeRelay(),
            now=self.fixture.now,
            submission_authority=self.prepared.authority,
        )
        self.assertEqual(submitted.transaction_state, ExecutionState.PRIVATE_SUBMITTED)
        self.assertEqual(submitted.nonce_state, NonceStatus.SUBMITTED)
        self.assertEqual(self.store.get_transaction(replacement.transaction_record.record_hash()).state, ExecutionState.PRIVATE_SUBMITTED)

    def test_fee_bump_policy_blocks_insufficient_replacement_before_signing(self):
        with self.assertRaisesRegex(ReplacementCoordinatorError, "minimum bump"):
            self._replacement(max_max_fee_per_gas=101)

    def test_replacement_requires_explicit_drop_or_replaced_source(self):
        fresh = self.fixture._prepare()
        with self.assertRaises(ReplacementCoordinatorError):
            prepare_replacement_execution(
                store=self.store,
                source_record_hash=fresh.transaction_record.record_hash(),
                simulation=fresh.assembly.simulation,
                economic_proof=fresh.assembly.economic_proof,
                replacement_policy=self.policy,
                executor=fresh.assembly.intent.executor,
                sender=fresh.assembly.intent.sender,
                executor_authority=fresh.authority,
                deadline=fresh.assembly.intent.deadline,
                first_on_quickswap=True,
                amount_out_min_first=100,
                amount_out_min_second=95,
                minimum_surplus=1,
                aave_pool="0x" + "11" * 20,
                quickswap_router="0x" + "22" * 20,
                uniswap_v3_router="0x" + "33" * 20,
                gas_limit=300_000,
                max_fee_per_gas=115,
                max_priority_fee_per_gas=35,
                policy=self.fixture.policy,
                signer=_Signer("0x" + "01" * 32),
                now=self.fixture.now,
                current_block_number=5001,
            )


class _Signer:
    def __init__(self, private_key):
        from phantomx.signer import EthereumEip1559Signer
        self._signer = EthereumEip1559Signer(private_key)
        self.address = self._signer.address

    def sign(self, envelope):
        return self._signer.sign(envelope)


if __name__ == "__main__":
    unittest.main(verbosity=2)
