"""Deprecated compatibility shim for the canonical Phase-19 governor.

Canonical governor policy and decision logic live in :mod:`phantomx.governor`.
This module intentionally contains no independent policy implementation.
"""
from __future__ import annotations

from .governor import GovernorDecision, GovernorPolicy, GovernorError

ExecutionGovernorError = GovernorError


def govern_execution(*args, **kwargs):
    """Delegate to the canonical governor implementation.

    Callers should import ``GovernorPolicy``, ``GovernorDecision`` and
    ``govern_execution`` from ``phantomx.governor`` directly.
    """
    from .governor import govern_execution as _canonical_govern_execution
    return _canonical_govern_execution(*args, **kwargs)


__all__ = ["ExecutionGovernorError", "GovernorPolicy", "GovernorDecision", "govern_execution"]
