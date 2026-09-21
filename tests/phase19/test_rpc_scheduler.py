import unittest

from phantomx.rpc_scheduler import RPCProviderScheduler, RPCSchedulerError


class RPCSchedulerTests(unittest.TestCase):
    def records(self, n=10):
        return [
            {"provider_id": f"p{i}", "endpoint_url": f"https://rpc{i}.example", "health_score": 1.0, "max_concurrency": 2}
            for i in range(n)
        ]

    def test_large_registry_has_bounded_active_assignments(self):
        scheduler = RPCProviderScheduler.from_records(self.records(250), max_active=4)
        assignments = scheduler.select(task_ids=[f"t{i}" for i in range(20)], now=100.0)
        self.assertLessEqual(len({a.provider_id for a in assignments}), 4)
        self.assertLessEqual(len(assignments), 8)

    def test_unhealthy_providers_are_excluded(self):
        records=self.records(4)
        records[0]["health_score"]=0
        scheduler=RPCProviderScheduler.from_records(records,max_active=3)
        assignments=scheduler.select(task_ids=("a","b","c"),now=100)
        self.assertNotIn("p0",{a.provider_id for a in assignments})

    def test_circuit_opens_after_failures(self):
        scheduler=RPCProviderScheduler.from_records(self.records(2),max_active=2,failure_threshold=2,circuit_cooldown_seconds=60)
        scheduler.select(task_ids=("a",),now=100)
        scheduler.record_failure("p0",now=100)
        scheduler.select(task_ids=("b",),now=101)
        scheduler.record_failure("p0",now=101)
        scheduler.providers["p0"].in_flight=0
        assignments=scheduler.select(task_ids=("c","d"),now=102)
        self.assertNotIn("p0",{a.provider_id for a in assignments})

    def test_provider_concurrency_is_bounded(self):
        scheduler=RPCProviderScheduler.from_records(self.records(1),max_active=1)
        assignments=scheduler.select(task_ids=("a","b","c"),now=100)
        self.assertEqual(len(assignments),2)

    def test_unknown_provider_failure_is_rejected(self):
        scheduler=RPCProviderScheduler.from_records(self.records(1))
        with self.assertRaises(RPCSchedulerError):
            scheduler.record_failure("missing",now=1)


if __name__=="__main__":
    unittest.main(verbosity=2)
