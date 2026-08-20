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

Send/approve/reject mechanics live in scripts/queue_lib.py, shared with
dashboard/server.py — this file is just the terminal UI on top of it.
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import queue_lib as ql


def edit_body(body: str) -> str:
    import os
    editor = os.environ.get("EDITOR", "notepad")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
        tf.write(body)
        tmp_path = Path(tf.name)
    subprocess.run([editor, str(tmp_path)])
    edited = tmp_path.read_text(encoding="utf-8")
    tmp_path.unlink(missing_ok=True)
    return edited


def review_one(path: Path) -> str:
    meta, body = ql.parse_draft(path)
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
        if not meta.get("thread_id"):
            print("No thread_id in frontmatter — cannot send. Skipping.")
            return "skip"
        if ql.approve_draft(path):
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
        if not meta.get("thread_id"):
            print("No thread_id in frontmatter — cannot send. Skipping.")
            return "skip"
        summary = input("One-line summary of what you changed (for learnings log): ").strip()
        if ql.send_edited_draft(path, edited, summary):
            print("Sent and logged.")
        else:
            print("Send failed — left in queue as pending.")
        return "handled"

    if choice == "r":
        reason = input("Reason (optional): ").strip()
        ql.reject_draft(path, reason)
        print("Rejected and logged.")
        return "handled"

    print("Unrecognized choice, skipping.")
    return "skip"


def main():
    parser = argparse.ArgumentParser(description="Review pending email drafts.")
    parser.parse_args()

    pending = ql.list_pending()
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
