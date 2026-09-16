#!/usr/bin/env python3
"""Orchestrate offline validation of a Phase-19 consolidated evidence session.

This coordinator never contacts production infrastructure, signs, submits,
broadcasts, or releases capital. It validates the session manifest structure and
runs only the already-approved lane validators for evidence files that exist.
Missing lanes remain BLOCKED rather than being inferred GREEN.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REQUIRED_LANES = (
    "signer",
    "polygon_authority",
    "private_relay",
    "shadow_staging",
    "realized_pnl",
)
REQUIRED_MANIFEST = {
    "schema_version",
    "session_id",
    "verified_artifact_commit",
    "intended_executor",
    "expected_signer",
    "operator_identity",
    "witness_identity",
    "observed_at_utc",
    "lanes",
}

VALIDATORS = {
    "signer": "scripts/validate_signer_evidence.py",
    "polygon_authority": "scripts/validate_production_authority_evidence.py",
    "private_relay": "scripts/validate_private_relay_evidence.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a consolidated Phase-19 evidence session")
    parser.add_argument("manifest", type=Path)
    return parser


def _nonempty_text(record: dict[str, object], field: str) -> None:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a JSON object")
        missing = sorted(REQUIRED_MANIFEST - set(manifest))
        if missing:
            raise ValueError("missing required manifest fields: " + ", ".join(missing))
        unknown = sorted(set(manifest) - REQUIRED_MANIFEST)
        if unknown:
            raise ValueError("manifest contains unknown fields: " + ", ".join(unknown))
        if manifest["schema_version"] != 1:
            raise ValueError("unsupported manifest schema version")
        for field in (
            "session_id",
            "verified_artifact_commit",
            "intended_executor",
            "expected_signer",
            "operator_identity",
            "witness_identity",
            "observed_at_utc",
        ):
            _nonempty_text(manifest, field)

        lanes = manifest["lanes"]
        if not isinstance(lanes, dict):
            raise ValueError("lanes must be an object")
        if set(lanes) != set(REQUIRED_LANES):
            raise ValueError("lanes must contain exactly the required lane names")

        results: dict[str, dict[str, object]] = {}
        repo_root = Path(__file__).resolve().parents[1]
        for lane in REQUIRED_LANES:
            entry = lanes[lane]
            if not isinstance(entry, dict):
                raise ValueError(f"lane {lane} must be an object")
            status = entry.get("status")
            evidence_path = entry.get("evidence_file")
            if status not in {"GREEN", "BLOCKED", "FAILED"}:
                raise ValueError(f"lane {lane}: status must be GREEN, BLOCKED, or FAILED")
            if evidence_path is not None and not isinstance(evidence_path, str):
                raise ValueError(f"lane {lane}: evidence_file must be text when supplied")

            if lane not in VALIDATORS:
                results[lane] = {"status": status, "validation": "NOT_AVAILABLE"}
                continue

            if not evidence_path:
                results[lane] = {"status": "BLOCKED", "validation": "MISSING_EVIDENCE_FILE"}
                continue

            candidate = (repo_root / evidence_path).resolve()
            try:
                candidate.relative_to(repo_root)
            except ValueError as exc:
                raise ValueError(f"lane {lane}: evidence_file escapes repository root") from exc
            if not candidate.is_file():
                results[lane] = {"status": "BLOCKED", "validation": "EVIDENCE_FILE_NOT_FOUND"}
                continue

            completed = subprocess.run(
                [sys.executable, str(repo_root / VALIDATORS[lane]), str(candidate)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode == 0:
                results[lane] = {"status": "GREEN", "validation": "ACCEPTED_FOR_INDEPENDENT_REVIEW"}
            else:
                results[lane] = {
                    "status": "FAILED",
                    "validation": "BLOCKED_BY_LANE_VALIDATOR",
                }

        failed = [lane for lane, result in results.items() if result["status"] == "FAILED"]
        output = {
            "schema_version": 1,
            "session_id": manifest["session_id"],
            "verified_artifact_commit": manifest["verified_artifact_commit"],
            "lane_results": results,
            "overall_status": "FAILED" if failed else "REVIEW_REQUIRED",
        }
        print(json.dumps(output, sort_keys=True, separators=(",", ":")))
        return 2 if failed else 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
