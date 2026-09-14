"""Read-only, block-pinned QuickSwap V2 exact quote adapter."""
from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from .market_block import MarketBlockSnapshot, acquire_market_block
from .quote_engine import ExactQuote, QuoteEngineError
from .quote_snapshot import QuoteSnapshot

POLYGON_CHAIN_ID = 137
GET_AMOUNTS_OUT_SELECTOR = "d06ca61f"


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform one JSON-RPC request and return its result."""


class QuickSwapV2Error(QuoteEngineError):
    """Raised when an exact QuickSwap V2 quote cannot be proven valid."""


BlockSnapshot = MarketBlockSnapshot


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
    if int.from_bytes(raw[:32], "big") != 32:
        raise QuickSwapV2Error("unexpected uint256[] ABI offset")
    count = int.from_bytes(raw[32:64], "big")
    if count != expected_length:
        raise QuickSwapV2Error("router returned an unexpected path length")
    end = 64 + count * 32
    if len(raw) < end:
        raise QuickSwapV2Error("truncated uint256[] ABI result")
    return [int.from_bytes(raw[i:i + 32], "big") for i in range(64, end, 32)]


class QuickSwapV2ExactQuoter:
    """Exact QuickSwap V2 router quoting over injected read-only RPC."""

    def __init__(self, rpc: RpcTransport, router_address: str, chain_id: int = POLYGON_CHAIN_ID) -> None:
        if chain_id != POLYGON_CHAIN_ID:
            raise QuickSwapV2Error("QuickSwap V2 adapter is Polygon-mainnet only")
        _address_word(router_address)
        self._rpc = rpc
        self.router_address = router_address
        self.chain_id = chain_id

    def snapshot(self) -> BlockSnapshot:
        try:
            return acquire_market_block(self._rpc, expected_chain_id=self.chain_id)
        except Exception as exc:
            raise QuickSwapV2Error(str(exc)) from exc

    def quote(self, amount_in: int, path: Sequence[str], snapshot: BlockSnapshot) -> ExactQuote:
        if snapshot.chain_id != self.chain_id:
            raise QuickSwapV2Error("snapshot chain identity mismatch")
        if amount_in <= 0:
            raise QuickSwapV2Error("amount_in must be positive")
        if len(path) < 2:
            raise QuickSwapV2Error("path must contain at least two tokens")
        result = self._rpc.call("eth_call", [
            {"to": self.router_address, "data": _encode_get_amounts_out(amount_in, path)},
            _hex_uint(snapshot.block_number, name="block_number"),
        ])
        if isinstance(result, Mapping):
            raise QuickSwapV2Error("eth_call returned an RPC error object")
        amounts = _decode_uint_array(result, len(path))
        if amounts[0] != amount_in:
            raise QuickSwapV2Error("router quote input does not match requested input")
        if amounts[-1] <= 0:
            raise QuickSwapV2Error("router returned zero output")
        return ExactQuote("quickswap_v2", path[0], path[-1], amount_in, amounts[-1], snapshot.block_number, 0)

    def quote_snapshot(self, amount_in: int, path: Sequence[str], snapshot: BlockSnapshot,
                       *, gas_estimate: int | None = None) -> QuoteSnapshot:
        quote = self.quote(amount_in, path, snapshot)
        return QuoteSnapshot.from_exact_quote(
            quote, chain_id=self.chain_id, observed_at_unix=snapshot.timestamp,
            pool_or_router=self.router_address, gas_estimate=gas_estimate,
        )


def quote_quickswap_v2_exact(rpc: RpcTransport, router_address: str, amount_in: int,
                             path: Sequence[str]) -> ExactQuote:
    quoter = QuickSwapV2ExactQuoter(rpc, router_address)
    return quoter.quote(amount_in, path, quoter.snapshot())
