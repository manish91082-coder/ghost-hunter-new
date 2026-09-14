"""Deterministic Phase-19 executor calldata binding.

The on-chain executor needs the quote-route identity inside calldata, while the
full off-chain intent also contains calldata_hash. Putting the full intent hash
inside its own calldata would create a cryptographic fixed-point cycle.
Phase-19 therefore uses ExecutionIntent.execution_commitment_hash(), which
commits every intent field except calldata_hash.

The off-chain quote route hash and executable topology hash are additionally
joined into one end-to-end route commitment. The executor recomputes that
commitment from the supplied quote-route hash and its own canonical topology,
so neither side can silently drift.
"""

from __future__ import annotations

from dataclasses import dataclass

from .execution import ExecutionIntent, TransactionEnvelope
from .hashing import keccak256_hex


EXECUTE_SIGNATURE = (
    "execute((address,address,bool,uint24,uint256,uint256,uint256,uint256,bytes32,bytes32,bytes32),uint256)"
)
EXECUTE_WORD_COUNT = 12
EXECUTE_TOTAL_LENGTH = 4 + EXECUTE_WORD_COUNT * 32


class ExecutorCalldataError(ValueError):
    """Raised when executor calldata cannot be constructed or decoded safely."""


def _require_address(value: str, field: str) -> bytes:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise ExecutorCalldataError(f"{field} must be a 20-byte 0x address")
    try:
        raw = bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ExecutorCalldataError(f"{field} is not valid hex") from exc
    if len(raw) != 20 or raw == b"\x00" * 20:
        raise ExecutorCalldataError(f"{field} must be non-zero")
    return raw


def _word_address(value: str, field: str) -> bytes:
    return b"\x00" * 12 + _require_address(value, field)


def _word_uint(value: int, field: str, *, max_value: int = (1 << 256) - 1) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > max_value:
        raise ExecutorCalldataError(f"{field} is outside its unsigned integer range")
    return value.to_bytes(32, "big")


def _word_bool(value: bool, field: str) -> bytes:
    if not isinstance(value, bool):
        raise ExecutorCalldataError(f"{field} must be boolean")
    return _word_uint(1 if value else 0, field)


def _word_hash(value: str, field: str) -> bytes:
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        raise ExecutorCalldataError(f"{field} must be a 32-byte 0x hash")
    try:
        raw = bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ExecutorCalldataError(f"{field} is not valid hex") from exc
    if len(raw) != 32 or raw == b"\x00" * 32:
        raise ExecutorCalldataError(f"{field} must be non-zero")
    return raw


def executor_selector() -> bytes:
    """Return the Ethereum Keccak selector for Phase-19 execute(...)."""
    return bytes.fromhex(keccak256_hex(EXECUTE_SIGNATURE.encode("ascii"))[2:10])


def executor_topology_hash(
    *,
    asset: str,
    token_mid: str,
    first_on_quickswap: bool,
    uniswap_fee: int,
    aave_pool: str,
    quickswap_router: str,
    uniswap_v3_router: str,
) -> str:
    """Reproduce Phase19Executor.routeTopologyHash() exactly."""
    if not isinstance(uniswap_fee, int) or isinstance(uniswap_fee, bool) or not 0 < uniswap_fee <= 0xFFFFFF:
        raise ExecutorCalldataError("uniswap_fee must fit uint24 and be non-zero")
    payload = b"".join(
        (
            _word_address(asset, "asset"),
            _word_address(token_mid, "token_mid"),
            _word_bool(first_on_quickswap, "first_on_quickswap"),
            _word_uint(uniswap_fee, "uniswap_fee", max_value=0xFFFFFF),
            _word_address(aave_pool, "aave_pool"),
            _word_address(quickswap_router, "quickswap_router"),
            _word_address(uniswap_v3_router, "uniswap_v3_router"),
        )
    )
    return keccak256_hex(payload)


def executor_route_commitment(*, route_hash: str, topology_hash: str) -> str:
    """Join quote-route evidence and executable topology into one commitment."""
    return keccak256_hex(_word_hash(route_hash, "route_hash") + _word_hash(topology_hash, "topology_hash"))


