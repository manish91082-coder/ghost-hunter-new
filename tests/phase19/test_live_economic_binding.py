import unittest
from decimal import Decimal

from phantomx.live_economic_binding import bind_live_economic_proof
from phantomx.gas_cost import build_gas_cost_evidence
from phantomx.gas_observation import GasObservation
from phantomx.native_valuation import ConservativeNativeValuation
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import simulate_two_leg
from phantomx.opportunity_discovery import OpportunityCandidate

class LiveEconomicBindingTests(unittest.TestCase):
    def candidate(self):
        def q(tin,tout,ai,ao,dex,fee):
            f=dict(schema_version=1,chain_id=137,block_number=100,observed_at_unix=1,dex=dex,pool_or_router="0x"+"11"*20,token_in=tin,token_out=tout,amount_in=ai,amount_out=ao,fee_raw=fee,gas_estimate=None,quote_hash="")
            from phantomx.hashing import keccak256_hex
            import json
            f["quote_hash"]=keccak256_hex(json.dumps({k:v for k,v in f.items() if k!="quote_hash"},sort_keys=True,separators=(",",":")).encode())
            return QuoteSnapshot(**f)
        a="0x"+"aa"*20; b="0x"+"bb"*20
        l1=q(a,b,100_000_000,101_000_000,"quickswap_v2",0)
        l2=q(b,a,101_000_000,100_200_000,"uniswap_v3:pool",500)
        sim=simulate_two_leg(l1,l2)
        return OpportunityCandidate(simulation=sim,loan_amount=100_000_000,venue_path="quickswap_v2->uniswap_v3",token_a=a,token_b=b)

    def gas(self):
        obs=GasObservation(schema_version=1,chain_id=137,block_number=100,gas_estimate=100000,gas_limit=120000,base_fee_per_gas=1_000_000_000,priority_fee_per_gas=100_000_000,max_fee_per_gas=2_100_000_000)
        return build_gas_cost_evidence(obs,native_usd_price="0.60",valuation_evidence_hash="0x"+"11"*32)

    def valuation(self):
        return ConservativeNativeValuation(chain_id=137,block_number=100,native_token="0x"+"aa"*20,stable_token="0x"+"bb"*20,native_amount_raw=10**18,conservative_price_usd=Decimal("0.60"),evidence_hashes=("0x"+"11"*32,))

    def test_exact_quotes_do_not_double_count_embedded_dex_fee_or_impact(self):
        binding=bind_live_economic_proof(self.candidate(),flash_loan_premium_bps=0,gas_cost=self.gas(),native_valuation=self.valuation())
        self.assertEqual(binding.proof.gross_surplus_usd,Decimal("0.20"))
        self.assertEqual(binding.proof.costs.dex_fees,Decimal("0"))
        self.assertEqual(binding.proof.costs.price_impact,Decimal("0"))
        self.assertEqual(binding.proof.worst_case_net_profit_usd,Decimal("0.4998488"))
        self.assertFalse(binding.economically_valid)

if __name__=="__main__":
    unittest.main(verbosity=2)
