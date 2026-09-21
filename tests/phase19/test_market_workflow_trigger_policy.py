import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANUAL_ONLY_MARKET_WORKFLOWS = (
    ".github/workflows/polygon-inventory-diagnostic.yml",
    ".github/workflows/s1-qsv3-live-read.yml",
    ".github/workflows/s2-uv4-uv3-live-read.yml",
    ".github/workflows/s3-ramses-uv3-live-read.yml",
    ".github/workflows/s5-curve-uv3-live-read.yml",
    ".github/workflows/s5a-curve-mai-probe.yml",
    ".github/workflows/s6-triangular-live-read.yml",
    ".github/workflows/s9-qsv2-ramses-v3-live-read.yml",
    ".github/workflows/s10-qsv3-ramses-v3-live-read.yml",
    ".github/workflows/s10-candidate-refinement.yml",
    ".github/workflows/x1-uv3-fee-dislocation-live-read.yml",
)


class MarketWorkflowTriggerPolicyTests(unittest.TestCase):
    def test_market_hunts_are_manual_dispatch_only(self):
        for relative in MANUAL_ONLY_MARKET_WORKFLOWS:
            content = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("\n  push:", content, relative)
            self.assertIn("\n  workflow_dispatch:", content, relative)

    def test_controlled_automatic_triggers_remain_narrow(self):
        first_hunt = (ROOT / ".github/workflows/first-hunt-live-read.yml").read_text(encoding="utf-8")
        self.assertIn("\n  push:", first_hunt)
        self.assertIn(".github/PHANTOMX_FIRST_HUNT_KICK", first_hunt)

        phase19 = (ROOT / ".github/workflows/phase19-tests.yml").read_text(encoding="utf-8")
        self.assertIn("\n  push:", phase19)

        history = (ROOT / ".github/workflows/polygon-universe-history-crawler.yml").read_text(encoding="utf-8")
        self.assertIn("\n  push:", history)
        self.assertIn(".github/PHANTOMX_HISTORY_KICK", history)


if __name__ == "__main__":
    unittest.main(verbosity=2)
