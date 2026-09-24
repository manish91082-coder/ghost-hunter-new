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
from time import monotonic, perf_counter, sleep
from threading import RLock
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
    # Two bounded lanes per public provider prevent an 8-worker hunt from
    # self-starving when only a small subset of free providers remains usable.
    max_concurrency: int = 2
    chain_id: int = POLYGON_CHAIN_ID


# Public Polygon PoS endpoints verified against the current Polygon RPC endpoint
# documentation/static registry on 2026-09-23. No API keys or credentials are embedded.
# Public endpoints remain best-effort and may impose rate/traffic limits.
DEFAULT_FREE_POLYGON_RPC_POOL: tuple[PublicRPCRecord, ...] = (
    PublicRPCRecord("drpc-public", "https://polygon.drpc.org/", "drpc"),
    PublicRPCRecord("tenderly-public", "https://tenderly.rpc.polygon.community", "tenderly"),
    PublicRPCRecord("publicnode-public", "https://polygon.publicnode.com", "publicnode"),
    PublicRPCRecord("nodies-public", "https://polygon-public.nodies.app/", "nodies"),
    PublicRPCRecord("one-rpc-public", "https://1rpc.io/matic", "1rpc"),
    PublicRPCRecord("onfinality-public", "https://polygon.api.onfinality.io/public", "onfinality"),
    # Polygon current official public list: use the public QuickNode lane; keyless polygon-rpc.com is deprecated.\n    PublicRPCRecord("quicknode-public", "https://rpc-mainnet.matic.quiknode.pro", "quicknode"),
    PublicRPCRecord("tatum-public", "https://polygon-mainnet.gateway.tatum.io/", "tatum"),
)


class RPCPoolError(RuntimeError):
    """Raised when no remaining provider can satisfy a read request."""


