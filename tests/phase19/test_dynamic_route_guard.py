import unittest

from phantomx.dynamic_route_guard import (
    DynamicRouteGuardError,
    compute_rate_degradation_bps,
    evaluate_dynamic_route_domain,
)
from phantomx.route_simulator import RouteSimulation
from phantomx.quote_snapshot import QuoteSnapshot


def q(token_in, token_out, amount_in, amount_out, block=100):
    fields = dict(
        schema_version=1, chain_id=137, block_number=block, observed_at_unix=1,
        dex="test", pool_or_router="0x"+"11"*20, token_in=token_in,
        token_out=token_out, amount_in=amount_in, amount_out=amount_out,
        fee_raw=0, gas_estimate=None, quote_hash=""
    )
    fields["quote_hash"] = QuoteSnapshot.compute_hash if False else ""
    # Build via canonical constructor helper.
    from phantomx.hashing import keccak256_hex
    import json
    payload={k:v for k,v in fields.items() if k!="quote_hash"}
    fields["quote_hash"]=keccak256_hex(json.dumps(payload,sort_keys=True,separators=(",",":")).encode())
    return QuoteSnapshot(**fields)


def sim(amount, final, block=100):
    first=q("0x"+"aa"*20,"0x"+"bb"*20,amount,final+1,block)
    second=q("0x"+"bb"*20,"0x"+"aa"*20,final+1,final,block)
    return RouteSimulation(
        schema_version=1, chain_id=137, block_number=block,
        initial_amount=amount, final_amount=final, legs=(first,second),
        route_hash=RouteSimulation.__dict__["route_hash"].fget if False else __import__(
            "phantomx.route_simulator", fromlist=["compute_route_hash"]
        ).compute_route_hash((first,second)),
    )


class DynamicRouteGuardTests(unittest.TestCase):
    def test_no_degradation_when_rate_improves(self):
        self.assertEqual(compute_rate_degradation_bps(sim(100, 99), sim(200, 200)), 0)

    def test_degradation_is_deterministic(self):
        ref=sim(100,100)
        cand=sim(1000,990)
        self.assertEqual(compute_rate_degradation_bps(ref,cand),100)

    def test_selects_max_safe_amount_over_explicit_domain(self):
        amounts=(100,200,400,800)
        result=evaluate_dynamic_route_domain(
            amounts,
            evaluate_forward=lambda a: sim(a, a if a <= 400 else 780),
            evaluate_reverse=lambda a: sim(a, a if a <= 400 else 780),
            max_degradation_bps=100,
        )
        self.assertEqual(result.reference_amount,100)
        self.assertEqual(result.max_safe_amount,400)

    def test_route_must_exist_in_both_directions(self):
        with self.assertRaises(DynamicRouteGuardError):
            evaluate_dynamic_route_domain(
                (100,200),
                evaluate_forward=lambda a: (_ for _ in ()).throw(RuntimeError("no forward")),
                evaluate_reverse=lambda a: sim(a,a),
            )


if __name__ == "__main__":
    unittest.main()
