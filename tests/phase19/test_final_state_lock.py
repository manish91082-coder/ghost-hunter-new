import unittest
from decimal import Decimal

from phantomx.economics import CostBreakdown
from phantomx.economic_proof import EconomicProof
from phantomx.final_state_lock import FinalStateLockError, lock_final_requote
from phantomx.opportunity_discovery import OpportunityCandidate
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import simulate_two_leg


def q(tin, tout, ai, ao, dex="test", fee=0):
    f = dict(
        schema_version=1, chain_id=137, block_number=100, observed_at_unix=1,
        dex=dex, pool_or_router="0x"+"11"*20, token_in=tin, token_out=tout,
        amount_in=ai, amount_out=ao, fee_raw=fee, gas_estimate=None, quote_hash="",
    )
    from phantomx.hashing import keccak256_hex
    import json
    f["quote_hash"] = keccak256_hex(json.dumps({k:v for k,v in f.items() if k!="quote_hash"},sort_keys=True,separators=(",",":")).encode())
    return QuoteSnapshot(**f)


class FinalStateLockTests(unittest.TestCase):
    def candidate_and_proof(self):
        a="0x"+"aa"*20
        b="0x"+"bb"*20
        l1=q(a,b,1_000_000,1_010_000,"qs")
        l2=q(b,a,1_010_000,1_202_000,"u3",500)
        sim=simulate_two_leg(l1,l2)
        cand=OpportunityCandidate(a,b,"qs->u3",1_000_000,sim)
        proof=EconomicProof(
            schema_version=1,
            route_hash=sim.route_hash,
            quote_hashes=tuple(x.quote_hash for x in sim.legs),
            valuation_hash="0x"+"22"*32,
            final_settlement_usd=Decimal("1.202"),
            loan_principal_usd=Decimal("1"),
            costs=CostBreakdown(gas=Decimal("0.0001")),
            max_gas_usd=Decimal("0.001"),
            max_relay_usd=Decimal("0"),
            minimum_net_profit_usd=Decimal("0.20"),
        )
        return cand, proof

    def test_current_block_and_fresh_hashes_lock(self):
        cand, proof=self.candidate_and_proof()
        lock=lock_final_requote(
            candidate=cand, final_proof=proof, current_block_number=100,
            final_valuation_hash=proof.valuation_hash, final_gas_block_number=100,
        )
        self.assertEqual(lock.block_number,100)
        self.assertEqual(lock.loan_amount,1_000_000)
        self.assertEqual(lock.economic_proof_hash,proof.proof_hash)
        self.assertTrue(lock.state_lock_hash.startswith("0x"))

    def test_stale_final_requote_is_rejected(self):
        cand, proof=self.candidate_and_proof()
        with self.assertRaisesRegex(FinalStateLockError,"stale"):
            lock_final_requote(
                candidate=cand, final_proof=proof, current_block_number=101,
                final_valuation_hash=proof.valuation_hash, final_gas_block_number=100,
            )

    def test_mismatched_valuation_is_rejected(self):
        cand, proof=self.candidate_and_proof()
        with self.assertRaises(FinalStateLockError):
            lock_final_requote(
                candidate=cand, final_proof=proof, current_block_number=100,
                final_valuation_hash="0x"+"33"*32, final_gas_block_number=100,
            )

    def test_below_floor_is_rejected(self):
        cand, proof=self.candidate_and_proof()
        low=EconomicProof(
            schema_version=1,
            route_hash=proof.route_hash,
            quote_hashes=proof.quote_hashes,
            valuation_hash=proof.valuation_hash,
            final_settlement_usd=Decimal("1.1"),
            loan_principal_usd=Decimal("1"),
            costs=CostBreakdown(gas=Decimal("0.0001")),
            max_gas_usd=Decimal("0.001"),
            max_relay_usd=Decimal("0"),
            minimum_net_profit_usd=Decimal("0.20"),
        )
        with self.assertRaises(FinalStateLockError):
            lock_final_requote(
                candidate=cand, final_proof=low, current_block_number=100,
                final_valuation_hash=low.valuation_hash, final_gas_block_number=100,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
