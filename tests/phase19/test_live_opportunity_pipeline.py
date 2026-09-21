import unittest
from decimal import Decimal

from phantomx.economic_proof import build_economic_proof
from phantomx.economics import CostBreakdown
from phantomx.executor_authority import ExecutorAuthorityEvidence
from phantomx.live_opportunity_pipeline import (
    LiveOpportunityPipelineError,
    discover_and_prepare_best_opportunity_execution,
    discover_prepare_and_preflight_best_opportunity,
)
from phantomx.quickswap_v2 import QuickSwapV2ExactQuoter
from phantomx.uniswap_v3 import UniswapV3ExactQuoter

ROUTER = "0x" + "11" * 20
FACTORY = "0x" + "22" * 20
QUOTER = "0x" + "33" * 20
A = "0x" + "aa" * 20
B = "0x" + "bb" * 20
POOL = "0x" + "cc" * 20


def array_result(amount_in, amount_out):
    values = (amount_in, amount_out)
    raw = bytearray((32).to_bytes(32, "big") + len(values).to_bytes(32, "big"))
    for value in values:
        raw.extend(value.to_bytes(32, "big"))
    return "0x" + bytes(raw).hex()


def address_result(address):
    return "0x" + (b"\x00" * 12 + bytes.fromhex(address[2:])).hex()


def amount_result(value):
    return "0x" + value.to_bytes(32, "big").hex()


class FakeRpc:
    def __init__(self):
        self.calls = []

    @staticmethod
    def _quick_amount(data):
        return int(data[10:74], 16)

    @staticmethod
    def _uniswap_amount(data):
        return int(data[202:266], 16)

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId":
            return "0x89"
        if method == "eth_blockNumber":
            return "0x1234"
        if method == "eth_getBlockByNumber":
            return {"timestamp": "0x1000"}
        if method == "eth_call":
            to = params[0]["to"]
            data = params[0]["data"]
            if to == ROUTER:
                amount = self._quick_amount(data)
                return array_result(amount, amount + 100)
            if to == FACTORY:
                return address_result(POOL)
            if to == QUOTER:
                amount = self._uniswap_amount(data)
                return amount_result(amount + 100)
        raise AssertionError((method, params))


