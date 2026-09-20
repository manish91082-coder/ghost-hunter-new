"""Shared immutable market-block context for cross-venue quote acquisition.

A route must be evaluated against one canonical Polygon block. This module
owns only read-only block identity acquisition and contains no signing or
transaction submission capability.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

POLYGON_CHAIN_ID = 137


class MarketBlockError(ValueError):
    """Raised when a canonical market block cannot be proven."""


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform one read-only JSON-RPC request."""


@dataclass(frozen=True)
class MarketBlockSnapshot:
    chain_id: int
    block_number: int
    timestamp: int

    def __post_init__(self) -> None:
        if self.chain_id != POLYGON_CHAIN_ID:
            raise MarketBlockError("market block must be Polygon mainnet")
        if self.block_number < 0:
            raise MarketBlockError("block number cannot be negative")
        if self.timestamp <= 0:
            raise MarketBlockError("block timestamp must be positive")


def _parse_quantity(value: Any, name: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise MarketBlockError(f"{name} is malformed")
    try:
        parsed = int(value, 16)
    except ValueError as exc:
        raise MarketBlockError(f"{name} is not valid hexadecimal") from exc
    if parsed < 0:
        raise MarketBlockError(f"{name} cannot be negative")
    return parsed


def acquire_market_block_at(rpc: RpcTransport, block_number: int, *, expected_chain_id: int = POLYGON_CHAIN_ID) -> MarketBlockSnapshot:
    """Acquire a chain-verified timestamp for an already selected block."""
    if expected_chain_id != POLYGON_CHAIN_ID:
        raise MarketBlockError("only Polygon mainnet is supported")
    if block_number < 0:
        raise MarketBlockError("block number cannot be negative")
    chain_id = _parse_quantity(rpc.call('eth_chainId', []), 'chainId')
    if chain_id != expected_chain_id:
        raise MarketBlockError(f"unexpected chain id: {chain_id}")
    block = rpc.call('eth_getBlockByNumber', [hex(block_number), False])
    if not isinstance(block, Mapping):
        raise MarketBlockError("block result must be an object")
    timestamp = _parse_quantity(block.get('timestamp'), 'block timestamp')
    return MarketBlockSnapshot(chain_id, block_number, timestamp)
def acquire_market_block(rpc: RpcTransport, *, expected_chain_id: int = POLYGON_CHAIN_ID) -> MarketBlockSnapshot:
    """Acquire one chain-verified block and its canonical timestamp."""
    if expected_chain_id != POLYGON_CHAIN_ID:
        raise MarketBlockError("only Polygon mainnet is supported")
    chain_id = _parse_quantity(rpc.call("eth_chainId", []), "chainId")
    if chain_id != expected_chain_id:
        raise MarketBlockError(f"unexpected chain id: {chain_id}")
    block_number = _parse_quantity(rpc.call("eth_blockNumber", []), "blockNumber")
    block = rpc.call("eth_getBlockByNumber", [hex(block_number), False])
    if not isinstance(block, Mapping):
        raise MarketBlockError("block result must be an object")
    timestamp = _parse_quantity(block.get("timestamp"), "block timestamp")
    return MarketBlockSnapshot(chain_id, block_number, timestamp)