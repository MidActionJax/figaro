"""
Shared queue/approval logic used by both scripts/review_queue.py (terminal) and
dashboard/server.py (web). Keeping this in one place means the send/approve/reject
mechanics — and the safety boundary around what the nested claude call is allowed
to do — only exist in one spot rather than being duplicated and drifting apart.
"""

import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = REPO_ROOT / "queue"
DONE_DIR = QUEUE_DIR / "done"
REJECTED_DIR = QUEUE_DIR / "rejected"
LEARNINGS_FILE = REPO_ROOT / "learnings" / "email-rejections.md"

# Confirmed on this machine via `claude -p "list gmail tool names"` — the connector
# is named "claude_ai_Gmail", not "gmail". Re-check with the same command if this
# ever stops matching (e.g. after reconnecting the Gmail connector).
SEND_TOOL_NAME = "mcp__claude_ai_Gmail__reply"

# subprocess.run() doesn't do PATHEXT resolution on Windows the way a shell does, so
# a bare "claude" fails to find claude.cmd even though `where claude` finds it fine.
CLAUDE_BIN = shutil.which("claude")
if CLAUDE_BIN is None:
    sys.exit("Could not find 'claude' on PATH. Is Claude Code installed and on PATH?")


def parse_draft(path: Path):
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
    if not QUEUE_DIR.exists():
        return []
    return sorted(
        p for p in QUEUE_DIR.glob("*.md")
        if parse_draft(p)[0].get("status", "pending") == "pending"
    )


def log_learning(action: str, meta: dict, reason: str = "", diff_summary: str = ""):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    entry = [
        f"### {ts} {meta.get('subject', 'unknown')[:60]}",
        f"- action: {action}",
        f"- subject: {meta.get('subject', 'unknown')}",
        f"- reason: {reason or 'not given'}",
    ]
    if diff_summary:
        entry.append(f"- diff/summary: {diff_summary}")
    entry.append("")
    with LEARNINGS_FILE.open("a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(entry))


def send_via_claude(thread_id: str, body: str) -> bool:
    prompt = (
        f"Using the Gmail MCP reply tool, send the following exact reply to Gmail "
        f"thread {thread_id}. Do not alter the wording, do not add a signature or "
        f"disclaimer, do not touch any other thread or message.\n\n---\n{body}\n---"
    )
    cmd = [
        CLAUDE_BIN, "-p", prompt,
        "--allowedTools", SEND_TOOL_NAME,
        "--permission-mode", "acceptEdits",
        "--output-format", "text",
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode == 0


def approve_draft(path: Path) -> bool:
    """Send a draft as-is. Returns True and moves/logs it on success."""
    meta, body = parse_draft(path)
    thread_id = meta.get("thread_id", "")
    if not thread_id:
        return False
    if not send_via_claude(thread_id, body.strip()):
        return False
    DONE_DIR.mkdir(exist_ok=True)
    shutil.move(str(path), DONE_DIR / path.name)
    log_learning("approve", meta)
    return True


def send_edited_draft(path: Path, edited_body: str, diff_summary: str) -> bool:
    """Send an edited version of a draft. Returns True and moves/logs it on success."""
    meta, _ = parse_draft(path)
    thread_id = meta.get("thread_id", "")
    if not thread_id:
        return False
    if not send_via_claude(thread_id, edited_body.strip()):
        return False
    DONE_DIR.mkdir(exist_ok=True)
    shutil.move(str(path), DONE_DIR / path.name)
    log_learning("edit", meta, diff_summary=diff_summary)
    return True


def reject_draft(path: Path, reason: str) -> None:
    meta, _ = parse_draft(path)
    REJECTED_DIR.mkdir(exist_ok=True)
    shutil.move(str(path), REJECTED_DIR / path.name)
    log_learning("reject", meta, reason=reason)
