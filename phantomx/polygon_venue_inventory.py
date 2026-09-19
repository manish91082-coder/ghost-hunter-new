"""Polygon venue pool-event inventory primitives.

The module is network-free. It converts already retrieved, block-pinned logs
into deterministic PoolEdge records for the market graph. Each pool or pool
configuration remains distinct.

Event schemas are bound to documented Polygon venue contracts:
- QuickSwap V2 PairCreated
- QuickSwap V3 Algebra Pool
- Uniswap V3 PoolCreated
- Ramses V3 PoolCreated
- Uniswap V4 PoolManager Initialize

V4 uses a singleton PoolManager and bytes32 poolId, so the graph identity is
poolId + PoolKey parameters rather than a per-pool contract address.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .market_graph import PoolEdge
from .polygon_log_inventory import InventoryLog


@dataclass(frozen=True)
class VenueInventorySpec:
    venue_id: str
    factory_or_manager: str
    event_signature: str
    topic0: str
    indexed_fields: tuple[str, ...]
    data_fields: tuple[tuple[str, int], ...]
    pool_identity_field: str
    singleton: bool = False


QUICKSWAP_V2_FACTORY = "0x5757371414417b8c6caad45baef941abc7d3ab32"
QUICKSWAP_V3_FACTORY = "0x411b0facc3489691f28ad58c47006af5e3ab3a28"
UNISWAP_V3_FACTORY = "0x1f98431c8ad98523631ae4a59f267346ea31f984"
RAMSES_V3_FACTORY = "0x2bef16a0081565e72100d73cbe19b1bd2d802380"
UNISWAP_V4_POOL_MANAGER = "0x67366782805870060151383f4bbff9dab53e5cd6"

PAIR_CREATED_TOPIC = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
ALGEBRA_POOL_TOPIC = "0x91ccaa7a278130b65168c3a0c8d3bcae84cf5e43704342bd3ec0b59e59c036db"
V3_POOL_CREATED_TOPIC = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"
V4_INITIALIZE_TOPIC = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"

VENUE_SPECS: tuple[VenueInventorySpec, ...] = (
    VenueInventorySpec(
        "quickswap_v2",
        QUICKSWAP_V2_FACTORY,
        "PairCreated(address,address,address,uint256)",
        PAIR_CREATED_TOPIC,
        ("token0", "token1"),
        (("pair", 0), ("allPairsLength", 1)),
        "pair",
    ),
    VenueInventorySpec(
        "quickswap_v3",
        QUICKSWAP_V3_FACTORY,
        "Pool(address,address,address)",
        ALGEBRA_POOL_TOPIC,
        ("token0", "token1"),
        (("pool", 0),),
        "pool",
    ),
    VenueInventorySpec(
        "uniswap_v3",
        UNISWAP_V3_FACTORY,
        "PoolCreated(address,address,uint24,int24,address)",
        V3_POOL_CREATED_TOPIC,
        ("token0", "token1", "fee"),
        (("tickSpacing", 0), ("pool", 1)),
        "pool",
    ),
    VenueInventorySpec(
        "ramses_v3",
        RAMSES_V3_FACTORY,
        "PoolCreated(address,address,uint24,int24,address)",
        V3_POOL_CREATED_TOPIC,
        ("token0", "token1", "fee"),
        (("tickSpacing", 0), ("pool", 1)),
        "pool",
    ),
    VenueInventorySpec(
        "uniswap_v4",
        UNISWAP_V4_POOL_MANAGER,
        "Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)",
        V4_INITIALIZE_TOPIC,
        ("id", "currency0", "currency1"),
        (("fee", 0), ("tickSpacing", 1), ("hooks", 2), ("sqrtPriceX96", 3), ("tick", 4)),
        "id",
        singleton=True,
    ),
)


class VenueInventoryError(ValueError):
    """Raised when an inventory log cannot be trusted or decoded."""


def _word(raw: str, index: int) -> int:
    if not isinstance(raw, str) or not raw.startswith("0x"):
        raise VenueInventoryError("log data must be 0x-prefixed")
    body = raw[2:]
    start = index * 64
    end = start + 64
    if end > len(body):
        raise VenueInventoryError("log data is shorter than the declared ABI fields")
    try:
        return int(body[start:end], 16)
    except ValueError as exc:
        raise VenueInventoryError("log data contains non-hex ABI word") from exc


def _address_word(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise VenueInventoryError("indexed address topic is malformed")
    body = value[2:]
    if len(body) != 64:
        raise VenueInventoryError("indexed topic must be one ABI word")
    try:
        int(body, 16)
    except ValueError as exc:
        raise VenueInventoryError("indexed topic is not hexadecimal") from exc
    return "0x" + body[-40:]


def _bytes32_topic(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise VenueInventoryError("bytes32 indexed topic is malformed")
    try:
        bytes.fromhex(value[2:])
    except ValueError as exc:
        raise VenueInventoryError("bytes32 topic is not hexadecimal") from exc
    return value.lower()


def decode_inventory_log(log: InventoryLog, spec: VenueInventorySpec) -> PoolEdge:
    if log.address.lower() != spec.factory_or_manager.lower():
        raise VenueInventoryError("log emitter does not match venue inventory contract")
    if not log.topics or log.topics[0].lower() != spec.topic0.lower():
        raise VenueInventoryError("log topic0 does not match venue event")
    if len(log.topics) != len(spec.indexed_fields) + 1:
        raise VenueInventoryError("unexpected topic count for venue event")

    indexed: dict[str, str] = {}
    for index, name in enumerate(spec.indexed_fields, start=1):
        value = log.topics[index]
        if name in {"token0", "token1", "currency0", "currency1"}:
            indexed[name] = _address_word(value)
        elif name == "fee":
            indexed[name] = str(int(value, 16))
        elif name == "id":
            indexed[name] = _bytes32_topic(value)
        else:
            indexed[name] = value.lower()

    data_values = {name: _word(log.data, offset) for name, offset in spec.data_fields}
    if spec.venue_id == "quickswap_v2":
        token0 = indexed["token0"]
        token1 = indexed["token1"]
        pool = _address_word("0x" + _word(log.data, 0).to_bytes(32, "big").hex())
        params = (("creation_index", str(data_values["allPairsLength"])),)
        edge_id = f"quickswap-v2:{pool.lower()}"
        return PoolEdge(edge_id, spec.venue_id, pool, token0, token1, params)

    if spec.venue_id == "quickswap_v3":
        pool = _address_word("0x" + data_values["pool"].to_bytes(32, "big").hex())
        edge_id = f"quickswap-v3:{pool.lower()}"
        return PoolEdge(edge_id, spec.venue_id, pool, indexed["token0"], indexed["token1"])

    if spec.venue_id in {"uniswap_v3", "ramses_v3"}:
        pool = _address_word("0x" + data_values["pool"].to_bytes(32, "big").hex())
        params = (
            ("fee", indexed["fee"]),
            ("tickSpacing", str(data_values["tickSpacing"])),
        )
        edge_id = f"{spec.venue_id}:{pool.lower()}:{indexed['fee']}:{data_values['tickSpacing']}"
        return PoolEdge(edge_id, spec.venue_id, pool, indexed["token0"], indexed["token1"], params)

    if spec.venue_id == "uniswap_v4":
        pool_id = indexed["id"]
        currency0 = indexed["currency0"]
        currency1 = indexed["currency1"]
        params = (
            ("fee", str(data_values["fee"])),
            ("tickSpacing", str(data_values["tickSpacing"])),
            ("hooks", _address_word("0x" + data_values["hooks"].to_bytes(32, "big").hex())),
            ("sqrtPriceX96", str(data_values["sqrtPriceX96"])),
            ("tick", str(data_values["tick"])),
        )
        edge_id = f"uniswap-v4:{pool_id}:{currency0}:{currency1}"
        singleton_id = spec.factory_or_manager.lower()
        return PoolEdge(edge_id, spec.venue_id, singleton_id, currency0, currency1, params)

    raise VenueInventoryError(f"unsupported venue: {spec.venue_id}")


def inventory_edges(logs: Iterable[InventoryLog], spec: VenueInventorySpec) -> tuple[PoolEdge, ...]:
    edges: dict[str, PoolEdge] = {}
    for log in logs:
        try:
            edge = decode_inventory_log(log, spec)
        except VenueInventoryError:
            raise
        edges[edge.edge_id.lower()] = edge
    return tuple(sorted(edges.values(), key=lambda edge: edge.identity))
