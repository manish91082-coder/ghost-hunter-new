"""Read-only, block-pinned Uniswap V4 exact quote adapter for Polygon.

This adapter uses the deployed V4Quoter and explicit PoolKey data
(currency0, currency1, fee, tickSpacing, hooks). It never signs or submits.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .market_block import MarketBlockSnapshot
from .quote_engine import ExactQuote, QuoteEngineError
from .quote_snapshot import QuoteSnapshot

POLYGON_CHAIN_ID = 137
V4_QUOTER = "0xb3d5c3dfc3a7aebff71895a7191796bffc2c81b9"
POOL_MANAGER = "0x67366782805870060151383f4bbff9dab53e5cd6"
QUOTE_EXACT_INPUT_SINGLE_SELECTOR = "aa9d21cb"

DEFAULT_FEE_TIERS = (100, 500, 3000, 10000)
DEFAULT_TICK_SPACINGS = (1, 10, 20, 60, 100, 200)
ZERO_HOOK = "0x0000000000000000000000000000000000000000"


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform one JSON-RPC request."""


class UniswapV4Error(QuoteEngineError):
    """Raised when a Uniswap V4 quote cannot be proven valid."""


BlockSnapshot = MarketBlockSnapshot


@dataclass(frozen=True)
class V4PoolKey:
    currency0: str
    currency1: str
    fee: int
    tick_spacing: int
    hooks: str = ZERO_HOOK


def _address_word(address: str) -> bytes:
    if not isinstance(address, str):
        raise UniswapV4Error("address must be a string")
    raw = address[2:] if address.startswith(("0x", "0X")) else address
    if len(raw) != 40:
        raise UniswapV4Error("address must contain exactly 20 bytes")
    try:
        data = bytes.fromhex(raw)
    except ValueError as exc:
        raise UniswapV4Error("address is not valid hexadecimal") from exc
    return b"\x00" * 12 + data


def _uint_word(value: int, name: str, bits: int = 256) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value >= 1 << bits:
        raise UniswapV4Error(f"{name} is outside uint{bits} range")
    return value.to_bytes(32, "big")


def _int24_word(value: int) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0 or value >= 1 << 23:
        raise UniswapV4Error("tick_spacing must be positive int24")
    return value.to_bytes(32, "big")


def _encode_quote_exact_input_single(
    pool_key: V4PoolKey,
    zero_for_one: bool,
    exact_amount: int,
    hook_data: bytes = b"",
) -> str:
    if exact_amount <= 0 or exact_amount >= 1 << 128:
        raise UniswapV4Error("exact_amount is outside uint128 range")
    if pool_key.currency0.lower() >= pool_key.currency1.lower():
        raise UniswapV4Error("PoolKey currencies must be sorted")
    if not 0 <= pool_key.fee <= 1_000_000:
        raise UniswapV4Error("fee is outside LP fee range")
    if pool_key.hooks.lower() != ZERO_HOOK.lower():
        _address_word(pool_key.hooks)
    head = b"".join(
        (
            _uint_word(0x20, "tuple_offset"),
        )
    )
    tuple_head = b"".join(
        (
            _address_word(pool_key.currency0),
            _address_word(pool_key.currency1),
            _uint_word(pool_key.fee, "fee", 24),
            _int24_word(pool_key.tick_spacing),
            _address_word(pool_key.hooks),
            _uint_word(1 if zero_for_one else 0, "zero_for_one", 8),
            _uint_word(exact_amount, "exact_amount", 128),
            _uint_word(0x100, "hook_data_offset"),
        )
    )
    tail = _uint_word(len(hook_data), "hook_data_length") + hook_data
    padded = tail + b"\x00" * ((32 - len(tail) % 32) % 32)
    return "0x" + (bytes.fromhex(QUOTE_EXACT_INPUT_SINGLE_SELECTOR) + head + tuple_head + padded).hex()


