"""Read-only Balancer V2 Polygon pool inventory adapter.

Verified protocol primitives:
- canonical Polygon Vault address;
- PoolRegistered(bytes32 indexed,address indexed,uint8);
- getPoolTokens(bytes32).

This module inventories pool token sets and converts positive-balance token
pairs into graph edges. Quote execution is intentionally separate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .market_block import MarketBlockSnapshot
from .market_graph import PoolEdge

POLYGON_CHAIN_ID = 137
BALANCER_V2_VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
POOL_REGISTERED_TOPIC = "0x3c13bc30b8e878c53fd2a36b679409c073afd75950be43d8858768e956fbc20e"
GET_POOL_TOKENS_SELECTOR = "0xf94d4668"
GET_POOL_SELECTOR = "0xf6c00927"


class BalancerInventoryError(RuntimeError):
    pass


@dataclass(frozen=True)
class BalancerPool:
    pool_id: str
    pool_address: str
    specialization: int
    tokens: tuple[str, ...]
    balances: tuple[int, ...]
    last_change_block: int
    block_number: int

    def __post_init__(self) -> None:
        if len(self.tokens) != len(self.balances):
            raise BalancerInventoryError("token/balance lengths differ")
        if len(self.tokens) < 2:
            raise BalancerInventoryError("Balancer pool must expose at least two tokens")


def _word(data: str, index: int) -> bytes:
    if not isinstance(data, str) or not data.startswith("0x"):
        raise BalancerInventoryError("ABI data must be 0x-prefixed")
    raw = bytes.fromhex(data[2:])
    start = index * 32
    if len(raw) < start + 32:
        raise BalancerInventoryError("ABI data shorter than required")
    return raw[start:start + 32]


def _address_topic(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise BalancerInventoryError("indexed address topic malformed")
    bytes.fromhex(value[2:])
    return "0x" + value[-40:].lower()


def _bytes32_topic(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise BalancerInventoryError("bytes32 topic malformed")
    bytes.fromhex(value[2:])
    return value.lower()


def _decode_dynamic_array(raw: bytes, offset: int, *, address: bool) -> list[int] | list[str]:
    if offset < 0 or offset + 32 > len(raw):
        raise BalancerInventoryError("ABI dynamic offset outside return data")
    length = int.from_bytes(raw[offset:offset + 32], "big")
    start = offset + 32
    end = start + 32 * length
    if end > len(raw):
        raise BalancerInventoryError("ABI dynamic array exceeds return data")
    if address:
        return ["0x" + raw[start + 12 + 32 * i:start + 32 + 32 * i].hex() for i in range(length)]
    return [int.from_bytes(raw[start + 32 * i:start + 32 + 32 * i], "big") for i in range(length)]


class BalancerV2Inventory:
    def __init__(self, rpc: Any, vault: str = BALANCER_V2_VAULT) -> None:
        self.rpc = rpc
        self.vault = vault.lower()

    def _call(self, data: str, snapshot: MarketBlockSnapshot) -> Any:
        return self.rpc.call("eth_call", [{"to": self.vault, "data": data}, hex(snapshot.block_number)])

    def decode_pool_registered(self, log: Mapping[str, Any]) -> tuple[str, str, int]:
        address = str(log.get("address", "")).lower()
        topics = log.get("topics")
        data = str(log.get("data", "0x"))
        if address != self.vault:
            raise BalancerInventoryError("PoolRegistered emitter mismatch")
        if not isinstance(topics, Sequence) or len(topics) != 3:
            raise BalancerInventoryError("PoolRegistered topic count mismatch")
        if str(topics[0]).lower() != POOL_REGISTERED_TOPIC:
            raise BalancerInventoryError("PoolRegistered topic0 mismatch")
        pool_id = _bytes32_topic(str(topics[1]))
        pool_address = _address_topic(str(topics[2]))
        specialization = int.from_bytes(_word(data, 0), "big")
        if specialization > 2:
            raise BalancerInventoryError("unknown Balancer specialization")
        return pool_id, pool_address, specialization

    def get_pool_tokens(self, pool_id: str, snapshot: MarketBlockSnapshot) -> tuple[tuple[str, ...], tuple[int, ...], int]:
        if _bytes32_topic(pool_id) != pool_id.lower():
            raise BalancerInventoryError("pool id malformed")
        result = self._call(GET_POOL_TOKENS_SELECTOR + pool_id[2:], snapshot)
        if not isinstance(result, str) or not result.startswith("0x"):
            raise BalancerInventoryError("getPoolTokens result malformed")
        raw = bytes.fromhex(result[2:])
        if len(raw) < 96:
            raise BalancerInventoryError("getPoolTokens result too short")
        tokens_offset = int.from_bytes(raw[0:32], "big")
        balances_offset = int.from_bytes(raw[32:64], "big")
        last_change = int.from_bytes(raw[64:96], "big")
        tokens = tuple(_decode_dynamic_array(raw, tokens_offset, address=True))
        balances = tuple(_decode_dynamic_array(raw, balances_offset, address=False))
        if len(tokens) != len(balances):
            raise BalancerInventoryError("getPoolTokens token/balance mismatch")
        return tokens, balances, last_change

    def load_pool(self, pool_id: str, pool_address: str, specialization: int, snapshot: MarketBlockSnapshot) -> BalancerPool:
        tokens, balances, last_change = self.get_pool_tokens(pool_id, snapshot)
        return BalancerPool(
            pool_id=pool_id.lower(),
            pool_address=pool_address.lower(),
            specialization=specialization,
            tokens=tokens,
            balances=balances,
            last_change_block=last_change,
            block_number=snapshot.block_number,
        )

    @staticmethod
    def graph_edges(pool: BalancerPool) -> tuple[PoolEdge, ...]:
        edges: list[PoolEdge] = []
        for i, token_in in enumerate(pool.tokens):
            for j, token_out in enumerate(pool.tokens):
                if i == j or pool.balances[i] <= 0 or pool.balances[j] <= 0:
                    continue
                edge_id = f"balancer-v2:{pool.pool_id}:{token_in.lower()}:{token_out.lower()}"
                params = (
                    ("specialization", str(pool.specialization)),
                    ("balance_in", str(pool.balances[i])),
                    ("balance_out", str(pool.balances[j])),
                    ("last_change_block", str(pool.last_change_block)),
                )
                edges.append(PoolEdge(
                    edge_id, "balancer_v2", pool.pool_id, token_in, token_out, params
                ))
        return tuple(sorted(edges, key=lambda edge: edge.identity))
