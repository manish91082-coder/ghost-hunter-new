"""Read-only, block-pinned Curve registry quote adapter for Polygon.

The adapter discovers pools through Curve registry contracts, resolves coin
indices via the registry, and quotes directly against the pool with get_dy or
get_dy_underlying. It never signs, submits, or executes swaps.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .market_block import MarketBlockSnapshot
from .quote_engine import ExactQuote, QuoteEngineError
from .quote_snapshot import QuoteSnapshot

POLYGON_CHAIN_ID = 137

CURVE_FACTORY_REGISTRY = "0x722272d36ef0da72ff51c5a65db7b870e2e8d4ee"
CURVE_CRYPTO_REGISTRY = "0x47bB542B9dE58b970bA50c9dae444DDB4c16751a"
CURVE_FACTORY_CRYPTO_REGISTRY = "0xE5De15A9C9bBedb4F5EC13B131E61245f2983A69"
CURVE_FACTORY_STABLESWAP_NG_REGISTRY = "0x1764ee18e8B3ccA4787249Ceb249356192594585"
CURVE_FACTORY_TWOCRYPTO_REGISTRY = "0x98EE851a00abeE0d95D08cF4CA2BdCE32aeaAF7F"
CURVE_FACTORY_TRICRYPTO_REGISTRY = "0xC1b393EfEF38140662b91441C6710Aa704973228"

REGISTRY_TYPES = (
    ("factory", CURVE_FACTORY_REGISTRY),
    ("crypto", CURVE_CRYPTO_REGISTRY),
    ("factory-crypto", CURVE_FACTORY_CRYPTO_REGISTRY),
    ("stableswap-ng", CURVE_FACTORY_STABLESWAP_NG_REGISTRY),
    ("twocrypto", CURVE_FACTORY_TWOCRYPTO_REGISTRY),
    ("tricrypto", CURVE_FACTORY_TRICRYPTO_REGISTRY),
)

POOL_COUNT_SELECTOR = "0x956aae3a"
POOL_LIST_SELECTOR = "0x3a1d5d8e"
GET_COIN_INDICES_SELECTOR = "0xeb85226d"
GET_FEES_SELECTOR = "0x7cdb72b0"
FIND_POOL_FOR_COINS_SELECTOR = "0xa87df06c"
FIND_POOL_FOR_COINS_INDEXED_SELECTOR = "0x6982eb0b"
GET_DY_SELECTOR = "0x5e0d443f"
GET_DY_UNDERLYING_SELECTOR = "0x07211ef7"
COINS_SELECTOR = "0xc6610657"
FEE_SELECTOR = "0xddca3f43"


class RpcTransport(Protocol):
    def call(self, method: str, params: Sequence[Any]) -> Any:
        """Perform one JSON-RPC request."""


class CurveError(QuoteEngineError):
    """Raised when a Curve pool quote cannot be proven valid."""


BlockSnapshot = MarketBlockSnapshot


@dataclass(frozen=True)
class CurvePoolRef:
    registry_name: str
    registry_address: str
    pool: str
    token_in: str
    token_out: str
    i: int
    j: int
    underlying: bool
    fee_raw: int

    def reversed(self) -> "CurvePoolRef":
        return CurvePoolRef(
            self.registry_name,
            self.registry_address,
            self.pool,
            self.token_out,
            self.token_in,
            self.j,
            self.i,
            self.underlying,
            self.fee_raw,
        )


def _address_word(address: str) -> bytes:
    if not isinstance(address, str):
        raise CurveError("address must be a string")
    raw = address[2:] if address.startswith(("0x", "0X")) else address
    if len(raw) != 40:
        raise CurveError("address must contain exactly 20 bytes")
    try:
        return b"\x00" * 12 + bytes.fromhex(raw)
    except ValueError as exc:
        raise CurveError("address is not valid hexadecimal") from exc


def _uint_word(value: int) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value >= 1 << 256:
        raise CurveError("uint256 value is invalid")
    return value.to_bytes(32, "big")


def _int128_word(value: int) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < -(1 << 127) or value >= 1 << 127:
        raise CurveError("int128 value is invalid")
    return (value & ((1 << 256) - 1)).to_bytes(32, "big")


def _result_bytes(result: Any, label: str) -> bytes:
    if isinstance(result, Mapping):
        raise CurveError(f"{label}: RPC error object")
    if not isinstance(result, str) or not result.startswith("0x"):
        raise CurveError(f"{label}: result must be 0x-prefixed hex")
    try:
        return bytes.fromhex(result[2:])
    except ValueError as exc:
        raise CurveError(f"{label}: malformed hexadecimal result") from exc


def _encode_pool_count() -> str:
    return POOL_COUNT_SELECTOR


def _encode_pool_list(index: int) -> str:
    return POOL_LIST_SELECTOR + _uint_word(index).hex()


def _encode_get_coin_indices(pool: str, token_in: str, token_out: str) -> str:
    return GET_COIN_INDICES_SELECTOR + (
        _address_word(pool) + _address_word(token_in) + _address_word(token_out)
    ).hex()


def _encode_get_fees(pool: str) -> str:
    return GET_FEES_SELECTOR + _address_word(pool).hex()


def _encode_get_dy(selector: str, i: int, j: int, amount_in: int) -> str:
    return selector + (_int128_word(i) + _int128_word(j) + _uint_word(amount_in)).hex()


def _decode_one_address(result: Any, label: str) -> str:
    raw = _result_bytes(result, label)
    if len(raw) != 32:
        raise CurveError(f"{label}: expected one ABI word")
    addr = raw[12:]
    if addr == bytes(20):
        raise CurveError(f"{label}: zero address")
    return "0x" + addr.hex()


def _decode_uint(result: Any, label: str) -> int:
    raw = _result_bytes(result, label)
    if len(raw) != 32:
        raise CurveError(f"{label}: expected one ABI word")
    return int.from_bytes(raw, "big")


def _decode_indices(result: Any) -> tuple[int, int, bool]:
    raw = _result_bytes(result, "get_coin_indices")
    if len(raw) != 96:
        raise CurveError("get_coin_indices: expected 3 ABI words")
    i = int.from_bytes(raw[:32], "big")
    j = int.from_bytes(raw[32:64], "big")
    underlying = int.from_bytes(raw[64:96], "big") != 0
    if i >= 1 << 127 or j >= 1 << 127:
        raise CurveError("coin index outside int128 range")
    return i, j, underlying


def _decode_fees(result: Any) -> int:
    raw = _result_bytes(result, "get_fees")
    if len(raw) < 32 or len(raw) % 32:
        raise CurveError("get_fees: malformed ABI array")
    return int.from_bytes(raw[:32], "big")


class CurveRegistryExactQuoter:
    """Curve registry-driven exact single-pool quoter."""

    def __init__(
        self,
        rpc: RpcTransport,
        registries: Sequence[tuple[str, str]] = REGISTRY_TYPES,
        chain_id: int = POLYGON_CHAIN_ID,
    ) -> None:
        if chain_id != POLYGON_CHAIN_ID:
            raise CurveError("Curve adapter is Polygon-mainnet only")
        for _name, address in registries:
            _address_word(address)
        self._rpc = rpc
        self.chain_id = chain_id
        self.registries = tuple(registries)

    def _call(self, to: str, data: str, snapshot: BlockSnapshot) -> bytes:
        try:
            result = self._rpc.call(
                "eth_call",
                [{"to": to, "data": data}, hex(snapshot.block_number)],
            )
        except Exception as exc:
            raise CurveError(f"eth_call transport failure: {type(exc).__name__}: {exc}") from exc
        return _result_bytes(result, "eth_call")

    def pool_count(self, registry: str, snapshot: BlockSnapshot) -> int:
        raw = self._call(registry, _encode_pool_count(), snapshot)
        if len(raw) != 32:
            raise CurveError("pool_count: malformed result")
        return int.from_bytes(raw, "big")

    def _find_pool(self, registry: str, token_in: str, token_out: str, index: int | None, snapshot: BlockSnapshot) -> str | None:
        if index is None:
            data = FIND_POOL_FOR_COINS_SELECTOR + (_address_word(token_in) + _address_word(token_out)).hex()
        else:
            data = FIND_POOL_FOR_COINS_INDEXED_SELECTOR + (_address_word(token_in) + _address_word(token_out) + _uint_word(index)).hex()
        try:
            raw = self._call(registry, data, snapshot)
        except CurveError as exc:
            message = str(exc).lower()
            if "all bounded polygon rpc recovery passes failed" in message:
                raise
            if "execution reverted" in message:
                return None
            if "transport failure" in message or "rpc error code=429" in message:
                raise
            return None
        if len(raw) != 32:
            return None
        address = raw[12:]
        if address == bytes(20):
            return None
        return "0x" + address.hex()

    def find_pools_for_pair(self, token_in: str, token_out: str, snapshot: BlockSnapshot, *, max_pools_per_registry: int = 8) -> list[CurvePoolRef]:
        found: list[CurvePoolRef] = []
        for registry_name, registry in self.registries:
            seen: set[str] = set()
            for index in range(max_pools_per_registry):
                # Curve's registry uses i=0 for the first matching market.
                # There is no special non-indexed path that should shift the
                # enumeration to i=1.
                pool = self._find_pool(registry, token_in, token_out, index, snapshot)
                if pool is None or pool.lower() in seen:
                    break
                seen.add(pool.lower())
                try:
                    i, j, underlying = _decode_indices("0x" + self._call(registry, _encode_get_coin_indices(pool, token_in, token_out), snapshot).hex())
                    fee_raw = 0
                    try:
                        fee_raw = _decode_fees("0x" + self._call(registry, _encode_get_fees(pool), snapshot).hex())
                    except CurveError:
                        pass
                    found.append(CurvePoolRef(registry_name, registry, pool, token_in, token_out, i, j, underlying, fee_raw))
                except CurveError:
                    continue
        return found
    def pools_for_pair(
        self,
        token_in: str,
        token_out: str,
        snapshot: BlockSnapshot,
        *,
        max_pools_per_registry: int = 256,
    ) -> list[CurvePoolRef]:
        found: list[CurvePoolRef] = []
        for registry_name, registry in self.registries:
            count = self.pool_count(registry, snapshot)
            if count > max_pools_per_registry:
                count = max_pools_per_registry
            for index in range(count):
                raw = self._call(registry, _encode_pool_list(index), snapshot)
                if len(raw) != 32:
                    continue
                pool = "0x" + raw[12:].hex()
                if int.from_bytes(raw[12:], "big") == 0:
                    continue
                try:
                    idx_raw = self._call(
                        registry,
                        _encode_get_coin_indices(pool, token_in, token_out),
                        snapshot,
                    )
                    i, j, underlying = _decode_indices("0x" + idx_raw.hex())
                    fee_raw = 0
                    try:
                        fee_raw = _decode_fees(
                            "0x" + self._call(registry, _encode_get_fees(pool), snapshot).hex()
                        )
                    except CurveError:
                        pass
                    found.append(
                        CurvePoolRef(
                            registry_name,
                            registry,
                            pool,
                            token_in,
                            token_out,
                            i,
                            j,
                            underlying,
                            fee_raw,
                        )
                    )
                except CurveError:
                    continue
        return found

    def direct_pool_ref(self, pool: str, token_in: str, token_out: str, snapshot: BlockSnapshot, *, max_coins: int = 8) -> CurvePoolRef:
        if snapshot.chain_id != self.chain_id:
            raise CurveError("snapshot chain identity mismatch")
        _address_word(pool)
        if token_in.lower() == token_out.lower():
            raise CurveError("token_in and token_out must differ")
        indices: dict[str, int] = {}
        for i in range(max_coins):
            try:
                raw = self._call(pool, COINS_SELECTOR + _uint_word(i).hex(), snapshot)
                if len(raw) != 32:
                    continue
                coin = raw[12:]
                if coin == bytes(20):
                    break
                indices["0x" + coin.hex()] = i
            except CurveError:
                break
        i = indices.get(token_in.lower())
        j = indices.get(token_out.lower())
        if i is None or j is None:
            raise CurveError("seeded Curve pool does not contain requested token pair")
        fee_raw = 0
        try:
            fee_raw = _decode_uint("0x" + self._call(pool, FEE_SELECTOR, snapshot).hex(), "fee")
        except CurveError:
            pass
        return CurvePoolRef("direct-seed", pool, pool, token_in, token_out, i, j, False, fee_raw)
    def quote_snapshot(
        self,
        amount_in: int,
        pool_ref: CurvePoolRef,
        snapshot: BlockSnapshot,
    ) -> QuoteSnapshot:
        if snapshot.chain_id != self.chain_id:
            raise CurveError("snapshot chain identity mismatch")
        if amount_in <= 0:
            raise CurveError("amount_in must be positive")
        selector = GET_DY_UNDERLYING_SELECTOR if pool_ref.underlying else GET_DY_SELECTOR
        result = self._rpc.call(
            "eth_call",
            [
                {
                    "to": pool_ref.pool,
                    "data": _encode_get_dy(selector, pool_ref.i, pool_ref.j, amount_in),
                },
                hex(snapshot.block_number),
            ],
        )
        amount_out = _decode_uint(result, "get_dy_underlying" if pool_ref.underlying else "get_dy")
        if amount_out <= 0:
            raise CurveError("Curve returned zero output")
        quote = ExactQuote(
            f"curve:{pool_ref.registry_name}:{pool_ref.pool.lower()}",
            pool_ref.token_in,
            pool_ref.token_out,
            amount_in,
            amount_out,
            snapshot.block_number,
            pool_ref.fee_raw,
        )
        return QuoteSnapshot.from_exact_quote(
            quote,
            chain_id=self.chain_id,
            observed_at_unix=snapshot.timestamp,
            pool_or_router=pool_ref.pool,
            gas_estimate=None,
        )


__all__ = [
    "BlockSnapshot",
    "CURVE_CRYPTO_REGISTRY",
    "CURVE_FACTORY_CRYPTO_REGISTRY",
    "CURVE_FACTORY_REGISTRY",
    "CURVE_FACTORY_STABLESWAP_NG_REGISTRY",
    "CURVE_FACTORY_TWOCRYPTO_REGISTRY",
    "CURVE_FACTORY_TRICRYPTO_REGISTRY",
    "CurveError",
    "CurvePoolRef",
    "CurveRegistryExactQuoter",
    "FIND_POOL_FOR_COINS_INDEXED_SELECTOR",
    "FIND_POOL_FOR_COINS_SELECTOR",
    "GET_COIN_INDICES_SELECTOR",
    "GET_DY_SELECTOR",
    "COINS_SELECTOR",
    "FEE_SELECTOR",
    "GET_DY_UNDERLYING_SELECTOR",
    "GET_FEES_SELECTOR",
    "POOL_COUNT_SELECTOR",
    "POOL_LIST_SELECTOR",
    "REGISTRY_TYPES",
]
