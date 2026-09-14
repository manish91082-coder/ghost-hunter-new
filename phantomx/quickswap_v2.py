"""Read-only, block-pinned QuickSwap V2 exact quote adapter.

The adapter deliberately avoids reserve/spot-price reconstruction. It calls the
QuickSwap V2 router's getAmountsOut() with integer token units and a fixed
Ethereum block tag, then converts the returned integer array into ExactQuote.
No signing, transaction submission, or public/private relay behavior exists in
this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .quote_engine import ExactQuote, QuoteEngineError
from .quote_snapshot import QuoteSnapshot

POLYGON_CHAIN_ID = 137
GET_AMOUNTS_OUT_SELECTOR = "d06ca61f"


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform one JSON-RPC request and return its result."""


class QuickSwapV2Error(QuoteEngineError):
    """Raised when an exact QuickSwap V2 quote cannot be proven valid."""


@dataclass(frozen=True)
class BlockSnapshot:
    chain_id: int
    block_number: int
    timestamp: int


def _hex_uint(value: int, *, name: str) -> str:
    if not isinstance(value, int) or value < 0:
        raise QuickSwapV2Error(f"{name} must be a non-negative integer")
    return hex(value)


def _address_word(address: str) -> bytes:
    if not isinstance(address, str):
        raise QuickSwapV2Error("token address must be a string")
    raw = address[2:] if address.startswith(("0x", "0X")) else address
    if len(raw) != 40:
        raise QuickSwapV2Error("token address must contain exactly 20 bytes")
    try:
        data = bytes.fromhex(raw)
    except ValueError as exc:
        raise QuickSwapV2Error("token address is not valid hexadecimal") from exc
    return b"\x00" * 12 + data


def _encode_get_amounts_out(amount_in: int, path: Sequence[str]) -> str:
    if amount_in <= 0:
        raise QuickSwapV2Error("amount_in must be positive")
    if len(path) < 2:
        raise QuickSwapV2Error("QuickSwap V2 path must contain at least two tokens")

    payload = bytearray.fromhex(GET_AMOUNTS_OUT_SELECTOR)
    payload.extend(amount_in.to_bytes(32, "big"))
    payload.extend((64).to_bytes(32, "big"))
    payload.extend(len(path).to_bytes(32, "big"))
    for address in path:
        payload.extend(_address_word(address))
    return "0x" + bytes(payload).hex()


def _decode_uint_array(result: Any, expected_length: int) -> list[int]:
    if not isinstance(result, str) or not result.startswith("0x"):
        raise QuickSwapV2Error("RPC quote result must be 0x-prefixed hex")
    try:
        raw = bytes.fromhex(result[2:])
    except ValueError as exc:
        raise QuickSwapV2Error("RPC quote result is not valid hexadecimal") from exc

    if len(raw) < 64 or len(raw) % 32:
        raise QuickSwapV2Error("malformed uint256[] ABI result")
    offset = int.from_bytes(raw[:32], "big")
    if offset != 32:
        raise QuickSwapV2Error("unexpected uint256[] ABI offset")
    count = int.from_bytes(raw[32:64], "big")
    if count != expected_length:
        raise QuickSwapV2Error("router returned an unexpected path length")
    end = 64 + count * 32
    if len(raw) < end:
        raise QuickSwapV2Error("truncated uint256[] ABI result")
    return [int.from_bytes(raw[i : i + 32], "big") for i in range(64, end, 32)]


def _parse_chain_id(value: Any) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise QuickSwapV2Error("eth_chainId returned malformed data")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise QuickSwapV2Error("eth_chainId returned invalid hexadecimal") from exc


def _parse_block_number(value: Any) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise QuickSwapV2Error("eth_blockNumber returned malformed data")
    try:
        block = int(value, 16)
    except ValueError as exc:
        raise QuickSwapV2Error("eth_blockNumber returned invalid hexadecimal") from exc
    if block < 0:
        raise QuickSwapV2Error("negative block number")
    return block


