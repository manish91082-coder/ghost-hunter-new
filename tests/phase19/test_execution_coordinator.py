import tempfile
import unittest
from pathlib import Path

from phantomx.economic_proof import build_economic_proof
from phantomx.economics import CostBreakdown
from phantomx.execution import ExecutionState
from phantomx.execution_coordinator import ExecutionCoordinatorError, prepare_signed_execution
from phantomx.quote_engine import ExactQuote
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import simulate_two_leg
from phantomx.governor import GovernorPolicy
from phantomx.signer import EthereumEip1559Signer
from phantomx.sqlite_execution_store import SQLiteExecutionStore

TOKEN_A = "0x" + "aa" * 20
TOKEN_B = "0x" + "bb" * 20
EXECUTOR = "0x" + "cc" * 20
PRIVATE_KEY = "0x" + "01" * 32
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


class ExecutionCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SQLiteExecutionStore(Path(self.tmp.name) / "execution.sqlite3")
        self.block = 5000
        self.now = 1_700_000_000
        leg_one = QuoteSnapshot.from_exact_quote(
            ExactQuote("QuickSwapV2", TOKEN_A, TOKEN_B, 100, 110, self.block, 3),
            chain_id=137,
            observed_at_unix=self.now,
            pool_or_router=QUICKSWAP,
            gas_estimate=100_000,
        )
        leg_two = QuoteSnapshot.from_exact_quote(
            ExactQuote("UniswapV3", TOKEN_B, TOKEN_A, 110, 101, self.block, 3000),
            chain_id=137,
            observed_at_unix=self.now,
            pool_or_router=UNISWAP,
            gas_estimate=120_000,
        )
        self.simulation = simulate_two_leg(leg_one, leg_two)
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

    def _run(self, *, policy=None, signer=None, reservation_id="res-test"):
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
            policy=policy or self.policy,
            signer=signer or FakeSigner(),
            now=self.now,
            current_block_number=self.block + 1,
            ai_rank="0.88",
            reservation_id=reservation_id,
        )

    def test_full_preparation_reserves_binds_governs_signs_and_persists(self):
        signer = FakeSigner()
        prepared = self._run(signer=signer)
        self.assertEqual(signer.calls, 1)
        self.assertEqual(prepared.reservation.nonce, 7)
        self.assertEqual(prepared.reservation.intent_hash, prepared.assembly.intent_hash)
        self.assertTrue(prepared.governor.approved)
        self.assertEqual(prepared.transaction_record.state, ExecutionState.SIGNED)
        durable = self.store.get_transaction(prepared.transaction_record.record_hash())
        self.assertEqual(durable.tx_hash, prepared.signed_transaction.transaction_hash)
        self.assertEqual(self.store.get_nonce(SENDER, 7).status.value, "SIGNED")

    def test_governor_block_releases_unsigned_reservation_and_never_signs(self):
        signer = FakeSigner()
        with self.assertRaises(ExecutionCoordinatorError):
            self._run(policy=GovernorPolicy(
                live_execution_enabled=False,
                approved_executors=(EXECUTOR,),
                approved_senders=(SENDER,),
                allowed_loan_assets=(TOKEN_A,),
                allowed_route_hashes=(self.simulation.route_hash,),
                max_gas_limit=300_000,
                max_fee_per_gas=100,
                max_priority_fee_per_gas=30,
                max_gas_usd="0.01",
                max_relay_usd="0.01",
            ), signer=signer, reservation_id="res-blocked")
        self.assertEqual(signer.calls, 0)
        self.assertEqual(self.store.get_nonce(SENDER, 7).status.value, "RELEASED")

    def test_two_reservations_cannot_share_nonce_and_second_uses_next_sequence(self):
        first = self._run(reservation_id="res-first")
        signer = FakeSigner()
        second = self._run(signer=signer, reservation_id="res-second")
        self.assertEqual(first.reservation.nonce, 7)
        self.assertEqual(second.reservation.nonce, 8)
        self.assertEqual(self.store.get_nonce(SENDER, 8).status.value, "SIGNED")


if __name__ == "__main__":
    unittest.main(verbosity=2)