class LiveOpportunityPipelineTests(unittest.TestCase):
    def setUp(self):
        self.rpc = FakeRpc()
        self.quickswap = QuickSwapV2ExactQuoter(self.rpc, ROUTER)
        self.uniswap = UniswapV3ExactQuoter(self.rpc, FACTORY, QUOTER)
        self.addresses = {
            "executor": "0x" + "01" * 20,
            "sender": "0x" + "02" * 20,
            "aave_pool": "0x" + "03" * 20,
            "quickswap_router": ROUTER,
            "uniswap_v3_router": "0x" + "05" * 20,
        }

    def _proof(self, candidate):
        return build_economic_proof(
            route_hash=candidate.simulation.route_hash,
            quote_hashes=tuple(leg.quote_hash for leg in candidate.simulation.legs),
            valuation_hash="0x" + "44" * 32,
            final_settlement_usd=Decimal("101.00"),
            loan_principal_usd=Decimal("100.00"),
            costs=CostBreakdown(flash_loan_fee=Decimal("0.10")),
            max_gas_usd=Decimal("0.10"),
            max_relay_usd=Decimal("0.05"),
        )

    def _prepare(self, builder=None):
        return discover_and_prepare_best_opportunity_execution(
            self.rpc,
            self.quickswap,
            self.uniswap,
            token_pairs=((A, B),),
            loan_amounts=(1000,),
            uniswap_fee=500,
            build_proof_for=builder or self._proof,
            **self.addresses,
            nonce=7,
            deadline=2000,
            amount_out_min_first=1090,
            amount_out_min_second=1110,
            minimum_surplus=1,
            gas_limit=500000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=10,
        )

    def _authority(self, owner=None, block=0x1234):
        return ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=self.addresses["executor"],
            owner=owner or self.addresses["sender"],
            observed_block=block,
            runtime_code_hash="0x" + "99" * 32,
            attesting_provider_names=("fake-primary", "fake-secondary"),
        )

    def test_concrete_discovery_flows_into_economics_and_assembly(self):
        discovery, economics, assembly = self._prepare()
        self.assertEqual(len(discovery.evaluated), 2)
        self.assertEqual(len(economics.evaluated), 2)
        self.assertEqual(economics.best.candidate.venue_path, "uniswap_v3->quickswap_v2")
        self.assertTrue(economics.best.economically_valid)
        self.assertEqual(assembly.intent.loan_amount, economics.best.candidate.loan_amount)
        self.assertEqual(assembly.intent.route_hash, economics.best.proof.route_hash)
        self.assertEqual({item.simulation.block_number for item in discovery.evaluated}, {0x1234})

    def test_builder_failure_never_reaches_execution_assembly(self):
        def fail(candidate):
            raise ValueError("valuation unavailable")

        with self.assertRaises(LiveOpportunityPipelineError):
            self._prepare(fail)

    def test_discovery_failure_is_wrapped_without_partial_execution_artifact(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            discover_and_prepare_best_opportunity_execution(
                self.rpc,
                self.quickswap,
                self.uniswap,
                token_pairs=(),
                loan_amounts=(1000,),
                uniswap_fee=500,
                build_proof_for=self._proof,
                **self.addresses,
                nonce=7,
                deadline=2000,
                amount_out_min_first=1090,
                amount_out_min_second=1110,
                minimum_surplus=1,
                gas_limit=500000,
                max_fee_per_gas=100,
                max_priority_fee_per_gas=10,
            )

    def test_complete_live_pipeline_reaches_evm_preflight(self):
        discovery, economics, assembly, preflight = discover_prepare_and_preflight_best_opportunity(
            self.rpc,
            self.quickswap,
            self.uniswap,
            token_pairs=((A, B),),
            loan_amounts=(1000,),
            uniswap_fee=500,
            build_proof_for=self._proof,
            **self.addresses,
            nonce=7,
            deadline=2000,
            amount_out_min_first=1090,
            amount_out_min_second=1110,
            minimum_surplus=1,
            gas_limit=500000,
            max_fee_per_gas=100,
            max_priority_fee_per_gas=10,
            now=1500,
            executor_authority=self._authority(),
        )
        self.assertEqual(len(discovery.evaluated), 2)
        self.assertEqual(economics.best.candidate.loan_amount, assembly.intent.loan_amount)
        self.assertTrue(preflight.passed)
        self.assertEqual(preflight.block_number, 0x1234)
        self.assertEqual(preflight.intent_hash, assembly.intent_hash)
        self.assertEqual(preflight.authority_evidence_hash, self._authority().evidence_hash)

    def test_preflight_failure_is_wrapped_and_never_reaches_signer(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            discover_prepare_and_preflight_best_opportunity(
                self.rpc,
                self.quickswap,
                self.uniswap,
                token_pairs=((A, B),),
                loan_amounts=(1000,),
                uniswap_fee=500,
                build_proof_for=self._proof,
                **self.addresses,
                nonce=7,
                deadline=2000,
                amount_out_min_first=1090,
                amount_out_min_second=1110,
                minimum_surplus=1,
                gas_limit=500000,
                max_fee_per_gas=100,
                max_priority_fee_per_gas=10,
                now=2500,
                executor_authority=self._authority(),
            )

    def test_preflight_rejects_executor_owner_mismatch(self):
        with self.assertRaises(LiveOpportunityPipelineError):
            discover_prepare_and_preflight_best_opportunity(
                self.rpc,
                self.quickswap,
                self.uniswap,
                token_pairs=((A, B),),
                loan_amounts=(1000,),
                uniswap_fee=500,
                build_proof_for=self._proof,
                **self.addresses,
                nonce=7,
                deadline=2000,
                amount_out_min_first=1090,
                amount_out_min_second=1110,
                minimum_surplus=1,
                gas_limit=500000,
                max_fee_per_gas=100,
                max_priority_fee_per_gas=10,
                now=1500,
                executor_authority=self._authority(owner="0x" + "06" * 20),
            )


if __name__ == "__main__":
    unittest.main()
