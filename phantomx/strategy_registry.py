"""Canonical Polygon strategy readiness registry.

Strategy IDs S0/S1/S2/S3/S5/S5A/S6/S9/S10 are reserved for the repository's
existing named strategies. X-series IDs are expansion strategies.
Production execution remains globally gated elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    family: str
    min_legs: int
    max_legs: int
    discovery_enabled: bool
    execution_supported: bool
    production_authorized: bool
    notes: str

    def __post_init__(self) -> None:
        if not self.strategy_id.strip() or not self.family.strip():
            raise ValueError("strategy_id and family are required")
        if self.min_legs < 2 or self.max_legs < self.min_legs:
            raise ValueError("invalid leg bounds")
        if self.execution_supported and not self.discovery_enabled:
            raise ValueError("execution support requires discovery support")
        if self.production_authorized and not self.execution_supported:
            raise ValueError("production authorization requires execution support")


DEFAULT_STRATEGIES = (
    StrategySpec("S0", "QSV2_UV3", 2, 2, True, True, False, "Canonical direct First-Hunt."),
    StrategySpec("S1", "QSV3_UV3", 2, 2, True, True, False, "QuickSwap V3 <-> Uniswap V3."),
    StrategySpec("S2", "UV4_UV3", 2, 2, True, True, False, "Uniswap V4 hookless scope."),
    StrategySpec("S3", "RAMSES_UV3", 2, 2, True, True, False, "Ramses V3 <-> Uniswap V3."),
    StrategySpec("S5", "CURVE_UV3", 2, 2, True, True, False, "Curve <-> Uniswap V3."),
    StrategySpec("S5A", "CURVE_MAI", 2, 2, True, False, False, "Exploratory Curve/MAI probe."),
    StrategySpec("S6", "TRIANGULAR", 3, 3, True, False, False, "Three-leg bounded cycle."),
    StrategySpec("S9", "QSV2_RAMSES", 2, 2, True, True, False, "QuickSwap V2 <-> Ramses V3."),
    StrategySpec("S10", "QSV3_RAMSES", 2, 2, True, True, False, "QuickSwap V3 <-> Ramses V3."),
    StrategySpec("X1", "SAME_VENUE_MULTI_POOL", 2, 2, True, False, False, "Same-protocol pool/fee dislocation."),
    StrategySpec("X2", "SPLIT_ROUTE", 2, 4, True, False, False, "Multi-pool exact allocation."),
    StrategySpec("X3", "STABLECOIN_GRAPH", 2, 4, True, False, False, "Stable and bridged-stable cycles."),
    StrategySpec("X4", "FOUR_LEG", 4, 4, True, False, False, "Bounded four-leg cycles."),
    StrategySpec("X5", "CROSS_CURVE", 2, 4, True, False, False, "Mixed V2/V3/V4/Curve/weighted curves."),
    StrategySpec("X6", "EVENT_DRIVEN", 2, 4, True, False, False, "State-change-triggered rescans."),
    StrategySpec("X7", "NEW_POOL_WINDOW", 2, 4, True, False, False, "Newly initialized pool burst scans."),
    StrategySpec("X8", "V4_HOOK_AWARE", 2, 4, True, False, False, "Hook-aware V4 research."),
    StrategySpec("X9", "ALT_FLASH_LIQUIDITY", 2, 4, True, False, False, "Alternative atomic liquidity."),
    StrategySpec("X10", "CROSS_PROTOCOL_ATOMIC", 2, 4, True, False, False, "Deterministic composability."),
    StrategySpec("X11", "STATE_BACKRUN_DETECTOR", 2, 4, True, False, False, "State-dislocation detector."),
    StrategySpec("X12", "CORRELATED_ASSET", 2, 4, True, False, False, "Wrapped/LST/correlated asset cycles."),
    StrategySpec("X13", "ORACLE_DIVERGENCE_DETECTOR", 2, 4, True, False, False, "Detector only; oracle never executable truth."),
)


def get_strategy(strategy_id: str) -> StrategySpec:
    for spec in DEFAULT_STRATEGIES:
        if spec.strategy_id == strategy_id:
            return spec
    raise KeyError(strategy_id)


def discovery_strategies() -> tuple[StrategySpec, ...]:
    return tuple(spec for spec in DEFAULT_STRATEGIES if spec.discovery_enabled)


def execution_supported_strategies() -> tuple[StrategySpec, ...]:
    return tuple(spec for spec in DEFAULT_STRATEGIES if spec.execution_supported)


def production_authorized_strategies() -> tuple[StrategySpec, ...]:
    return tuple(spec for spec in DEFAULT_STRATEGIES if spec.production_authorized)


def execution_eligible(strategy_id: str) -> bool:
    return get_strategy(strategy_id).production_authorized
