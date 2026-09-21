"""Polygon chain-state nonce reconciliation primitives.

This module is deliberately transport-agnostic. It validates JSON-RPC shaped
responses but never opens a network connection itself. Production wiring must
supply an approved Polygon RPC transport and keep this read-only path separate
from signing and private submission.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence


class PolygonNonceError(ValueError):
    """Base error for malformed or unsafe chain nonce observations."""


@dataclass(frozen=True)
class ChainNonceObservation:
    sender: str
    pending_nonce: int
    latest_nonce: int | None = None
    provider: str | None = None

    def __post_init__(self) -> None:
        if not self.sender or not self.sender.startswith("0x"):
            raise PolygonNonceError("sender must be a non-empty 0x address")
        if self.pending_nonce < 0:
            raise PolygonNonceError("pending nonce cannot be negative")
        if self.latest_nonce is not None and self.latest_nonce < 0:
            raise PolygonNonceError("latest nonce cannot be negative")
        if self.latest_nonce is not None and self.latest_nonce > self.pending_nonce:
            raise PolygonNonceError("latest nonce cannot exceed pending nonce")


@dataclass(frozen=True)
class NonceReconciliation:
    sender: str
    local_next_nonce: int
    chain_pending_nonce: int
    reconciled_next_nonce: int
    advanced: bool

    def __post_init__(self) -> None:
        if self.reconciled_next_nonce < self.local_next_nonce:
            raise PolygonNonceError("reconciliation must never roll nonce state backward")
        if self.reconciled_next_nonce < self.chain_pending_nonce:
            raise PolygonNonceError("reconciled nonce cannot trail chain pending nonce")


def parse_quantity(value: Any, *, field: str) -> int:
    """Parse an Ethereum JSON-RPC quantity without accepting ambiguous values."""
    if not isinstance(value, str) or not value.startswith("0x"):
        raise PolygonNonceError(f"{field} must be a hex quantity")
    if value == "0x":
        raise PolygonNonceError(f"{field} is empty")
    try:
        number = int(value, 16)
    except ValueError as exc:
        raise PolygonNonceError(f"{field} is not a valid hex quantity") from exc
    if number < 0:
        raise PolygonNonceError(f"{field} cannot be negative")
    return number


def parse_rpc_nonce_response(response: Mapping[str, Any], *, sender: str, provider: str | None = None) -> ChainNonceObservation:
    """Validate an ``eth_getTransactionCount(..., 'pending')`` JSON-RPC result."""
    if not isinstance(response, Mapping):
        raise PolygonNonceError("RPC response must be an object")
    if response.get("error") is not None:
        raise PolygonNonceError(f"RPC nonce error: {response['error']}")
    if "result" not in response:
        raise PolygonNonceError("RPC response missing result")
    pending = parse_quantity(response["result"], field="result")
    return ChainNonceObservation(sender=sender.lower(), pending_nonce=pending, provider=provider)


def pending_nonce(transport: Callable[[str, str, str], Mapping[str, Any]], sender: str, *, provider: str | None = None) -> ChainNonceObservation:
    """Read the chain's pending nonce through an injected read-only transport."""
    if not sender:
        raise PolygonNonceError("sender is required")
    response = transport("eth_getTransactionCount", sender, "pending")
    return parse_rpc_nonce_response(response, sender=sender, provider=provider)


def reconcile(local_next_nonce: int, observation: ChainNonceObservation) -> NonceReconciliation:
    """Advance local allocation state to chain pending nonce, never backward."""
    if local_next_nonce < 0:
        raise PolygonNonceError("local_next_nonce cannot be negative")
    reconciled = max(local_next_nonce, observation.pending_nonce)
    return NonceReconciliation(
        sender=observation.sender,
        local_next_nonce=local_next_nonce,
        chain_pending_nonce=observation.pending_nonce,
        reconciled_next_nonce=reconciled,
        advanced=reconciled > local_next_nonce,
    )


def quorum_pending_nonce(observations: Sequence[ChainNonceObservation], *, quorum: int) -> ChainNonceObservation:
    """Return a quorum-backed pending nonce observation.

    Each observation must identify a distinct provider. The same sender and
    nonce must be reported by at least ``quorum`` providers. A minority/stale
    provider therefore cannot advance local nonce state by itself.
    """
    if not observations:
        raise PolygonNonceError("at least one observation is required")
    if quorum < 1 or quorum > len(observations):
        raise PolygonNonceError("quorum must be within the observation count")
    senders = {item.sender.lower() for item in observations}
    if len(senders) != 1:
        raise PolygonNonceError("quorum observations must target one sender")
    providers = [item.provider for item in observations]
    if any(not provider for provider in providers):
        raise PolygonNonceError("quorum observations require provider identities")
    if len(set(providers)) != len(providers):
        raise PolygonNonceError("quorum observations require distinct providers")

    counts: dict[int, int] = {}
    for item in observations:
        counts[item.pending_nonce] = counts.get(item.pending_nonce, 0) + 1
    winners = [nonce for nonce, count in counts.items() if count >= quorum]
    if len(winners) != 1:
        raise PolygonNonceError("no unique pending nonce reached quorum")
    winner = winners[0]
    source = next(item for item in observations if item.pending_nonce == winner)
    return ChainNonceObservation(
        sender=source.sender,
        pending_nonce=winner,
        provider="quorum:" + ",".join(sorted(x.provider for x in observations if x.pending_nonce == winner and x.provider)),
    )
