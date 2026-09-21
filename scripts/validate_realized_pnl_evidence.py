#!/usr/bin/env python3
"""Offline validator for non-secret Phase-19 realized-PnL evidence.

This validator never contacts production infrastructure, signs, submits,
broadcasts, or releases capital. It verifies arithmetic consistency,
immutable-artifact identity, provenance, and the strict net-profit threshold.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
import sys
from pathlib import Path

_REQUIRED = {
    "schema_version",
    "artifact_commit",
    "execution_evidence_identity",
    "settlement_evidence_identity",
    "gross_profit_usd",
    "gas_cost_usd",
    "loan_cost_usd",
    "dex_cost_usd",
    "relay_cost_usd",
    "other_cost_usd",
    "realized_net_profit_usd",
    "operator_identity",
    "witness_identity",
    "observed_at_utc",
    "evidence_hash",
}

_CANONICAL_FIELDS = tuple(sorted(_REQUIRED - {"evidence_hash"}))
_GIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
_DECIMAL = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate realized Phase-19 PnL evidence")
    parser.add_argument("evidence_file", type=Path)
    return parser


def _text(record: dict[str, object], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _money(record: dict[str, object], field: str) -> Decimal:
    value = _text(record, field)
    if not _DECIMAL.fullmatch(value):
        raise ValueError(f"{field} must be a non-negative decimal string")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is not a valid decimal") from exc
    if amount < 0:
        raise ValueError(f"{field} must be non-negative")
    return amount


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

        artifact = _text(record, "artifact_commit").lower()
        if not _GIT_SHA.fullmatch(artifact):
            raise ValueError("artifact_commit must be a 40-character git SHA")
        for field in (
            "execution_evidence_identity",
            "settlement_evidence_identity",
            "operator_identity",
            "witness_identity",
            "observed_at_utc",
        ):
            _text(record, field)

        gross = _money(record, "gross_profit_usd")
        costs = {
            field: _money(record, field)
            for field in (
                "gas_cost_usd",
                "loan_cost_usd",
                "dex_cost_usd",
                "relay_cost_usd",
                "other_cost_usd",
            )
        }
        realized = _money(record, "realized_net_profit_usd")
        expected = gross - sum(costs.values(), Decimal("0"))
        if realized != expected:
            raise ValueError(
                f"realized_net_profit_usd mismatch: expected {expected}, observed {realized}"
            )
        if realized <= Decimal("0.20"):
            raise ValueError("realized net profit must be strictly greater than $0.20")

        supplied_hash = _text(record, "evidence_hash").lower()
        if not re.fullmatch(r"0x[0-9a-f]{64}", supplied_hash):
            raise ValueError("evidence_hash must be a 32-byte 0x SHA-256 digest")
        expected_hash = "0x" + hashlib.sha256(
            _canonical_payload(record).encode("utf-8")
        ).hexdigest()
        if supplied_hash != expected_hash:
            raise ValueError("evidence_hash does not match canonical evidence payload")

    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({
        "schema_version": 1,
        "status": "ACCEPTED_FOR_INDEPENDENT_REVIEW",
        "artifact_commit": artifact,
        "gross_profit_usd": format(gross, "f"),
        "total_cost_usd": format(sum(costs.values(), Decimal("0")), "f"),
        "realized_net_profit_usd": format(realized, "f"),
        "economic_gate": "PASS_NET_GT_0_20",
        "evidence_hash": expected_hash,
        "operator_identity": record["operator_identity"],
        "witness_identity": record["witness_identity"],
        "observed_at_utc": record["observed_at_utc"],
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
