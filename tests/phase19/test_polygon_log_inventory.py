import unittest
from unittest.mock import Mock
from phantomx.polygon_log_inventory import InventoryLog, PolygonLogInventory, PolygonLogInventoryError

class LogInventoryTests(unittest.TestCase):
    @staticmethod
    def log(block="0x1"):
        return {
            "blockNumber": block, "transactionHash": "0x"+"11"*32, "logIndex":"0x0",
            "address":"0x"+"22"*20, "topics":["0x"+"33"*32], "data":"0x"
        }

    def test_scan_reads_and_dedupes(self):
        rpc=Mock()
        rpc.call.side_effect=[[self.log("0x1")],[dict(self.log("0x2"),transactionHash="0x"+"22"*32)]]
        out=PolygonLogInventory(rpc,initial_chunk_size=1).scan(from_block=1,to_block=2)
        self.assertEqual([x.block_number for x in out],[1,2])

    def test_range_failure_shrinks_chunk(self):
        rpc=Mock()
        rpc.call.side_effect=[RuntimeError("query returned too many logs"),[self.log("0xa")],[dict(self.log("0xa"),transactionHash="0x"+"22"*32)]]
        out=PolygonLogInventory(rpc,initial_chunk_size=2).scan(from_block=10,to_block=11)
        self.assertEqual({x.block_number for x in out},{10,11})

    def test_non_range_failure_is_failed_closed(self):
        rpc=Mock()
        rpc.call.side_effect=RuntimeError("execution reverted")
        with self.assertRaises(PolygonLogInventoryError):
            PolygonLogInventory(rpc).scan(from_block=1,to_block=2)

if __name__=="__main__":
    unittest.main(verbosity=2)