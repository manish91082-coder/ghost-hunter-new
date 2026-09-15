"""Controlled production Polygon authority assembly.

This module converts explicitly supplied operator configuration into the
existing read-only RPC provider and executor-authority quorum layers. It never
contains provider defaults, private keys, signing, transaction submission, or
broadcast capability. Missing/ambiguous configuration fails closed.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

from .executor_authority import ExecutorAuthorityEvidence, observe_executor_authority_quorum, verify_executor_authority
from .polygon_rpc import RPCProvider
from .polygon_rpc_http import PolygonRPCHTTPConfig, PolygonRPCHTTPTransport


class ProductionAuthorityConfigError(ValueError):
    """Raised when production authority configuration is absent or unsafe."""


@dataclass(frozen=True)
class ProductionProviderConfig:
    """One operator-approved production Polygon read endpoint."""

    name: str
    endpoint_url: str
    timeout_seconds: float = 5.0

    def as_transport(self) -> PolygonRPCHTTPTransport:
        return PolygonRPCHTTPTransport(
            PolygonRPCHTTPConfig(
                provider_name=self.name,
                endpoint_url=self.endpoint_url,
                timeout_seconds=self.timeout_seconds,
            )
        )

    def as_rpc_provider(self) -> RPCProvider:
        return self.as_transport().as_provider()


@dataclass(frozen=True)
class ProductionAuthorityConfig:
    """Complete operator-supplied authority inputs for a read-only check."""

    providers: tuple[ProductionProviderConfig, ...]
    quorum: int
    executor_address: str
    expected_signer_address: str

    def __post_init__(self) -> None:
        if not self.providers:
            raise ProductionAuthorityConfigError("at least one approved provider is required")
        if len({provider.name for provider in self.providers}) != len(self.providers):
            raise ProductionAuthorityConfigError("approved provider names must be unique")
        if not isinstance(self.quorum, int) or isinstance(self.quorum, bool) or not 1 <= self.quorum <= len(self.providers):
            raise ProductionAuthorityConfigError("quorum must be between one and provider count")
        if _is_zero_address(self.executor_address):
            raise ProductionAuthorityConfigError("executor address must be a non-zero 20-byte address")
        if _is_zero_address(self.expected_signer_address):
            raise ProductionAuthorityConfigError("expected signer address must be a non-zero 20-byte address")
        for provider in self.providers:
            _validate_production_endpoint(provider.endpoint_url)

    def rpc_providers(self) -> tuple[RPCProvider, ...]:
        """Instantiate only read-only provider transports."""
        return tuple(provider.as_rpc_provider() for provider in self.providers)


def _is_zero_address(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise ProductionAuthorityConfigError("address must be a 20-byte 0x-prefixed value")
    try:
        raw = bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ProductionAuthorityConfigError("address must be hexadecimal") from exc
    return raw == b"\x00" * 20


def _validate_production_endpoint(endpoint_url: str) -> None:
    if not isinstance(endpoint_url, str) or not endpoint_url.strip():
        raise ProductionAuthorityConfigError("provider endpoint is required")
    parsed = urlsplit(endpoint_url)
    if parsed.scheme != "https":
        raise ProductionAuthorityConfigError("production Polygon endpoints must use HTTPS")
    if not parsed.hostname:
        raise ProductionAuthorityConfigError("production provider endpoint hostname is required")
    if parsed.username is not None or parsed.password is not None:
        raise ProductionAuthorityConfigError("production provider endpoint must not contain embedded credentials")


def load_production_authority_config_from_env(env: dict[str, str] | None = None) -> ProductionAuthorityConfig:
    """Load operator-approved authority inputs from environment only.

    Expected variables:
      PHANTOMX_POLYGON_PROVIDERS_JSON
        JSON array of objects containing name, endpoint_url, and optionally
        timeout_seconds. No built-in endpoint list is provided.
      PHANTOMX_POLYGON_QUORUM
        Required integer quorum.
      PHANTOMX_EXECUTOR_ADDRESS
        Intended deployed executor address.
      PHANTOMX_EXPECTED_SIGNER_ADDRESS
        Expected production signer address.
    """
    source = os.environ if env is None else env
    required = (
        "PHANTOMX_POLYGON_PROVIDERS_JSON",
        "PHANTOMX_POLYGON_QUORUM",
        "PHANTOMX_EXECUTOR_ADDRESS",
        "PHANTOMX_EXPECTED_SIGNER_ADDRESS",
    )
    missing = [name for name in required if not source.get(name)]
    if missing:
        raise ProductionAuthorityConfigError("required production authority configuration is missing")

    try:
        raw_providers = json.loads(source["PHANTOMX_POLYGON_PROVIDERS_JSON"])
    except (TypeError, json.JSONDecodeError) as exc:
        raise ProductionAuthorityConfigError("provider configuration is not valid JSON") from exc
    if not isinstance(raw_providers, list) or not raw_providers:
        raise ProductionAuthorityConfigError("provider configuration must be a non-empty JSON array")

    providers: list[ProductionProviderConfig] = []
    for item in raw_providers:
        if not isinstance(item, dict):
            raise ProductionAuthorityConfigError("each provider configuration must be an object")
        allowed = {"name", "endpoint_url", "timeout_seconds"}
        if set(item) - allowed:
            raise ProductionAuthorityConfigError("provider configuration contains unknown fields")
        providers.append(
            ProductionProviderConfig(
                name=item.get("name", ""),
                endpoint_url=item.get("endpoint_url", ""),
                timeout_seconds=item.get("timeout_seconds", 5.0),
            )
        )

    try:
        quorum = int(source["PHANTOMX_POLYGON_QUORUM"])
    except (TypeError, ValueError) as exc:
        raise ProductionAuthorityConfigError("production quorum must be an integer") from exc

    return ProductionAuthorityConfig(
        providers=tuple(providers),
        quorum=quorum,
        executor_address=source["PHANTOMX_EXECUTOR_ADDRESS"].lower(),
        expected_signer_address=source["PHANTOMX_EXPECTED_SIGNER_ADDRESS"].lower(),
    )


def observe_production_executor_authority(config: ProductionAuthorityConfig) -> ExecutorAuthorityEvidence:
    """Perform a read-only multi-provider authority observation and exact owner check."""
    evidence = observe_executor_authority_quorum(
        config.rpc_providers(),
        config.executor_address,
        quorum=config.quorum,
    )
    verify_executor_authority(
        evidence,
        chain_id=137,
        executor=config.executor_address,
        sender=config.expected_signer_address,
        minimum_observed_block=evidence.observed_block,
    )
    return evidence