def _encode_execute(
    *,
    asset: str,
    token_mid: str,
    first_on_quickswap: bool,
    uniswap_fee: int,
    amount_out_min_first: int,
    amount_out_min_second: int,
    minimum_surplus: int,
    deadline: int,
    route_hash: str,
    topology_hash: str,
    intent_commitment_hash: str,
    amount: int,
) -> bytes:
    """ABI-encode execute((static tuple),uint256) exactly."""
    if amount == 0:
        raise ExecutorCalldataError("amount must be positive")
    if amount_out_min_first == 0 or amount_out_min_second == 0:
        raise ExecutorCalldataError("per-leg minimum outputs must be positive")
    if minimum_surplus == 0:
        raise ExecutorCalldataError("minimum_surplus must be positive")
    words = (
        _word_address(asset, "asset"),
        _word_address(token_mid, "token_mid"),
        _word_bool(first_on_quickswap, "first_on_quickswap"),
        _word_uint(uniswap_fee, "uniswap_fee", max_value=0xFFFFFF),
        _word_uint(amount_out_min_first, "amount_out_min_first"),
        _word_uint(amount_out_min_second, "amount_out_min_second"),
        _word_uint(minimum_surplus, "minimum_surplus"),
        _word_uint(deadline, "deadline"),
        _word_hash(route_hash, "route_hash"),
        _word_hash(topology_hash, "topology_hash"),
        _word_hash(intent_commitment_hash, "intent_commitment_hash"),
        _word_uint(amount, "amount"),
    )
    return executor_selector() + b"".join(words)


def _decode_uint(word: bytes, field: str, *, max_value: int = (1 << 256) - 1) -> int:
    if len(word) != 32:
        raise ExecutorCalldataError(f"{field} is not a 32-byte ABI word")
    value = int.from_bytes(word, "big")
    if value > max_value:
        raise ExecutorCalldataError(f"{field} exceeds its declared unsigned width")
    return value


def _decode_address(word: bytes, field: str) -> str:
    if len(word) != 32 or word[:12] != b"\x00" * 12:
        raise ExecutorCalldataError(f"{field} is not a canonical ABI address word")
    return "0x" + word[12:].hex()


def _decode_bool(word: bytes, field: str) -> bool:
    value = _decode_uint(word, field, max_value=1)
    return bool(value)


def _decode_hash(word: bytes, field: str) -> str:
    if len(word) != 32 or word == b"\x00" * 32:
        raise ExecutorCalldataError(f"{field} must be a non-zero 32-byte hash")
    return "0x" + word.hex()


@dataclass(frozen=True)
class DecodedExecutorCall:
    """Semantically decoded Phase-19 executor calldata."""

    asset: str
    token_mid: str
    first_on_quickswap: bool
    uniswap_fee: int
    amount_out_min_first: int
    amount_out_min_second: int
    minimum_surplus: int
    deadline: int
    route_hash: str
    topology_hash: str
    intent_commitment_hash: str
    amount: int

    @property
    def route_commitment(self) -> str:
        return executor_route_commitment(route_hash=self.route_hash, topology_hash=self.topology_hash)


def decode_executor_calldata(calldata: bytes) -> DecodedExecutorCall:
    """Decode and validate the exact static Phase-19 execute calldata layout."""
    if not isinstance(calldata, (bytes, bytearray, memoryview)):
        raise ExecutorCalldataError("calldata must be bytes-like")
    raw = bytes(calldata)
    if len(raw) != EXECUTE_TOTAL_LENGTH:
        raise ExecutorCalldataError("unexpected executor calldata length")
    if raw[:4] != executor_selector():
        raise ExecutorCalldataError("unexpected executor selector")

    body = raw[4:]
    words = tuple(body[i : i + 32] for i in range(0, len(body), 32))
    if len(words) != EXECUTE_WORD_COUNT:
        raise ExecutorCalldataError("unexpected executor ABI word count")

    result = DecodedExecutorCall(
        asset=_decode_address(words[0], "asset"),
        token_mid=_decode_address(words[1], "token_mid"),
        first_on_quickswap=_decode_bool(words[2], "first_on_quickswap"),
        uniswap_fee=_decode_uint(words[3], "uniswap_fee", max_value=0xFFFFFF),
        amount_out_min_first=_decode_uint(words[4], "amount_out_min_first"),
        amount_out_min_second=_decode_uint(words[5], "amount_out_min_second"),
        minimum_surplus=_decode_uint(words[6], "minimum_surplus"),
        deadline=_decode_uint(words[7], "deadline"),
        route_hash=_decode_hash(words[8], "route_hash"),
        topology_hash=_decode_hash(words[9], "topology_hash"),
        intent_commitment_hash=_decode_hash(words[10], "intent_commitment_hash"),
        amount=_decode_uint(words[11], "amount"),
    )
    if result.uniswap_fee == 0:
        raise ExecutorCalldataError("uniswap_fee must be non-zero")
    if result.amount == 0:
        raise ExecutorCalldataError("amount must be positive")
    if result.amount_out_min_first == 0 or result.amount_out_min_second == 0:
        raise ExecutorCalldataError("per-leg minimum outputs must be positive")
    if result.minimum_surplus == 0:
        raise ExecutorCalldataError("minimum_surplus must be positive")
    if result.deadline == 0:
        raise ExecutorCalldataError("deadline must be positive")
    _word_hash(executor_route_commitment(route_hash=result.route_hash, topology_hash=result.topology_hash), "route_commitment")
    return result


