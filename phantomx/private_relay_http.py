"""Strict HTTP JSON-RPC transport for an explicitly private Phase-19 relay.

This boundary is intentionally narrower than a generic RPC client. It exposes
only ``eth_sendRawTransaction`` and requires an explicit operator assertion that
the configured endpoint is a private relay. There is no read path, no public
fallback, and no signer responsibility.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class PrivateRelayHTTPError(ValueError):
    """Raised when the configured private relay cannot be trusted."""


@dataclass(frozen=True)
class PrivateRelayHTTPConfig:
    """Explicit private-relay endpoint configuration.

    Authentication material is supplied separately and is intentionally hidden
    from repr/equality so it cannot become routine diagnostic output.
    """

    name: str
    endpoint_url: str
    timeout_seconds: float = 5.0
    is_private: bool = True
    auth_token: str | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise PrivateRelayHTTPError("private relay name is required")
        if not isinstance(self.endpoint_url, str) or not self.endpoint_url.strip():
            raise PrivateRelayHTTPError("private relay endpoint is required")
        parsed = urlsplit(self.endpoint_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise PrivateRelayHTTPError("private relay endpoint must use HTTPS")
        if parsed.username is not None or parsed.password is not None:
            raise PrivateRelayHTTPError("private relay endpoint must not contain embedded credentials")
        if self.is_private is not True:
            raise PrivateRelayHTTPError("private relay requires an explicit private assertion")
        if (
            not isinstance(self.timeout_seconds, (int, float))
            or isinstance(self.timeout_seconds, bool)
            or self.timeout_seconds <= 0
            or self.timeout_seconds > 60
        ):
            raise PrivateRelayHTTPError("timeout must be greater than zero and at most 60 seconds")
        if self.auth_token is not None and (not isinstance(self.auth_token, str) or not self.auth_token):
            raise PrivateRelayHTTPError("auth token must be a non-empty string when supplied")


class PrivateRelayHTTPTransport:
    """One-endpoint private relay transport implementing the PrivateRelay contract."""

    is_private = True

    def __init__(self, config: PrivateRelayHTTPConfig) -> None:
        if not isinstance(config, PrivateRelayHTTPConfig):
            raise PrivateRelayHTTPError("config must be PrivateRelayHTTPConfig")
        self.config = config
        self.name = config.name
        self._request_id = 0

    def submit_raw_transaction(self, raw_transaction: bytes) -> str:
        if not isinstance(raw_transaction, bytes) or not raw_transaction:
            raise PrivateRelayHTTPError("raw transaction must be non-empty bytes")
        self._request_id += 1
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": "eth_sendRawTransaction",
                "params": ["0x" + raw_transaction.hex()],
            },
            separators=(",", ":"),
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.auth_token is not None:
            headers["Authorization"] = "Bearer " + self.config.auth_token
        request = Request(self.config.endpoint_url, data=payload, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=float(self.config.timeout_seconds)) as response:
                body = response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise PrivateRelayHTTPError("private relay HTTP transport failure") from exc

        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PrivateRelayHTTPError("private relay response is not valid UTF-8 JSON") from exc
        if not isinstance(decoded, Mapping):
            raise PrivateRelayHTTPError("private relay JSON-RPC response must be an object")
        if decoded.get("jsonrpc") not in (None, "2.0"):
            raise PrivateRelayHTTPError("private relay returned an invalid JSON-RPC version")
        if decoded.get("id") not in (None, self._request_id):
            raise PrivateRelayHTTPError("private relay returned a mismatched JSON-RPC id")
        if "error" in decoded:
            raise PrivateRelayHTTPError("private relay rejected the transaction")
        result = decoded.get("result")
        if not isinstance(result, str) or len(result) != 66 or not result.startswith("0x"):
            raise PrivateRelayHTTPError("private relay returned an invalid transaction hash")
        try:
            bytes.fromhex(result[2:])
        except ValueError as exc:
            raise PrivateRelayHTTPError("private relay returned a non-hex transaction hash") from exc
        return result.lower()
