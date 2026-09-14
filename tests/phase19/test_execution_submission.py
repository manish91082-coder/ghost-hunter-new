import tempfile
import unittest
from pathlib import Path

from phantomx.economic_proof import build_economic_proof
from phantomx.economics import CostBreakdown
from phantomx.execution import ExecutionState
from phantomx.execution_coordinator import ExecutionCoordinatorError, prepare_signed_execution
from phantomx.execution_submission import ExecutionSubmissionError, submit_prepared_execution
from phantomx.governor import GovernorPolicy
from phantomx.hashing import keccak256_hex
from phantomx.quote_engine import ExactQuote
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.signer import EthereumEip1559Signer
from phantomx.sqlite_execution_store import SQLiteExecutionStore
from phantomx.durable_nonce import NonceStatus
from phantomx.route_simulator import simulate_two_leg

TOKEN_A = "0x" + "aa" * 20
TOKEN_B = "0x" + "bb" * 20
EXECUTOR = "0x" + "cc" * 20
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf3be6bd"
SENDER = EthereumEip1559Signer(PRIVATE_KEY).address
AAVE_POOL = "0x" + "11" * 20
QUICKSWAP = "0x" + "22" * 20
UNISWAP = "0x" + "33" * 20
VALUATION = "0x" + "44" * 32


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
        simulation = simulate_two_leg(leg_one, leg_two)
        self.simulation = simulation
        self.proof = build_economic_proof(
            route_hash=simulation.route_hash,
            quote_hashes=tuple(leg.quote_hash for leg in simulation.legs),
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
            allowed_route_hashes=(simulation.route_hash,),
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

    def test_private_submission_updates_both_durable_states(self):
        prepared = self._prepare()
        relay = FakeRelay()
        submitted = submit_prepared_execution(store=self.store, prepared=prepared, relay=relay, now=self.now)
        self.assertEqual(relay.calls, 1)
        self.assertEqual(submitted.transaction_state, ExecutionState.PRIVATE_SUBMITTED)
        self.assertEqual(submitted.nonce_state, NonceStatus.SUBMITTED)
        self.assertEqual(self.store.get_transaction(prepared.transaction_record.record_hash()).state, ExecutionState.PRIVATE_SUBMITTED)
        nonce = self.store.get_nonce(SENDER, 7)
        self.assertEqual(nonce.status, NonceStatus.SUBMITTED)
        self.assertEqual(nonce.tx_hash, prepared.signed_transaction.transaction_hash)

    def test_public_relay_is_rejected_before_network_call(self):
        prepared = self._prepare()
        relay = FakeRelay(private=False)
        with self.assertRaises(ExecutionSubmissionError):
            submit_prepared_execution(store=self.store, prepared=prepared, relay=relay, now=self.now)
        self.assertEqual(relay.calls, 0)
        self.assertEqual(self.store.get_transaction(prepared.transaction_record.record_hash()).state, ExecutionState.SIGNED)

    def test_relay_hash_mismatch_is_rejected_and_state_stays_signed(self):
        prepared = self._prepare()
        relay = FakeRelay(returned_hash="0x" + "99" * 32)
        with self.assertRaises(ExecutionSubmissionError):
            submit_prepared_execution(store=self.store, prepared=prepared, relay=relay, now=self.now)
        self.assertEqual(self.store.get_transaction(prepared.transaction_record.record_hash()).state, ExecutionState.SIGNED)
        self.assertEqual(self.store.get_nonce(SENDER, 7).status, NonceStatus.SIGNED)

    def test_relay_failure_keeps_durable_record_signed_for_chain_reconciliation(self):
        prepared = self._prepare()
        relay = FakeRelay(fail=True)
        with self.assertRaises(ExecutionSubmissionError):
            submit_prepared_execution(store=self.store, prepared=prepared, relay=relay, now=self.now)
        self.assertEqual(self.store.get_transaction(prepared.transaction_record.record_hash()).state, ExecutionState.SIGNED)
        self.assertEqual(self.store.get_nonce(SENDER, 7).status, NonceStatus.SIGNED)


if __name__ == "__main__":
    unittest.main(verbosity=2)