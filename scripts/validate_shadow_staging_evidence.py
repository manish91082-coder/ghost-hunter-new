#!/usr/bin/env python3
"""Offline validator for identical-artifact Phase-19 shadow/staging evidence.

This validator never contacts production infrastructure, signs, submits,
broadcasts, or releases capital. It proves only that a staging record is
internally consistent with the frozen artifact and carries the required
non-secret provenance and immutable-input identities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = {
    "schema_version",
    "artifact_commit",
    "executor_identity",
    "expected_signer",
    "route_proof_identity",
    "economic_proof_identity",
    "authority_evidence_identity",
    "staging_environment_identity",
    "submission_policy_identity",
    "operator_identity",
    "witness_identity",
    "observed_at_utc",
    "execution_result",
    "evidence_hash",
}
HEX40 = re.compile(r"^0x[0-9a-fA-F]{40}$")
SHA256_HEX = re.compile(r"^(?:0x)?[0-9a-fA-F]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def _text(data: dict[str, object], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def canonical_payload(data: dict[str, object]) -> bytes:
    payload = {key: data[key] for key in sorted(REQUIRED_FIELDS - {"evidence_hash"})}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate identical-artifact shadow/staging evidence")
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.evidence.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("evidence must be a JSON object")
        missing = sorted(REQUIRED_FIELDS - set(data))
        if missing:
            raise ValueError("missing required fields: " + ", ".join(missing))
        unknown = sorted(set(data) - REQUIRED_FIELDS)
        if unknown:
            raise ValueError("unknown fields: " + ", ".join(unknown))
        if data["schema_version"] != 1:
            raise ValueError("unsupported schema_version")

        artifact = _text(data, "artifact_commit").lower()
        if not GIT_SHA.fullmatch(artifact):
            raise ValueError("artifact_commit must be a 40-character git SHA")
        for field in ("executor_identity", "expected_signer"):
            value = _text(data, field)
            if not HEX40.fullmatch(value):
                raise ValueError(f"{field} must be a valid nonzero EVM address")
            if value.lower() == "0x" + "0" * 40:
                raise ValueError(f"{field} must not be zero")
        for field in (
            "route_proof_identity",
            "economic_proof_identity",
            "authority_evidence_identity",
            "staging_environment_identity",
            "submission_policy_identity",
            "operator_identity",
            "witness_identity",
            "observed_at_utc",
        ):
            _text(data, field)

        result = data["execution_result"]
        if not isinstance(result, dict):
            raise ValueError("execution_result must be an object")
        required_result = {"mode", "live_capital", "broadcast", "outcome"}
        if set(result) != required_result:
            raise ValueError("execution_result must contain exactly mode, live_capital, broadcast, outcome")
        if result["mode"] != "SHADOW_STAGING":
            raise ValueError("execution_result.mode must be SHADOW_STAGING")
        if result["live_capital"] is not False:
            raise ValueError("shadow/staging evidence must state live_capital=false")
        if result["broadcast"] is not False:
            raise ValueError("shadow/staging evidence must state broadcast=false")
        if not isinstance(result["outcome"], str) or result["outcome"] not in {"PASS", "FAIL", "BLOCKED"}:
            raise ValueError("execution_result.outcome must be PASS, FAIL, or BLOCKED")

        evidence_hash = _text(data, "evidence_hash")
        if not SHA256_HEX.fullmatch(evidence_hash):
            raise ValueError("evidence_hash must be a 32-byte SHA-256 hex digest")
        expected = "0x" + hashlib.sha256(canonical_payload(data)).hexdigest()
        if evidence_hash.lower() != expected.lower():
            raise ValueError("evidence_hash does not match canonical evidence")

        print(json.dumps({
            "status": "ACCEPTED_FOR_INDEPENDENT_REVIEW",
            "artifact_commit": artifact,
            "execution_mode": result["mode"],
            "execution_outcome": result["outcome"],
            "evidence_hash": expected,
        }, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
