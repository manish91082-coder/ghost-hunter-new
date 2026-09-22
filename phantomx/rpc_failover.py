"""Resilient, zero-cost Polygon read-only RPC pool with task-preserving failover.

The logical route/task is independent from the provider used to serve it:
provider failure causes provider rotation, not route deletion. Market callers pin
their own block context, so a successful failover can continue serving the same
block when the replacement provider supports historical reads.

No credentials, signing, transaction submission, relay, or broadcast exists in
this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic, perf_counter
from typing import Any, Mapping, Sequence
from urllib.error import URLError

from .polygon_rpc_http import PolygonRPCHTTPConfig, PolygonRPCHTTPTransport, PolygonRPCHTTPError

POLYGON_CHAIN_ID = 137


@dataclass(frozen=True)
class PublicRPCRecord:
    provider_id: str
    endpoint_url: str
    family: str
    enabled: bool = True
    max_concurrency: int = 1
    chain_id: int = POLYGON_CHAIN_ID


DEFAULT_FREE_POLYGON_RPC_POOL: tuple[PublicRPCRecord, ...] = (
    PublicRPCRecord("drpc-public", "https://polygon.drpc.org/", "drpc"),
    PublicRPCRecord("publicnode-bor", "https://polygon-bor-rpc.publicnode.com", "publicnode"),
    PublicRPCRecord("one-rpc-public", "https://public.1rpc.io/matic", "1rpc"),
    PublicRPCRecord("blast-public", "https://polygon-mainnet.public.blastapi.io", "blast"),
    PublicRPCRecord("blockpi-public", "https://polygon.blockpi.network/v1/rpc/public", "blockpi"),
    PublicRPCRecord("onfinality-public", "https://polygon.api.onfinality.io/public", "onfinality"),
    PublicRPCRecord("omnia-public", "https://endpoints.omniatech.io/v1/matic/mainnet/public", "omnia"),
    PublicRPCRecord("subquery-public", "https://polygon.rpc.subquery.network/public", "subquery"),
    PublicRPCRecord("llamanodes-public", "https://polygon.llamarpc.com", "llamanodes"),
    PublicRPCRecord("polkachu-public", "https://polygon-rpc.polkachu.com", "polkachu"),
    PublicRPCRecord("unifra-public", "https://polygon-mainnet-public.unifra.io", "unifra"),
    PublicRPCRecord("croswap-public", "https://polygon.croswap.com/rpc", "croswap"),
)


class RPCPoolError(RuntimeError):
    """Raised when no remaining provider can satisfy a read request."""


@dataclass
class _State:
    record: PublicRPCRecord
    transport: PolygonRPCHTTPTransport
    health_score: float = 1.0
    consecutive_failures: int = 0
    circuit_open_until: float = 0.0
    latency_ms: float = 0.0
    last_success_monotonic: float = 0.0
    in_flight: int = 0
    last_error: str | None = None

    @property
    def eligible(self) -> bool:
        return (
            self.record.enabled
            and self.record.chain_id == POLYGON_CHAIN_ID
            and self.circuit_open_until <= monotonic()
            and self.health_score > 0
            and self.in_flight < self.record.max_concurrency
        )


@dataclass(frozen=True)
class RPCAttempt:
    provider_id: str
    success: bool
    recoverable: bool
    latency_ms: float
    error: str | None = None


@dataclass
class PolygonRPCFailoverPool:
    """Fail over each logical read before a caller can classify it as unavailable."""

    records: tuple[PublicRPCRecord, ...] = DEFAULT_FREE_POLYGON_RPC_POOL
    failure_threshold: int = 2
    circuit_cooldown_seconds: float = 20.0
    _states: dict[str, _State] = field(default_factory=dict, init=False, repr=False)
    _preferred_provider_id: str | None = field(default=None, init=False, repr=False)
    _history: list[RPCAttempt] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.records:
            raise RPCPoolError("at least one RPC record is required")
        if self.failure_threshold < 1:
            raise RPCPoolError("failure_threshold must be positive")
        if self.circuit_cooldown_seconds <= 0:
            raise RPCPoolError("circuit cooldown must be positive")
        seen: set[str] = set()
        for record in self.records:
            if record.provider_id in seen:
                raise RPCPoolError("duplicate provider_id")
            seen.add(record.provider_id)
            if record.chain_id != POLYGON_CHAIN_ID:
                raise RPCPoolError("all providers must target Polygon mainnet")
            if not record.endpoint_url.startswith(("https://", "http://")):
                raise RPCPoolError("RPC endpoint must use HTTP(S)")
            if record.max_concurrency < 1:
                raise RPCPoolError("provider max_concurrency must be positive")
            self._states[record.provider_id] = _State(
                record=record,
                transport=PolygonRPCHTTPTransport(
                    PolygonRPCHTTPConfig(
                        provider_name=record.provider_id,
                        endpoint_url=record.endpoint_url,
                        timeout_seconds=8.0,
                    )
                ),
            )

    @property
    def history(self) -> tuple[RPCAttempt, ...]:
        return tuple(self._history)

    def provider_stats(self) -> tuple[dict[str, Any], ...]:
        now = monotonic()
        return tuple(
            {
                "provider_id": state.record.provider_id,
                "family": state.record.family,
                "health_score": round(state.health_score, 6),
                "consecutive_failures": state.consecutive_failures,
                "circuit_open": state.circuit_open_until > now,
                "latency_ms": round(state.latency_ms, 3),
                "last_error": state.last_error,
            }
            for state in sorted(self._states.values(), key=lambda item: item.record.provider_id)
        )

    def _ordered_eligible(self) -> list[_State]:
        states = [state for state in self._states.values() if state.eligible]
        states.sort(
            key=lambda state: (
                state.latency_ms if state.latency_ms > 0 else 10_000,
                -state.health_score,
                state.consecutive_failures,
                state.record.provider_id,
            )
        )
        if self._preferred_provider_id is None:
            return states
        preferred = next(
            (state for state in states if state.record.provider_id == self._preferred_provider_id),
            None,
        )
        if preferred is None:
            return states
        return [preferred, *[state for state in states if state is not preferred]]

    @staticmethod
    def _extract_result(response: Mapping[str, Any], method: str) -> Any:
        if not isinstance(response, Mapping):
            raise RPCPoolError(f"{method}: provider returned non-object response")
        error = response.get("error")
        if error is not None:
            if isinstance(error, Mapping):
                code = error.get("code", "UNKNOWN")
                message = str(error.get("message", "RPC error"))
                raise RPCPoolError(f"{method}: RPC error code={code} message={message}")
            raise RPCPoolError(f"{method}: RPC error {error}")
        if "result" not in response:
            raise RPCPoolError(f"{method}: missing result")
        return response["result"]

    @staticmethod
    def _recoverable(exc: BaseException) -> bool:
        message = str(exc).lower()
        if isinstance(exc, (TimeoutError, URLError, PolygonRPCHTTPError)):
            return True
        # A provider returning a reasoned EVM execution revert is giving semantic
        # route/call feedback, not a transport failure. Retrying the same call across
        # the full fleet can turn one deterministic route rejection into an RPC storm.
        # Preserve that fail-closed behavior. A bare "Unexpected error" revert reason
        # is different: it is not an informative route verdict and has appeared as a
        # provider-specific read anomaly on otherwise read-only factory discovery, so
        # allow the bounded fleet failover to seek an independent answer.
        if "execution reverted" in message:
            # A revert with a concrete reason is semantic route/call evidence and
            # must remain terminal. A reason-less revert is ambiguous because the
            # provider may have dropped the revert payload; allow bounded failover
            # so an independent provider can establish the actual result.
            marker = "execution reverted"
            suffix = message.split(marker, 1)[1].strip()
            if suffix.startswith(":"):
                suffix = suffix[1:].strip()
            return suffix in {"", "unexpected error"}
        markers = (
            "401", "402", "403", "408", "410", "429", "500", "502", "503", "504",
            "rate limit", "too many requests", "timeout",
            "temporarily unavailable", "service unavailable", "gateway",
            "overloaded", "header not found", "historical state",
            "missing trie", "pruned", "connection reset", "connection refused", "unexpected provider chain id",
            "rpc error code=",
        )
        return any(marker in message for marker in markers)

    def _record_success(self, state: _State, latency_ms: float) -> None:
        state.in_flight = max(0, state.in_flight - 1)
        state.consecutive_failures = 0
        state.health_score = min(1.0, state.health_score * 0.85 + 0.15)
        state.latency_ms = latency_ms
        state.last_success_monotonic = monotonic()
        state.last_error = None

    def _record_failure(self, state: _State, message: str, recoverable: bool) -> None:
        state.in_flight = max(0, state.in_flight - 1)
        state.consecutive_failures += 1
        state.last_error = message
        state.health_score = max(0.0, state.health_score * (0.65 if recoverable else 0.4))
        if recoverable and state.consecutive_failures >= self.failure_threshold:
            state.circuit_open_until = monotonic() + self.circuit_cooldown_seconds

    def call(self, method: str, params: Sequence[Any] = ()) -> Any:
        """Call one read, rotating providers with one bounded recovery pass."""
        if not isinstance(params, Sequence) or isinstance(params, (str, bytes, bytearray)):
            raise RPCPoolError("params must be a sequence")

        attempts: list[str] = []
        for round_index in range(2):
            eligible = self._ordered_eligible()
            if not eligible:
                if round_index == 0:
                    self.reset_circuits()
                    eligible = self._ordered_eligible()
                if not eligible:
                    break

            for state in eligible:
                state.in_flight += 1
                started = perf_counter()
                try:
                    response = state.transport.call(method, params)
                    value = self._extract_result(response, method)
                    if method == "eth_chainId" and value != "0x89":
                        raise RPCPoolError(f"eth_chainId: unexpected provider chain id {value}")
                    latency_ms = (perf_counter() - started) * 1000
                    self._record_success(state, latency_ms)
                    self._preferred_provider_id = state.record.provider_id
                    self._history.append(RPCAttempt(state.record.provider_id, True, False, latency_ms))
                    return value
                except Exception as exc:
                    latency_ms = (perf_counter() - started) * 1000
                    recoverable = self._recoverable(exc)
                    self._record_failure(state, str(exc), recoverable)
                    self._history.append(RPCAttempt(state.record.provider_id, False, recoverable, latency_ms, str(exc)))
                    if self._preferred_provider_id == state.record.provider_id:
                        self._preferred_provider_id = None
                    attempts.append(f"round={round_index + 1} {state.record.provider_id}: {type(exc).__name__}: {exc}")
                    if not recoverable:
                        raise
            if round_index == 0:
                self.reset_circuits()
        raise RPCPoolError("all bounded Polygon RPC recovery passes failed: " + " | ".join(attempts))
    def failure_history(self) -> tuple[RPCAttempt, ...]:
        return tuple(item for item in self._history if not item.success)

    def reset_circuits(self) -> None:
        for state in self._states.values():
            state.circuit_open_until = 0.0
            state.consecutive_failures = 0
        self._preferred_provider_id = None


def build_free_polygon_rpc_pool() -> PolygonRPCFailoverPool:
    return PolygonRPCFailoverPool()