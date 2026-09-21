import os
import unittest

from scripts import s6_triangular_live_scan as s6


class TestS6BridgeScope(unittest.TestCase):
    def setUp(self):
        self._original = os.environ.get("PHANTOMX_S6_BRIDGE_NAMES")

    def tearDown(self):
        if self._original is None:
            os.environ.pop("PHANTOMX_S6_BRIDGE_NAMES", None)
        else:
            os.environ["PHANTOMX_S6_BRIDGE_NAMES"] = self._original

    def test_selected_pair_is_bidirectional(self):
        os.environ["PHANTOMX_S6_BRIDGE_NAMES"] = "WETH,WPOL"

        pairs = s6._selected_bridge_ordered_pairs()

        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0][0][0], "WETH")
        self.assertEqual(pairs[0][1][0], "WPOL")
        self.assertEqual(pairs[1][0][0], "WPOL")
        self.assertEqual(pairs[1][1][0], "WETH")
        self.assertTrue(pairs[0][0][1].startswith("0x"))
        self.assertTrue(pairs[0][1][1].startswith("0x"))

    def test_default_scope_is_42_directed_pairs(self):
        os.environ.pop("PHANTOMX_S6_BRIDGE_NAMES", None)

        pairs = s6._selected_bridge_ordered_pairs()

        self.assertEqual(len(pairs), 42)
        self.assertEqual(len({pair for pair in pairs}), 42)


if __name__ == "__main__":
    unittest.main()