class RPCSemanticRevertConsensusError(RPCPoolError):
    """Raised when distinct providers independently reproduce an ambiguous revert."""


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
    quarantined_until: float = 0.0
    last_error: str | None = None

    @property
    def eligible(self) -> bool:
        return (
            self.record.enabled
            and self.record.chain_id == POLYGON_CHAIN_ID
            and self.circuit_open_until <= monotonic()
            and self.quarantined_until <= monotonic()
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
    provider_fatal_cooldown_seconds: float = 3600.0
    provider_temporary_cooldown_seconds: float = 60.0
    provider_admission_wait_seconds: float = 5.0
    ambiguous_revert_retry_delay_seconds: float = 1.0
    _states: dict[str, _State] = field(default_factory=dict, init=False, repr=False)
    _preferred_provider_id: str | None = field(default=None, init=False, repr=False)
    _history: list[RPCAttempt] = field(default_factory=list, init=False, repr=False)
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.records:
            raise RPCPoolError("at least one RPC record is required")
        if self.failure_threshold < 1:
            raise RPCPoolError("failure_threshold must be positive")
        if self.circuit_cooldown_seconds <= 0:
            raise RPCPoolError("circuit cooldown must be positive")
        if self.provider_fatal_cooldown_seconds <= 0:
            raise RPCPoolError("provider fatal cooldown must be positive")
        if self.provider_temporary_cooldown_seconds <= 0:
            raise RPCPoolError("provider temporary cooldown must be positive")
        if self.provider_admission_wait_seconds <= 0:
            raise RPCPoolError("provider admission wait must be positive")
        if self.ambiguous_revert_retry_delay_seconds <= 0:
            raise RPCPoolError("ambiguous revert retry delay must be positive")
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
        with self._lock:
            return tuple(self._history)

    def provider_stats(self) -> tuple[dict[str, Any], ...]:
        with self._lock:
            now = monotonic()
            states = sorted(self._states.values(), key=lambda item: item.record.provider_id)
            return tuple(
                {
                    "provider_id": state.record.provider_id,
                    "family": state.record.family,
                    "health_score": round(state.health_score, 6),
                    "consecutive_failures": state.consecutive_failures,
                    "circuit_open": state.circuit_open_until > now,
                    "quarantined": state.quarantined_until > now,
                    "latency_ms": round(state.latency_ms, 3),
                    "last_error": state.last_error,
                }
                for state in states
            )

    def _ordered_eligible(self, exclude_provider_ids: Sequence[str] = ()) -> list[_State]:
        excluded = set(exclude_provider_ids)
        with self._lock:
            states = [
                state
                for state in self._states.values()
                if state.record.provider_id not in excluded and state.eligible
            ]
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

    def _try_reserve(self, state: _State) -> bool:
        with self._lock:
            if not state.eligible:
                return False
            state.in_flight += 1
            return True

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
    def _ambiguous_execution_revert(exc: BaseException) -> bool:
        """Return True only for a reason-less/"Unexpected error" EVM revert."""
        message = str(exc).lower()
        if "execution reverted" not in message:
            return False
        suffix = message.split("execution reverted", 1)[1].strip()
        if suffix.startswith(":"):
            suffix = suffix[1:].strip()
        return suffix in {"", "unexpected error"}

    @staticmethod
    def _provider_fatal(exc: BaseException) -> bool:
        message = str(exc).lower()
        return "status=401" in message or "paid plans only" in message or "api key required" in message or "authentication required" in message

    @staticmethod
    def _historical_state_unavailable(exc: BaseException) -> bool:
        message = str(exc).lower()
        return "historical state" in message

    @staticmethod
    def _provider_temporary_failure(exc: BaseException) -> bool:
        """Identify provider-local overload/access failures that should be quarantined briefly.

        Historical-state availability is task-local because a provider may still serve
        current/latest reads even when it cannot serve one pinned block.
        """
        message = str(exc).lower()
        markers = (
            "status=403",
            "status=408",
            "status=429",
            "rate limit",
            "too many requests",
            "temporarily unavailable",
            "service unavailable",
        )
        return any(marker in message for marker in markers)

    @staticmethod
    def _recoverable(exc: BaseException, *, allow_ambiguous_revert: bool = False) -> bool:
        message = str(exc).lower()
        if isinstance(exc, (TimeoutError, URLError, PolygonRPCHTTPError)):
            return True
        # By default, an EVM execution revert remains terminal because callers such
        # as Curve registry discovery use reverts as semantic "no match" signals.
        # Quote execution can explicitly opt into bounded failover when the provider
        # omitted a concrete revert reason.
        if "execution reverted" in message:
            # A revert with a concrete reason is semantic route/call evidence and
            # must remain terminal. A reason-less revert is ambiguous because the
            # provider may have dropped the revert payload; only callers that
            # explicitly opt into ambiguous-revert recovery may fail over.
            return allow_ambiguous_revert and PolygonRPCFailoverPool._ambiguous_execution_revert(exc)
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
        with self._lock:
            state.in_flight = max(0, state.in_flight - 1)
            state.consecutive_failures = 0
            state.health_score = min(1.0, state.health_score * 0.85 + 0.15)
            state.latency_ms = latency_ms
            state.last_success_monotonic = monotonic()
            state.last_error = None

    def _record_ambiguous_revert(self, state: _State, message: str, latency_ms: float) -> None:
        """Record ambiguous semantic evidence without poisoning provider health."""
        with self._lock:
            state.in_flight = max(0, state.in_flight - 1)
            state.last_error = message
            state.latency_ms = latency_ms

    def _record_task_local_failure(self, state: _State, message: str, latency_ms: float) -> None:
        """Record a read-local failure without degrading provider-wide health."""
        with self._lock:
            state.in_flight = max(0, state.in_flight - 1)
            state.last_error = message
            state.latency_ms = latency_ms

    def _record_failure(self, state: _State, message: str, recoverable: bool) -> None:
        with self._lock:
            state.in_flight = max(0, state.in_flight - 1)
            state.consecutive_failures += 1
            state.last_error = message
            state.health_score = max(0.0, state.health_score * (0.65 if recoverable else 0.4))
            if recoverable and state.consecutive_failures >= self.failure_threshold:
                state.circuit_open_until = monotonic() + self.circuit_cooldown_seconds

    def _has_busy_usable_provider(self, exclude_provider_ids: Sequence[str] = ()) -> bool:
        """Return whether a healthy non-excluded provider is temporarily saturated."""
        excluded = set(exclude_provider_ids)
        now = monotonic()
        with self._lock:
            return any(
                state.record.provider_id not in excluded
                and state.record.enabled
                and state.record.chain_id == POLYGON_CHAIN_ID
                and state.circuit_open_until <= now
                and state.quarantined_until <= now
                and state.health_score > 0
                and state.in_flight >= state.record.max_concurrency
                for state in self._states.values()
            )

    def _wait_for_provider_capacity(self, exclude_provider_ids: Sequence[str] = ()) -> bool:
        """Wait boundedly for a non-excluded provider slot; never spin indefinitely."""
        deadline = monotonic() + self.provider_admission_wait_seconds
        while True:
            if self._ordered_eligible(exclude_provider_ids):
                return True
            if not self._has_busy_usable_provider(exclude_provider_ids):
                return False
            remaining = deadline - monotonic()
            if remaining <= 0:
                return False
            sleep(min(0.05, remaining))

    def _call_internal(
        self,
        method: str,
        params: Sequence[Any] = (),
        *,
        allow_ambiguous_revert: bool = False,
    ) -> Any:
        """Call one read, rotating providers with one bounded recovery pass."""
        if not isinstance(params, Sequence) or isinstance(params, (str, bytes, bytearray)):
            raise RPCPoolError("params must be a sequence")

        attempts: list[str] = []
        excluded_provider_ids: set[str] = set()
        ambiguous_revert_providers: set[str] = set()
        ambiguous_revert_retries: set[str] = set()
        for round_index in range(2):
            while True:
                eligible = self._ordered_eligible(excluded_provider_ids)
                if eligible:
                    break
                if self._wait_for_provider_capacity(excluded_provider_ids):
                    continue
                if round_index == 0:
                    self.reset_circuits()
                    if self._ordered_eligible(excluded_provider_ids):
                        continue
                    if self._wait_for_provider_capacity(excluded_provider_ids):
                        continue
                elif excluded_provider_ids:
                    # A lone ambiguous-revert provider is still healthy. When every
                    # alternate is unavailable, allow exactly one delayed retry before
                    # declaring bounded recovery exhausted.
                    if (
                        len(excluded_provider_ids) == 1
                        and excluded_provider_ids == ambiguous_revert_providers
                        and not ambiguous_revert_retries
                    ):
                        sleep(self.ambiguous_revert_retry_delay_seconds)
                        ambiguous_revert_retries.update(excluded_provider_ids)
                        excluded_provider_ids.clear()
                        eligible = self._ordered_eligible()
                        if eligible:
                            continue
                    if len(excluded_provider_ids) >= 2:
                        excluded_provider_ids.clear()
                        if self._wait_for_provider_capacity():
                            continue
                        eligible = self._ordered_eligible()
                        if eligible:
                            break
                break

            if not eligible:
                break

            reserved_any = False
            for state in eligible:
                if not self._try_reserve(state):
                    continue
                reserved_any = True
                started = perf_counter()
                try:
                    response = state.transport.call(method, params)
                    value = self._extract_result(response, method)
                    if method == "eth_chainId" and value != "0x89":
                        raise RPCPoolError(f"eth_chainId: unexpected provider chain id {value}")
                    latency_ms = (perf_counter() - started) * 1000
                    self._record_success(state, latency_ms)
                    with self._lock:
                        self._preferred_provider_id = state.record.provider_id
                        self._history.append(RPCAttempt(state.record.provider_id, True, False, latency_ms))
                    return value
                except Exception as exc:
                    latency_ms = (perf_counter() - started) * 1000
                    recoverable = self._recoverable(
                        exc,
                        allow_ambiguous_revert=allow_ambiguous_revert,
                    )
                    ambiguous_revert = (
                        recoverable
                        and allow_ambiguous_revert
                        and self._ambiguous_execution_revert(exc)
                    )
                    if self._provider_fatal(exc):
                        with self._lock:
                            state.quarantined_until = max(
                                state.quarantined_until,
                                monotonic() + self.provider_fatal_cooldown_seconds,
                            )
                    elif self._provider_temporary_failure(exc):
                        with self._lock:
                            state.quarantined_until = max(
                                state.quarantined_until,
                                monotonic() + self.provider_temporary_cooldown_seconds,
                            )
                    if ambiguous_revert:
                        # Ambiguous EVM reverts are route/call evidence, not proof
                        # that the serving provider is unhealthy. Exclude this provider
                        # only from this logical recovery pass.
                        self._record_ambiguous_revert(state, str(exc), latency_ms)
                    elif self._historical_state_unavailable(exc):
                        # A provider can lack one pinned historical block while still
                        # serving current/latest state. Fail over for this logical read
                        # without degrading provider-wide health or opening its circuit.
                        self._record_task_local_failure(state, str(exc), latency_ms)
                    else:
                        self._record_failure(state, str(exc), recoverable)
                    excluded_provider_ids.add(state.record.provider_id)
                    with self._lock:
                        self._history.append(
                            RPCAttempt(
                                state.record.provider_id,
                                False,
                                recoverable,
                                latency_ms,
                                str(exc),
                            )
                        )
                        if self._preferred_provider_id == state.record.provider_id:
                            self._preferred_provider_id = None
                    attempts.append(
                        f"round={round_index + 1} {state.record.provider_id}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    if recoverable and self._ambiguous_execution_revert(exc):
                        ambiguous_revert_providers.add(state.record.provider_id)
                        if len(ambiguous_revert_providers) >= 2:
                            providers = ", ".join(sorted(ambiguous_revert_providers))
                            raise RPCSemanticRevertConsensusError(
                                "ambiguous execution revert consensus across distinct "
                                f"Polygon RPC providers: {providers}"
                            )
                    if not recoverable:
                        raise

            # A concurrent caller may claim every provider between eligibility
            # discovery and reservation. Wait once for a bounded release rather
            # than creating a false zero-attempt infrastructure failure.
            if not reserved_any and self._wait_for_provider_capacity(excluded_provider_ids):
                continue
            if round_index == 0:
                self.reset_circuits()

        if attempts:
            raise RPCPoolError(
                "all bounded Polygon RPC recovery passes failed: " + " | ".join(attempts)
            )
        raise RPCPoolError(
            "all bounded Polygon RPC recovery passes failed: "
            "provider admission wait exhausted"
        )
    def call(self, method: str, params: Sequence[Any] = ()) -> Any:
        """Call one read using default fail-closed revert semantics."""
        return self._call_internal(method, params)

    def call_with_ambiguous_revert_failover(
        self,
        method: str,
        params: Sequence[Any] = (),
    ) -> Any:
        """Call one read allowing bounded recovery for reason-less reverts."""
        return self._call_internal(
            method,
            params,
            allow_ambiguous_revert=True,
        )

    def probe_historical_state(self, block_number: int, address: str) -> tuple[dict[str, Any], ...]:
        """Probe per-provider historical state support without changing provider health."""
        if block_number < 0:
            raise RPCPoolError("historical probe block cannot be negative")
        if not isinstance(address, str) or not address.startswith(("0x", "0X")):
            raise RPCPoolError("historical probe address must be a hex address")
        block_tag = hex(block_number)
        results: list[dict[str, Any]] = []
        for state in sorted(self._states.values(), key=lambda item: item.record.provider_id):
            started = perf_counter()
            try:
                response = state.transport.call("eth_getCode", [address, block_tag])
                code = self._extract_result(response, "eth_getCode")
                if not isinstance(code, str):
                    raise RPCPoolError("eth_getCode: provider returned malformed code")
                results.append(
                    {
                        "provider_id": state.record.provider_id,
                        "compatible": True,
                        "latency_ms": round((perf_counter() - started) * 1000, 3),
                        "error": None,
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "provider_id": state.record.provider_id,
                        "compatible": False,
                        "latency_ms": round((perf_counter() - started) * 1000, 3),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        return tuple(results)

    def scoped_historical_records(
        self,
        block_number: int,
        address: str,
        *,
        minimum_providers: int = 2,
    ) -> tuple[PublicRPCRecord, ...]:
        """Return only providers proven able to serve one historical block."""
        if minimum_providers < 1:
            raise RPCPoolError("minimum historical providers must be positive")
        probes = self.probe_historical_state(block_number, address)
        capable_ids = {
            item["provider_id"] for item in probes if item["compatible"]
        }
        records = tuple(
            record for record in self.records
            if record.provider_id in capable_ids
        )
        if len(records) < minimum_providers:
            raise RPCPoolError(
                f"historical provider quorum unavailable at block {block_number}: "
                f"{len(records)} < {minimum_providers}"
            )
        return records

    def failure_history(self) -> tuple[RPCAttempt, ...]:
        with self._lock:
            return tuple(item for item in self._history if not item.success)

    def reset_circuits(self) -> None:
        with self._lock:
            for state in self._states.values():
                state.circuit_open_until = 0.0
                state.consecutive_failures = 0
            self._preferred_provider_id = None


def build_free_polygon_rpc_pool() -> PolygonRPCFailoverPool:
    return PolygonRPCFailoverPool()