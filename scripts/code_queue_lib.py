"""
Shared queue/approval logic for Salsbergs' code-change approvals - the coding
equivalent of scripts/queue_lib.py's email queue. Salsbergs prepares (diff +
commit message + PR title/description) while doing the actual work; the
commit/push/PR mechanics here are deterministic subprocess calls with real
verification at each step, not trusted to an LLM's own report of success -
same lesson learned from the Gmail send path (queue_lib.py / gmail_api.py):
verify what actually happened, don't trust a clean exit code alone.

Queue file format (code_queue/*.md):
---
status: pending
repo_name: CLEAR
repo_path: C:/Users/jaxon/OneDrive/Desktop/Github/CLEAR
base_branch: jax
new_branch: fix/heartbeat-log-dir
files: RealTimeSW/heartbeat_check.sh
pr_title: Fix heartbeat_check.sh dying when log directory doesn't exist yet
---
<PR description / commit message body, markdown>
"""

import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CODE_QUEUE_DIR = REPO_ROOT / "code_queue"
DONE_DIR = CODE_QUEUE_DIR / "done"
REJECTED_DIR = CODE_QUEUE_DIR / "rejected"
LEARNINGS_FILE = REPO_ROOT / "learnings" / "nasa-notes.md"


def parse_task(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    frontmatter_block = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    frontmatter = {}
    for line in frontmatter_block.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip()
    return frontmatter, body


def list_pending():
    if not CODE_QUEUE_DIR.exists():
        return []
    return sorted(
        p for p in CODE_QUEUE_DIR.glob("*.md")
        if parse_task(p)[0].get("status", "pending") == "pending"
    )


def log_learning(action: str, meta: dict, reason: str = "", pr_url: str = ""):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    entry = [
        f"### {ts} {meta.get('pr_title', 'unknown')[:60]}",
        f"- repo: {meta.get('repo_name', 'unknown')}",
        f"- request: {meta.get('pr_title', 'unknown')}",
        f"- outcome: {action}",
    ]
    if pr_url:
        entry.append(f"- notes: PR opened at {pr_url}")
    elif reason:
        entry.append(f"- notes: {reason}")
    entry.append("")
    with LEARNINGS_FILE.open("a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(entry))


def get_live_diff(repo_path: str, files: list) -> str:
    """Live git diff, not a stored snapshot - the queue file only holds
    metadata, so this can never go stale relative to the working tree."""
    cmd = ["git", "-C", repo_path, "diff", "--"] + files
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=30)
    except subprocess.TimeoutExpired:
        return "(diff timed out)"
    return result.stdout or "(no diff - files may already be committed or unchanged)"


def approve_task(path: Path) -> tuple[bool, str]:
    """Creates a branch, commits the specified files, pushes, opens a PR.
    Verifies each step actually happened before proceeding to the next -
    a failed git command stops here rather than continuing on a false
    assumption of success, and both the commit and the PR are independently
    confirmed to exist afterward, not just inferred from exit codes."""
    meta, body = parse_task(path)
    repo_path = meta.get("repo_path", "")
    base_branch = meta.get("base_branch", "")
    new_branch = meta.get("new_branch", "")
    files = [f.strip() for f in meta.get("files", "").split(",") if f.strip()]
    pr_title = meta.get("pr_title", "")

    if not (repo_path and base_branch and new_branch and files and pr_title):
        return False, "Missing required frontmatter (repo_path/base_branch/new_branch/files/pr_title)."

    def run(cmd, timeout=60):
        try:
            return subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True,
                                   encoding="utf-8", timeout=timeout)
        except subprocess.TimeoutExpired:
            return None

    r = run(["git", "checkout", "-b", new_branch])
    if r is None or r.returncode != 0:
        return False, f"git checkout -b failed: {(r.stderr.strip() if r else 'timed out')}"

    r = run(["git", "add"] + files)
    if r is None or r.returncode != 0:
        return False, f"git add failed: {(r.stderr.strip() if r else 'timed out')}"

    commit_message = f"{pr_title}\n\n{body.strip()}"
    r = run(["git", "commit", "-m", commit_message])
    if r is None or r.returncode != 0:
        return False, f"git commit failed: {(r.stderr.strip() if r else 'timed out')}"

    # Verify the commit actually landed before doing anything remote/irreversible.
    r = run(["git", "log", "-1", "--pretty=%H"])
    if r is None or r.returncode != 0 or not r.stdout.strip():
        return False, "Could not verify the commit actually landed - stopping before push."
    commit_sha = r.stdout.strip()

    r = run(["git", "push", "-u", "origin", new_branch])
    if r is None or r.returncode != 0:
        return False, f"git push failed (commit {commit_sha[:8]} is local-only, not lost): {(r.stderr.strip() if r else 'timed out')}"

    r = run(["gh", "pr", "create", "--title", pr_title, "--body", body.strip(),
             "--base", base_branch, "--head", new_branch], timeout=90)
    if r is None or r.returncode != 0:
        return False, f"gh pr create failed (branch is pushed, commit {commit_sha[:8]}): {(r.stderr.strip() if r else 'timed out')}"
    reported_url = r.stdout.strip()

    # Don't trust gh's exit code alone - independently confirm the PR exists.
    r = run(["gh", "pr", "view", new_branch, "--json", "url"], timeout=30)
    if r is None or r.returncode != 0:
        return False, f"Pushed and gh reported success (url: {reported_url}) but couldn't independently verify the PR exists - check manually."

    DONE_DIR.mkdir(exist_ok=True)
    shutil.move(str(path), DONE_DIR / path.name)
    log_learning("approve", meta, pr_url=reported_url)
    return True, reported_url


def reject_task(path: Path, reason: str) -> None:
    meta, _ = parse_task(path)
    REJECTED_DIR.mkdir(exist_ok=True)
    shutil.move(str(path), REJECTED_DIR / path.name)
    log_learning("reject", meta, reason=reason)
