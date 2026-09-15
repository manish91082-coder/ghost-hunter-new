"""Dependency-free execution-control primitives for Phase 19 adversarial tests.

These are policy/test models, not production nonce/signing infrastructure.
They make replay, nonce, and lifecycle invariants executable before the real
Polygon integration is wired.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .execution import ExecutionState


_ALLOWED: dict[ExecutionState, frozenset[ExecutionState]] = {
    ExecutionState.CREATED: frozenset({ExecutionState.SIMULATED}),
    ExecutionState.SIMULATED: frozenset({ExecutionState.AUTHORIZED}),
    ExecutionState.AUTHORIZED: frozenset({ExecutionState.NONCE_RESERVED}),
    ExecutionState.NONCE_RESERVED: frozenset({ExecutionState.BUILT}),
    ExecutionState.BUILT: frozenset({ExecutionState.VERIFIED}),
    ExecutionState.VERIFIED: frozenset({ExecutionState.SIGNED}),
    ExecutionState.SIGNED: frozenset({ExecutionState.PRIVATE_SUBMITTED}),
    ExecutionState.PRIVATE_SUBMITTED: frozenset({ExecutionState.PENDING}),
    ExecutionState.PENDING: frozenset({ExecutionState.INCLUDED}),
    ExecutionState.INCLUDED: frozenset({ExecutionState.RECONCILED}),
    ExecutionState.RECONCILED: frozenset({ExecutionState.PROFIT_CONFIRMED, ExecutionState.PROFIT_FAILED}),
    ExecutionState.PROFIT_CONFIRMED: frozenset(),
    ExecutionState.PROFIT_FAILED: frozenset(),
}


@dataclass
class Lifecycle:
    state: ExecutionState = ExecutionState.CREATED

    def advance(self, target: ExecutionState) -> None:
        if target not in _ALLOWED[self.state]:
            raise ValueError(f"invalid lifecycle transition: {self.state.value} -> {target.value}")
        self.state = target

    def walk(self, states: Iterable[ExecutionState]) -> None:
        for state in states:
            self.advance(state)


class ReplayRegistry:
    """Single-use intent registry for tests.

    Production must replace this with a durable, race-safe replay mechanism
    appropriate to the signer/executor boundary.
    """

    def __init__(self) -> None:
        self._consumed: set[str] = set()

    def consume(self, intent_hash: str) -> None:
        if intent_hash in self._consumed:
            raise ValueError("intent replay detected")
        self._consumed.add(intent_hash)

    def is_consumed(self, intent_hash: str) -> bool:
        return intent_hash in self._consumed


class NonceBook:
    """Minimal atomic-model nonce allocator used only by deterministic tests."""

    def __init__(self, starting_nonce: int = 0) -> None:
        if starting_nonce < 0:
            raise ValueError("starting nonce must be non-negative")
        self._next = starting_nonce

    def reserve(self) -> int:
        nonce = self._next
        self._next += 1
        return nonce

    @property
    def next_nonce(self) -> int:
        return self._next
