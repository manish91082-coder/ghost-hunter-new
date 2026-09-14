"""Read-only, block-pinned Uniswap V3 exact quote adapter.

This module is intentionally independent of legacy PhantomX execution code.
It resolves a concrete V3 pool for an explicit fee tier, then asks the V3
Quoter for the exact output at a pinned block. No spot-price reconstruction,
reserve approximation, signing, submission, or relay capability exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .quote_engine import ExactQuote, QuoteEngineError

POLYGON_CHAIN_ID = 137
GET_POOL_SELECTOR = "1698ee82"  # factory.getPool(address,address,uint24)
QUOTE_EXACT_INPUT_SINGLE_SELECTOR = "414bf389"  # QuoterV2-compatible single-hop shape


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform one JSON-RPC request and return its result."""


class UniswapV3Error(QuoteEngineError):
    """Raised when an exact Uniswap V3 quote cannot be proven valid."""


@dataclass(frozen=True)
class BlockSnapshot:
    chain_id: int
    block_number: int


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
    return "0x" + (bytes.fromhex(GET_POOL_SELECTOR)
        + _address_word(token_a) + _address_word(token_b) + _uint_word(fee, "fee", 24)).hex()


def _encode_quote_exact_input_single(token_in: str, token_out: str, fee: int, amount_in: int) -> str:
    # Quoter.quoteExactInputSingle(address,address,uint24,uint256,uint160)
    return "0x" + (bytes.fromhex(QUOTE_EXACT_INPUT_SINGLE_SELECTOR)
        + _address_word(token_in)
        + _address_word(token_out)
        + _uint_word(fee, "fee", 24)
        + _uint_word(amount_in, "amount_in")
        + _uint_word(0, "sqrt_price_limit_x96")).hex()


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


def _parse_quantity(value: Any, name: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise UniswapV3Error(f"{name}: malformed quantity")
    try:
        parsed = int(value, 16)
    except ValueError as exc:
        raise UniswapV3Error(f"{name}: invalid hexadecimal") from exc
    if parsed < 0:
        raise UniswapV3Error(f"{name}: negative value")
    return parsed


class UniswapV3ExactQuoter:
    """Exact single-hop Uniswap V3 quoting over an injected read-only RPC."""

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

    def snapshot(self) -> BlockSnapshot:
        chain_id = _parse_quantity(self._rpc.call("eth_chainId", []), "chainId")
        if chain_id != self.chain_id:
            raise UniswapV3Error(f"unexpected chain id: {chain_id}")
        block = _parse_quantity(self._rpc.call("eth_blockNumber", []), "blockNumber")
        return BlockSnapshot(chain_id, block)

    def resolve_pool(self, token_in: str, token_out: str, fee: int, snapshot: BlockSnapshot) -> str:
        if snapshot.chain_id != self.chain_id:
            raise UniswapV3Error("snapshot chain identity mismatch")
        if token_in.lower() == token_out.lower():
            raise UniswapV3Error("token_in and token_out must differ")
        data = _encode_get_pool(token_in, token_out, fee)
        result = self._rpc.call("eth_call", [
            {"to": self.factory_address, "data": data}, hex(snapshot.block_number)
        ])
        return _decode_address(result)

    def quote(self, amount_in: int, token_in: str, token_out: str, fee: int,
              snapshot: BlockSnapshot) -> ExactQuote:
        if amount_in <= 0:
            raise UniswapV3Error("amount_in must be positive")
        pool = self.resolve_pool(token_in, token_out, fee, snapshot)
        data = _encode_quote_exact_input_single(token_in, token_out, fee, amount_in)
        result = self._rpc.call("eth_call", [
            {"to": self.quoter_address, "data": data}, hex(snapshot.block_number)
        ])
        amount_out = _decode_amount_out(result)
        return ExactQuote(
            venue=f"uniswap_v3:{pool.lower()}",
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            amount_out=amount_out,
            block_number=snapshot.block_number,
            fee_raw=fee,
        )


def quote_uniswap_v3_exact(rpc: RpcTransport, factory_address: str, quoter_address: str,
                           amount_in: int, token_in: str, token_out: str, fee: int) -> ExactQuote:
    """Pin one Polygon block and obtain one exact V3 single-hop quote."""
    quoter = UniswapV3ExactQuoter(rpc, factory_address, quoter_address)
    return quoter.quote(amount_in, token_in, token_out, fee, quoter.snapshot())
