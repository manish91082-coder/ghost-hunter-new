#!/usr/bin/env python3
"""Validate a non-secret Phase-19 controlled Polygon authority evidence package.

This utility performs offline consistency verification only. It never contacts
an RPC endpoint, handles credentials, signs transactions, submits transactions,
or authorizes live execution.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from phantomx.executor_authority import ExecutorAuthorityEvidence, ExecutorAuthorityError

_REQUIRED = {
    "schema_version",
    "chain_id",
    "executor",
    "expected_signer",
    "common_block",
    "observed_owner",
    "runtime_code_hash",
    "quorum",
    "attesting_provider_names",
    "provider_observations",
    "evidence_hash",
    "observed_at_utc",
    "operator_identity",
    "witness_identity",
}

_OBS_REQUIRED = {
    "provider_name",
    "chain_id",
    "observed_block",
    "owner",
    "runtime_code_hash",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate controlled Polygon production authority evidence")
    parser.add_argument("evidence_file", type=Path)
    return parser


def _address(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise ValueError(f"{field} must be a 20-byte 0x address")
    try:
        bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ValueError(f"{field} is not hexadecimal") from exc
    if value.lower() == "0x" + "00" * 20:
        raise ValueError(f"{field} must be non-zero")
    return value.lower()


def _hash(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        raise ValueError(f"{field} must be a 32-byte 0x hash")
    try:
        bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ValueError(f"{field} is not hexadecimal") from exc
    return value.lower()


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
        if record["chain_id"] != 137:
            raise ValueError("chain_id must be Polygon 137")
        executor = _address(record["executor"], "executor")
        expected_signer = _address(record["expected_signer"], "expected_signer")
        observed_owner = _address(record["observed_owner"], "observed_owner")
        runtime_code_hash = _hash(record["runtime_code_hash"], "runtime_code_hash")
        if not isinstance(record["common_block"], int) or isinstance(record["common_block"], bool) or record["common_block"] < 0:
            raise ValueError("common_block must be a non-negative integer")
        if not isinstance(record["quorum"], int) or isinstance(record["quorum"], bool) or record["quorum"] <= 0:
            raise ValueError("quorum must be a positive integer")
        if not isinstance(record["attesting_provider_names"], list) or not record["attesting_provider_names"]:
            raise ValueError("attesting_provider_names must be a non-empty list")
        if any(not isinstance(name, str) or not name.strip() for name in record["attesting_provider_names"]):
            raise ValueError("attesting provider names must be non-empty strings")
        if len(set(record["attesting_provider_names"])) != len(record["attesting_provider_names"]):
            raise ValueError("attesting provider names must be unique")
        if record["quorum"] > len(record["attesting_provider_names"]):
            raise ValueError("quorum exceeds attesting provider count")

        observations = record["provider_observations"]
        if not isinstance(observations, list) or not observations:
            raise ValueError("provider_observations must be a non-empty list")
        if len(observations) != len(record["attesting_provider_names"]):
            raise ValueError("provider observation count must match attesting provider count")

        canonical_names = set(record["attesting_provider_names"])
        observed_names: set[str] = set()
        for item in observations:
            if not isinstance(item, dict):
                raise ValueError("each provider observation must be an object")
            if set(item) != _OBS_REQUIRED:
                raise ValueError("provider observation fields must match the required schema exactly")
            name = item["provider_name"]
            if not isinstance(name, str) or not name.strip():
                raise ValueError("provider_name must be non-empty text")
            if name in observed_names:
                raise ValueError("provider observations must be unique")
            observed_names.add(name)
            if item["chain_id"] != 137:
                raise ValueError(f"{name}: chain_id must be Polygon 137")
            if item["observed_block"] != record["common_block"]:
                raise ValueError(f"{name}: observation block differs from common_block")
            if _address(item["owner"], f"{name}: owner") != observed_owner:
                raise ValueError(f"{name}: owner differs from observed_owner")
            if _hash(item["runtime_code_hash"], f"{name}: runtime_code_hash") != runtime_code_hash:
                raise ValueError(f"{name}: runtime_code_hash differs from evidence")

        if observed_names != canonical_names:
            raise ValueError("provider observation identities do not match attesting_provider_names")
        if len(observed_names) < record["quorum"]:
            raise ValueError("provider quorum is not reached")
        if observed_owner != expected_signer:
            raise ValueError("observed executor owner does not match expected signer")

        evidence = ExecutorAuthorityEvidence(
            schema_version=1,
            chain_id=137,
            executor=executor,
            owner=observed_owner,
            observed_block=record["common_block"],
            runtime_code_hash=runtime_code_hash,
            attesting_provider_names=tuple(sorted(observed_names)),
            evidence_hash=record["evidence_hash"],
        )
        for field in ("observed_at_utc", "operator_identity", "witness_identity"):
            if not isinstance(record[field], str) or not record[field].strip():
                raise ValueError(f"{field} must be non-empty text")
    except (OSError, json.JSONDecodeError, ValueError, ExecutorAuthorityError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({
        "schema_version": 1,
        "status": "ACCEPTED_FOR_INDEPENDENT_REVIEW",
        "chain_id": 137,
        "executor": evidence.executor,
        "expected_signer": expected_signer,
        "observed_owner": evidence.owner,
        "common_block": evidence.observed_block,
        "runtime_code_hash": evidence.runtime_code_hash,
        "quorum": record["quorum"],
        "attesting_provider_names": list(evidence.attesting_provider_names),
        "evidence_hash": evidence.evidence_hash,
        "observed_at_utc": record["observed_at_utc"],
        "operator_identity": record["operator_identity"],
        "witness_identity": record["witness_identity"],
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
