"""Fail-closed, read-only Polygon JSON-RPC boundary.

This module deliberately has no signing, transaction submission, or relay
capability. It verifies chain identity and provider observations before they
can influence nonce reconciliation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .polygon_nonce import ChainNonceObservation, PolygonNonceError, parse_quantity, quorum_pending_nonce

POLYGON_CHAIN_ID = 137


class PolygonRPCError(RuntimeError):
    """Raised when an approved read observation cannot be trusted."""


@dataclass(frozen=True)
class RPCProvider:
    name: str
    transport: Callable[[str, Any], Mapping[str, Any]]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise PolygonRPCError("provider name is required")


def _result(response: Mapping[str, Any], method: str) -> Any:
    if not isinstance(response, Mapping):
        raise PolygonRPCError(f"{method}: response must be an object")
    if response.get("error") is not None:
        raise PolygonRPCError(f"{method}: RPC error")
    if "result" not in response:
        raise PolygonRPCError(f"{method}: missing result")
    return response["result"]


def verify_chain(provider: RPCProvider, expected_chain_id: int = POLYGON_CHAIN_ID) -> int:
    """Verify eth_chainId before accepting any other provider observation."""
    value = _result(provider.transport("eth_chainId",), "eth_chainId")
    chain_id = parse_quantity(value, field="chainId")
    if chain_id != expected_chain_id:
        raise PolygonRPCError(f"unexpected chain id: {chain_id}")
    return chain_id


def pending_nonce_observation(provider: RPCProvider, sender: str) -> ChainNonceObservation:
    """Obtain a pending nonce only after chain identity verification."""
    verify_chain(provider)
    response = provider.transport("eth_getTransactionCount", sender, "pending")
    if not isinstance(response, Mapping):
        raise PolygonRPCError("eth_getTransactionCount: malformed response")
    if response.get("error") is not None:
        raise PolygonRPCError("eth_getTransactionCount: RPC error")
    if "result" not in response:
        raise PolygonRPCError("eth_getTransactionCount: missing result")
    try:
        nonce = parse_quantity(response["result"], field="pending nonce")
        return ChainNonceObservation(sender.lower(), nonce, provider=provider.name)
    except PolygonNonceError as exc:
        raise PolygonRPCError(str(exc)) from exc


def quorum_pending_nonce_from_providers(providers: Sequence[RPCProvider], sender: str, *, quorum: int) -> ChainNonceObservation:
    """Require unique provider consensus before returning a nonce observation."""
    if not providers:
        raise PolygonRPCError("at least one provider is required")
    observations = [pending_nonce_observation(provider, sender) for provider in providers]
    try:
        return quorum_pending_nonce(observations, quorum=quorum)
    except PolygonNonceError as exc:
        raise PolygonRPCError(str(exc)) from exc
