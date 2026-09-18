import json
import unittest

from phantomx.cross_venue_qsv2_ramses_v3_route import (
    build_quickswap_v2_to_ramses_v3_route,
    build_ramses_v3_to_quickswap_v2_route,
)
from phantomx.cross_venue_qsv3_ramses_v3_route import (
    build_quickswap_v3_to_ramses_v3_route,
    build_ramses_v3_to_quickswap_v3_route,
)
from phantomx.hashing import keccak256_hex
from phantomx.market_block import MarketBlockSnapshot
from phantomx.quote_snapshot import QuoteSnapshot


A = "0x" + "aa" * 20
B = "0x" + "bb" * 20
BLOCK = MarketBlockSnapshot(chain_id=137, block_number=100, timestamp=1_700_000_000)


def make_quote(token_in, token_out, amount_in, amount_out, dex, fee):
    payload = {
        "schema_version": 1,
        "chain_id": 137,
        "block_number": 100,
        "observed_at_unix": 1_700_000_000,
        "dex": dex,
        "pool_or_router": "0x" + "11" * 20,
        "token_in": token_in,
        "token_out": token_out,
        "amount_in": amount_in,
        "amount_out": amount_out,
        "fee_raw": fee,
        "gas_estimate": None,
    }
    payload["quote_hash"] = keccak256_hex(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    )
    return QuoteSnapshot(**payload)


class FakeV3Quoter:
    def __init__(self, token_in, token_out, output, dex, fee):
        self.token_in = token_in
        self.token_out = token_out
        self.output = output
        self.dex = dex
        self.fee = fee

    def quote_snapshot(self, amount_in, token_in, token_out, *args, **kwargs):
        if token_in != self.token_in or token_out != self.token_out:
            raise AssertionError("unexpected token direction")
        return make_quote(token_in, token_out, amount_in, self.output, self.dex, self.fee)


class FakeV2Quoter:
    def __init__(self, token_in, token_out, output, dex):
        self.token_in = token_in
        self.token_out = token_out
        self.output = output
        self.dex = dex

    def quote_snapshot(self, amount_in, path, *args, **kwargs):
        if tuple(path) != (self.token_in, self.token_out):
            raise AssertionError("unexpected QuickSwap V2 path")
        return make_quote(
            self.token_in,
            self.token_out,
            amount_in,
            self.output,
            self.dex,
            0,
        )


class CrossVenueRamsesRouteTests(unittest.TestCase):
    def test_qsv2_to_ramses_v3_route_preserves_exact_leg_continuity(self):
        qs = FakeV2Quoter(A, B, 101_000, "quickswap_v2")
        rv3 = FakeV3Quoter(B, A, 100_700, "ramses_v3:pool", 13)
        sim = build_quickswap_v2_to_ramses_v3_route(
            None, qs, rv3, amount_in=100_000, token_a=A, token_b=B,
            ramses_tick_spacing=1, block=BLOCK,
        )
        self.assertEqual(sim.initial_amount, 100_000)
        self.assertEqual(sim.legs[0].amount_out, 101_000)
        self.assertEqual(sim.final_amount, 100_700)
        self.assertEqual(sim.legs[1].amount_in, 101_000)

    def test_ramses_v3_to_qsv2_route_preserves_exact_leg_continuity(self):
        rv3 = FakeV3Quoter(A, B, 101_000, "ramses_v3:pool", 13)
        qs = FakeV2Quoter(B, A, 100_700, "quickswap_v2")
        sim = build_ramses_v3_to_quickswap_v2_route(
            None, qs, rv3, amount_in=100_000, token_a=A, token_b=B,
            ramses_tick_spacing=1, block=BLOCK,
        )
        self.assertEqual(sim.final_amount, 100_700)
        self.assertEqual(sim.legs[1].amount_in, 101_000)

    def test_qsv3_to_ramses_v3_route_preserves_exact_leg_continuity(self):
        qs = FakeV3Quoter(A, B, 101_100, "quickswap_v3:pool", 37)
        rv3 = FakeV3Quoter(B, A, 100_900, "ramses_v3:pool", 13)
        sim = build_quickswap_v3_to_ramses_v3_route(
            None, qs, rv3, amount_in=100_000, token_a=A, token_b=B,
            ramses_tick_spacing=1, block=BLOCK,
        )
        self.assertEqual(sim.final_amount, 100_900)
        self.assertEqual(sim.legs[0].fee_raw, 37)
        self.assertEqual(sim.legs[1].fee_raw, 13)

    def test_ramses_v3_to_qsv3_route_preserves_exact_leg_continuity(self):
        rv3 = FakeV3Quoter(A, B, 101_100, "ramses_v3:pool", 13)
        qs = FakeV3Quoter(B, A, 100_900, "quickswap_v3:pool", 41)
        sim = build_ramses_v3_to_quickswap_v3_route(
            None, qs, rv3, amount_in=100_000, token_a=A, token_b=B,
            ramses_tick_spacing=1, block=BLOCK,
        )
        self.assertEqual(sim.final_amount, 100_900)
        self.assertEqual(sim.legs[0].fee_raw, 13)
        self.assertEqual(sim.legs[1].fee_raw, 41)


if __name__ == "__main__":
    unittest.main(verbosity=2)
