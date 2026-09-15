import ast
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from phantomx.private_relay_http import PrivateRelayHTTPConfig, PrivateRelayHTTPError, PrivateRelayHTTPTransport
from phantomx.production_private_relay import (
    ProductionPrivateRelayConfigError,
    load_production_private_relay_config_from_env,
)

ROOT = Path(__file__).resolve().parents[2]
PHANTOMX = ROOT / "phantomx"


class ProductionPrivateRelayTests(unittest.TestCase):
    def test_missing_configuration_fails_closed(self):
        with self.assertRaises(ProductionPrivateRelayConfigError):
            load_production_private_relay_config_from_env({})

    def test_private_assertion_is_required(self):
        env = {
            "PHANTOMX_PRIVATE_RELAY_JSON": json.dumps(
                {"name": "relay", "endpoint_url": "https://relay.example", "is_private": False}
            )
        }
        with self.assertRaisesRegex(ProductionPrivateRelayConfigError, "private=true"):
            load_production_private_relay_config_from_env(env)

    def test_embedded_credentials_and_non_https_are_rejected(self):
        for endpoint in ("http://relay.example", "https://user:pass@relay.example"):
            with self.assertRaises(ProductionPrivateRelayConfigError):
                load_production_private_relay_config_from_env(
                    {
                        "PHANTOMX_PRIVATE_RELAY_JSON": json.dumps(
                            {"name": "relay", "endpoint_url": endpoint, "is_private": True}
                        )
                    }
                )

    def test_auth_token_is_loaded_only_from_separate_environment_variable(self):
        env = {
            "PHANTOMX_PRIVATE_RELAY_JSON": json.dumps(
                {"name": "relay", "endpoint_url": "https://relay.example", "is_private": True}
            ),
            "PHANTOMX_PRIVATE_RELAY_AUTH_TOKEN": "secret-token",
        }
        config = load_production_private_relay_config_from_env(env)
        self.assertEqual(config.auth_token, "secret-token")
        self.assertNotIn("secret-token", repr(config))

    def test_unknown_configuration_fields_are_rejected(self):
        env = {
            "PHANTOMX_PRIVATE_RELAY_JSON": json.dumps(
                {
                    "name": "relay",
                    "endpoint_url": "https://relay.example",
                    "is_private": True,
                    "fallback": "public",
                }
            )
        }
        with self.assertRaises(ProductionPrivateRelayConfigError):
            load_production_private_relay_config_from_env(env)

    def test_assembly_returns_private_transport_implementation(self):
        env = {
            "PHANTOMX_PRIVATE_RELAY_JSON": json.dumps(
                {"name": "relay", "endpoint_url": "https://relay.example", "is_private": True}
            )
        }
        relay = load_production_private_relay_config_from_env(env).as_private_relay()
        self.assertIsInstance(relay, PrivateRelayHTTPTransport)
        self.assertEqual(relay.name, "relay")
        self.assertTrue(relay.is_private)

    def test_transport_requires_explicit_private_assertion(self):
        with self.assertRaises(PrivateRelayHTTPError):
            PrivateRelayHTTPConfig(
                name="relay",
                endpoint_url="https://relay.example",
                is_private=False,
            )

    def test_transport_sends_only_raw_transaction_rpc_method(self):
        transport = PrivateRelayHTTPTransport(
            PrivateRelayHTTPConfig(
                name="relay",
                endpoint_url="https://relay.example",
                auth_token="secret-token",
            )
        )

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"jsonrpc":"2.0","id":1,"result":"0x' + b"11" * 32 + b'"}'

        with patch("phantomx.private_relay_http.urlopen", return_value=Response()) as mocked:
            tx_hash = transport.submit_raw_transaction(b"signed")
        request = mocked.call_args.args[0]
        self.assertEqual(tx_hash, "0x" + "11" * 32)
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.headers["Authorization"], "Bearer secret-token")
        body = request.data.decode("utf-8")
        self.assertIn('"method":"eth_sendRawTransaction"', body)
        self.assertNotIn("public", body)

    def test_transport_does_not_leak_endpoint_or_token_on_http_failure(self):
        transport = PrivateRelayHTTPTransport(
            PrivateRelayHTTPConfig(
                name="relay",
                endpoint_url="https://relay.example/private",
                auth_token="secret-token",
            )
        )
        with patch(
            "phantomx.private_relay_http.urlopen",
            side_effect=OSError("https://relay.example/private secret-token"),
        ):
            with self.assertRaises(PrivateRelayHTTPError) as ctx:
                transport.submit_raw_transaction(b"signed")
        self.assertNotIn("relay.example", str(ctx.exception))
        self.assertNotIn("secret-token", str(ctx.exception))

    def test_transport_timeout_is_fail_closed_and_does_not_claim_acceptance(self):
        transport = PrivateRelayHTTPTransport(
            PrivateRelayHTTPConfig(name="relay", endpoint_url="https://relay.example")
        )
        with patch("phantomx.private_relay_http.urlopen", side_effect=TimeoutError("request timed out")):
            with self.assertRaisesRegex(PrivateRelayHTTPError, "HTTP transport failure"):
                transport.submit_raw_transaction(b"signed")

    def test_relay_json_error_is_fail_closed_without_transaction_hash(self):
        transport = PrivateRelayHTTPTransport(
            PrivateRelayHTTPConfig(name="relay", endpoint_url="https://relay.example")
        )

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"jsonrpc":"2.0","id":1,"error":{"code":-32000,"message":"rejected"}}'

        with patch("phantomx.private_relay_http.urlopen", return_value=Response()):
            with self.assertRaisesRegex(PrivateRelayHTTPError, "rejected"):
                transport.submit_raw_transaction(b"signed")

    def test_invalid_relay_result_fails_closed(self):
        transport = PrivateRelayHTTPTransport(
            PrivateRelayHTTPConfig(name="relay", endpoint_url="https://relay.example")
        )

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"jsonrpc":"2.0","id":1,"result":"bad"}'

        with patch("phantomx.private_relay_http.urlopen", return_value=Response()):
            with self.assertRaises(PrivateRelayHTTPError):
                transport.submit_raw_transaction(b"signed")

    def test_empty_raw_transaction_is_rejected_before_network(self):
        transport = PrivateRelayHTTPTransport(
            PrivateRelayHTTPConfig(name="relay", endpoint_url="https://relay.example")
        )
        with patch("phantomx.private_relay_http.urlopen") as mocked:
            with self.assertRaises(PrivateRelayHTTPError):
                transport.submit_raw_transaction(b"")
        mocked.assert_not_called()

    def test_private_relay_assembly_has_no_signer_or_public_fallback(self):
        source = (PHANTOMX / "production_private_relay.py").read_text(encoding="utf-8")
        tree = ast.parse(source, filename="production_private_relay.py")
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertTrue(all("signer" not in name and "private_submit" not in name for name in imports))
        self.assertNotIn("fallback", source.lower())

    def test_execution_submission_only_crosses_high_level_private_submit_boundary(self):
        source = (PHANTOMX / "execution_submission.py").read_text(encoding="utf-8")
        tree = ast.parse(source, filename="execution_submission.py")
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    calls.append(func.id)
                elif isinstance(func, ast.Attribute):
                    calls.append(func.attr)
        self.assertIn("submit_governed_transaction", calls)
        self.assertNotIn("submit_raw_transaction", calls)


if __name__ == "__main__":
    unittest.main(verbosity=2)
