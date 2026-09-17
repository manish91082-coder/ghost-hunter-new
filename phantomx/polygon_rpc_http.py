"""Strict read-only HTTP transport for Phase-19 Polygon JSON-RPC.

The transport is deliberately narrower than a generic JSON-RPC client: only
allowlisted read methods can cross the network boundary. It has no signing,
transaction submission, relay, or broadcast capability.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .polygon_rpc import PolygonRPCError, RPCProvider

READ_ONLY_METHODS = frozenset(
    {
        "eth_chainId",
        "eth_blockNumber",
        "eth_getBlockByNumber",
        "eth_getTransactionCount",
        "eth_getTransactionByHash",
        "eth_getTransactionReceipt",
        "eth_getCode",
        "eth_call",
    }
)
_BLOCKED_METHODS = frozenset(
    {
        "eth_sendRawTransaction",
        "eth_sendTransaction",
        "personal_sendTransaction",
        "parity_submitTransaction",
        "wallet_sendTransaction",
    }
)


class PolygonRPCHTTPError(PolygonRPCError):
    """Raised when an HTTP JSON-RPC read cannot be trusted."""


@dataclass(frozen=True)
class PolygonRPCHTTPConfig:
    """Validated endpoint configuration for one explicit provider."""

    provider_name: str
    endpoint_url: str
    timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        if not isinstance(self.provider_name, str) or not self.provider_name.strip():
            raise PolygonRPCHTTPError("provider name is required")
        if not isinstance(self.endpoint_url, str) or not self.endpoint_url.strip():
            raise PolygonRPCHTTPError("endpoint URL is required")
        if not self.endpoint_url.startswith(("https://", "http://")):
            raise PolygonRPCHTTPError("endpoint URL must use HTTP(S)")
        if "://" in self.endpoint_url and "@" in self.endpoint_url.split("://", 1)[1].split("/", 1)[0]:
            raise PolygonRPCHTTPError("endpoint URL must not contain embedded userinfo")
        if (
            not isinstance(self.timeout_seconds, (int, float))
            or isinstance(self.timeout_seconds, bool)
            or self.timeout_seconds <= 0
            or self.timeout_seconds > 60
        ):
            raise PolygonRPCHTTPError("timeout must be greater than zero and at most 60 seconds")


class PolygonRPCHTTPTransport:
    """One-provider, read-only JSON-RPC-over-HTTP transport."""

    def __init__(self, config: PolygonRPCHTTPConfig) -> None:
        if not isinstance(config, PolygonRPCHTTPConfig):
            raise PolygonRPCHTTPError("config must be PolygonRPCHTTPConfig")
        self.config = config
        self._request_id = 0

    def __call__(self, method: str, *params: Any) -> Mapping[str, Any]:
        return self.call(method, params)

    def call(self, method: str, params: Sequence[Any] = ()) -> Mapping[str, Any]:
        if method in _BLOCKED_METHODS or method not in READ_ONLY_METHODS:
            raise PolygonRPCHTTPError(f"RPC method is not allowlisted for read-only transport: {method}")
        if not isinstance(params, Sequence) or isinstance(params, (str, bytes, bytearray)):
            raise PolygonRPCHTTPError("RPC params must be a sequence")

        self._request_id += 1
        payload = json.dumps(
            {"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": list(params)},
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            self.config.endpoint_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "PhantomX-ReadOnly-RPC/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=float(self.config.timeout_seconds)) as response:
                body = response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", None)
            reason_type = type(reason).__name__ if reason is not None else type(exc).__name__
            status = getattr(exc, "code", None)
            status_part = f" status={status}" if isinstance(status, int) else ""
            raise PolygonRPCHTTPError(
                f"{method}: HTTP transport failure [{type(exc).__name__}: {reason_type}{status_part}]"
            ) from exc

        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PolygonRPCHTTPError(f"{method}: response is not valid UTF-8 JSON") from exc
        if not isinstance(decoded, Mapping):
            raise PolygonRPCHTTPError(f"{method}: JSON-RPC response must be an object")
        if decoded.get("jsonrpc") not in (None, "2.0"):
            raise PolygonRPCHTTPError(f"{method}: invalid JSON-RPC version")
        if decoded.get("id") not in (None, self._request_id):
            raise PolygonRPCHTTPError(f"{method}: JSON-RPC response id mismatch")
        if "error" not in decoded and "result" not in decoded:
            raise PolygonRPCHTTPError(f"{method}: response has neither result nor error")
        return decoded

    def as_provider(self) -> RPCProvider:
        """Expose the transport through the existing fail-closed RPC boundary."""
        return RPCProvider(name=self.config.provider_name, transport=self)
