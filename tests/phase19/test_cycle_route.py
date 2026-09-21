import unittest
from phantomx.cycle_route import CycleSimulationError, simulate_cycle
from phantomx.quote_snapshot import QuoteSnapshot

class CycleRouteTests(unittest.TestCase):
    def q(self,h,ti,to,ai,ao):
        from phantomx.quote_engine import ExactQuote
        quote = ExactQuote("uv3", ti, to, ai, ao, 100, 500)
        snapshot = QuoteSnapshot.from_exact_quote(
            quote,
            chain_id=137,
            observed_at_unix=1,
            pool_or_router="pool",
        )
        self.assertEqual(snapshot.quote_hash, snapshot.compute_hash())
        return snapshot
    def test_two_leg_cycle(self):
        sim=simulate_cycle([self.q("0x"+"11"*32,"USDC","WETH",100,200),self.q("0x"+"22"*32,"WETH","USDC",200,101)])
        self.assertEqual(sim.final_amount,101)
    def test_return_asset_required(self):
        with self.assertRaises(CycleSimulationError):
            simulate_cycle([self.q("0x"+"11"*32,"USDC","WETH",100,200),self.q("0x"+"22"*32,"WETH","DAI",200,101)])
if __name__=="__main__": unittest.main(verbosity=2)