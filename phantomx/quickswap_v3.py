"""Read-only, block-pinned QuickSwap V3 (Algebra) exact quote adapter.

QuickSwap Polygon V3 is Algebra-based. Unlike Uniswap V3, the base pool is
resolved by poolByPair(tokenA, tokenB), and the quoter returns both amountOut
and the dynamically selected fee for the exact input quote.

This adapter is discovery-only until router calldata and execution-proof gates
are separately certified.
"""
from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from .market_block import MarketBlockSnapshot, acquire_market_block
from .quote_engine import ExactQuote, QuoteEngineError
from .quote_snapshot import QuoteSnapshot

POLYGON_CHAIN_ID = 137
POOL_BY_PAIR_SELECTOR = "d9a641e1"
QUOTE_EXACT_INPUT_SINGLE_SELECTOR = "2d9ebd1d"


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform one JSON-RPC request and return its result."""


class QuickSwapV3Error(QuoteEngineError):
    """Raised when an exact QuickSwap V3 quote cannot be proven valid."""


BlockSnapshot = MarketBlockSnapshot


def _address_word(address: str) -> bytes:
    if not isinstance(address, str):
        raise QuickSwapV3Error("address must be a string")
    raw = address[2:] if address.startswith(("0x", "0X")) else address
    if len(raw) != 40:
        raise QuickSwapV3Error("address must contain exactly 20 bytes")
    try:
        data = bytes.fromhex(raw)
    except ValueError as exc:
        raise QuickSwapV3Error("address is not valid hexadecimal") from exc
    return b"\x00" * 12 + data


def _uint_word(value: int, name: str, bits: int = 256) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value >= 1 << bits:
        raise QuickSwapV3Error(f"{name} is outside uint{bits} range")
    return value.to_bytes(32, "big")


def _encode_pool_by_pair(token_a: str, token_b: str) -> str:
    return "0x" + (
        bytes.fromhex(POOL_BY_PAIR_SELECTOR)
        + _address_word(token_a)
        + _address_word(token_b)
    ).hex()


def _encode_quote_exact_input_single(
    token_in: str, token_out: str, amount_in: int, limit_sqrt_price: int = 0
) -> str:
    if amount_in <= 0:
        raise QuickSwapV3Error("amount_in must be positive")
    return "0x" + (
        bytes.fromhex(QUOTE_EXACT_INPUT_SINGLE_SELECTOR)
        + _address_word(token_in)
        + _address_word(token_out)
        + _uint_word(amount_in, "amount_in")
        + _uint_word(limit_sqrt_price, "limit_sqrt_price", 160)
    ).hex()


def _result_bytes(result: Any, label: str) -> bytes:
    if isinstance(result, Mapping):
        raise QuickSwapV3Error(f"{label}: RPC error object")
    if not isinstance(result, str) or not result.startswith("0x"):
        raise QuickSwapV3Error(f"{label}: result must be 0x-prefixed hex")
    try:
        return bytes.fromhex(result[2:])
    except ValueError as exc:
        raise QuickSwapV3Error(f"{label}: malformed hexadecimal result") from exc


def _decode_pool(result: Any) -> str:
    raw = _result_bytes(result, "poolByPair")
    if len(raw) != 32:
        raise QuickSwapV3Error("poolByPair: malformed ABI result")
    address = raw[12:]
    if address == bytes(20):
        raise QuickSwapV3Error("QuickSwap V3 pool does not exist for requested pair")
    return "0x" + address.hex()


def _decode_quote(result: Any) -> tuple[int, int]:
    raw = _result_bytes(result, "quoteExactInputSingle")
    if len(raw) < 64 or len(raw) % 32:
        raise QuickSwapV3Error("quoteExactInputSingle: malformed ABI result")
    amount_out = int.from_bytes(raw[:32], "big")
    fee = int.from_bytes(raw[32:64], "big")
    if amount_out <= 0:
        raise QuickSwapV3Error("QuickSwap V3 returned zero output")
    if fee < 0 or fee >= 1 << 16:
        raise QuickSwapV3Error("QuickSwap V3 fee is outside uint16 range")
    return amount_out, fee


class QuickSwapV3ExactQuoter:
    """Exact single-hop QuickSwap V3 Algebra Quoter over read-only RPC."""

    def __init__(self, rpc: RpcTransport, factory_address: str, quoter_address: str,
                 chain_id: int = POLYGON_CHAIN_ID) -> None:
        if chain_id != POLYGON_CHAIN_ID:
            raise QuickSwapV3Error("QuickSwap V3 adapter is Polygon-mainnet only")
        _address_word(factory_address)
        _address_word(quoter_address)
        self._rpc = rpc
        self.factory_address = factory_address
        self.quoter_address = quoter_address
        self.chain_id = chain_id

    def snapshot(self) -> BlockSnapshot:
        try:
            return acquire_market_block(self._rpc, expected_chain_id=self.chain_id)
        except Exception as exc:
            raise QuickSwapV3Error(str(exc)) from exc

    def resolve_pool(self, token_in: str, token_out: str, snapshot: BlockSnapshot) -> str:
        if snapshot.chain_id != self.chain_id:
            raise QuickSwapV3Error("snapshot chain identity mismatch")
        if token_in.lower() == token_out.lower():
            raise QuickSwapV3Error("token_in and token_out must differ")
        result = self._rpc.call(
            "eth_call",
            [
                {"to": self.factory_address, "data": _encode_pool_by_pair(token_in, token_out)},
                hex(snapshot.block_number),
            ],
        )
        return _decode_pool(result)

    def quote(
        self,
        amount_in: int,
        token_in: str,
        token_out: str,
        snapshot: BlockSnapshot,
        *,
        limit_sqrt_price: int = 0,
    ) -> ExactQuote:
        if amount_in <= 0:
            raise QuickSwapV3Error("amount_in must be positive")
        pool = self.resolve_pool(token_in, token_out, snapshot)
        result = self._rpc.call(
            "eth_call",
            [
                {
                    "to": self.quoter_address,
                    "data": _encode_quote_exact_input_single(
                        token_in, token_out, amount_in, limit_sqrt_price
                    ),
                },
                hex(snapshot.block_number),
            ],
        )
        amount_out, fee = _decode_quote(result)
        return ExactQuote(
            f"quickswap_v3:{pool.lower()}",
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
        snapshot: BlockSnapshot,
        *,
        gas_estimate: int | None = None,
        limit_sqrt_price: int = 0,
    ) -> QuoteSnapshot:
        quote = self.quote(
            amount_in,
            token_in,
            token_out,
            snapshot,
            limit_sqrt_price=limit_sqrt_price,
        )
        pool = quote.venue.split(":", 1)[1]
        return QuoteSnapshot.from_exact_quote(
            quote,
            chain_id=self.chain_id,
            observed_at_unix=snapshot.timestamp,
            pool_or_router=pool,
            gas_estimate=gas_estimate,
        )


__all__ = [
    "BlockSnapshot",
    "POOL_BY_PAIR_SELECTOR",
    "QUOTE_EXACT_INPUT_SINGLE_SELECTOR",
    "QuickSwapV3Error",
    "QuickSwapV3ExactQuoter",
    "_encode_pool_by_pair",
    "_encode_quote_exact_input_single",
]
