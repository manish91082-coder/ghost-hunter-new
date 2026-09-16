#!/usr/bin/env python3
"""Orchestrate offline validation of a Phase-19 consolidated evidence session.

This coordinator never contacts production infrastructure, signs, submits,
broadcasts, or releases capital. It validates the session manifest structure,
runs only the approved offline lane validators, and binds accepted evidence to
the session's immutable artifact, executor, signer, private relay, operator,
and witness identities. Missing or contradictory lanes remain BLOCKED/FAILED
rather than being inferred GREEN.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

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
    "intended_private_relay",
    "operator_identity",
    "witness_identity",
    "observed_at_utc",
    "lanes",
}

VALIDATORS = {
    "signer": "scripts/validate_signer_evidence.py",
    "polygon_authority": "scripts/validate_production_authority_evidence.py",
    "private_relay": "scripts/validate_private_relay_evidence.py",
    "shadow_staging": "scripts/validate_shadow_staging_evidence.py",
    "realized_pnl": "scripts/validate_realized_pnl_evidence.py",
}

HEX40 = re.compile(r"^0x[0-9a-fA-F]{40}$")
GIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a consolidated Phase-19 evidence session")
    parser.add_argument("manifest", type=Path)
    return parser


def _nonempty_text(record: dict[str, object], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _address(record: dict[str, object], field: str) -> str:
    value = _nonempty_text(record, field)
    if not HEX40.fullmatch(value) or value.lower() == "0x" + "0" * 40:
        raise ValueError(f"{field} must be a valid non-zero EVM address")
    return value.lower()


def _artifact(record: dict[str, object], field: str) -> str:
    value = _nonempty_text(record, field).lower()
    if not GIT_SHA.fullmatch(value):
        raise ValueError(f"{field} must be a 40-character git SHA")
    return value


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"lane {label}: evidence is not readable JSON") from exc
    if not isinstance(data, dict):
        raise ValueError(f"lane {label}: evidence must be a JSON object")
    return data


def _bind_lane_identities(
    lane: str,
    evidence: dict[str, Any],
    manifest: dict[str, object],
) -> None:
    manifest_artifact = _artifact(manifest, "verified_artifact_commit")
    manifest_executor = _address(manifest, "intended_executor")
    manifest_signer = _address(manifest, "expected_signer")
    manifest_relay = _nonempty_text(manifest, "intended_private_relay")
    operator = _nonempty_text(manifest, "operator_identity")
    witness = _nonempty_text(manifest, "witness_identity")

    if lane == "signer":
        checks = {
            "expected_address": manifest_signer,
            "recovered_address": manifest_signer,
            "operator_identity": operator,
            "witness_identity": witness,
        }
    elif lane == "polygon_authority":
        checks = {
            "executor": manifest_executor,
            "expected_signer": manifest_signer,
            "observed_owner": manifest_signer,
            "operator_identity": operator,
            "witness_identity": witness,
        }
    elif lane == "private_relay":
        checks = {
            "relay_name": manifest_relay,
            "operator_identity": operator,
            "witness_identity": witness,
        }
    elif lane == "shadow_staging":
        checks = {
            "artifact_commit": manifest_artifact,
            "executor_identity": manifest_executor,
            "expected_signer": manifest_signer,
            "operator_identity": operator,
            "witness_identity": witness,
        }
    elif lane == "realized_pnl":
        checks = {
            "artifact_commit": manifest_artifact,
            "operator_identity": operator,
            "witness_identity": witness,
        }
    else:
        return

    for field, expected in checks.items():
        actual = evidence.get(field)
        if not isinstance(actual, str) or not actual.strip():
            raise ValueError(f"lane {lane}: evidence field {field} is missing or empty")
        if actual.strip().lower() != str(expected).lower():
            raise ValueError(
                f"lane {lane}: identity binding mismatch for {field}: "
                f"expected {expected}, observed {actual.strip()}"
            )


def _resolve_evidence_file(session_root: Path, evidence_path: str, lane: str) -> Path:
    relative = Path(evidence_path)
    if relative.is_absolute():
        raise ValueError(f"lane {lane}: evidence_file must be relative to the manifest workspace")
    candidate = (session_root / relative).resolve()
    try:
        candidate.relative_to(session_root)
    except ValueError as exc:
        raise ValueError(f"lane {lane}: evidence_file escapes manifest workspace") from exc
    return candidate


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest_path = args.manifest.resolve()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
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
        _nonempty_text(manifest, "session_id")
        _artifact(manifest, "verified_artifact_commit")
        _address(manifest, "intended_executor")
        _address(manifest, "expected_signer")
        _nonempty_text(manifest, "intended_private_relay")
        for field in (
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
        session_root = manifest_path.parent
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

            if not evidence_path:
                results[lane] = {"status": "BLOCKED", "validation": "MISSING_EVIDENCE_FILE"}
                continue

            candidate = _resolve_evidence_file(session_root, evidence_path, lane)
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
                try:
                    evidence = _read_json_object(candidate, lane)
                    _bind_lane_identities(lane, evidence, manifest)
                except ValueError as exc:
                    results[lane] = {
                        "status": "FAILED",
                        "validation": "BLOCKED_BY_SESSION_IDENTITY_BINDING",
                        "reason": str(exc),
                    }
                    continue
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
