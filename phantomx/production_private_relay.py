"""Controlled production private-relay assembly for Phase 19.

The module accepts only explicitly supplied operator configuration and wires it
to the dedicated private-relay transport. It never chooses defaults, never
creates signing keys, and never provides a public-RPC fallback.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .private_relay_http import PrivateRelayHTTPConfig, PrivateRelayHTTPTransport


class ProductionPrivateRelayConfigError(ValueError):
    """Raised when private-relay configuration is missing or unsafe."""


@dataclass(frozen=True)
class ProductionPrivateRelayConfig:
    """Complete operator-supplied configuration for one private relay."""

    name: str
    endpoint_url: str
    timeout_seconds: float = 5.0
    auth_token: str | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ProductionPrivateRelayConfigError("private relay name is required")
        if not isinstance(self.endpoint_url, str) or not self.endpoint_url.strip():
            raise ProductionPrivateRelayConfigError("private relay endpoint is required")
        parsed = urlsplit(self.endpoint_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ProductionPrivateRelayConfigError("production private relay endpoint must use HTTPS")
        if parsed.username is not None or parsed.password is not None:
            raise ProductionPrivateRelayConfigError("private relay endpoint must not contain embedded credentials")
        if (
            not isinstance(self.timeout_seconds, (int, float))
            or isinstance(self.timeout_seconds, bool)
            or self.timeout_seconds <= 0
            or self.timeout_seconds > 60
        ):
            raise ProductionPrivateRelayConfigError("timeout must be greater than zero and at most 60 seconds")
        if self.auth_token is not None and (not isinstance(self.auth_token, str) or not self.auth_token):
            raise ProductionPrivateRelayConfigError("auth token must be a non-empty string when supplied")

    def as_private_relay(self) -> PrivateRelayHTTPTransport:
        return PrivateRelayHTTPTransport(
            PrivateRelayHTTPConfig(
                name=self.name,
                endpoint_url=self.endpoint_url,
                timeout_seconds=self.timeout_seconds,
                is_private=True,
                auth_token=self.auth_token,
            )
        )


def load_production_private_relay_config_from_env(
    env: dict[str, str] | None = None,
) -> ProductionPrivateRelayConfig:
    """Load an explicit private-relay endpoint and optional token from environment."""
    source = os.environ if env is None else env
    raw = source.get("PHANTOMX_PRIVATE_RELAY_JSON")
    if not raw:
        raise ProductionPrivateRelayConfigError("required private relay configuration is missing")
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ProductionPrivateRelayConfigError("private relay configuration is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ProductionPrivateRelayConfigError("private relay configuration must be a JSON object")
    allowed = {"name", "endpoint_url", "timeout_seconds", "is_private"}
    if set(data) - allowed:
        raise ProductionPrivateRelayConfigError("private relay configuration contains unknown fields")
    if data.get("is_private") is not True:
        raise ProductionPrivateRelayConfigError("private relay configuration must explicitly assert private=true")

    return ProductionPrivateRelayConfig(
        name=data.get("name", ""),
        endpoint_url=data.get("endpoint_url", ""),
        timeout_seconds=data.get("timeout_seconds", 5.0),
        auth_token=source.get("PHANTOMX_PRIVATE_RELAY_AUTH_TOKEN") or None,
    )
