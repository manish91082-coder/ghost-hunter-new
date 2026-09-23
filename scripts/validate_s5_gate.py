#!/usr/bin/env python3
"""Validate the S5 evidence contract before allowing automatic S0 progression."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Mapping

def validate_s5_artifact(payload: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    if payload.get("read_only") is not True:
        errors.append("read_only must be true")
    for key in ("signing", "submission", "broadcast", "live_capital"):
        if payload.get(key) is not False:
            errors.append(f"{key} must be false")
    if payload.get("chain_id_expected") != 137:
        errors.append("chain_id_expected must be 137")
    if payload.get("economic_certification") != "NOT_PERFORMED":
        errors.append("economic_certification must remain NOT_PERFORMED")
    if payload.get("profit_claim") != "NONE":
        errors.append("profit_claim must remain NONE")

    provenance = payload.get("provenance")
    if not isinstance(provenance, Mapping):
        errors.append("provenance is missing")
    elif not provenance.get("git_commit_sha") or provenance.get("git_commit_sha") == "UNKNOWN":
        errors.append("provenance.git_commit_sha is missing")

    results = payload.get("successful_endpoints")
    if not isinstance(results, list) or not results:
        errors.append("successful_endpoints must contain at least one result")
    else:
        for index, result in enumerate(results):
            if not isinstance(result, Mapping):
                errors.append(f"successful_endpoints[{index}] is not an object")
                continue
            if result.get("status") != "SUCCESS":
                errors.append(f"successful_endpoints[{index}].status is not SUCCESS")
            coverage = result.get("coverage")
            if not isinstance(coverage, Mapping) or coverage.get("status") != "COMPLETE":
                errors.append(f"successful_endpoints[{index}] coverage is not COMPLETE")
            pair_universe = result.get("pair_universe")
            if not isinstance(pair_universe, Mapping) or pair_universe.get("status") != "COMPLETE_RECENT_WINDOW":
                errors.append(f"successful_endpoints[{index}] pair universe is not COMPLETE_RECENT_WINDOW")

    pair_universe = payload.get("pair_universe")
    if not isinstance(pair_universe, Mapping) or pair_universe.get("status") != "COMPLETE_RECENT_WINDOW":
        errors.append("aggregate pair universe is not COMPLETE_RECENT_WINDOW")

    failed = payload.get("failed_endpoints")
    if failed not in ([], None):
        errors.append("failed_endpoints is non-empty")

    return (not errors, tuple(errors))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.artifact.read_text(encoding="utf-8"))
    ok, errors = validate_s5_artifact(payload)
    if ok:
        print("S5_GATE=PASS")
        print("S5_GATE_REASON=declared S5 coverage is complete and safety/economic non-claiming invariants hold")
        return 0
    print("S5_GATE=BLOCKED")
    for error in errors:
        print(f"REASON={error}")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
