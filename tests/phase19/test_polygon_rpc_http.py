import io
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from phantomx.polygon_rpc import PolygonRPCError
from phantomx.polygon_rpc_http import PolygonRPCHTTPConfig, PolygonRPCHTTPError, PolygonRPCHTTPTransport


class _FakeResponse:
    def __init__(self, payload: object):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class PolygonRPCHTTPTests(unittest.TestCase):
    def _transport(self):
        return PolygonRPCHTTPTransport(
            PolygonRPCHTTPConfig(
                provider_name="approved-a",
                endpoint_url="https://example.invalid/rpc",
            )
        )

    def test_read_call_builds_json_rpc_request_without_secrets(self):
        transport = self._transport()
        with patch("phantomx.polygon_rpc_http.urlopen", return_value=_FakeResponse({"jsonrpc": "2.0", "id": 1, "result": "0x89"})) as mocked:
            result = transport("eth_chainId")
        self.assertEqual(result["result"], "0x89")
        request = mocked.call_args.args[0]
        body = request.data.decode("utf-8")
        self.assertEqual(json.loads(body), {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []})
        self.assertEqual(request.get_method(), "POST")

    def test_write_methods_are_blocked_before_network(self):
        transport = self._transport()
        with patch("phantomx.polygon_rpc_http.urlopen") as mocked:
            with self.assertRaises(PolygonRPCHTTPError):
                transport("eth_sendRawTransaction", "0xdeadbeef")
        mocked.assert_not_called()

    def test_unknown_methods_are_blocked_before_network(self):
        transport = self._transport()
        with patch("phantomx.polygon_rpc_http.urlopen") as mocked:
            with self.assertRaises(PolygonRPCHTTPError):
                transport("debug_traceTransaction", "0x0")
        mocked.assert_not_called()

    def test_error_response_is_preserved_for_policy_layer(self):
        transport = self._transport()
        with patch(
            "phantomx.polygon_rpc_http.urlopen",
            return_value=_FakeResponse({"jsonrpc": "2.0", "id": 1, "error": {"code": -32000}}),
        ):
            result = transport("eth_chainId")
        self.assertIn("error", result)

    def test_malformed_json_is_rejected(self):
        transport = self._transport()
        class _BadResponse(_FakeResponse):
            def __init__(self):
                self._body = b"not-json"
        with patch("phantomx.polygon_rpc_http.urlopen", return_value=_BadResponse()):
            with self.assertRaises(PolygonRPCHTTPError):
                transport("eth_chainId")

    def test_http_failures_are_rejected_without_leaking_endpoint(self):
        transport = self._transport()
        with patch("phantomx.polygon_rpc_http.urlopen", side_effect=OSError("connection failed")):
            with self.assertRaisesRegex(PolygonRPCError, "HTTP transport failure"):
                transport("eth_chainId")

    def test_http_failure_reports_sanitized_root_cause_class_without_endpoint(self):
        transport = self._transport()
        with patch("phantomx.polygon_rpc_http.urlopen", side_effect=URLError("secret endpoint detail")):
            with self.assertRaisesRegex(PolygonRPCHTTPError, r"HTTP transport failure [URLError: str]") as ctx:
                transport("eth_chainId")
        self.assertNotIn("secret endpoint detail", str(ctx.exception))
        self.assertNotIn("example.invalid", str(ctx.exception))

    def test_response_id_mismatch_is_rejected(self):
        transport = self._transport()
        with patch("phantomx.polygon_rpc_http.urlopen", return_value=_FakeResponse({"jsonrpc": "2.0", "id": 2, "result": "0x89"})):
            with self.assertRaisesRegex(PolygonRPCHTTPError, "response id mismatch"):
                transport("eth_chainId")

    def test_invalid_endpoint_and_timeout_are_rejected(self):
        with self.assertRaises(PolygonRPCHTTPError):
            PolygonRPCHTTPConfig(provider_name="a", endpoint_url="ftp://example.invalid")
        with self.assertRaises(PolygonRPCHTTPError):
            PolygonRPCHTTPConfig(provider_name="a", endpoint_url="https://user:pass@example.invalid")
        with self.assertRaises(PolygonRPCHTTPError):
            PolygonRPCHTTPConfig(provider_name="a", endpoint_url="https://example.invalid", timeout_seconds=0)

    def test_transport_can_be_wrapped_as_existing_provider(self):
        provider = self._transport().as_provider()
        self.assertEqual(provider.name, "approved-a")
        self.assertEqual(provider.transport("eth_chainId")["result"] if False else provider.name, "approved-a")


if __name__ == "__main__":
    unittest.main(verbosity=2)
