import unittest
from phantomx.aave_v3_dynamic import (
    AAVE_V3_POLYGON_POOL,
    BALANCE_OF_SELECTOR,
    FLASHLOAN_PREMIUM_TOTAL_SELECTOR,
    GET_POOL_SELECTOR,
    GET_RESERVE_DATA_SELECTOR,
    AaveFlashLiquiditySnapshot,
    AaveV3PolygonDynamicReader,
)
from phantomx.market_block import MarketBlockSnapshot


class FakeRPC:
    def __init__(self):
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        to = params[0]["to"].lower()
        data = params[0]["data"][2:]
        if data == GET_POOL_SELECTOR:
            return "0x" + "00" * 12 + AAVE_V3_POLYGON_POOL[2:].lower()
        if data.startswith(GET_RESERVE_DATA_SELECTOR):
            words = [0] * 14
            words[0] = (1 << 56) | (1 << 63)
            words[8] = int("11" * 20, 16)
            return "0x" + "".join(f"{x:064x}" for x in words)
        if data == FLASHLOAN_PREMIUM_TOTAL_SELECTOR:
            return f"0x{9:064x}"
        if data.startswith(BALANCE_OF_SELECTOR):
            return f"0x{1_000_000:064x}"
        raise AssertionError(f"unexpected calldata: {data}")


class AaveDynamicTests(unittest.TestCase):
    def test_reads_live_liquidity_premium_and_flags(self):
        block = MarketBlockSnapshot(chain_id=137, block_number=100, timestamp=1_700_000_000)
        rpc = FakeRPC()
        snap = AaveV3PolygonDynamicReader(rpc).snapshot(
            "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", block
        )
        self.assertEqual(snap.pool.lower(), AAVE_V3_POLYGON_POOL.lower())
        self.assertEqual(snap.available_liquidity_raw, 1_000_000)
        self.assertEqual(snap.flash_loan_premium_bps, 9)
        self.assertTrue(snap.reserve_active)
        self.assertFalse(snap.reserve_paused)
        self.assertTrue(snap.flashloan_enabled)

    def test_premium_uses_aave_percentage_math_rounding(self):
        snap = AaveFlashLiquiditySnapshot(
            137, 1, "0x" + "11" * 20, "0x" + "22" * 20, "0x" + "33" * 20,
            "0x" + "44" * 20, 1000, 9, True, False, True
        )
        self.assertEqual(snap.premium_raw(1000), 1)
        self.assertEqual(snap.repayment_raw(1000), 1001)

    def test_safe_ceiling_respects_headroom(self):
        snap = AaveFlashLiquiditySnapshot(
            137, 1, "0x" + "11" * 20, "0x" + "22" * 20, "0x" + "33" * 20,
            "0x" + "44" * 20, 1_000_000, 9, True, False, True
        )
        self.assertEqual(snap.safe_borrow_ceiling_raw(safety_headroom_bps=500), 950_000)

    def test_inactive_paused_or_disabled_fails_closed(self):
        for active, paused, enabled in ((False, False, True), (True, True, True), (True, False, False)):
            with self.subTest(active=active, paused=paused, enabled=enabled):
                with self.assertRaises(ValueError):
                    AaveFlashLiquiditySnapshot(
                        137, 1, "0x" + "11" * 20, "0x" + "22" * 20, "0x" + "33" * 20,
                        "0x" + "44" * 20, 1_000_000, 9, active, paused, enabled
                    )


if __name__ == "__main__":
    unittest.main()
