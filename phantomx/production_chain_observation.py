"""Quorum-bound production Polygon transaction observation.

This boundary consumes only read-only providers and converts agreeing provider
observations into one immutable, non-secret evidence record. It has no signing
or submission capability. Provider disagreement or insufficient quorum fails
closed instead of allowing a single endpoint to drive settlement recovery.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping, Sequence

from .chain_observer import ChainEvidence, ObservationDecision, observe
from .hashing import keccak256_hex
from .polygon_nonce import parse_quantity
from .polygon_rpc import POLYGON_CHAIN_ID, RPCProvider


class ProductionChainObservationError(ValueError):
    """Raised when production chain evidence is unavailable or ambiguous."""


def _result(response: Mapping[str, Any], method: str) -> Any:
    if not isinstance(response, Mapping):
        raise ProductionChainObservationError(f"{method}: response must be an object")
    if response.get("error") is not None or "result" not in response:
        raise ProductionChainObservationError(f"{method}: RPC result unavailable")
    return response["result"]


def _quantity(value: Any, field: str) -> int:
    try:
        return parse_quantity(value, field=field)
    except Exception as exc:
        raise ProductionChainObservationError(str(exc)) from exc


def _hash(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        raise ProductionChainObservationError(f"{field} must be a 32-byte 0x hash")
    try:
        bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ProductionChainObservationError(f"{field} is not hexadecimal") from exc
    return value.lower()


@dataclass(frozen=True)
class QuorumChainObservation:
    """Canonical chain observation plus the providers that agreed on it."""

    schema_version: int
    chain_id: int
    tx_hash: str
    decision: ObservationDecision
    common_observed_block: int
    attesting_provider_names: tuple[str, ...]
    evidence_hash: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ProductionChainObservationError("unsupported chain-observation schema")
        if self.chain_id != POLYGON_CHAIN_ID:
            raise ProductionChainObservationError("production chain observation is Polygon-only")
        if not isinstance(self.common_observed_block, int) or isinstance(self.common_observed_block, bool) or self.common_observed_block < 0:
            raise ProductionChainObservationError("common observed block must be non-negative")
        if not isinstance(self.attesting_provider_names, tuple) or not self.attesting_provider_names:
            raise ProductionChainObservationError("attesting providers are required")
        if len(set(self.attesting_provider_names)) != len(self.attesting_provider_names):
            raise ProductionChainObservationError("attesting providers must be unique")
        expected = self._digest()
        if self.evidence_hash and self.evidence_hash.lower() != expected:
            raise ProductionChainObservationError("chain observation evidence hash mismatch")
        object.__setattr__(self, "evidence_hash", expected)

    def _digest(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "chain_id": self.chain_id,
            "tx_hash": self.tx_hash.lower(),
            "decision": {
                "state": self.decision.state.value,
                "tx_hash": self.decision.tx_hash.lower(),
                "replacement_tx_hash": self.decision.replacement_tx_hash.lower() if self.decision.replacement_tx_hash else None,
                "evidence_reason": self.decision.evidence_reason,
            },
            "common_observed_block": self.common_observed_block,
            "attesting_provider_names": list(self.attesting_provider_names),
        }
        return keccak256_hex(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())


def _provider_observation(
    provider: RPCProvider,
    *,
    tx_hash: str,
    sender: str,
    tx_nonce: int,
    common_block: int,
) -> ChainEvidence:
    tx_result = _result(provider.transport("eth_getTransactionByHash", tx_hash), f"{provider.name}: eth_getTransactionByHash")
    receipt_result = _result(provider.transport("eth_getTransactionReceipt", tx_hash), f"{provider.name}: eth_getTransactionReceipt")
    pending_result = _result(provider.transport("eth_getTransactionCount", sender, "pending"), f"{provider.name}: eth_getTransactionCount")

    pending_nonce = _quantity(pending_result, f"{provider.name} pending nonce")
    tx_present = tx_result is not None
    receipt_present = receipt_result is not None
    receipt_status = None
    block_hash = None
    block_number = None

    if tx_present:
        if not isinstance(tx_result, Mapping):
            raise ProductionChainObservationError(f"{provider.name}: transaction result malformed")
        observed_nonce = _quantity(tx_result.get("nonce"), f"{provider.name} transaction nonce")
        if observed_nonce != tx_nonce:
            raise ProductionChainObservationError(f"{provider.name}: transaction nonce mismatch")
        observed_hash = tx_result.get("hash") or tx_hash
        if not isinstance(observed_hash, str) or observed_hash.lower() != tx_hash.lower():
            raise ProductionChainObservationError(f"{provider.name}: transaction hash mismatch")

    if receipt_present:
        if not isinstance(receipt_result, Mapping):
            raise ProductionChainObservationError(f"{provider.name}: receipt result malformed")
        receipt_tx_hash = receipt_result.get("transactionHash")
        if not isinstance(receipt_tx_hash, str) or receipt_tx_hash.lower() != tx_hash.lower():
            raise ProductionChainObservationError(f"{provider.name}: receipt transaction hash mismatch")
        receipt_status = _quantity(receipt_result.get("status"), f"{provider.name} receipt status")
        if receipt_status not in (0, 1):
            raise ProductionChainObservationError(f"{provider.name}: invalid receipt status")
        block_hash = _hash(receipt_result.get("blockHash"), f"{provider.name} receipt block hash")
        block_number = _quantity(receipt_result.get("blockNumber"), f"{provider.name} receipt block number")
        canonical = _result(
            provider.transport("eth_getBlockByNumber", "0x" + format(block_number, "x"), False),
            f"{provider.name}: eth_getBlockByNumber",
        )
        canonical_block_hash = None
        if canonical is not None:
            if not isinstance(canonical, Mapping):
                raise ProductionChainObservationError(f"{provider.name}: canonical block result malformed")
            canonical_block_hash = _hash(canonical.get("hash"), f"{provider.name} canonical block hash")
    else:
        canonical_block_hash = None

    return ChainEvidence(
        tx_hash=tx_hash.lower(),
        tx_nonce=tx_nonce,
        pending_nonce=pending_nonce,
        tx_present=tx_present,
        receipt_present=receipt_present,
        receipt_status=receipt_status,
        block_hash=block_hash,
        block_number=block_number,
        canonical_block_hash=canonical_block_hash,
    )


def observe_production_chain_quorum(
    providers: Sequence[RPCProvider],
    *,
    tx_hash: str,
    sender: str,
    tx_nonce: int,
    quorum: int,
) -> QuorumChainObservation:
    """Require a unique quorum-backed transaction/receipt observation."""
    if not providers:
        raise ProductionChainObservationError("at least one provider is required")
    if not isinstance(quorum, int) or isinstance(quorum, bool) or quorum <= 0 or quorum > len(providers):
        raise ProductionChainObservationError("quorum must be between one and provider count")
    if not isinstance(tx_hash, str) or len(tx_hash) != 66 or not tx_hash.startswith("0x"):
        raise ProductionChainObservationError("tx hash must be a 32-byte 0x hash")
    if tx_nonce < 0:
        raise ProductionChainObservationError("transaction nonce must be non-negative")
    names = [provider.name for provider in providers]
    if len(set(names)) != len(names):
        raise ProductionChainObservationError("provider names must be unique")

    chain_blocks: list[int] = []
    for provider in providers:
        chain_id = _quantity(_result(provider.transport("eth_chainId"), f"{provider.name}: eth_chainId"), f"{provider.name} chain id")
        if chain_id != POLYGON_CHAIN_ID:
            raise ProductionChainObservationError(f"{provider.name}: unexpected chain id")
        chain_blocks.append(_quantity(_result(provider.transport("eth_blockNumber"), f"{provider.name}: eth_blockNumber"), f"{provider.name} block number"))
    common_block = min(chain_blocks)

    observations: list[tuple[str, ChainEvidence]] = []
    errors: list[Exception] = []
    for provider in providers:
        try:
            observations.append((provider.name, _provider_observation(provider, tx_hash=tx_hash, sender=sender, tx_nonce=tx_nonce, common_block=common_block)))
        except Exception as exc:
            errors.append(exc)

    if len(observations) < quorum:
        raise ProductionChainObservationError("chain observation provider quorum not reached")

    grouped: dict[tuple[object, ...], list[str]] = {}
    decisions: dict[tuple[object, ...], ObservationDecision] = {}
    for name, evidence in observations:
        decision = observe(evidence)
        key = (
            decision.state.value,
            decision.tx_hash.lower(),
            decision.replacement_tx_hash.lower() if decision.replacement_tx_hash else None,
            evidence.tx_present,
            evidence.receipt_present,
            evidence.receipt_status,
            evidence.block_hash,
            evidence.block_number,
            evidence.canonical_block_hash,
            evidence.pending_nonce,
        )
        grouped.setdefault(key, []).append(name)
        decisions[key] = decision

    ranked = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    winner_key, winner_names = ranked[0]
    if len(winner_names) < quorum:
        raise ProductionChainObservationError("chain observation decision did not reach quorum")
    if len(ranked) > 1 and len(ranked[1][1]) == len(winner_names):
        raise ProductionChainObservationError("chain observation quorum is ambiguous")

    return QuorumChainObservation(
        schema_version=1,
        chain_id=POLYGON_CHAIN_ID,
        tx_hash=tx_hash.lower(),
        decision=decisions[winner_key],
        common_observed_block=common_block,
        attesting_provider_names=tuple(sorted(winner_names)),
    )
