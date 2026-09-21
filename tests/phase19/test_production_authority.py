import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from phantomx.production_authority import (
    ProductionAuthorityConfigError,
    ProductionProviderConfig,
    load_production_authority_config_from_env,
    observe_production_executor_authority,
)
from phantomx.polygon_rpc import RPCProvider


EXECUTOR = "0x1111111111111111111111111111111111111111"
SIGNER = "0x2222222222222222222222222222222222222222"


class ProductionAuthorityConfigTests(unittest.TestCase):
    def _env(self):
        return {
            "PHANTOMX_POLYGON_PROVIDERS_JSON": json.dumps([
                {"name": "primary", "endpoint_url": "https://rpc.primary.example/rpc"},
                {"name": "secondary", "endpoint_url": "https://rpc.secondary.example/rpc"},
            ]),
            "PHANTOMX_POLYGON_QUORUM": "2",
            "PHANTOMX_EXECUTOR_ADDRESS": EXECUTOR,
            "PHANTOMX_EXPECTED_SIGNER_ADDRESS": SIGNER,
        }

    def test_loads_only_explicit_operator_configuration(self):
        config = load_production_authority_config_from_env(self._env())
        self.assertEqual(config.quorum, 2)
        self.assertEqual([p.name for p in config.providers], ["primary", "secondary"])
        self.assertEqual(config.executor_address, EXECUTOR)
        self.assertEqual(config.expected_signer_address, SIGNER)

    def test_missing_configuration_fails_closed(self):
        with self.assertRaises(ProductionAuthorityConfigError):
            load_production_authority_config_from_env({})

    def test_production_endpoint_must_use_https(self):
        env = self._env()
        env["PHANTOMX_POLYGON_PROVIDERS_JSON"] = json.dumps([
            {"name": "primary", "endpoint_url": "http://rpc.primary.example/rpc"},
        ])
        env["PHANTOMX_POLYGON_QUORUM"] = "1"
        with self.assertRaisesRegex(ProductionAuthorityConfigError, "HTTPS"):
            load_production_authority_config_from_env(env)

    def test_embedded_provider_credentials_are_rejected(self):
        env = self._env()
        env["PHANTOMX_POLYGON_PROVIDERS_JSON"] = json.dumps([
            {"name": "primary", "endpoint_url": "https://user:secret@rpc.example/rpc"},
        ])
        env["PHANTOMX_POLYGON_QUORUM"] = "1"
        with self.assertRaises(ProductionAuthorityConfigError):
            load_production_authority_config_from_env(env)

    def test_duplicate_provider_names_are_rejected(self):
        env = self._env()
        env["PHANTOMX_POLYGON_PROVIDERS_JSON"] = json.dumps([
            {"name": "same", "endpoint_url": "https://one.example/rpc"},
            {"name": "same", "endpoint_url": "https://two.example/rpc"},
        ])
        with self.assertRaises(ProductionAuthorityConfigError):
            load_production_authority_config_from_env(env)

    def test_unknown_provider_fields_are_rejected(self):
        env = self._env()
        env["PHANTOMX_POLYGON_PROVIDERS_JSON"] = json.dumps([
            {"name": "primary", "endpoint_url": "https://rpc.example/rpc", "secret": "x"},
        ])
        env["PHANTOMX_POLYGON_QUORUM"] = "1"
        with self.assertRaises(ProductionAuthorityConfigError):
            load_production_authority_config_from_env(env)

    def test_zero_executor_or_signer_is_rejected(self):
        env = self._env()
        env["PHANTOMX_EXECUTOR_ADDRESS"] = "0x" + "00" * 20
        with self.assertRaises(ProductionAuthorityConfigError):
            load_production_authority_config_from_env(env)

    def test_provider_factory_exposes_existing_read_only_boundary(self):
        provider = ProductionProviderConfig("primary", "https://rpc.example/rpc").as_rpc_provider()
        self.assertIsInstance(provider, RPCProvider)
        self.assertEqual(provider.name, "primary")
        self.assertEqual(provider.transport.__class__.__name__, "PolygonRPCHTTPTransport")

    def test_observation_uses_existing_quorum_and_owner_binding(self):
        config = load_production_authority_config_from_env(self._env())
        fake_evidence = SimpleNamespace(observed_block=123)
        with patch("phantomx.production_authority.observe_executor_authority_quorum", return_value=fake_evidence) as observe, patch(
            "phantomx.production_authority.verify_executor_authority"
        ) as verify:
            result = observe_production_executor_authority(config)
        self.assertIs(result, fake_evidence)
        observe.assert_called_once()
        observe_call = observe.call_args
        self.assertEqual(observe_call.args[1], EXECUTOR)
        self.assertEqual(observe_call.kwargs["quorum"], 2)
        verify.assert_called_once_with(
            fake_evidence,
            chain_id=137,
            executor=EXECUTOR,
            sender=SIGNER,
            minimum_observed_block=123,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
