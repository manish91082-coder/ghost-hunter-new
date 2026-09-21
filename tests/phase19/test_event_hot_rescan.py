import unittest

from phantomx.event_hot_rescan import HOT_EVENT_TOPICS, apply_hot_triggers, triggers_from_events
from phantomx.hunt_scheduler import HuntTask


class EventHotRescanTests(unittest.TestCase):
    def test_swap_marks_route_hot(self):
        triggers = triggers_from_events(
            [{"topic":"SWAP","pool":"0xabc","block_number":101,"transaction_hash":"0x1","log_index":0}],
            {"0xabc":["r1"]},
        )
        self.assertEqual(len(triggers),1)
        task = HuntTask("t1","r1",100)
        hot = apply_hot_triggers([task], triggers)[0]
        self.assertTrue(hot.state_changed)

    def test_unknown_event_is_ignored(self):
        self.assertEqual(
            triggers_from_events([{"topic":"TRANSFER","pool":"0xabc","block_number":101}], {"0xabc":["r1"]}),
            (),
        )

    def test_trigger_dedup_is_deterministic(self):
        e={"topic":"SWAP","pool":"0xabc","block_number":101,"transaction_hash":"0x1","log_index":0}
        self.assertEqual(triggers_from_events([e,e],{"0xabc":["r1"]}),triggers_from_events([e,e],{"0xabc":["r1"]}))


if __name__=="__main__":
    unittest.main(verbosity=2)
