#!/usr/bin/env python3
"""Fail-closed consistency checks for Phase-19 control-room metadata."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

FROZEN_ARTIFACT = "e117b6550686cf5e0ff787d9bd7d85e83996db07"
ENGINEERING_BASELINE = "213c781368af684ce9af58daeacdf2baade6c453"
REQUIRED_FILES = (
    "PROJECT_STATUS.md",
    "PHASE19_EXTERNAL_GATE_LAUNCH_PACKET.md",
    "PHASE19_CONSOLIDATED_EXTERNAL_EVIDENCE_SESSION.md",
    "PHASE19_90_MINUTE_EXECUTION_PLAN.md",
    "PHASE19_ACCELERATED_GATE_PLAN.md",
    "scripts/phase19_gate_console.py",
    "scripts/phase19_one_shot_external_session.ps1",
    "scripts/validate_consolidated_evidence_session.py",
    "scripts/validate_signer_evidence.py",
    "scripts/validate_production_authority_evidence.py",
    "scripts/validate_private_relay_evidence.py",
    "scripts/validate_shadow_staging_evidence.py",
    "scripts/validate_realized_pnl_evidence.py",
)


def fail(message: str) -> int:
    print(f"BLOCKED: {message}")
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--expected-artifact", default=FROZEN_ARTIFACT)
    parser.add_argument("--expected-engineering-baseline", default=ENGINEERING_BASELINE)
    args = parser.parse_args([] if argv is None else argv)
    root = Path(args.root).resolve()

    for rel in REQUIRED_FILES:
        if not (root / rel).is_file():
            return fail(f"required control-room file missing: {rel}")

    status = (root / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    packet = (root / "PHASE19_EXTERNAL_GATE_LAUNCH_PACKET.md").read_text(encoding="utf-8")
    plan = (root / "PHASE19_90_MINUTE_EXECUTION_PLAN.md").read_text(encoding="utf-8")

    for label, text in (("PROJECT_STATUS.md", status), ("launch packet", packet), ("90-minute plan", plan)):
        if args.expected_artifact not in text:
            return fail(f"{label} is not bound to frozen artifact {args.expected_artifact}")

    required_status_fragments = (
        "Live capital: **LOCKED**",
        "**LIVE SIGNING = BLOCKED**",
        "**PUBLIC BROADCAST = BLOCKED**",
        "realized net profit must be **strictly greater than $0.20 after all applicable costs**",
    )
    for fragment in required_status_fragments:
        if fragment not in status:
            return fail(f"canonical safety/control statement missing from PROJECT_STATUS.md: {fragment}")

    readiness_markers = (
        "Production readiness: **NOT ACHIEVED**",
        "Production readiness decision: **NOT ACHIEVED**",
    )
    if not any(marker in status for marker in readiness_markers):
        return fail("canonical production-readiness statement missing from PROJECT_STATUS.md")

    if "No public fallback" not in packet and "No public fallback" not in plan:
        return fail("private execution public-fallback prohibition is missing")

    if re.search(r"PHANTOMX_(?:PRIVATE_KEY|SEED|MNEMONIC|RELAY_TOKEN|AUTH_TOKEN|API_KEY)=", status):
        return fail("secret-like environment material detected in PROJECT_STATUS.md")

    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return fail("unable to resolve repository HEAD")

    try:
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", args.expected_engineering_baseline, head],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return fail(f"verified engineering baseline {args.expected_engineering_baseline} is not reachable from HEAD {head}")

    tracked = subprocess.check_output(["git", "ls-files"], cwd=root, text=True).splitlines()
    forbidden_prefixes = ("external_evidence/", "phase19_external_session/", "external-session/")
    tracked_evidence = [p for p in tracked if p.startswith(forbidden_prefixes)]
    if tracked_evidence:
        return fail("external evidence workspace is tracked in repository: " + ", ".join(tracked_evidence))

    print("CONTROL_ROOM_GREEN: repository coordination invariants consistent")
    print(f"HEAD={head}")
    print(f"ENGINEERING_BASELINE={args.expected_engineering_baseline}")
    print(f"FROZEN_ARTIFACT={args.expected_artifact}")
    print("PRODUCTION_AUTHORIZATION=NOT_GRANTED")
    print("LIVE_CAPITAL=LOCKED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
