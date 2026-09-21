#!/usr/bin/env python3
"""Batch/offline Phase-19 evidence-session manifest preparer.

Builds one deterministic session manifest from the standard segregated evidence
layout. Presence of a file is not acceptance: lanes stay BLOCKED until the
consolidated offline coordinator validates the referenced evidence. This tool
never contacts production, signs, submits, broadcasts, or releases capital.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

LANE_FILES = {
    "signer": "signer/signer_evidence.json",
    "polygon_authority": "polygon_authority/polygon_authority_evidence.json",
    "private_relay": "private_relay/private_relay_evidence.json",
    "shadow_staging": "shadow_staging/shadow_staging_evidence.json",
    "realized_pnl": "realized_pnl/realized_pnl_evidence.json",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch Phase-19 evidence session preparation")
    parser.add_argument("workspace", type=Path, help="Evidence session workspace")
    parser.add_argument("--artifact-commit", required=True, help="Frozen 40-character git commit")
    parser.add_argument("--executor", required=True, help="Intended executor EVM address")
    parser.add_argument("--signer", required=True, help="Expected signer EVM address")
    parser.add_argument("--private-relay", required=True, help="Intended approved private relay name")
    parser.add_argument("--operator", required=True, help="Operator identity")
    parser.add_argument("--witness", required=True, help="Independent witness identity")
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--output", type=Path, default=None, help="Manifest output path")
    return parser


def _require_sha(value: str) -> str:
    value = value.strip().lower()
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError("--artifact-commit must be a 40-character lowercase hexadecimal git SHA")
    return value


def _require_address(value: str, field: str) -> str:
    value = value.strip()
    if len(value) != 42 or not value.startswith("0x"):
        raise ValueError(f"{field} must be a 20-byte EVM address")
    int(value[2:], 16)
    if value.lower() == "0x" + "0" * 40:
        raise ValueError(f"{field} must not be zero")
    return value


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        workspace = args.workspace.resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        artifact = _require_sha(args.artifact_commit)
        executor = _require_address(args.executor, "--executor")
        signer = _require_address(args.signer, "--signer")
        private_relay = args.private_relay.strip()
        operator = args.operator.strip()
        witness = args.witness.strip()
        if not private_relay or not operator or not witness:
            raise ValueError("--private-relay, --operator and --witness must be non-empty")

        session_id = args.session_id or datetime.now(timezone.utc).strftime("phase19-%Y%m%dT%H%M%SZ")
        lanes = {}
        for lane, relative_path in LANE_FILES.items():
            candidate = workspace / relative_path
            if candidate.is_file():
                lanes[lane] = {"status": "BLOCKED", "evidence_file": relative_path}
            else:
                lanes[lane] = {"status": "BLOCKED"}

        manifest = {
            "schema_version": 1,
            "session_id": session_id,
            "verified_artifact_commit": artifact,
            "intended_executor": executor,
            "expected_signer": signer,
            "intended_private_relay": private_relay,
            "operator_identity": operator,
            "witness_identity": witness,
            "observed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "lanes": lanes,
        }
        output = (args.output or (workspace / "session_manifest.json")).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        counts = {status: sum(1 for item in lanes.values() if item["status"] == status) for status in ("GREEN", "BLOCKED", "FAILED")}
        referenced = sum(1 for item in lanes.values() if "evidence_file" in item)
        print(json.dumps({
            "status": "MANIFEST_READY",
            "session_id": session_id,
            "artifact_commit": artifact,
            "manifest": str(output),
            "evidence_files_referenced": referenced,
            "lane_counts": counts,
        }, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
