"""Fail-closed, read-only Polygon JSON-RPC boundary.

This module deliberately has no signing, transaction submission, or relay
capability. It verifies chain identity and provider observations before they
can influence nonce reconciliation or executor-authority attestation.
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


def read_contract_owner(provider: RPCProvider, contract: str) -> str:
    """Read owner() at one explicit latest block after verifying Polygon chain identity."""
    verify_chain(provider)
    if not isinstance(contract, str) or len(contract) != 42 or not contract.startswith("0x"):
        raise PolygonRPCError("contract must be a 20-byte 0x address")
    try:
        raw = bytes.fromhex(contract[2:])
    except ValueError as exc:
        raise PolygonRPCError("contract is not valid hexadecimal") from exc
    if raw == b"\x00" * 20:
        raise PolygonRPCError("contract must be non-zero")

    block_number = parse_quantity(_result(provider.transport("eth_blockNumber"), "eth_blockNumber"), field="block number")
    block_tag = "0x" + format(block_number, "x")
    call_result = _result(
        provider.transport("eth_call", {"to": contract.lower(), "data": "0x8da5cb5b"}, block_tag),
        "eth_call owner",
    )
    if not isinstance(call_result, str) or not call_result.startswith("0x"):
        raise PolygonRPCError("owner() result must be hex")
    try:
        encoded = bytes.fromhex(call_result[2:])
    except ValueError as exc:
        raise PolygonRPCError("owner() result is not valid hexadecimal") from exc
    if len(encoded) != 32 or encoded[:12] != b"\x00" * 12:
        raise PolygonRPCError("owner() result is not a canonical ABI address word")
    owner = "0x" + encoded[12:].hex()
    if owner == "0x" + "00" * 20:
        raise PolygonRPCError("owner() returned zero address")
    return owner


def read_contract_code(provider: RPCProvider, contract: str) -> tuple[int, str]:
    """Read runtime bytecode at the same explicit latest block used for authority evidence."""
    verify_chain(provider)
    if not isinstance(contract, str) or len(contract) != 42 or not contract.startswith("0x"):
        raise PolygonRPCError("contract must be a 20-byte 0x address")
    block_number = parse_quantity(_result(provider.transport("eth_blockNumber"), "eth_blockNumber"), field="block number")
    block_tag = "0x" + format(block_number, "x")
    code = _result(provider.transport("eth_getCode", contract.lower(), block_tag), "eth_getCode")
    if not isinstance(code, str) or not code.startswith("0x") or len(code) <= 2 or (len(code) - 2) % 2:
        raise PolygonRPCError("runtime code must be non-empty even-length hex")
    return block_number, code.lower()
