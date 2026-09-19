import unittest
from unittest.mock import Mock

from phantomx.polygon_log_inventory import (
    InventoryLog,
    PolygonLogInventory,
    PolygonLogInventoryError,
)


class PolygonLogInventoryTests(unittest.TestCase):
    def _log(self, block="0x1", tx="0x" + "11" * 32, idx="0x0"):
        return {
            "blockNumber": block,
            "transactionHash": tx,
            "logIndex": idx,
            "address": "0x" + "22" * 20,
            "topics": ["0x" + "33" * 32],
            "data": "0x",
        }

    def test_chunked_scan_deduplicates_log_identity(self):
        rpc = Mock()
        rpc.call.side_effect = [
            [self._log(block="0x1")],
            [self._log(block="0x2")],
        ]
        reader = PolygonLogInventory(rpc, initial_chunk_size=2)
        logs = reader.scan(from_block=1, to_block=2)
        self.assertEqual([x.block_number for x in logs], [1, 2])
        self.assertEqual(rpc.call.call_count, 1)

    def test_range_limit_shrinks_and_retries(self):
        rpc = Mock()
        rpc.call.side_effect = [
            RuntimeError("query returned too many logs"),
            [self._log(block="0xa")],
            [self._log(block="0xb")],
        ]
        reader = PolygonLogInventory(rpc, initial_chunk_size=4, minimum_chunk_size=1)
        logs = reader.scan(from_block=10, to_block=13)
        self.assertEqual([x.block_number for x in logs], [10, 11])
        self.assertEqual(rpc.call.call_count, 3)

    def test_non_range_error_fails_closed(self):
        rpc = Mock()
        rpc.call.side_effect = RuntimeError("execution reverted")
        reader = PolygonLogInventory(rpc, initial_chunk_size=4)
        with self.assertRaises(PolygonLogInventoryError):
            reader.scan(from_block=1, to_block=2)

    def test_malformed_log_is_rejected(self):
        with self.assertRaises(PolygonLogInventoryError):
            InventoryLog.from_rpc({"blockNumber": "0x1"})

    def test_invalid_range_is_rejected(self):
        reader = PolygonLogInventory(Mock())
        with self.assertRaises(PolygonLogInventoryError):
            reader.scan(from_block=3, to_block=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
