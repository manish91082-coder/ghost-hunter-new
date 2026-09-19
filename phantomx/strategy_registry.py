"""Canonical Polygon strategy registry and readiness controls.

The registry is descriptive control-plane metadata. It does not authorize live
execution. A strategy can be discovery-enabled while execution remains locked.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StrategyStage(str, Enum):
    DISCOVERY = "DISCOVERY"
    ECONOMIC_CERTIFICATION = "ECONOMIC_CERTIFICATION"
    EXECUTION_CERTIFICATION = "EXECUTION_CERTIFICATION"


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    family: str
    min_legs: int
    max_legs: int
    discovery_enabled: bool
    execution_enabled: bool
    notes: str

    def __post_init__(self) -> None:
        if not self.strategy_id.strip() or not self.family.strip():
            raise ValueError("strategy_id and family are required")
        if self.min_legs < 2 or self.max_legs < self.min_legs:
            raise ValueError("invalid leg bounds")
        if self.execution_enabled and not self.discovery_enabled:
            raise ValueError("execution cannot be enabled when discovery is disabled")


DEFAULT_STRATEGIES: tuple[StrategySpec, ...] = (
    StrategySpec("S0", "DIRECT_CROSS_VENUE", 2, 2, True, True, "Canonical direct two-leg route."),
    StrategySpec("S1", "CLMM_CROSS_VENUE", 2, 2, True, True, "QuickSwap V3 <-> Uniswap V3."),
    StrategySpec("S2", "V4_CROSS_VENUE", 2, 2, True, False, "Uniswap V4 routes remain separately certified."),
    StrategySpec("S3", "RAMSES_CROSS_VENUE", 2, 2, True, True, "Ramses V3 <-> Uniswap V3."),
    StrategySpec("S4", "CURVE_AMM", 2, 4, True, False, "Curve/stable-swap graph family."),
    StrategySpec("S5", "BALANCER_AMM", 2, 4, True, False, "Balancer weighted/stable family."),
    StrategySpec("S6", "TRIANGULAR", 3, 3, True, False, "Three-leg bounded cycle discovery."),
    StrategySpec("S7", "FOUR_LEG", 4, 4, True, False, "Four-leg bounded cycle discovery."),
    StrategySpec("S8", "STABLECOIN_DEPEG", 2, 4, True, False, "Stable/bridged-stable graph."),
    StrategySpec("S9", "SAME_VENUE_MULTI_POOL", 2, 2, True, False, "Same-protocol pool/fee dislocation."),
    StrategySpec("S10", "SPLIT_ROUTE", 2, 4, True, False, "Multi-pool exact allocation search."),
    StrategySpec("S11", "CROSS_CURVE", 2, 4, True, False, "V2/V3/V4/stableswap/weighted curve mix."),
    StrategySpec("S12", "EVENT_DRIVEN", 2, 4, True, False, "State-change-triggered local rescans."),
    StrategySpec("S13", "NEW_POOL_WINDOW", 2, 4, True, False, "Burst scans for newly initialized pools."),
    StrategySpec("S14", "CORRELATED_ASSET", 2, 4, True, False, "Wrapped/LST/correlated asset cycles."),
    StrategySpec("S15", "ALT_FLASH_LIQUIDITY", 2, 4, True, False, "Alternative atomic liquidity variants."),
    StrategySpec("S16", "STATE_BACKRUN_DETECTOR", 2, 4, True, False, "Post-state-change discovery only."),
    StrategySpec("S17", "V4_HOOK_AWARE", 2, 4, True, False, "Hook semantics require dedicated certification."),
    StrategySpec("S18", "CROSS_PROTOCOL_ATOMIC", 2, 4, True, False, "Deterministic composability candidates."),
    StrategySpec("S19", "ORACLE_DIVERGENCE_DETECTOR", 2, 4, True, False, "Detector/ranking signal only."),
)


def get_strategy(strategy_id: str) -> StrategySpec:
    for spec in DEFAULT_STRATEGIES:
        if spec.strategy_id == strategy_id:
            return spec
    raise KeyError(strategy_id)


def execution_eligible(strategy_id: str) -> bool:
    return get_strategy(strategy_id).execution_enabled


def discovery_strategies() -> tuple[StrategySpec, ...]:
    return tuple(spec for spec in DEFAULT_STRATEGIES if spec.discovery_enabled)


def execution_strategies() -> tuple[StrategySpec, ...]:
    return tuple(spec for spec in DEFAULT_STRATEGIES if spec.execution_enabled)
