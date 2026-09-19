"""Chunked Polygon log inventory with provider-preserving failover.

This is a read-only primitive for full on-chain pool/event enumeration.
It never treats RPC exhaustion as market absence and shrinks block ranges when
a provider cannot service an oversized log query.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class PolygonLogInventoryError(RuntimeError):
    """Raised when a requested log range cannot be completed."""


@dataclass(frozen=True)
class LogQuery:
    address: str | None = None
    topics: tuple[str | None, ...] = ()
    from_block: int = 0
    to_block: int = 0

    def to_rpc_filter(self) -> dict[str, Any]:
        if self.from_block < 0 or self.to_block < self.from_block:
            raise PolygonLogInventoryError("invalid log block range")
        result: dict[str, Any] = {
            "fromBlock": hex(self.from_block),
            "toBlock": hex(self.to_block),
        }
        if self.address:
            result["address"] = self.address
        if self.topics:
            result["topics"] = list(self.topics)
        return result


@dataclass(frozen=True)
class InventoryLog:
    block_number: int
    transaction_hash: str
    log_index: int
    address: str
    topics: tuple[str, ...]
    data: str

    @classmethod
    def from_rpc(cls, raw: Mapping[str, Any]) -> "InventoryLog":
        required = ("blockNumber", "transactionHash", "logIndex", "address", "topics", "data")
        if any(key not in raw for key in required):
            raise PolygonLogInventoryError("log object is missing required fields")
        return cls(
            block_number=int(str(raw["blockNumber"]), 16),
            transaction_hash=str(raw["transactionHash"]).lower(),
            log_index=int(str(raw["logIndex"]), 16),
            address=str(raw["address"]).lower(),
            topics=tuple(str(item).lower() for item in raw["topics"]),
            data=str(raw["data"]).lower(),
        )

    @property
    def identity(self) -> tuple[str, int]:
        return self.transaction_hash, self.log_index


def _looks_like_range_limit(exc: BaseException) -> bool:
    message = str(exc).lower()
    markers = (
        "too many results", "too many logs", "query returned",
        "block range", "range limit", "max range", "more than",
        "limit exceeded", "result set", "timeout", "timed out",
        "gateway timeout", "query timeout", "-32005",
    )
    return any(marker in message for marker in markers)


@dataclass
class PolygonLogInventory:
    rpc: Any
    initial_chunk_size: int = 2000
    minimum_chunk_size: int = 1

    def __post_init__(self) -> None:
        if self.initial_chunk_size < 1:
            raise PolygonLogInventoryError("initial_chunk_size must be positive")
        if self.minimum_chunk_size < 1 or self.minimum_chunk_size > self.initial_chunk_size:
            raise PolygonLogInventoryError("minimum_chunk_size must be within initial chunk size")

    def _read_chunk(self, query: LogQuery) -> tuple[InventoryLog, ...]:
        try:
            raw = self.rpc.call("eth_getLogs", [query.to_rpc_filter()])
        except Exception as exc:
            if not _looks_like_range_limit(exc):
                raise
            if query.from_block == query.to_block or (query.to_block - query.from_block + 1) <= self.minimum_chunk_size:
                raise
            raise
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
            raise PolygonLogInventoryError("eth_getLogs result must be an array")
        return tuple(InventoryLog.from_rpc(item) for item in raw if isinstance(item, Mapping))

    def scan(
        self,
        *,
        from_block: int,
        to_block: int,
        address: str | None = None,
        topics: Sequence[str | None] = (),
    ) -> tuple[InventoryLog, ...]:
        if from_block < 0 or to_block < from_block:
            raise PolygonLogInventoryError("invalid scan range")
        chunk = min(self.initial_chunk_size, to_block - from_block + 1)
        output: dict[tuple[str, int], InventoryLog] = {}
        cursor = from_block
        while cursor <= to_block:
            end = min(cursor + chunk - 1, to_block)
            try:
                logs = self._read_chunk(
                    LogQuery(
                        address=address,
                        topics=tuple(topics),
                        from_block=cursor,
                        to_block=end,
                    )
                )
            except Exception as exc:
                if chunk <= self.minimum_chunk_size or not _looks_like_range_limit(exc):
                    raise PolygonLogInventoryError(
                        f"log scan exhausted at {cursor}-{end}: {type(exc).__name__}: {exc}"
                    ) from exc
                chunk = max(self.minimum_chunk_size, chunk // 2)
                continue
            for log in logs:
                output[log.identity] = log
            cursor = end + 1
            if chunk < self.initial_chunk_size:
                chunk = min(self.initial_chunk_size, max(chunk * 2, self.minimum_chunk_size))
        return tuple(sorted(output.values(), key=lambda item: (item.block_number, item.transaction_hash, item.log_index)))
