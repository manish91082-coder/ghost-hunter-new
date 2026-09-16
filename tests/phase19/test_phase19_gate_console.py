import json
import tempfile
import unittest
from pathlib import Path

from scripts.phase19_gate_console import main


class Phase19GateConsoleTests(unittest.TestCase):
    def test_missing_lanes_are_blocked_and_present_lanes_are_referenced(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "signer").mkdir()
            (root / "signer" / "signer_evidence.json").write_text("{}", encoding="utf-8")
            output = root / "manifest.json"
            rc = main([
                str(root),
                "--artifact-commit", "eea845af1388ea619c54ffc4faf8a34d215e2aa1",
                "--executor", "0x1111111111111111111111111111111111111111",
                "--signer", "0x2222222222222222222222222222222222222222",
                "--operator", "operator",
                "--witness", "witness",
                "--session-id", "sess-test",
                "--output", str(output),
            ])
            self.assertEqual(rc, 0)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["verified_artifact_commit"], "eea845af1388ea619c54ffc4faf8a34d215e2aa1")
            self.assertEqual(data["lanes"]["signer"]["status"], "GREEN")
            self.assertEqual(data["lanes"]["polygon_authority"]["status"], "BLOCKED")
            self.assertEqual(data["lanes"]["private_relay"]["status"], "BLOCKED")
            self.assertEqual(data["lanes"]["shadow_staging"]["status"], "BLOCKED")
            self.assertEqual(data["lanes"]["realized_pnl"]["status"], "BLOCKED")

    def test_rejects_bad_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            rc = main([
                temp,
                "--artifact-commit", "not-a-sha",
                "--executor", "0x1111111111111111111111111111111111111111",
                "--signer", "0x2222222222222222222222222222222222222222",
                "--operator", "operator",
                "--witness", "witness",
            ])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