def _parse_block_timestamp(value: Any) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise QuickSwapV2Error("block timestamp is malformed")
    try:
        timestamp = int(value, 16)
    except ValueError as exc:
        raise QuickSwapV2Error("block timestamp is not valid hexadecimal") from exc
    if timestamp <= 0:
        raise QuickSwapV2Error("block timestamp must be positive")
    return timestamp


class QuickSwapV2ExactQuoter:
    """Exact QuickSwap V2 router quoting over an injected read-only RPC."""

    def __init__(self, rpc: RpcTransport, router_address: str, chain_id: int = POLYGON_CHAIN_ID) -> None:
        if chain_id != POLYGON_CHAIN_ID:
            raise QuickSwapV2Error("QuickSwap V2 adapter is Polygon-mainnet only")
        _address_word(router_address)
        self._rpc = rpc
        self.router_address = router_address
        self.chain_id = chain_id

    def snapshot(self) -> BlockSnapshot:
        chain_id = _parse_chain_id(self._rpc.call("eth_chainId", []))
        if chain_id != self.chain_id:
            raise QuickSwapV2Error(f"unexpected chain id: {chain_id}")
        block_number = _parse_block_number(self._rpc.call("eth_blockNumber", []))
        block_tag = _hex_uint(block_number, name="block_number")
        block = self._rpc.call("eth_getBlockByNumber", [block_tag, False])
        if not isinstance(block, Mapping) or "timestamp" not in block:
            raise QuickSwapV2Error("eth_getBlockByNumber returned malformed data")
        timestamp = _parse_block_timestamp(block["timestamp"])
        return BlockSnapshot(chain_id=chain_id, block_number=block_number, timestamp=timestamp)

    def quote(
        self,
        amount_in: int,
        path: Sequence[str],
        snapshot: BlockSnapshot,
    ) -> ExactQuote:
        if snapshot.chain_id != self.chain_id:
            raise QuickSwapV2Error("snapshot chain identity mismatch")
        if snapshot.block_number < 0:
            raise QuickSwapV2Error("snapshot block number cannot be negative")
        if snapshot.timestamp <= 0:
            raise QuickSwapV2Error("snapshot timestamp must be positive")
        if amount_in <= 0:
            raise QuickSwapV2Error("amount_in must be positive")
        if len(path) < 2:
            raise QuickSwapV2Error("path must contain at least two tokens")

        data = _encode_get_amounts_out(amount_in, path)
        params = [
            {"to": self.router_address, "data": data},
            _hex_uint(snapshot.block_number, name="block_number"),
        ]
        result = self._rpc.call("eth_call", params)
        if isinstance(result, Mapping):
            raise QuickSwapV2Error("eth_call returned an RPC error object")
        amounts = _decode_uint_array(result, len(path))
        if amounts[0] != amount_in:
            raise QuickSwapV2Error("router quote input does not match requested input")
        amount_out = amounts[-1]
        if amount_out <= 0:
            raise QuickSwapV2Error("router returned zero output")

        return ExactQuote(
            venue="quickswap_v2",
            token_in=path[0],
            token_out=path[-1],
            amount_in=amount_in,
            amount_out=amount_out,
            block_number=snapshot.block_number,
            fee_raw=0,
        )

    def quote_snapshot(
        self,
        amount_in: int,
        path: Sequence[str],
        snapshot: BlockSnapshot,
        *,
        gas_estimate: int | None = None,
    ) -> QuoteSnapshot:
        """Create evidence anchored to the actual timestamp of the pinned block."""
        quote = self.quote(amount_in, path, snapshot)
        return QuoteSnapshot.from_exact_quote(
            quote,
            chain_id=self.chain_id,
            observed_at_unix=snapshot.timestamp,
            pool_or_router=self.router_address,
            gas_estimate=gas_estimate,
        )


def quote_quickswap_v2_exact(
    rpc: RpcTransport,
    router_address: str,
    amount_in: int,
    path: Sequence[str],
) -> ExactQuote:
    """Convenience API: pin one Polygon block, then quote against that block."""
    quoter = QuickSwapV2ExactQuoter(rpc, router_address)
    snapshot = quoter.snapshot()
    return quoter.quote(amount_in, path, snapshot)
