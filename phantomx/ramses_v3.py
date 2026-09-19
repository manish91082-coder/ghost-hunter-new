"""Read-only, block-pinned Ramses V3 exact quote adapter for Polygon.

Ramses V3 CL uses tickSpacing as the pool-discovery key. The pool exposes its
fee separately, while QuoterV2 accepts (tokenIn, tokenOut, amountIn,
tickSpacing, sqrtPriceLimitX96) and returns amountOut plus quote metadata.
This adapter never signs, submits, or executes swaps.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .market_block import MarketBlockSnapshot, acquire_market_block
from .quote_engine import ExactQuote, QuoteEngineError
from .quote_snapshot import QuoteSnapshot

POLYGON_CHAIN_ID = 137
GET_POOL_SELECTOR = "28af8d0b"
QUOTE_EXACT_INPUT_SINGLE_SELECTOR = "9e7defe6"
FEE_SELECTOR = "ddca3f43"
SLOT0_SELECTOR = "3850c7bd"
LIQUIDITY_SELECTOR = "1a686502"
DEFAULT_TICK_SPACINGS = (1, 5, 10, 50, 100, 200)


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform one JSON-RPC request and return its result."""


class RamsesV3Error(QuoteEngineError):
    """Raised when an exact Ramses V3 quote cannot be proven valid."""


BlockSnapshot = MarketBlockSnapshot


def _address_word(address: str) -> bytes:
    if not isinstance(address, str):
        raise RamsesV3Error("address must be a string")
    raw = address[2:] if address.startswith(("0x", "0X")) else address
    if len(raw) != 40:
        raise RamsesV3Error("address must contain exactly 20 bytes")
    try:
        data = bytes.fromhex(raw)
    except ValueError as exc:
        raise RamsesV3Error("address is not valid hexadecimal") from exc
    return b"\x00" * 12 + data


def _uint_word(value: int, name: str, bits: int = 256) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value >= 1 << bits:
        raise RamsesV3Error(f"{name} is outside uint{bits} range")
    return value.to_bytes(32, "big")


def _int24_word(value: int) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < -(1 << 23) or value >= 1 << 23:
        raise RamsesV3Error("tick_spacing is outside int24 range")
    return (value & ((1 << 256) - 1)).to_bytes(32, "big")


def _encode_get_pool(token_a: str, token_b: str, tick_spacing: int) -> str:
    return "0x" + (
        bytes.fromhex(GET_POOL_SELECTOR)
        + _address_word(token_a)
        + _address_word(token_b)
        + _int24_word(tick_spacing)
    ).hex()


def _encode_quote_exact_input_single(
    token_in: str,
    token_out: str,
    amount_in: int,
    tick_spacing: int,
    limit_sqrt_price: int = 0,
) -> str:
    if amount_in <= 0:
        raise RamsesV3Error("amount_in must be positive")
    return "0x" + (
        bytes.fromhex(QUOTE_EXACT_INPUT_SINGLE_SELECTOR)
        + _address_word(token_in)
        + _address_word(token_out)
        + _uint_word(amount_in, "amount_in")
        + _int24_word(tick_spacing)
        + _uint_word(limit_sqrt_price, "limit_sqrt_price", 160)
    ).hex()


def _result_bytes(result: Any, label: str) -> bytes:
    if isinstance(result, Mapping):
        raise RamsesV3Error(f"{label}: RPC error object")
    if not isinstance(result, str) or not result.startswith("0x"):
        raise RamsesV3Error(f"{label}: result must be 0x-prefixed hex")
    try:
        return bytes.fromhex(result[2:])
    except ValueError as exc:
        raise RamsesV3Error(f"{label}: malformed hexadecimal result") from exc


def _decode_address(result: Any, label: str) -> str:
    raw = _result_bytes(result, label)
    if len(raw) != 32:
        raise RamsesV3Error(f"{label}: malformed ABI address result")
    address = raw[12:]
    if address == bytes(20):
        raise RamsesV3Error("Ramses V3 pool does not exist for requested tick spacing")
    return "0x" + address.hex()


