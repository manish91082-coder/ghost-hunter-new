"""Read-only, block-pinned Uniswap V3 exact quote adapter."""
from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from .market_block import MarketBlockSnapshot, acquire_market_block
from .quote_engine import ExactQuote, QuoteEngineError
from .quote_snapshot import QuoteSnapshot

POLYGON_CHAIN_ID = 137
GET_POOL_SELECTOR = "1698ee82"
QUOTE_EXACT_INPUT_SINGLE_SELECTOR = "f7729d43"


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform one JSON-RPC request and return its result."""


class UniswapV3Error(QuoteEngineError):
    """Raised when an exact Uniswap V3 quote cannot be proven valid."""


BlockSnapshot = MarketBlockSnapshot


def _address_word(address: str) -> bytes:
    if not isinstance(address, str):
        raise UniswapV3Error("address must be a string")
    raw = address[2:] if address.startswith(("0x", "0X")) else address
    if len(raw) != 40:
        raise UniswapV3Error("address must contain exactly 20 bytes")
    try:
        return b"\x00" * 12 + bytes.fromhex(raw)
    except ValueError as exc:
        raise UniswapV3Error("address is not valid hexadecimal") from exc


def _uint_word(value: int, name: str, bits: int = 256) -> bytes:
    if not isinstance(value, int) or value < 0 or value >= 1 << bits:
        raise UniswapV3Error(f"{name} is outside uint{bits} range")
    return value.to_bytes(32, "big")


def _encode_get_pool(token_a: str, token_b: str, fee: int) -> str:
    return "0x" + (bytes.fromhex(GET_POOL_SELECTOR) + _address_word(token_a) +
                     _address_word(token_b) + _uint_word(fee, "fee", 24)).hex()


def _encode_quote_exact_input_single(token_in: str, token_out: str, fee: int, amount_in: int) -> str:
    return "0x" + (bytes.fromhex(QUOTE_EXACT_INPUT_SINGLE_SELECTOR) + _address_word(token_in) +
                     _address_word(token_out) + _uint_word(fee, "fee", 24) +
                     _uint_word(amount_in, "amount_in") + _uint_word(0, "sqrt_price_limit_x96")).hex()


def _result_hex(result: Any, label: str) -> bytes:
    if isinstance(result, Mapping):
        raise UniswapV3Error(f"{label}: RPC error object")
    if not isinstance(result, str) or not result.startswith("0x"):
        raise UniswapV3Error(f"{label}: result must be 0x-prefixed hex")
    try:
        return bytes.fromhex(result[2:])
    except ValueError as exc:
        raise UniswapV3Error(f"{label}: malformed hexadecimal result") from exc


def _decode_address(result: Any) -> str:
    raw = _result_hex(result, "getPool")
    if len(raw) != 32:
        raise UniswapV3Error("getPool: malformed address ABI result")
    address = raw[12:]
    if address == b"\x00" * 20:
        raise UniswapV3Error("Uniswap V3 pool does not exist for requested fee tier")
    return "0x" + address.hex()


def _decode_amount_out(result: Any) -> int:
    raw = _result_hex(result, "quoteExactInputSingle")
    if len(raw) < 32 or len(raw) % 32:
        raise UniswapV3Error("quoteExactInputSingle: malformed ABI result")
    amount_out = int.from_bytes(raw[:32], "big")
    if amount_out <= 0:
        raise UniswapV3Error("Uniswap V3 returned zero output")
    return amount_out


class UniswapV3ExactQuoter:
    """Exact single-hop Uniswap V3 Quoter V1 over injected read-only RPC."""

    def __init__(self, rpc: RpcTransport, factory_address: str, quoter_address: str,
                 chain_id: int = POLYGON_CHAIN_ID) -> None:
        if chain_id != POLYGON_CHAIN_ID:
            raise UniswapV3Error("Uniswap V3 adapter is Polygon-mainnet only")
        _address_word(factory_address)
        _address_word(quoter_address)
        self._rpc = rpc
        self.factory_address = factory_address
        self.quoter_address = quoter_address
        self.chain_id = chain_id
        self._pool_cache: dict[tuple[str, str, int, int], str] = {}
        self._missing_pool_cache: set[tuple[str, str, int, int]] = set()

    @staticmethod
    def _pool_cache_key(token_in: str, token_out: str, fee: int, block_number: int) -> tuple[str, str, int, int]:
        token0, token1 = sorted((token_in.lower(), token_out.lower()))
        return token0, token1, fee, block_number

    def snapshot(self) -> BlockSnapshot:
        try:
            return acquire_market_block(self._rpc, expected_chain_id=self.chain_id)
        except Exception as exc:
            raise UniswapV3Error(str(exc)) from exc

    def resolve_pool(self, token_in: str, token_out: str, fee: int, snapshot: BlockSnapshot) -> str:
        if snapshot.chain_id != self.chain_id:
            raise UniswapV3Error("snapshot chain identity mismatch")
        if token_in.lower() == token_out.lower():
            raise UniswapV3Error("token_in and token_out must differ")
        key = self._pool_cache_key(token_in, token_out, fee, snapshot.block_number)
        missing_error = "Uniswap V3 pool does not exist for requested fee tier"
        if key in self._missing_pool_cache:
            raise UniswapV3Error(missing_error)
        cached = self._pool_cache.get(key)
        if cached is not None:
            return cached
        try:
            result = self._rpc.call("eth_call", [
                {"to": self.factory_address, "data": _encode_get_pool(token_in, token_out, fee)},
                hex(snapshot.block_number),
            ])
            pool = _decode_address(result)
        except UniswapV3Error as exc:
            if str(exc) == missing_error:
                self._missing_pool_cache.add(key)
            raise
        self._pool_cache[key] = pool
        return pool

    def quote(self, amount_in: int, token_in: str, token_out: str, fee: int,
              snapshot: BlockSnapshot) -> ExactQuote:
        if amount_in <= 0:
            raise UniswapV3Error("amount_in must be positive")
        pool = self.resolve_pool(token_in, token_out, fee, snapshot)
        call = getattr(
            self._rpc,
            "call_with_ambiguous_revert_failover",
            self._rpc.call,
        )
        result = call("eth_call", [
            {"to": self.quoter_address,
             "data": _encode_quote_exact_input_single(token_in, token_out, fee, amount_in)},
            hex(snapshot.block_number),
        ])
        return ExactQuote(f"uniswap_v3:{pool.lower()}", token_in, token_out,
                          amount_in, _decode_amount_out(result), snapshot.block_number, fee)

    def quote_snapshot(self, amount_in: int, token_in: str, token_out: str, fee: int,
                       snapshot: BlockSnapshot, gas_estimate: int | None = None) -> QuoteSnapshot:
        quote = self.quote(amount_in, token_in, token_out, fee, snapshot)
        pool = quote.venue.split(":", 1)[1]
        return QuoteSnapshot.from_exact_quote(
            quote, chain_id=self.chain_id, observed_at_unix=snapshot.timestamp,
            pool_or_router=pool, gas_estimate=gas_estimate,
        )


def quote_uniswap_v3_exact(rpc: RpcTransport, factory_address: str, quoter_address: str,
                           amount_in: int, token_in: str, token_out: str, fee: int) -> ExactQuote:
    quoter = UniswapV3ExactQuoter(rpc, factory_address, quoter_address)
    return quoter.quote(amount_in, token_in, token_out, fee, quoter.snapshot())