def _decode_two_uints(result: Any) -> tuple[int, int]:
    if isinstance(result, Mapping):
        raise UniswapV4Error("V4 quoter returned RPC error object")
    if not isinstance(result, str) or not result.startswith("0x"):
        raise UniswapV4Error("V4 quoter result must be 0x-prefixed hex")
    try:
        raw = bytes.fromhex(result[2:])
    except ValueError as exc:
        raise UniswapV4Error("V4 quoter result is malformed hex") from exc
    if len(raw) != 64:
        raise UniswapV4Error("V4 quoter result must contain amountOut and gasEstimate")
    amount_out = int.from_bytes(raw[:32], "big")
    gas_estimate = int.from_bytes(raw[32:], "big")
    if amount_out <= 0:
        raise UniswapV4Error("V4 quote returned zero output")
    return amount_out, gas_estimate


class UniswapV4ExactQuoter:
    """Exact single-hop Uniswap V4 quote adapter over Polygon JSON-RPC."""

    def __init__(self, rpc: RpcTransport, *, quoter_address: str = V4_QUOTER, pool_manager: str = POOL_MANAGER,
                 chain_id: int = POLYGON_CHAIN_ID) -> None:
        if chain_id != POLYGON_CHAIN_ID:
            raise UniswapV4Error("Uniswap V4 adapter is Polygon-mainnet only")
        _address_word(quoter_address)
        _address_word(pool_manager)
        self._rpc = rpc
        self.quoter_address = quoter_address
        self.pool_manager = pool_manager
        self.chain_id = chain_id

    def quote_snapshot(
        self,
        amount_in: int,
        token_a: str,
        token_b: str,
        pool_key: V4PoolKey,
        snapshot: BlockSnapshot,
        *,
        zero_for_one: bool | None = None,
        hook_data: bytes = b"",
    ) -> QuoteSnapshot:
        if snapshot.chain_id != self.chain_id:
            raise UniswapV4Error("snapshot chain identity mismatch")
        if amount_in <= 0:
            raise UniswapV4Error("amount_in must be positive")
        if token_a.lower() not in (pool_key.currency0.lower(), pool_key.currency1.lower()):
            raise UniswapV4Error("token_a is not in PoolKey")
        if token_b.lower() not in (pool_key.currency0.lower(), pool_key.currency1.lower()):
            raise UniswapV4Error("token_b is not in PoolKey")
        if zero_for_one is None:
            zero_for_one = token_a.lower() == pool_key.currency0.lower()
        expected_out = pool_key.currency1 if zero_for_one else pool_key.currency0
        if token_b.lower() != expected_out.lower():
            raise UniswapV4Error("token direction does not match PoolKey")
        result = self._rpc.call(
            "eth_call",
            [
                {
                    "to": self.quoter_address,
                    "data": _encode_quote_exact_input_single(
                        pool_key, zero_for_one, amount_in, hook_data
                    ),
                },
                hex(snapshot.block_number),
            ],
        )
        amount_out, gas_estimate = _decode_two_uints(result)
        pool_identity = (
            f"uniswap_v4:{pool_key.currency0.lower()}:{pool_key.currency1.lower()}:"
            f"{pool_key.fee}:{pool_key.tick_spacing}:{pool_key.hooks.lower()}"
        )
        quote = ExactQuote(
            pool_identity,
            token_a,
            token_b,
            amount_in,
            amount_out,
            snapshot.block_number,
            pool_key.fee,
        )
        return QuoteSnapshot.from_exact_quote(
            quote,
            chain_id=self.chain_id,
            observed_at_unix=snapshot.timestamp,
            pool_or_router=self.quoter_address,
            gas_estimate=gas_estimate,
        )


__all__ = [
    "BlockSnapshot",
    "DEFAULT_FEE_TIERS",
    "DEFAULT_TICK_SPACINGS",
    "POOL_MANAGER",
    "QUOTE_EXACT_INPUT_SINGLE_SELECTOR",
    "ZERO_HOOK",
    "V4PoolKey",
    "UniswapV4Error",
    "UniswapV4ExactQuoter",
    "_encode_quote_exact_input_single",
]
