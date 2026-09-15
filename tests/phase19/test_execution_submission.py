import tempfile
import unittest
from pathlib import Path
from dataclasses import replace

from phantomx.economic_proof import build_economic_proof
from phantomx.economics import CostBreakdown
from phantomx.execution import ExecutionState
from phantomx.execution_coordinator import prepare_signed_execution
from phantomx.execution_submission import ExecutionSubmissionError, submit_prepared_execution
from phantomx.executor_authority import ExecutorAuthorityEvidence
from phantomx.governor import GovernorPolicy
from phantomx.hashing import keccak256_hex
from phantomx.quote_engine import ExactQuote
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.signer import EthereumEip1559Signer
from phantomx.sqlite_execution_store import SQLiteExecutionStore
from phantomx.durable_nonce import NonceStatus
from phantomx.route_simulator import simulate_two_leg
from phantomx.production_authority_evidence import AuthorityEvidenceReusePolicy

TOKEN_A = "0x" + "aa" * 20
TOKEN_B = "0x" + "bb" * 20
EXECUTOR = "0x" + "cc" * 20
PRIVATE_KEY = "0x" + "01" * 32
SENDER = EthereumEip1559Signer(PRIVATE_KEY).address
AAVE_POOL = "0x" + "11" * 20
QUICKSWAP = "0x" + "22" * 20
UNISWAP = "0x" + "33" * 20
VALUATION = "0x" + "44" * 32
RUNTIME_CODE_HASH = "0x" + "55" * 32


class FakeSigner:
    def __init__(self):
        self.calls = 0
        self._signer = EthereumEip1559Signer(PRIVATE_KEY)
        self.address = self._signer.address

    def sign(self, envelope):
        self.calls += 1
        return self._signer.sign(envelope)


class FakeRelay:
    def __init__(self, *, private=True, returned_hash=None, fail=False):
        self.name = "fake-private-relay"
        self.is_private = private
        self.returned_hash = returned_hash
        self.fail = fail
        self.calls = 0

    def submit_raw_transaction(self, raw_transaction):
        self.calls += 1
        if self.fail:
            raise RuntimeError("relay unavailable")
        return self.returned_hash or keccak256_hex(raw_transaction)


class ExecutionSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SQLiteExecutionStore(Path(self.tmp.name) / "execution.sqlite3")
        self.now = 1_700_000_000
        block = 5000
        leg_one = QuoteSnapshot.from_exact_quote(
            ExactQuote("QuickSwapV2", TOKEN_A, TOKEN_B, 100, 110, block, 3),
            chain_id=137,
            observed_at_unix=self.now,
            pool_or_router=QUICKSWAP,
            gas_estimate=100_000,
        )
        leg_two = QuoteSnapshot.from_exact_quote(
            ExactQuote("UniswapV3", TOKEN_B, TOKEN_A, 110, 101, block, 3000),
            chain_id=137,
            observed_at_unix=self.now,
            pool_or_router=UNISWAP,
            gas_estimate=120_000,
        )
        self.simulation = simulate_two_leg(leg_one, leg_two)
        self.authority = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=SENDER,
            observed_block=block + 1,
            runtime_code_hash=RUNTIME_CODE_HASH,
        )
        self.authority_reuse_policy = AuthorityEvidenceReusePolicy(maximum_age_blocks=2)
        self.proof = build_economic_proof(
            route_hash=self.simulation.route_hash,
            quote_hashes=tuple(leg.quote_hash for leg in self.simulation.legs),
            valuation_hash=VALUATION,
            final_settlement_usd="101.00",
            loan_principal_usd="100.00",
            costs=CostBreakdown(flash_loan_fee="0.05", dex_fees="0.02", gas="0.01", relay="0.01", other="0.01"),
            max_gas_usd="0.01",
            max_relay_usd="0.01",
        )
        self.policy = GovernorPolicy(
            live_execution_enabled=True,
            approved_executors=(EXECUTOR,),
            approved_senders=(SENDER,),
            allowed_loan_assets=(TOKEN_A,),
            allowed_route_hashes=(self.simulation.route_hash,),
            max_gas_limit=300_000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=30,
            max_gas_usd="0.01",
            max_relay_usd="0.01",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _prepare(self):
        return prepare_signed_execution(
            store=self.store,
            simulation=self.simulation,
            economic_proof=self.proof,
            executor=EXECUTOR,
            sender=SENDER,
            executor_authority=self.authority,
            authority_evidence_reuse_policy=self.authority_reuse_policy,
            chain_pending_nonce=7,
            deadline=self.now + 60,
            first_on_quickswap=True,
            amount_out_min_first=100,
            amount_out_min_second=95,
            minimum_surplus=1,
            aave_pool=AAVE_POOL,
            quickswap_router=QUICKSWAP,
            uniswap_v3_router=UNISWAP,
            gas_limit=300_000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=30,
            policy=self.policy,
            signer=FakeSigner(),
            now=self.now,
            current_block_number=5001,
            reservation_id="res-submit",
        )

    def _submit(self, prepared, relay=None, authority=None, store=None):
        return submit_prepared_execution(
            store=store or self.store,
            prepared=prepared,
            relay=relay or FakeRelay(),
            now=self.now,
            submission_authority=authority or self.authority,
        )

    def test_private_submission_updates_both_durable_states(self):
        prepared = self._prepare()
        relay = FakeRelay()
        submitted = self._submit(prepared, relay=relay)
        self.assertEqual(relay.calls, 1)
        self.assertEqual(submitted.transaction_state, ExecutionState.PRIVATE_SUBMITTED)
        self.assertEqual(submitted.nonce_state, NonceStatus.SUBMITTED)
        self.assertEqual(self.store.get_transaction(prepared.transaction_record.record_hash()).state, ExecutionState.PRIVATE_SUBMITTED)
        nonce = self.store.get_nonce(SENDER, 7)
        self.assertEqual(nonce.status, NonceStatus.SUBMITTED)
        self.assertEqual(nonce.tx_hash, prepared.signed_transaction.transaction_hash)

    def test_repeated_submission_of_already_submitted_artifact_is_blocked_before_network(self):
        prepared = self._prepare()
        first_relay = FakeRelay()
        self._submit(prepared, relay=first_relay)
        retry_relay = FakeRelay()
        with self.assertRaisesRegex(ExecutionSubmissionError, "not in SIGNED state before private submission"):
            self._submit(prepared, relay=retry_relay)
        self.assertEqual(first_relay.calls, 1)
        self.assertEqual(retry_relay.calls, 0)
        self.assertEqual(self.store.get_transaction(prepared.transaction_record.record_hash()).state, ExecutionState.PRIVATE_SUBMITTED)
        self.assertEqual(self.store.get_nonce(SENDER, 7).status, NonceStatus.SUBMITTED)

    def test_ambiguous_relay_failure_is_durably_held_and_retry_is_blocked(self):
        prepared = self._prepare()
        failing_relay = FakeRelay(fail=True)
        with self.assertRaisesRegex(ExecutionSubmissionError, "outcome is uncertain"):
            self._submit(prepared, relay=failing_relay)
        self.assertEqual(failing_relay.calls, 1)
        self.assertEqual(
            self.store.get_transaction(prepared.transaction_record.record_hash()).state,
            ExecutionState.SUBMISSION_IN_FLIGHT,
        )
        reopened = SQLiteExecutionStore(self.store.path)
        retry_relay = FakeRelay()
        with self.assertRaisesRegex(ExecutionSubmissionError, "not in SIGNED state before private submission"):
            self._submit(prepared, relay=retry_relay, store=reopened)
        self.assertEqual(retry_relay.calls, 0)

    def test_relay_hash_mismatch_is_durably_held_for_reconciliation(self):
        prepared = self._prepare()
        relay = FakeRelay(returned_hash="0x" + "99" * 32)
        with self.assertRaisesRegex(ExecutionSubmissionError, "outcome is uncertain"):
            self._submit(prepared, relay=relay)
        self.assertEqual(
            self.store.get_transaction(prepared.transaction_record.record_hash()).state,
            ExecutionState.SUBMISSION_IN_FLIGHT,
        )

    def test_later_observation_with_same_runtime_identity_is_accepted(self):
        prepared = self._prepare()
        later = replace(self.authority, observed_block=self.authority.observed_block + 2, evidence_hash="")
        relay = FakeRelay()
        submitted = self._submit(prepared, relay=relay, authority=later)
        self.assertEqual(relay.calls, 1)
        self.assertEqual(submitted.transaction_state, ExecutionState.PRIVATE_SUBMITTED)

    def test_runtime_code_drift_is_rejected_before_network_and_durable_transition(self):
        prepared = self._prepare()
        mutated = replace(self.authority, observed_block=self.authority.observed_block + 1, runtime_code_hash="0x" + "66" * 32, evidence_hash="")
        relay = FakeRelay()
        with self.assertRaisesRegex(ExecutionSubmissionError, "runtime identity differs"):
            self._submit(prepared, relay=relay, authority=mutated)
        self.assertEqual(relay.calls, 0)
        self.assertEqual(self.store.get_transaction(prepared.transaction_record.record_hash()).state, ExecutionState.SIGNED)
        self.assertEqual(self.store.get_nonce(SENDER, 7).status, NonceStatus.SIGNED)

    def test_owner_drift_is_rejected_before_network_and_durable_transition(self):
        prepared = self._prepare()
        mutated = replace(self.authority, observed_block=self.authority.observed_block + 1, owner="0x" + "22" * 20, evidence_hash="")
        relay = FakeRelay()
        with self.assertRaises(ExecutionSubmissionError):
            self._submit(prepared, relay=relay, authority=mutated)
        self.assertEqual(relay.calls, 0)
        self.assertEqual(self.store.get_transaction(prepared.transaction_record.record_hash()).state, ExecutionState.SIGNED)

    def test_older_submission_observation_is_rejected_before_network(self):
        prepared = self._prepare()
        stale = replace(self.authority, observed_block=self.authority.observed_block - 2, evidence_hash="")
        relay = FakeRelay()
        with self.assertRaises(ExecutionSubmissionError):
            self._submit(prepared, relay=relay, authority=stale)
        self.assertEqual(relay.calls, 0)

    def test_public_relay_is_rejected_before_network_call(self):
        prepared = self._prepare()
        relay = FakeRelay(private=False)
        with self.assertRaises(ExecutionSubmissionError):
            self._submit(prepared, relay=relay)
        self.assertEqual(relay.calls, 0)
        self.assertEqual(self.store.get_transaction(prepared.transaction_record.record_hash()).state, ExecutionState.SIGNED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
