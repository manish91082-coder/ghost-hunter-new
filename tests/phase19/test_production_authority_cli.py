import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from scripts.observe_production_authority import main


EXECUTOR = "0x1111111111111111111111111111111111111111"
OWNER = "0x2222222222222222222222222222222222222222"
RUNTIME_HASH = "0x" + "33" * 32
EVIDENCE_HASH = "0x" + "44" * 32
SECRET_ENDPOINT = "https://user:supersecret@rpc.internal.example/rpc"


class ProductionAuthorityCliTests(unittest.TestCase):
    def test_success_emits_only_canonical_non_secret_evidence(self):
        evidence = SimpleNamespace(
            schema_version=1,
            chain_id=137,
            executor=EXECUTOR,
            owner=OWNER,
            observed_block=123456,
            runtime_code_hash=RUNTIME_HASH,
            evidence_hash=EVIDENCE_HASH,
        )
        stdout = StringIO()
        stderr = StringIO()
        with patch(
            "scripts.observe_production_authority.load_production_authority_config_from_env",
            return_value=object(),
        ), patch(
            "scripts.observe_production_authority.observe_production_executor_authority",
            return_value=evidence,
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(main([]), 0)

        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {
                "chain_id": 137,
                "evidence_hash": EVIDENCE_HASH,
                "executor": EXECUTOR,
                "observed_block": 123456,
                "owner": OWNER,
                "runtime_code_hash": RUNTIME_HASH,
                "schema_version": 1,
            },
        )
        self.assertNotIn(SECRET_ENDPOINT, stdout.getvalue())
        self.assertNotIn("timeout", stdout.getvalue().lower())

    def test_missing_configuration_is_blocked_without_exception_leak(self):
        stdout = StringIO()
        stderr = StringIO()
        with patch(
            "scripts.observe_production_authority.load_production_authority_config_from_env",
            side_effect=ValueError("required production authority configuration is missing"),
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(main([]), 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "BLOCKED: production authority observation failed closed\n")
        self.assertNotIn(SECRET_ENDPOINT, stderr.getvalue())

    def test_unexpected_runtime_error_is_blocked_without_exception_leak(self):
        stdout = StringIO()
        stderr = StringIO()
        with patch(
            "scripts.observe_production_authority.load_production_authority_config_from_env",
            return_value=object(),
        ), patch(
            "scripts.observe_production_authority.observe_production_executor_authority",
            side_effect=RuntimeError(SECRET_ENDPOINT),
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(main([]), 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "BLOCKED: production authority observation failed closed\n")
        self.assertNotIn(SECRET_ENDPOINT, stderr.getvalue())

    def test_cli_does_not_offer_submission_arguments(self):
        parser = __import__("scripts.observe_production_authority", fromlist=["build_parser"]).build_parser()
        option_strings = {option for action in parser._actions for option in action.option_strings}
        self.assertNotIn("--private-key", option_strings)
        self.assertNotIn("--submit", option_strings)
        self.assertNotIn("--broadcast", option_strings)


if __name__ == "__main__":
    unittest.main(verbosity=2)
