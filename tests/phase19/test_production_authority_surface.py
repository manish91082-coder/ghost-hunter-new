import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_SOURCE = REPO_ROOT / "scripts" / "observe_production_authority.py"
AUTHORITY_SOURCE = REPO_ROOT / "phantomx" / "production_authority.py"


class ProductionAuthoritySurfaceAuditTests(unittest.TestCase):
    def _tree(self, path):
        return ast.parse(path.read_text(encoding="utf-8"))

    def test_operator_authority_cli_imports_only_observation_boundary(self):
        tree = self._tree(CLI_SOURCE)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add(node.module or "")

        forbidden_fragments = (
            "phantomx.signer",
            "phantomx.private_submit",
            "phantomx.execution_submission",
            "web3",
        )
        for module in imported_modules:
            self.assertFalse(
                any(fragment in module for fragment in forbidden_fragments),
                f"operator authority CLI imports forbidden surface: {module}",
            )

    def test_operator_authority_cli_has_no_secret_or_submission_options(self):
        source = CLI_SOURCE.read_text(encoding="utf-8")
        forbidden_options = (
            "--private-key",
            "--mnemonic",
            "--secret",
            "--sign",
            "--submit",
            "--broadcast",
            "--relay",
        )
        for option in forbidden_options:
            self.assertNotIn(option, source)

    def test_production_authority_module_imports_no_signing_or_submission_layer(self):
        tree = self._tree(AUTHORITY_SOURCE)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add(node.module or "")

        forbidden_fragments = (
            "phantomx.signer",
            "phantomx.private_submit",
            "phantomx.execution_submission",
        )
        for module in imported_modules:
            self.assertFalse(
                any(fragment in module for fragment in forbidden_fragments),
                f"production authority module imports forbidden execution surface: {module}",
            )

    def test_operator_authority_cli_contains_no_provider_endpoint_literal(self):
        source = CLI_SOURCE.read_text(encoding="utf-8").lower()
        self.assertNotIn("https://", source)
        self.assertNotIn("http://", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