@dataclass(frozen=True)
class BoundExecutorCall:
    """Exact executor calldata plus the fully bound off-chain transaction view."""

    calldata: bytes
    calldata_hash: str
    topology_hash: str
    route_commitment: str
    intent_commitment_hash: str
    bound_intent: ExecutionIntent
    envelope: TransactionEnvelope


def build_executor_transaction(
    intent: ExecutionIntent,
    *,
    token_mid: str,
    first_on_quickswap: bool,
    uniswap_fee: int,
    amount_out_min_first: int,
    amount_out_min_second: int,
    minimum_surplus: int,
    aave_pool: str,
    quickswap_router: str,
    uniswap_v3_router: str,
    gas_limit: int,
    max_fee_per_gas: int,
    max_priority_fee_per_gas: int,
) -> BoundExecutorCall:
    """Build exact calldata and bind its hashes back into an immutable intent."""
    if intent.chain_id != 137:
        raise ExecutorCalldataError("Phase-19 executor is Polygon-only")
    if intent.loan_amount <= 0:
        raise ExecutorCalldataError("intent loan amount must be positive")
    _require_address(intent.loan_asset, "intent.loan_asset")
    _require_address(intent.executor, "intent.executor")
    _require_address(intent.sender, "intent.sender")
    if intent.deadline < 0:
        raise ExecutorCalldataError("deadline cannot be negative")

    topology_hash = executor_topology_hash(
        asset=intent.loan_asset,
        token_mid=token_mid,
        first_on_quickswap=first_on_quickswap,
        uniswap_fee=uniswap_fee,
        aave_pool=aave_pool,
        quickswap_router=quickswap_router,
        uniswap_v3_router=uniswap_v3_router,
    )
    route_commitment = executor_route_commitment(route_hash=intent.route_hash, topology_hash=topology_hash)
    commitment_hash = intent.execution_commitment_hash()
    calldata = _encode_execute(
        asset=intent.loan_asset,
        token_mid=token_mid,
        first_on_quickswap=first_on_quickswap,
        uniswap_fee=uniswap_fee,
        amount_out_min_first=amount_out_min_first,
        amount_out_min_second=amount_out_min_second,
        minimum_surplus=minimum_surplus,
        deadline=intent.deadline,
        route_hash=intent.route_hash,
        topology_hash=topology_hash,
        intent_commitment_hash=commitment_hash,
        amount=intent.loan_amount,
    )
    calldata_hash = keccak256_hex(calldata)
    bound_intent = intent.with_field(calldata_hash=calldata_hash)
    if bound_intent.execution_commitment_hash().lower() != commitment_hash.lower():
        raise ExecutorCalldataError("intent commitment changed during calldata binding")
    if executor_route_commitment(route_hash=bound_intent.route_hash, topology_hash=topology_hash).lower() != route_commitment.lower():
        raise ExecutorCalldataError("route commitment changed during calldata binding")

    envelope = TransactionEnvelope(
        chain_id=intent.chain_id,
        sender=intent.sender,
        executor=intent.executor,
        nonce=intent.nonce,
        calldata=calldata,
        gas_limit=gas_limit,
        max_fee_per_gas=max_fee_per_gas,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
    )
    return BoundExecutorCall(
        calldata=calldata,
        calldata_hash=calldata_hash,
        topology_hash=topology_hash,
        route_commitment=route_commitment,
        intent_commitment_hash=commitment_hash,
        bound_intent=bound_intent,
        envelope=envelope,
    )
