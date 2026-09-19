"""Chunked, failover-compatible Polygon eth_getLogs inventory primitive."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

class PolygonLogInventoryError(RuntimeError):
    pass

@dataclass(frozen=True)
class LogQuery:
    from_block: int
    to_block: int
    address: str | None = None
    topics: tuple[str | None, ...] = ()

    def as_filter(self) -> dict[str, Any]:
        if self.from_block < 0 or self.to_block < self.from_block:
            raise PolygonLogInventoryError("invalid block range")
        result: dict[str, Any] = {"fromBlock": hex(self.from_block), "toBlock": hex(self.to_block)}
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
        required = ("blockNumber","transactionHash","logIndex","address","topics","data")
        if any(k not in raw for k in required):
            raise PolygonLogInventoryError("malformed log: missing required field")
        try:
            return cls(
                block_number=int(str(raw["blockNumber"]),16),
                transaction_hash=str(raw["transactionHash"]).lower(),
                log_index=int(str(raw["logIndex"]),16),
                address=str(raw["address"]).lower(),
                topics=tuple(str(x).lower() for x in raw["topics"]),
                data=str(raw["data"]).lower(),
            )
        except (TypeError, ValueError) as exc:
            raise PolygonLogInventoryError("malformed log field") from exc

    @property
    def identity(self) -> tuple[str,int]:
        return self.transaction_hash, self.log_index

def _range_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(x in msg for x in (
        "too many logs","too many results","query returned","block range","blocks range","range limit","limited to",
        "result set","limit exceeded","-32005","timeout","timed out","gateway timeout",
    ))

@dataclass
class PolygonLogInventory:
    rpc: Any
    initial_chunk_size: int = 2000
    minimum_chunk_size: int = 1

    def __post_init__(self) -> None:
        if self.initial_chunk_size < 1:
            raise PolygonLogInventoryError("initial_chunk_size must be positive")
        if not 1 <= self.minimum_chunk_size <= self.initial_chunk_size:
            raise PolygonLogInventoryError("minimum_chunk_size must be within range")

    def _chunk(self, query: LogQuery) -> tuple[InventoryLog,...]:
        try:
            raw = self.rpc.call("eth_getLogs", [query.as_filter()])
        except Exception:
            raise
        if not isinstance(raw, Sequence) or isinstance(raw,(str,bytes,bytearray)):
            raise PolygonLogInventoryError("eth_getLogs must return an array")
        return tuple(InventoryLog.from_rpc(item) for item in raw if isinstance(item, Mapping))

    def scan(self, *, from_block:int, to_block:int, address:str|None=None, topics:Sequence[str|None]=()) -> tuple[InventoryLog,...]:
        if from_block < 0 or to_block < from_block:
            raise PolygonLogInventoryError("invalid scan range")
        chunk=min(self.initial_chunk_size,to_block-from_block+1)
        cursor=from_block
        out:dict[tuple[str,int],InventoryLog]={}
        while cursor<=to_block:
            end=min(cursor+chunk-1,to_block)
            try:
                logs=self._chunk(LogQuery(cursor,end,address,tuple(topics)))
            except Exception as exc:
                if not _range_error(exc) or chunk<=self.minimum_chunk_size:
                    raise PolygonLogInventoryError(f"log scan exhausted at {cursor}-{end}: {exc}") from exc
                chunk=max(self.minimum_chunk_size,chunk//2)
                continue
            for log in logs:
                out[log.identity]=log
            cursor=end+1
            if chunk<self.initial_chunk_size:
                chunk=min(self.initial_chunk_size,chunk*2)
        return tuple(sorted(out.values(),key=lambda x:(x.block_number,x.transaction_hash,x.log_index)))