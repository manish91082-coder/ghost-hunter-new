import unittest

from phantomx.coverage_ledger import (
    CoverageLedger,
    CoverageRecord,
    CoverageStatus,
    CoverageTask,
)


def record(task_id, status, attempts=1):
    task = CoverageTask(task_id, "S0", "route:"+task_id, 100)
    return CoverageRecord(task, status, "hash:"+task_id, attempts)


class CoverageLedgerTests(unittest.TestCase):
    def test_rpc_exhaustion_is_retryable_not_terminal(self):
        ledger = CoverageLedger()
        ledger.upsert(record("a", CoverageStatus.RPC_EXHAUSTED))
        self.assertEqual([r.task.task_id for r in ledger.retryable()], ["a"])
        self.assertEqual([r.task.task_id for r in ledger.incomplete()], ["a"])
        self.assertFalse(ledger.is_exhausted(["a"]))

    def test_quoted_is_terminal(self):
        ledger = CoverageLedger()
        ledger.upsert(record("a", CoverageStatus.QUOTED))
        self.assertTrue(ledger.is_exhausted(["a"]))

    def test_missing_expected_task_prevents_exhaustion(self):
        ledger = CoverageLedger()
        ledger.upsert(record("a", CoverageStatus.QUOTED))
        self.assertFalse(ledger.is_exhausted(["a","b"]))

    def test_attempt_count_cannot_regress(self):
        ledger = CoverageLedger()
        ledger.upsert(record("a", CoverageStatus.RPC_EXHAUSTED, attempts=2))
        with self.assertRaises(ValueError):
            ledger.upsert(record("a", CoverageStatus.PENDING, attempts=1))

    def test_snapshot_hash_is_deterministic(self):
        a = CoverageLedger()
        b = CoverageLedger()
        for x in [record("a", CoverageStatus.QUOTED), record("b", CoverageStatus.ECONOMIC_REJECTED)]:
            a.upsert(x)
        for x in [record("b", CoverageStatus.ECONOMIC_REJECTED), record("a", CoverageStatus.QUOTED)]:
            b.upsert(x)
        self.assertEqual(a.snapshot_hash(), b.snapshot_hash())


if __name__ == "__main__":
    unittest.main(verbosity=2)
