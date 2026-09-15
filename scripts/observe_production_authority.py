#!/usr/bin/env python3
"""Operator-safe Phase-19 production executor authority observation utility.

This command consumes only explicit operator environment configuration, uses
the existing read-only Polygon quorum boundary, verifies owner == expected
signer, and emits canonical non-secret authority evidence. It never accepts
private keys, writes to Polygon, signs, submits, or exposes endpoint values.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from phantomx.production_authority import load_production_authority_config_from_env, observe_production_executor_authority


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Observe and audit controlled Polygon executor authority without signing or submission."
    )


def _evidence_record(evidence) -> dict[str, object]:
    return {
        "schema_version": evidence.schema_version,
        "chain_id": evidence.chain_id,
        "executor": evidence.executor,
        "owner": evidence.owner,
        "observed_block": evidence.observed_block,
        "runtime_code_hash": evidence.runtime_code_hash,
        "evidence_hash": evidence.evidence_hash,
    }


def main(argv: Sequence[str] | None = None) -> int:
    build_parser().parse_args(argv)
    try:
        config = load_production_authority_config_from_env()
        evidence = observe_production_executor_authority(config)
    except Exception:
        # The operator-facing boundary must never echo configuration, endpoint,
        # transport, or provider exception detail into an audit terminal/log.
        print("BLOCKED: production authority observation failed closed", file=sys.stderr)
        return 2

    print(json.dumps(_evidence_record(evidence), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