def _decode_uint(result: Any, label: str, bits: int) -> int:
    raw = _result_bytes(result, label)
    if len(raw) != 32:
        raise RamsesV3Error(f"{label}: malformed ABI uint result")
    value = int.from_bytes(raw, "big")
    if value >= 1 << bits:
        raise RamsesV3Error(f"{label}: value exceeds uint{bits}")
    return value


def _decode_quote(result: Any) -> tuple[int, int, int, int]:
    raw = _result_bytes(result, "quoteExactInputSingle")
    if len(raw) != 128:
        raise RamsesV3Error("quoteExactInputSingle: expected four ABI words")
    amount_out = int.from_bytes(raw[:32], "big")
    sqrt_after = int.from_bytes(raw[32:64], "big")
    ticks_crossed = int.from_bytes(raw[64:96], "big")
    gas_estimate = int.from_bytes(raw[96:128], "big")
    if amount_out <= 0:
        raise RamsesV3Error("Ramses V3 returned zero output")
    if sqrt_after >= 1 << 160:
        raise RamsesV3Error("sqrtPriceX96After exceeds uint160")
    if ticks_crossed >= 1 << 32:
        raise RamsesV3Error("initializedTicksCrossed exceeds uint32")
    return amount_out, sqrt_after, ticks_crossed, gas_estimate


@dataclass(frozen=True)
class RamsesPoolState:
    pool: str
    block_number: int
    sqrt_price_x96: int
    active_liquidity: int
    unlocked: bool

    @property
    def initialized_and_swappable(self) -> bool:
        return self.sqrt_price_x96 > 0 and self.active_liquidity > 0 and self.unlocked


