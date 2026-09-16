#!/usr/bin/env python3
"""Validate a non-secret Phase-19 controlled private-relay evidence package.

Offline only. This tool never contacts a relay, handles credentials, signs,
submits, broadcasts, or authorizes live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_REQUIRED = {
    "schema_version",
    "relay_name",
    "endpoint_scheme",
    "private_assertion",
    "authentication_configured",
    "observed_response_class",
    "observed_at_utc",
    "operator_identity",
    "witness_identity",
    "evidence_hash",
}

_CANONICAL_FIELDS = (
    "schema_version",
    "relay_name",
    "endpoint_scheme",
    "private_assertion",
    "authentication_configured",
    "observed_response_class",
    "observed_at_utc",
    "operator_identity",
    "witness_identity",
)

_SECRET_MARKERS = (
    "private_key",
    "seed_phrase",
    "keystore",
    "authorization",
    "bearer ",
    "access_token",
    "api_key",
    "raw_transaction",
    "signed_transaction",
    "transaction_hash",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate controlled private relay evidence")
    parser.add_argument("evidence_file", type=Path)
    return parser


def _canonical_payload(record: dict[str, object]) -> str:
    return json.dumps(
        {field: record[field] for field in _CANONICAL_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        record = json.loads(args.evidence_file.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("evidence package must be a JSON object")
        missing = sorted(_REQUIRED - set(record))
        if missing:
            raise ValueError("missing required evidence fields: " + ", ".join(missing))
        unknown = sorted(set(record) - _REQUIRED)
        if unknown:
            raise ValueError("evidence package contains unknown fields: " + ", ".join(unknown))
        if record["schema_version"] != 1:
            raise ValueError("unsupported evidence schema version")
        if not isinstance(record["relay_name"], str) or not record["relay_name"].strip():
            raise ValueError("relay_name must be non-empty text")
        if record["endpoint_scheme"] != "https":
            raise ValueError("endpoint_scheme must be https")
        if record["private_assertion"] is not True:
            raise ValueError("private_assertion must be true")
        if record["authentication_configured"] is not True:
            raise ValueError("authentication_configured must be true")
        if not isinstance(record["observed_response_class"], str) or not record["observed_response_class"].strip():
            raise ValueError("observed_response_class must be non-empty text")
        for field in ("observed_at_utc", "operator_identity", "witness_identity"):
            if not isinstance(record[field], str) or not record[field].strip():
                raise ValueError(f"{field} must be non-empty text")

        serialized = json.dumps(record, sort_keys=True, separators=(",", ":")).lower()
        for marker in _SECRET_MARKERS:
            if marker in serialized:
                raise ValueError("evidence package contains prohibited secret or transaction material")

        expected_hash = "0x" + hashlib.sha256(_canonical_payload(record).encode("utf-8")).hexdigest()
        supplied_hash = record["evidence_hash"]
        if not isinstance(supplied_hash, str) or supplied_hash.lower() != expected_hash:
            raise ValueError("evidence_hash does not match canonical evidence payload")

    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(
        {
            "schema_version": 1,
            "status": "ACCEPTED_FOR_INDEPENDENT_REVIEW",
            "relay_name": record["relay_name"],
            "endpoint_scheme": record["endpoint_scheme"],
            "private_assertion": record["private_assertion"],
            "authentication_configured": record["authentication_configured"],
            "observed_response_class": record["observed_response_class"],
            "observed_at_utc": record["observed_at_utc"],
            "operator_identity": record["operator_identity"],
            "witness_identity": record["witness_identity"],
            "evidence_hash": record["evidence_hash"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
