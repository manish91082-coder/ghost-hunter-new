import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PHANTOMX = ROOT / "phantomx"
PRODUCTION_FILES = tuple(sorted(PHANTOMX.glob("*.py")))


class ProductionExecutionSurfaceTests(unittest.TestCase):
    def _source(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _calls_named(self, name: str):
        calls = []
        for path in PRODUCTION_FILES:
            tree = ast.parse(self._source(path), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id == name:
                        calls.append(path.name)
                    elif isinstance(func, ast.Attribute) and func.attr == name:
                        calls.append(path.name)
        return calls

    def test_private_key_materialization_is_confined_to_signer(self):
        offenders = [
            path.name
            for path in PRODUCTION_FILES
            if "PrivateKey(" in self._source(path) and path.name != "signer.py"
        ]
        self.assertEqual(offenders, [])

    def test_signature_primitive_is_confined_to_signer(self):
        offenders = [
            path.name
            for path in PRODUCTION_FILES
            if "sign_msg_hash(" in self._source(path) and path.name != "signer.py"
        ]
        self.assertEqual(offenders, [])

    def test_governed_transaction_signing_has_only_coordinator_callers(self):
        self.assertEqual(
            sorted(self._calls_named("sign_governed_transaction")),
            ["execution_coordinator.py", "replacement_coordinator.py"],
        )

    def test_raw_relay_submission_call_is_confined_to_private_boundary(self):
        self.assertEqual(self._calls_named("submit_raw_transaction"), ["private_submit.py"])

    def test_raw_transaction_rpc_method_is_only_present_in_explicit_blocklist(self):
        source = self._source(PHANTOMX / "polygon_rpc_http.py")
        self.assertIn("_BLOCKED_METHODS", source)
        self.assertIn('"eth_sendRawTransaction"', source)
        offenders = [
            path.name
            for path in PRODUCTION_FILES
            if "eth_sendRawTransaction" in self._source(path)
            and path.name != "polygon_rpc_http.py"
        ]
        self.assertEqual(offenders, [])

    def test_production_authority_does_not_import_signing_or_submission_layers(self):
        source = self._source(PHANTOMX / "production_authority.py")
        tree = ast.parse(source, filename="production_authority.py")
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)
        forbidden = {"phantomx.signer", "phantomx.private_submit", ".signer", ".private_submit"}
        self.assertTrue(forbidden.isdisjoint(imported_modules))

    def test_authority_observation_cli_has_no_signing_or_submission_dependency(self):
        source = (ROOT / "scripts" / "observe_production_authority.py").read_text(encoding="utf-8")
        self.assertNotIn("phantomx.signer", source)
        self.assertNotIn("phantomx.private_submit", source)
        self.assertNotIn("PrivateKey(", source)
        self.assertNotIn("sign_msg_hash(", source)
        self.assertNotIn("submit_raw_transaction(", source)
        self.assertNotIn("eth_sendRawTransaction", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
