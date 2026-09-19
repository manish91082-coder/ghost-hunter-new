import unittest
from phantomx.cycle_route import CycleSimulationError, simulate_cycle
from phantomx.quote_snapshot import QuoteSnapshot

class CycleRouteTests(unittest.TestCase):
    def q(self,h,ti,to,ai,ao):
        return QuoteSnapshot(h,137,100,ti,to,ai,ao,"uv3:pool","pool",500,None,1)
    def test_two_leg_cycle(self):
        sim=simulate_cycle([self.q("0x"+"11"*32,"USDC","WETH",100,200),self.q("0x"+"22"*32,"WETH","USDC",200,101)])
        self.assertEqual(sim.final_amount,101)
    def test_return_asset_required(self):
        with self.assertRaises(CycleSimulationError):
            simulate_cycle([self.q("0x"+"11"*32,"USDC","WETH",100,200),self.q("0x"+"22"*32,"WETH","DAI",200,101)])
if __name__=="__main__": unittest.main(verbosity=2)
