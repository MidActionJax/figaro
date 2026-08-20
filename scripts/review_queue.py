"""
Phase 1 approval queue: terminal-based review of pending email drafts.

Usage:
    python scripts/review_queue.py

For each file in queue/ with status: pending, shows the draft and asks:
  [a]pprove  - send as-is via Gmail (through a narrowly-scoped headless claude call)
  [e]dit     - open in $EDITOR, then send the edited version
  [r]eject   - do not send, log a reason
  [s]kip     - leave pending, move to the next draft
  [q]uit     - stop reviewing

Approved/edited drafts are sent by shelling out to `claude -p` with a prompt that
contains the exact final text and --allowedTools restricted to just the Gmail
send/reply tool, so send capability exists only for that one call, only after the
user has explicitly typed approve/edit-then-confirm here. This script never sends
anything itself.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = REPO_ROOT / "queue"
DONE_DIR = QUEUE_DIR / "done"
REJECTED_DIR = QUEUE_DIR / "rejected"
LEARNINGS_FILE = REPO_ROOT / "learnings" / "email-rejections.md"

# Must match the tool name Gmail MCP actually exposes on this machine — check with
# `claude mcp list` / the tool name observed when create_draft etc. are used.
SEND_TOOL_NAME = "mcp__gmail__reply"


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
        "claude", "-p", prompt,
        "--allowedTools", SEND_TOOL_NAME,
        "--permission-mode", "acceptEdits",
        "--output-format", "text",
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode == 0


def edit_body(body: str) -> str:
    editor = __import__("os").environ.get("EDITOR", "notepad")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
        tf.write(body)
        tmp_path = Path(tf.name)
    subprocess.run([editor, str(tmp_path)])
    edited = tmp_path.read_text(encoding="utf-8")
    tmp_path.unlink(missing_ok=True)
    return edited


def review_one(path: Path) -> str:
    meta, body = parse_draft(path)
    print("\n" + "=" * 70)
    print(f"File:     {path.name}")
    print(f"Subject:  {meta.get('subject', '?')}")
    print(f"From:     {meta.get('from', '?')}")
    print(f"Received: {meta.get('received', '?')}")
    print("-" * 70)
    print(body.strip())
    print("=" * 70)

    choice = input("[a]pprove / [e]dit / [r]eject / [s]kip / [q]uit: ").strip().lower()

    if choice == "q":
        return "quit"

    if choice == "s" or choice == "":
        return "skip"

    if choice == "a":
        thread_id = meta.get("thread_id", "")
        if not thread_id:
            print("No thread_id in frontmatter — cannot send. Skipping.")
            return "skip"
        if send_via_claude(thread_id, body.strip()):
            DONE_DIR.mkdir(exist_ok=True)
            shutil.move(str(path), DONE_DIR / path.name)
            log_learning("approve", meta)
            print("Sent and logged.")
        else:
            print("Send failed — left in queue as pending.")
        return "handled"

    if choice == "e":
        edited = edit_body(body)
        if edited.strip() == body.strip():
            print("No changes made.")
        confirm = input("Send edited version? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Not sent. Left in queue as pending.")
            return "handled"
        thread_id = meta.get("thread_id", "")
        if not thread_id:
            print("No thread_id in frontmatter — cannot send. Skipping.")
            return "skip"
        if send_via_claude(thread_id, edited.strip()):
            DONE_DIR.mkdir(exist_ok=True)
            shutil.move(str(path), DONE_DIR / path.name)
            summary = input("One-line summary of what you changed (for learnings log): ").strip()
            log_learning("edit", meta, diff_summary=summary)
            print("Sent and logged.")
        else:
            print("Send failed — left in queue as pending.")
        return "handled"

    if choice == "r":
        reason = input("Reason (optional): ").strip()
        REJECTED_DIR.mkdir(exist_ok=True)
        shutil.move(str(path), REJECTED_DIR / path.name)
        log_learning("reject", meta, reason=reason)
        print("Rejected and logged.")
        return "handled"

    print("Unrecognized choice, skipping.")
    return "skip"


def main():
    parser = argparse.ArgumentParser(description="Review pending email drafts.")
    parser.parse_args()

    pending = list_pending()
    if not pending:
        print("No pending drafts in queue/.")
        return

    print(f"{len(pending)} pending draft(s).")
    for path in pending:
        result = review_one(path)
        if result == "quit":
            break

    print("Done reviewing.")


if __name__ == "__main__":
    main()
