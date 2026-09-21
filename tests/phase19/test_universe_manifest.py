import json
import tempfile
import unittest
from pathlib import Path

from phantomx.universe_manifest import UniverseManifest, VenueSlice, load_inventory_artifact, merge_manifests, validate_expected_venues


class UniverseManifestTests(unittest.TestCase):
    def test_manifest_blocks_rpc_exhaustion(self):
        m = UniverseManifest(137)
        m.add_slice(VenueSlice("uniswap_v3", 1, 10, "RPC_EXHAUSTED", 0, 2, "h"))
        self.assertFalse(m.exhausted)
        self.assertEqual(m.summary()["status"], "INCOMPLETE")

    def test_manifest_can_be_exhausted(self):
        m = UniverseManifest(137)
        m.add_slice(VenueSlice("uniswap_v3", 1, 10, "QUOTED", 2, 0, "h"))
        m.add_pair("0x1", "0x2")
        self.assertTrue(m.exhausted)
        self.assertEqual(m.summary()["pair_count"], 1)

    def test_load_inventory_artifact(self):
        payload = {
            "chain_id_expected": 137,
            "venue": "uniswap_v3",
            "from_block": 100,
            "to_block": 200,
            "status": "QUOTED",
            "edges": [{"token_in":"0x1","token_out":"0x2"}],
            "rpc_pool": {"failover_events": []},
        }
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"a.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            m = load_inventory_artifact(p)
        self.assertEqual(len(m.pairs), 1)

    def test_merge_and_expected_venues(self):
        a = UniverseManifest(137)
        a.add_slice(VenueSlice("qsv2",1,2,"QUOTED",1,0,"a"))
        b = UniverseManifest(137)
        b.add_slice(VenueSlice("uv3",1,2,"QUOTED",1,0,"b"))
        merged = merge_manifests([a,b])
        self.assertEqual(validate_expected_venues(merged, ["qsv2","uv3"]), ())
        self.assertEqual(len(merged.venue_slices), 2)

    def test_hash_is_deterministic(self):
        m = UniverseManifest(137)
        m.add_slice(VenueSlice("uv3",1,2,"QUOTED",1,0,"a"))
        self.assertEqual(m.to_dict()["manifest_hash"], m.to_dict()["manifest_hash"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
