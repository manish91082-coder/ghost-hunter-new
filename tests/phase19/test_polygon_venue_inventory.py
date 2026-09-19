import unittest

from phantomx.polygon_venue_inventory import (
    VenueInventoryError,
    VenueInventorySpec,
    V3_POOL_CREATED_TOPIC,
    QUICKSWAP_V3_FACTORY,
    UNISWAP_V4_POOL_MANAGER,
    VENUE_SPECS,
    decode_inventory_log,
)
from phantomx.polygon_log_inventory import InventoryLog


def mklog(address, topics, data):
    return InventoryLog(
        block_number=1,
        transaction_hash="0x" + "11" * 32,
        log_index=0,
        address=address,
        topics=tuple(topics),
        data=data,
    )


class VenueInventoryTests(unittest.TestCase):
    def test_uniswap_v3_pool_created_decodes_pool_edge(self):
        spec = next(x for x in VENUE_SPECS if x.venue_id == "uniswap_v3")
        topics = [
            V3_POOL_CREATED_TOPIC,
            "0x" + "00" * 12 + "11" * 20,
            "0x" + "00" * 12 + "22" * 20,
            "0x" + (500).to_bytes(32, "big").hex(),
        ]
        data = "0x" + (10).to_bytes(32, "big").hex() + (0x33).to_bytes(32, "big").hex()
        edge = decode_inventory_log(mklog(spec.factory_or_manager, topics, data), spec)
        self.assertEqual(edge.token_in, "0x" + "11" * 20)
        self.assertEqual(edge.token_out, "0x" + "22" * 20)
        self.assertIn(("fee", "500"), edge.parameters)
        self.assertIn(("tickSpacing", "10"), edge.parameters)

    def test_v4_initialize_uses_pool_id_not_pool_contract(self):
        spec = next(x for x in VENUE_SPECS if x.venue_id == "uniswap_v4")
        topics = [
            "0x" + "aa" * 32,
            "0x" + "00" * 12 + "11" * 20,
            "0x" + "00" * 12 + "22" * 20,
        ]
        words = [
            (3000).to_bytes(32, "big"),
            (60).to_bytes(32, "big", signed=False),
            (0x33).to_bytes(32, "big"),
            (123).to_bytes(32, "big"),
            (5).to_bytes(32, "big", signed=True),
        ]
        data = "0x" + b"".join(words).hex()
        edge = decode_inventory_log(mklog(spec.factory_or_manager, topics, data), spec)
        self.assertEqual(edge.pool_id, UNISWAP_V4_POOL_MANAGER.lower())
        self.assertEqual(edge.parameters[0], ("fee", "3000"))

    def test_wrong_emitter_is_rejected(self):
        spec = next(x for x in VENUE_SPECS if x.venue_id == "uniswap_v3")
        topics = [V3_POOL_CREATED_TOPIC, "0x" + "00" * 12 + "11" * 20, "0x" + "00" * 12 + "22" * 20, "0x" + "00" * 32]
        data = "0x" + "00" * 64
        with self.assertRaises(VenueInventoryError):
            decode_inventory_log(mklog("0x" + "99" * 20, topics, data), spec)


if __name__ == "__main__":
    unittest.main(verbosity=2)
