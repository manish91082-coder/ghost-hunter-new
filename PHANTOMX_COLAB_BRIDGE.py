#!/usr/bin/env python3
"""PHANTOMX Colab Bridge v1.0

Deterministic, AI-free GitHub <-> Colab control/verification worker.
Designed for PHANTOMX / Flash Loan Ghost Hunter.

Design goals
============
* GitHub LIVE state is the source of truth.
* No Gemini/OpenAI/LLM dependency.
* No clone/push credentials required: GitHub REST API only.
* Atomic multi-file writes use Git blobs -> tree -> commit -> fast-forward ref.
* S5 is dispatched only after Phase-19 is GREEN on the exact current HEAD.
* S5 workflow is dispatched directly; no kick-file commit is required.
* Artifact ZIP digest + artifact provenance are verified before trusting evidence.
* A dedicated bridge-state branch stores machine-readable receipts without
  touching the engineering branch or triggering engineering workflows.
* The bridge never signs, broadcasts, or touches live capital.
* The bridge never invents architectural code fixes. When judgment is needed,
  it produces a deterministic LEAD_DECISION_REQUIRED state for ChatGPT/user.

Colab setup
===========
1. In Colab Secrets create GITHUB_TOKEN containing a fine-grained token scoped
   only to manish91082-coder/ghost-hunter-new.
2. Required repo permissions:
   - Contents: Read and Write
   - Actions: Read and Write
3. Save this file in the Colab runtime and run:
      python PHANTOMX_COLAB_BRIDGE.py report
      python PHANTOMX_COLAB_BRIDGE.py auto --s5

The `auto --s5` command is restart-safe. State is persisted on the dedicated
bridge-state branch, not in VM memory.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

API_VERSION = "2026-03-10"
REPO = "manish91082-coder/ghost-hunter-new"
ENGINEERING_BRANCH = "phase-19-e2e-harness"
STATE_BRANCH = "phantomx-bridge-state"
PHASE19_NAME = "Phase-19 Deterministic Tests"
S5_NAME = "PHANTOMX S5 Curve Uniswap V3 Live Hunt"
S5_WORKFLOW_FILE = ".github/workflows/s5-curve-uv3-live-read.yml"
BRIDGE_STATE_FILE = "bridge/LATEST_STATE.json"
BRIDGE_STATE_MD = "bridge/LATEST_STATE.md"

LIVE_SIGNING = False
PUBLIC_BROADCAST = False
LIVE_CAPITAL = False


class BridgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    repo: str = REPO
    engineering_branch: str = ENGINEERING_BRANCH
    state_branch: str = STATE_BRANCH
    poll_seconds: int = 15
    poll_timeout_seconds: int = 1800
    auto_s5: bool = False
    sync_state: bool = True


class GitHubClient:
    """Small standard-library-only GitHub REST client."""

    def __init__(self, token: str, repo: str):
        if not token:
            raise BridgeError("GITHUB_TOKEN is missing")
        if "/" not in repo:
            raise BridgeError(f"Invalid repository: {repo}")
        self.token = token
        self.repo = repo

    def _request(
        self,
        method: str,
        path: str,
        body: Any | None = None,
    ) -> tuple[int, bytes, dict[str, str]]:
        url = f"https://api.github.com/repos/{self.repo}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "PHANTOMX-Colab-Bridge/1.0",
        }

        data = None
        if body is not None:
            data = json.dumps(body, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return (
                    response.status,
                    response.read(),
                    dict(response.headers.items()),
                )
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", "replace")
            raise BridgeError(
                f"GitHub API {exc.code} {method} {path}: {payload[:2500]}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise BridgeError(
                f"GitHub transport failure {method} {path}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    def json(
        self,
        method: str,
        path: str,
        body: Any | None = None,
    ) -> Any:
        _, data, _ = self._request(method, path, body)

        if not data:
            return None

        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise BridgeError(
                f"Non-JSON GitHub response for {method} {path}"
            ) from exc

    def ref(self, branch: str) -> dict[str, Any]:
        encoded = urllib.parse.quote(branch, safe="")
        return self.json("GET", f"/git/ref/heads/{encoded}")

    def ref_optional(self, branch: str) -> dict[str, Any] | None:
        try:
            return self.ref(branch)
        except BridgeError as exc:
            if "GitHub API 404" in str(exc):
                return None
            raise

    def create_ref(self, branch: str, sha: str) -> None:
        self.json(
            "POST",
            "/git/refs",
            {
                "ref": f"refs/heads/{branch}",
                "sha": sha,
            },
        )

    def commit(self, sha: str) -> dict[str, Any]:
        return self.json("GET", f"/commits/{sha}")

    def file_text(self, path: str, ref: str) -> tuple[str, str]:
        query_ref = urllib.parse.quote(ref, safe="")
        encoded_path = urllib.parse.quote(path, safe="/")

        obj = self.json(
            "GET",
            f"/contents/{encoded_path}?ref={query_ref}",
        )

        if (
            not isinstance(obj, dict)
            or "content" not in obj
            or "sha" not in obj
        ):
            raise BridgeError(f"Expected file content: {path}")

        raw = base64.b64decode(
            obj["content"].replace("\n", "")
        )

        return str(obj["sha"]), raw.decode("utf-8")

    def runs(
        self,
        branch: str,
        per_page: int = 100,
    ) -> list[dict[str, Any]]:
        encoded_branch = urllib.parse.quote(branch, safe="")

        obj = self.json(
            "GET",
            f"/actions/runs?branch={encoded_branch}&per_page={per_page}",
        )

        return list(obj.get("workflow_runs", []))

    def run_jobs(self, run_id: int) -> list[dict[str, Any]]:
        obj = self.json(
            "GET",
            f"/actions/runs/{int(run_id)}/jobs?per_page=100",
        )
        return list(obj.get("jobs", []))

    def run_artifacts(self, run_id: int) -> list[dict[str, Any]]:
        obj = self.json(
            "GET",
            f"/actions/runs/{int(run_id)}/artifacts?per_page=100",
        )
        return list(obj.get("artifacts", []))

    def dispatch_workflow(
        self,
        workflow_file: str,
        ref: str,
    ) -> None:
        encoded_workflow = urllib.parse.quote(
            workflow_file,
            safe="/",
        )

        path = (
            f"/actions/workflows/"
            f"{encoded_workflow}/dispatches"
        )

        self.json(
            "POST",
            path,
            {"ref": ref},
        )

    def artifact_zip(self, artifact_id: int) -> bytes:
        url = (
            f"https://api.github.com/repos/"
            f"{self.repo}/actions/artifacts/"
            f"{int(artifact_id)}/zip"
        )

        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "PHANTOMX-Colab-Bridge/1.0",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return response.read()
        except Exception as exc:
            raise BridgeError(
                f"Artifact download failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    # Git database operations. These make one atomic branch commit.

    def create_blob(self, content: bytes) -> str:
        obj = self.json(
            "POST",
            "/git/blobs",
            {
                "content": base64.b64encode(content).decode("ascii"),
                "encoding": "base64",
            },
        )
        return obj["sha"]

    def create_tree(
        self,
        base_tree: str,
        entries: list[dict[str, Any]],
    ) -> str:
        obj = self.json(
            "POST",
            "/git/trees",
            {
                "base_tree": base_tree,
                "tree": entries,
            },
        )
        return obj["sha"]

    def create_commit(
        self,
        message: str,
        tree_sha: str,
        parent_sha: str,
    ) -> str:
        obj = self.json(
            "POST",
            "/git/commits",
            {
                "message": message,
                "tree": tree_sha,
                "parents": [parent_sha],
            },
        )
        return obj["sha"]

    def update_ref(
        self,
        branch: str,
        sha: str,
        force: bool = False,
    ) -> None:
        encoded_branch = urllib.parse.quote(
            branch,
            safe="",
        )

        self.json(
            "PATCH",
            f"/git/refs/heads/{encoded_branch}",
            {
                "sha": sha,
                "force": force,
            },
        )


def now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat().replace(
        "+00:00",
        "Z",
    )


def env_flag(
    name: str,
    default: bool,
) -> bool:
    raw = os.getenv(name)

    if raw is None:
        return default

    return raw.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def config_from_env() -> Config:
    return Config(
        repo=os.getenv(
            "PHANTOMX_REPO",
            REPO,
        ),
        engineering_branch=os.getenv(
            "PHANTOMX_BRANCH",
            ENGINEERING_BRANCH,
        ),
        state_branch=os.getenv(
            "PHANTOMX_STATE_BRANCH",
            STATE_BRANCH,
        ),
        poll_seconds=max(
            3,
            int(
                os.getenv(
                    "PHANTOMX_POLL_SECONDS",
                    "15",
                )
            ),
        ),
        poll_timeout_seconds=max(
            60,
            int(
                os.getenv(
                    "PHANTOMX_POLL_TIMEOUT",
                    "1800",
                )
            ),
        ),
        auto_s5=env_flag(
            "PHANTOMX_AUTO_S5",
            False,
        ),
        sync_state=env_flag(
            "PHANTOMX_SYNC_STATE",
            True,
        ),
    )


def safety_payload() -> dict[str, bool]:
    return {
        "live_signing": LIVE_SIGNING,
        "public_broadcast": PUBLIC_BROADCAST,
        "live_capital": LIVE_CAPITAL,
    }


def require_safety() -> None:
    if safety_payload() != {
        "live_signing": False,
        "public_broadcast": False,
        "live_capital": False,
    }:
        raise BridgeError(
            "Safety invariant violated"
        )


def latest_exact_run(
    runs: Iterable[dict[str, Any]],
    name: str,
    head_sha: str,
) -> dict[str, Any] | None:
    matches = [
        r
        for r in runs
        if r.get("name") == name
        and r.get("head_sha") == head_sha
    ]

    return max(
        matches,
        key=lambda r: r.get("id", 0),
        default=None,
    )


def active_run(
    run: dict[str, Any] | None,
) -> bool:
    return bool(
        run
        and run.get("status")
        in {
            "queued",
            "in_progress",
            "waiting",
            "requested",
            "pending",
        }
    )


def job_summary(
    client: GitHubClient,
    run: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not run:
        return []

    return [
        {
            "id": j.get("id"),
            "name": j.get("name"),
            "status": j.get("status"),
            "conclusion": j.get("conclusion"),
            "steps": [
                {
                    "name": s.get("name"),
                    "status": s.get("status"),
                    "conclusion": s.get("conclusion"),
                }
                for s in (j.get("steps") or [])
            ],
        }
        for j in client.run_jobs(
            int(run["id"])
        )
    ]


def artifact_summary(
    client: GitHubClient,
    run: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not run:
        return []

    return client.run_artifacts(
        int(run["id"])
    )


def current_state(
    client: GitHubClient,
    cfg: Config,
) -> dict[str, Any]:
    require_safety()

    ref = client.ref(
        cfg.engineering_branch
    )

    head_sha = ref["object"]["sha"]

    commit = client.commit(
        head_sha
    )

    runs = client.runs(
        cfg.engineering_branch
    )

    phase = latest_exact_run(
        runs,
        PHASE19_NAME,
        head_sha,
    )

    s5 = latest_exact_run(
        runs,
        S5_NAME,
        head_sha,
    )

    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "repo": cfg.repo,
        "engineering_branch": cfg.engineering_branch,
        "head_sha": head_sha,
        "commit_message": (
            commit.get("commit", {})
            .get("message", "")
        ),
        "phase19": (
            None
            if phase is None
            else {
                "id": phase["id"],
                "status": phase.get(
                    "status"
                ),
                "conclusion": phase.get(
                    "conclusion"
                ),
                "created_at": phase.get(
                    "created_at"
                ),
                "updated_at": phase.get(
                    "updated_at"
                ),
                "jobs": job_summary(
                    client,
                    phase,
                ),
            }
        ),
        "s5": (
            None
            if s5 is None
            else {
                "id": s5["id"],
                "status": s5.get(
                    "status"
                ),
                "conclusion": s5.get(
                    "conclusion"
                ),
                "created_at": s5.get(
                    "created_at"
                ),
                "updated_at": s5.get(
                    "updated_at"
                ),
                "artifacts": artifact_summary(
                    client,
                    s5,
                ),
                "jobs": job_summary(
                    client,
                    s5,
                ),
            }
        ),
        "safety": safety_payload(),
    }


def atomic_state_write(
    client: GitHubClient,
    cfg: Config,
    state: dict[str, Any],
    next_action: str,
    reason: str = "",
) -> str:
    """Persist bridge state on a dedicated branch
    without touching engineering branch.
    """
    require_safety()

    ref = client.ref_optional(
        cfg.state_branch
    )

    if ref is None:
        base_head = client.ref(
            cfg.engineering_branch
        )["object"]["sha"]

        client.create_ref(
            cfg.state_branch,
            base_head,
        )

        ref = client.ref(
            cfg.state_branch
        )

    parent_sha = ref["object"]["sha"]

    parent_commit = client.commit(
        parent_sha
    )

    base_tree = (
        parent_commit
        .get("commit", {})
        .get("tree", {})
        .get("sha")
    )

    if not base_tree:
        raise BridgeError(
            "Unable to resolve bridge-state base tree"
        )

    payload = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "repo": cfg.repo,
        "engineering_branch": cfg.engineering_branch,
        "engineering_head": state["head_sha"],
        "next_action": next_action,
        "reason": reason,
        "safety": safety_payload(),
        "state": state,
    }

    text = (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    md = (
        "# PHANTOMX Bridge State\n\n"
    )

    md += (
        f"**Generated:** "
        f"{payload['generated_at']}\n\n"
    )

    md += (
        f"**Engineering HEAD:** "
        f"`{state['head_sha']}`\n\n"
    )

    md += (
        f"**Next action:** "
        f"`{next_action}`\n\n"
    )

    if reason:
        md += (
            f"**Reason:** "
            f"{reason}\n\n"
        )

    p19 = state.get(
        "phase19"
    )

    s5 = state.get(
        "s5"
    )

    md += (
        f"Phase-19: "
        f"`{None if not p19 else p19.get('status')} / "
        f"{None if not p19 else p19.get('conclusion')}`\n\n"
    )

    md += (
        f"S5: "
        f"`{None if not s5 else s5.get('status')} / "
        f"{None if not s5 else s5.get('conclusion')}`\n\n"
    )

    b1 = client.create_blob(
        text.encode()
    )

    b2 = client.create_blob(
        md.encode()
    )

    tree = client.create_tree(
        base_tree,
        [
            {
                "path": BRIDGE_STATE_FILE,
                "mode": "100644",
                "type": "blob",
                "sha": b1,
            },
            {
                "path": BRIDGE_STATE_MD,
                "mode": "100644",
                "type": "blob",
                "sha": b2,
            },
        ],
    )

    message = (
        "bridge: "
        + next_action.lower()
        .replace("_", " ")
    )

    new_commit = client.create_commit(
        message,
        tree,
        parent_sha,
    )

    client.update_ref(
        cfg.state_branch,
        new_commit,
        force=False,
    )

    return new_commit


def phase19_green(
    state: dict[str, Any],
) -> bool:
    p = state.get(
        "phase19"
    )

    return bool(
        p
        and p.get("status")
        == "completed"
        and p.get("conclusion")
        == "success"
    )


def s5_active(
    state: dict[str, Any],
) -> bool:
    return active_run(
        state.get("s5")
    )


def choose_latest_artifact(
    s5: dict[str, Any],
) -> dict[str, Any] | None:
    artifacts = [
        a
        for a in s5.get(
            "artifacts",
            [],
        )
        if not a.get("expired")
    ]

    return max(
        artifacts,
        key=lambda x: x.get(
            "created_at",
            "",
        ),
        default=None,
    )


def zip_sha256(
    data: bytes,
) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def parse_s5_artifact(
    data: bytes,
) -> dict[str, Any]:
    with zipfile.ZipFile(
        io.BytesIO(data)
    ) as archive:
        names = archive.namelist()

        json_files = [
            n
            for n in names
            if n.endswith(".json")
        ]

        parsed: dict[str, Any] = {}

        for name in json_files:
            try:
                parsed[name] = json.loads(
                    archive.read(name)
                    .decode("utf-8")
                )
            except Exception as exc:
                parsed[name] = {
                    "parse_error":
                        f"{type(exc).__name__}: {exc}"
                }

        return {
            "files": names,
            "json": parsed,
        }


def extract_s5_metrics(
    forensic: dict[str, Any],
    expected_head: str,
    artifact_sha: str,
) -> dict[str, Any]:
    candidates = [
        v
        for v in forensic.get(
            "json",
            {},
        ).values()
        if isinstance(v, dict)
    ]

    artifact = next(
        (
            v
            for v in candidates
            if v.get(
                "mission",
                "",
            ).startswith(
                "PHANTOMX S5"
            )
        ),
        candidates[0]
        if candidates
        else {},
    )

    if artifact.get(
        "successful_endpoints"
    ):
        coverage = (
            artifact
            .get(
                "successful_endpoints",
                [{}],
            )[0]
            .get(
                "coverage",
                {},
            )
        )
    else:
        coverage = artifact.get(
            "coverage",
            {},
        )

    provenance = artifact.get(
        "provenance",
        {},
    )

    return {
        "artifact_zip_sha256": artifact_sha,
        "artifact_git_commit_sha":
            provenance.get(
                "git_commit_sha"
            ),
        "provenance_matches_head":
            provenance.get(
                "git_commit_sha"
            ) == expected_head,
        "coverage": coverage,
        "pair_universe":
            artifact.get(
                "pair_universe"
            ),
        "economic_certification":
            artifact.get(
                "economic_certification"
            ),
        "profit_claim":
            artifact.get(
                "profit_claim"
            ),
        "observation_count": sum(
            r.get(
                "observation_count",
                0,
            )
            for r in artifact.get(
                "successful_endpoints",
                [],
            )
            if isinstance(
                r,
                dict,
            )
        ),
        "gross_positive_count": sum(
            r.get(
                "gross_positive_count",
                0,
            )
            for r in artifact.get(
                "successful_endpoints",
                [],
            )
            if isinstance(
                r,
                dict,
            )
        ),
        "gross_max_usdc": [
            r.get(
                "gross_max_usdc"
            )
            for r in artifact.get(
                "successful_endpoints",
                [],
            )
            if isinstance(
                r,
                dict,
            )
        ],
    }


def terminal_forensic(
    client: GitHubClient,
    state: dict[str, Any],
) -> dict[str, Any] | None:
    s5 = state.get(
        "s5"
    )

    if not s5 or active_run(s5):
        return None

    artifact = choose_latest_artifact(
        s5
    )

    if not artifact:
        return {
            "artifact_present": False,
            "verified": False,
        }

    data = client.artifact_zip(
        int(
            artifact["id"]
        )    )

    digest = zip_sha256(
        data
    )

    api_digest = str(
        artifact.get(
            "digest",
            "",
        )
    )

    expected_digest = (
        api_digest.removeprefix(
            "sha256:"
        )
    )

    forensic = parse_s5_artifact(
        data
    )

    metrics = extract_s5_metrics(
        forensic,
        state["head_sha"],
        digest,
    )

    verified = bool(
        expected_digest
        == digest
        and metrics.get(
            "provenance_matches_head"
        )
        and metrics.get(
            "economic_certification"
        )
        in {
            "NOT_PERFORMED",
            "COMPLETED",
        }
    )

    metrics["artifact_id"] = artifact["id"]

    metrics["github_digest_matches_download"] = (
        expected_digest
        == digest
    )

    metrics["artifact_verification_pass"] = verified
    metrics["forensic"] = forensic

    return metrics


def wait_for_new_s5_run(
    client: GitHubClient,
    cfg: Config,
    head_sha: str,
    start_unix: float,
) -> dict[str, Any]:
    deadline = (
        time.time()
        + cfg.poll_timeout_seconds
    )

    while time.time() < deadline:
        runs = client.runs(
            cfg.engineering_branch
        )

        candidates = [
            r
            for r in runs
            if r.get("name")
            == S5_NAME
            and r.get("head_sha")
            == head_sha
            and _run_time_epoch(
                r.get("created_at")
            )
            >= start_unix - 5
        ]

        if candidates:
            return max(
                candidates,
                key=lambda x: x.get(
                    "id",
                    0,
                ),
            )

        time.sleep(
            cfg.poll_seconds
        )

    raise BridgeError(
        "Timed out waiting for dispatched "
        "S5 workflow run to appear"
    )


def _run_time_epoch(
    value: str | None,
) -> float:
    if not value:
        return 0.0

    try:
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        ).timestamp()
    except ValueError:
        return 0.0


def wait_for_terminal_run(
    client: GitHubClient,
    cfg: Config,
    run_id: int,
) -> dict[str, Any]:
    deadline = (
        time.time()
        + cfg.poll_timeout_seconds
    )

    while time.time() < deadline:
        runs = client.runs(
            cfg.engineering_branch
        )

        current = next(
            (
                r
                for r in runs
                if int(
                    r.get(
                        "id",
                        -1,
                    )
                )
                == int(run_id)
            ),
            None,
        )

        if current is None:
            time.sleep(
                cfg.poll_seconds
            )
            continue

        if current.get(
            "status"
        ) == "completed":
            return current

        time.sleep(
            cfg.poll_seconds
        )

    raise BridgeError(
        f"Timed out waiting for workflow run {run_id}"
    )


def cmd_report(
    client: GitHubClient,
    cfg: Config,
) -> int:
    state = current_state(
        client,
        cfg,
    )

    print(
        json.dumps(
            state,
            indent=2,
            sort_keys=True,
        )
    )

    if cfg.sync_state:
        action = "STATE_SYNC"

        atomic_state_write(
            client,
            cfg,
            state,
            action,
        )

    return 0


def cmd_terminal(
    client: GitHubClient,
    cfg: Config,
) -> int:
    state = current_state(
        client,
        cfg,
    )

    forensic = terminal_forensic(
        client,
        state,
    )

    report = {
        "state": state,
        "forensic": forensic,
    }

    print(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
    )

    if cfg.sync_state:
        action = "LEAD_DECISION_REQUIRED"

        if (
            state.get(
                "s5",
                {},
            ).get(
                "conclusion"
            )
            != "success"
        ):
            reason = (
                "S5 terminal; inspect "
                "forensic evidence before "
                "any engineering repair."
            )
        else:
            reason = (
                "S5 terminal success; verify "
                "certification contract and "
                "allow S0 progression."
            )

        atomic_state_write(
            client,
            cfg,
            state,
            action,
            reason,
        )

    return (
        0
        if forensic
        and forensic.get(
            "artifact_verification_pass"
        )
        else 4
    )


def _finish_s5(
    client: GitHubClient,
    cfg: Config,
    head_sha: str,
    run_id: int,
) -> int:
    run = wait_for_terminal_run(
        client,
        cfg,
        int(run_id),
    )

    print(
        json.dumps(
            {
                "s5_terminal": {
                    "id": run["id"],
                    "status":
                        run["status"],
                    "conclusion":
                        run["conclusion"],
                    "head_sha":
                        run["head_sha"],
                }
            },
            indent=2,
        )
    )

    final_state = current_state(
        client,
        cfg,
    )

    forensic = terminal_forensic(
        client,
        final_state,
    )

    if cfg.sync_state:
        if (
            forensic
            and forensic.get(
                "artifact_verification_pass"
            )
            and run.get(
                "conclusion"
            )
            == "success"
        ):
            next_action = "S0_EXPECTED"
            reason = (
                "S5 workflow success with "
                "verified artifact provenance."
            )
        else:
            next_action = "LEAD_DECISION_REQUIRED"
            reason = (
                "S5 terminal failure or "
                "incomplete/unverified evidence; "
                "architectural judgment required."
            )

        atomic_state_write(
            client,
            cfg,
            final_state,
            next_action,
            reason,
        )

    print(
        json.dumps(
            {
                "final_state": final_state,
                "forensic": forensic,
            },
            indent=2,
            sort_keys=True,
        )
    )

    return (
        0
        if run.get(
            "conclusion"
        )
        == "success"
        else 4
    )


def cmd_auto_s5(
    client: GitHubClient,
    cfg: Config,
) -> int:
    state = current_state(
        client,
        cfg,
    )

    if not phase19_green(
        state
    ):
        if cfg.sync_state:
            atomic_state_write(
                client,
                cfg,
                state,
                "WAIT_PHASE19_GREEN",
                (
                    "Exact engineering HEAD "
                    "does not yet have a "
                    "GREEN Phase-19 run."
                ),
            )

        print(
            "WAIT_PHASE19_GREEN"
        )

        return 2

    if s5_active(
        state
    ):
        run_id = int(
            state["s5"]["id"]
        )

        print(
            json.dumps(
                {
                    "action": "RESUME_S5",
                    "run_id": run_id,
                    "head_sha":
                        state["head_sha"],
                },
                indent=2,
            )
        )

        return _finish_s5(
            client,
            cfg,
            state["head_sha"],
            run_id,
        )

    head_sha = state[
        "head_sha"
    ]

    dispatch_start = time.time()

    client.dispatch_workflow(
        S5_WORKFLOW_FILE,
        cfg.engineering_branch,
    )

    if cfg.sync_state:
        atomic_state_write(
            client,
            cfg,
            state,
            "S5_DISPATCHED",
            (
                "workflow_dispatch on exact "
                f"GREEN HEAD {head_sha}"
            ),
        )

    print(
        f"S5_DISPATCHED head={head_sha}"
    )

    run = wait_for_new_s5_run(
        client,
        cfg,
        head_sha,
        dispatch_start,
    )

    print(
        f"S5_RUN_FOUND id={run['id']} "
        f"head={run['head_sha']}"
    )

    return _finish_s5(
        client,
        cfg,
        head_sha,
        int(run["id"]),
    )


def resolve_github_token() -> str:
    """Resolve token securely for Colab without hard-coding or persisting it."""
    token = os.getenv(
        "GITHUB_TOKEN",
        "",
    ).strip()

    if token:
        return token

    try:
        from google.colab import userdata  # type: ignore

        token = str(
            userdata.get(
                "GITHUB_TOKEN"
            )
            or ""
        ).strip()

    except Exception:
        token = ""

    if token:
        os.environ[
            "GITHUB_TOKEN"
        ] = token

        return token

    try:
        from getpass import getpass

        token = getpass(
            "Enter GitHub fine-grained token (hidden): "
        ).strip()

    except Exception as exc:
        raise BridgeError(
            "Unable to read GitHub token securely; "
            "create Colab Secret GITHUB_TOKEN."
        ) from exc

    if not token:
        raise BridgeError(
            "GitHub token is empty. "
            "Create Colab Secret GITHUB_TOKEN."
        )

    os.environ[
        "GITHUB_TOKEN"
    ] = token

    return token




def _running_in_ipython() -> bool:
    """Return True when running under IPython/Google Colab."""
    return "IPython" in sys.modules or "google.colab" in sys.modules


def _cli_argv(argv: list[str] | None = None) -> list[str]:
    """Return user CLI arguments while ignoring Colab/Jupyter bootstrap args."""
    raw = list(sys.argv[1:] if argv is None else argv)

    if not _running_in_ipython():
        return raw

    cleaned: list[str] = []
    index = 0

    while index < len(raw):
        arg = raw[index]
        name = Path(arg).name

        # Colab/Jupyter commonly injects:
        #   -f /root/.local/share/jupyter/runtime/kernel-<uuid>.json
        if arg == "-f" and index + 1 < len(raw):
            candidate = raw[index + 1]
            candidate_name = Path(candidate).name
            if (
                candidate_name.startswith("kernel-")
                and candidate_name.endswith(".json")
            ):
                index += 2
                continue

        # Defensive fallback for directly injected kernel JSON paths.
        if (
            name.startswith("kernel-")
            and name.endswith(".json")
            and (
                "/jupyter/" in arg
                or "/ipykernel" in arg
                or arg.startswith("/root/")
            )
        ):
            index += 1
            continue

        cleaned.append(arg)
        index += 1

    return cleaned

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "command",
        choices=[
            "report",
            "terminal",
            "auto",
        ],
        nargs="?",
        default="report",
    )

    parser.add_argument(
        "--s5",
        action="store_true",
        help=(
            "With auto: dispatch and monitor "
            "S5 after exact-head Phase-19 GREEN."
        ),
    )

    args = parser.parse_args(_cli_argv())

    cfg = config_from_env()

    token = resolve_github_token()

    try:
        client = GitHubClient(
            token,
            cfg.repo,
        )

        if args.command == "report":
            return cmd_report(
                client,
                cfg,
            )

        if args.command == "terminal":
            return cmd_terminal(
                client,
                cfg,
            )

        if not args.s5:
            raise BridgeError(
                "Use `auto --s5` for the "
                "PHANTOMX S5 automation lane"
            )

        return cmd_auto_s5(
            client,
            cfg,
        )

    except BridgeError as exc:
        print(
            f"BRIDGE_ERROR: {exc}"
        )

        return 10


if __name__ == "__main__":
    _exit_code = main()
    if not _running_in_ipython():
        raise SystemExit(_exit_code)