class RamsesV3ExactQuoter:
    """Exact single-hop Ramses V3 QuoterV2 over injected read-only RPC."""

    def __init__(
        self,
        rpc: RpcTransport,
        factory_address: str,
        quoter_address: str,
        chain_id: int = POLYGON_CHAIN_ID,
    ) -> None:
        if chain_id != POLYGON_CHAIN_ID:
            raise RamsesV3Error("Ramses V3 adapter is Polygon-mainnet only")
        _address_word(factory_address)
        _address_word(quoter_address)
        self._rpc = rpc
        self.factory_address = factory_address
        self.quoter_address = quoter_address
        self.chain_id = chain_id
        self._pool_cache: dict[tuple[str, str, int, int], str] = {}
        self._fee_cache: dict[tuple[str, int], int] = {}

    def snapshot(self) -> BlockSnapshot:
        try:
            return acquire_market_block(self._rpc, expected_chain_id=self.chain_id)
        except Exception as exc:
            raise RamsesV3Error(str(exc)) from exc

    def resolve_pool(
        self,
        token_in: str,
        token_out: str,
        tick_spacing: int,
        snapshot: BlockSnapshot,
    ) -> str:
        if snapshot.chain_id != self.chain_id:
            raise RamsesV3Error("snapshot chain identity mismatch")
        if token_in.lower() == token_out.lower():
            raise RamsesV3Error("token_in and token_out must differ")
        key = (token_in.lower(), token_out.lower(), tick_spacing, snapshot.block_number)
        cached = self._pool_cache.get(key)
        if cached is not None:
            return cached
        result = self._rpc.call(
            "eth_call",
            [
                {
                    "to": self.factory_address,
                    "data": _encode_get_pool(token_in, token_out, tick_spacing),
                },
                hex(snapshot.block_number),
            ],
        )
        pool = _decode_address(result, "getPool")
        self._pool_cache[key] = pool
        return pool

    def pool_fee(self, pool: str, snapshot: BlockSnapshot) -> int:
        if snapshot.chain_id != self.chain_id:
            raise RamsesV3Error("snapshot chain identity mismatch")
        key = (pool.lower(), snapshot.block_number)
        cached = self._fee_cache.get(key)
        if cached is not None:
            return cached
        result = self._rpc.call(
            "eth_call",
            [
                {"to": pool, "data": "0x" + FEE_SELECTOR},
                hex(snapshot.block_number),
            ],
        )
        fee = _decode_uint(result, "fee", 24)
        if fee == 0:
            raise RamsesV3Error("Ramses V3 pool returned zero fee")
        self._fee_cache[key] = fee
        return fee

    def pool_state(self, pool: str, snapshot: BlockSnapshot) -> RamsesPoolState:
        if snapshot.chain_id != self.chain_id:
            raise RamsesV3Error("snapshot chain identity mismatch")

        slot_result = self._rpc.call(
            "eth_call",
            [{"to": pool, "data": "0x" + SLOT0_SELECTOR}, hex(snapshot.block_number)],
        )
        slot_raw = _result_bytes(slot_result, "slot0")
        if len(slot_raw) != 224:
            raise RamsesV3Error("slot0: expected seven ABI words")
        sqrt_price_x96 = int.from_bytes(slot_raw[0:32], "big")
        unlocked = int.from_bytes(slot_raw[192:224], "big") != 0

        liquidity_result = self._rpc.call(
            "eth_call",
            [{"to": pool, "data": "0x" + LIQUIDITY_SELECTOR}, hex(snapshot.block_number)],
        )
        liquidity_raw = _result_bytes(liquidity_result, "liquidity")
        if len(liquidity_raw) != 32:
            raise RamsesV3Error("liquidity: expected one ABI word")
        active_liquidity = int.from_bytes(liquidity_raw, "big")

        return RamsesPoolState(
            pool=pool,
            block_number=snapshot.block_number,
            sqrt_price_x96=sqrt_price_x96,
            active_liquidity=active_liquidity,
            unlocked=unlocked,
        )

    def quote(
        self,
        amount_in: int,
        token_in: str,
        token_out: str,
        tick_spacing: int,
        snapshot: BlockSnapshot,
        *,
        limit_sqrt_price: int = 0,
    ) -> ExactQuote:
        if amount_in <= 0:
            raise RamsesV3Error("amount_in must be positive")
        pool = self.resolve_pool(token_in, token_out, tick_spacing, snapshot)
        fee = self.pool_fee(pool, snapshot)
        result = self._rpc.call(
            "eth_call",
            [
                {
                    "to": self.quoter_address,
                    "data": _encode_quote_exact_input_single(
                        token_in, token_out, amount_in, tick_spacing, limit_sqrt_price
                    ),
                },
                hex(snapshot.block_number),
            ],
        )
        amount_out, _sqrt_after, _ticks_crossed, _gas_estimate = _decode_quote(result)
        return ExactQuote(
            f"ramses_v3:{pool.lower()}",
            token_in,
            token_out,
            amount_in,
            amount_out,
            snapshot.block_number,
            fee,
        )

    def quote_snapshot(
        self,
        amount_in: int,
        token_in: str,
        token_out: str,
        tick_spacing: int,
        snapshot: BlockSnapshot,
        *,
        gas_estimate: int | None = None,
        limit_sqrt_price: int = 0,
    ) -> QuoteSnapshot:
        if amount_in <= 0:
            raise RamsesV3Error("amount_in must be positive")
        pool = self.resolve_pool(token_in, token_out, tick_spacing, snapshot)
        fee = self.pool_fee(pool, snapshot)
        result = self._rpc.call(
            "eth_call",
            [
                {
                    "to": self.quoter_address,
                    "data": _encode_quote_exact_input_single(
                        token_in, token_out, amount_in, tick_spacing, limit_sqrt_price
                    ),
                },
                hex(snapshot.block_number),
            ],
        )
        amount_out, _sqrt_after, _ticks_crossed, quoted_gas = _decode_quote(result)
        quote = ExactQuote(
            f"ramses_v3:{pool.lower()}",
            token_in,
            token_out,
            amount_in,
            amount_out,
            snapshot.block_number,
            fee,
        )
        return QuoteSnapshot.from_exact_quote(
            quote,
            chain_id=self.chain_id,
            observed_at_unix=snapshot.timestamp,
            pool_or_router=pool,
            gas_estimate=quoted_gas if gas_estimate is None else gas_estimate,
        )


__all__ = [
    "BlockSnapshot",
    "DEFAULT_TICK_SPACINGS",
    "FEE_SELECTOR",
    "GET_POOL_SELECTOR",
    "QUOTE_EXACT_INPUT_SINGLE_SELECTOR",
    "RamsesV3Error",
    "RamsesPoolState",
    "SLOT0_SELECTOR",
    "LIQUIDITY_SELECTOR",
    "RamsesV3ExactQuoter",
    "_encode_get_pool",
    "_encode_quote_exact_input_single",
]
