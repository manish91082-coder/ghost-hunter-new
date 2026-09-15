import tempfile
import unittest
from pathlib import Path

from phantomx.economic_proof import build_economic_proof
from phantomx.economics import CostBreakdown
from phantomx.execution import ExecutionState
from phantomx.execution_coordinator import ExecutionCoordinatorError, prepare_signed_execution
from phantomx.executor_authority import ExecutorAuthorityEvidence, runtime_code_binding_hash
from phantomx.executor_calldata import executor_route_commitment
from phantomx.quote_engine import ExactQuote
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import simulate_two_leg
from phantomx.governor import GovernorPolicy
from phantomx.signer import EthereumEip1559Signer
from phantomx.sqlite_execution_store import SQLiteExecutionStore
from phantomx.hashing import keccak256_hex
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
        self.authority = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=SENDER,
            observed_block=self.block + 1,
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

    def _run(self, *, policy=None, signer=None, authority=None, authority_reuse_policy=None, reservation_id="res-test", current_block=None):
        return prepare_signed_execution(
            store=self.store,
            simulation=self.simulation,
            economic_proof=self.proof,
            executor=EXECUTOR,
            sender=SENDER,
            executor_authority=authority or self.authority,
            authority_evidence_reuse_policy=authority_reuse_policy or self.authority_reuse_policy,
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
            current_block_number=self.block + 1 if current_block is None else current_block,
            ai_rank="0.88",
            reservation_id=reservation_id,
        )

    def test_full_preparation_reserves_binds_governs_signs_and_persists(self):
        signer = FakeSigner()
        prepared = self._run(signer=signer)
        self.assertEqual(signer.calls, 1)
        self.assertEqual(prepared.reservation.nonce, 7)
        self.assertEqual(prepared.reservation.intent_hash, prepared.assembly.intent_hash)
        self.assertEqual(prepared.authority.evidence_hash, self.authority.evidence_hash)
        self.assertTrue(prepared.governor.approved)
        self.assertEqual(prepared.transaction_record.state, ExecutionState.SIGNED)
        durable = self.store.get_transaction(prepared.transaction_record.record_hash())
        self.assertEqual(durable.tx_hash, prepared.signed_transaction.transaction_hash)
        self.assertEqual(self.store.get_nonce(SENDER, 7).status.value, "SIGNED")

    def test_complete_artifact_chain_reaches_signed_artifact(self):
        prepared = self._run(reservation_id="res-chain-cert")
        assembly = prepared.assembly
        intent = assembly.intent
        envelope = assembly.envelope
        signed = prepared.signed_transaction

        self.assertEqual(assembly.simulation.route_hash, assembly.bound_call.bound_intent.route_hash)
        self.assertEqual(assembly.economic_proof.route_hash, assembly.simulation.route_hash)
        self.assertEqual(
            assembly.bound_call.route_commitment,
            executor_route_commitment(
                route_hash=assembly.simulation.route_hash,
                topology_hash=assembly.bound_call.topology_hash,
            ),
        )
        self.assertEqual(intent.economic_proof_hash, assembly.economic_proof.proof_hash)
        self.assertEqual(intent.simulation_proof_hash, assembly.simulation_proof_hash)
        self.assertEqual(intent.calldata_hash, envelope.calldata_hash)
        self.assertEqual(intent.intent_hash(), prepared.governor.intent_hash)
        self.assertEqual(prepared.governor.route_hash, intent.route_hash)
        self.assertEqual(prepared.governor.economic_proof_hash, intent.economic_proof_hash)
        self.assertEqual(prepared.governor.simulation_proof_hash, intent.simulation_proof_hash)
        self.assertEqual(prepared.governor.calldata_hash, envelope.calldata_hash)
        self.assertEqual(prepared.governor.executor_authority_hash, prepared.authority.evidence_hash)
        self.assertEqual(prepared.preflight.intent_hash, intent.intent_hash())
        self.assertEqual(prepared.preflight.route_hash, intent.route_hash)
        self.assertEqual(prepared.preflight.economic_proof_hash, intent.economic_proof_hash)
        self.assertEqual(prepared.preflight.simulation_proof_hash, intent.simulation_proof_hash)
        self.assertEqual(prepared.preflight.calldata_hash, envelope.calldata_hash)
        self.assertEqual(prepared.preflight.authority_evidence_hash, prepared.authority.evidence_hash)
        self.assertEqual(signed.intent_hash, intent.intent_hash())
        self.assertEqual(signed.governor_decision_hash, prepared.governor.decision_hash)
        self.assertEqual(signed.executor_runtime_binding_hash, runtime_code_binding_hash(prepared.authority))
        self.assertEqual(signed.transaction_hash, keccak256_hex(signed.raw_transaction))
        self.assertEqual(prepared.transaction_record.tx_hash, signed.transaction_hash)
        self.assertEqual(prepared.transaction_record.intent_hash, intent.intent_hash())
        self.assertEqual(prepared.transaction_record.calldata_hash, envelope.calldata_hash)
        self.assertEqual(prepared.transaction_record.nonce, envelope.nonce)
        self.assertEqual(prepared.transaction_record.sender.lower(), envelope.sender.lower())
        self.assertEqual(prepared.transaction_record.executor.lower(), envelope.executor.lower())

    def test_invalid_executor_authority_releases_before_nonce_reservation(self):
        signer = FakeSigner()
        bad_authority = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner="0x" + "99" * 20,
            observed_block=self.block + 1,
            runtime_code_hash=RUNTIME_CODE_HASH,
        )
        with self.assertRaises(ExecutionCoordinatorError):
            self._run(authority=bad_authority, signer=signer, reservation_id="res-bad-authority")
        self.assertEqual(signer.calls, 0)
        with self.assertRaises(Exception):
            self.store.get_nonce(SENDER, 7)

    def test_stale_executor_authority_is_rejected_before_nonce_reservation(self):
        signer = FakeSigner()
        stale = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=SENDER,
            observed_block=self.block - 1,
            runtime_code_hash=RUNTIME_CODE_HASH,
        )
        with self.assertRaises(ExecutionCoordinatorError):
            self._run(authority=stale, signer=signer, reservation_id="res-stale-authority")
        self.assertEqual(signer.calls, 0)
        with self.assertRaises(Exception):
            self.store.get_nonce(SENDER, 7)

    def test_replayed_authority_is_rejected_by_freshness_window_before_nonce_reservation(self):
        signer = FakeSigner()
        replayed = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=SENDER,
            observed_block=self.block - 10,
            runtime_code_hash=RUNTIME_CODE_HASH,
        )
        with self.assertRaises(ExecutionCoordinatorError):
            self._run(
                authority=replayed,
                signer=signer,
                authority_reuse_policy=AuthorityEvidenceReusePolicy(maximum_age_blocks=2),
                reservation_id="res-replayed-authority",
            )
        self.assertEqual(signer.calls, 0)
        with self.assertRaises(Exception):
            self.store.get_nonce(SENDER, 7)

    def test_future_authority_is_rejected_by_freshness_window_before_nonce_reservation(self):
        signer = FakeSigner()
        future = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=SENDER,
            observed_block=self.block + 2,
            runtime_code_hash=RUNTIME_CODE_HASH,
        )
        with self.assertRaises(ExecutionCoordinatorError):
            self._run(
                authority=future,
                signer=signer,
                authority_reuse_policy=AuthorityEvidenceReusePolicy(maximum_age_blocks=2),
                reservation_id="res-future-authority",
            )
        self.assertEqual(signer.calls, 0)
        with self.assertRaises(Exception):
            self.store.get_nonce(SENDER, 7)

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
