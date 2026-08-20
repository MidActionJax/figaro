"""
Phase 1 entry point: run the email-triage agent headlessly against Gmail and
have it write draft replies into queue/.

Usage:
    python scripts/morning_email_run.py [--hours 48]

This shells out to `claude -p` (Claude Code headless mode) rather than talking to
Gmail directly, so the agent gets the same MCP-based Gmail access, the same
CLAUDE.md/agents/instructions context, and the same file tools it would have in an
interactive session.

IMPORTANT — before pointing Windows Task Scheduler at this script:
Run it manually a few times first (`python scripts/morning_email_run.py`) and watch
the output. The `--disallowed-tools` list below is a best-effort safety net based on
the Gmail MCP tool names observed on this machine (see `claude mcp list`); MCP tool
name prefixes can differ across environments/reconnects. Confirm no send/trash/spam
tool call happened before trusting this unattended. When in doubt, drop
`--permission-mode acceptEdits` and run without it once so Claude Code prompts you
interactively for every tool call.
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Gmail tools this agent must never call directly — sending/trashing/spam-marking is
# a separate, explicitly-approved action performed by review_queue.py, not here.
# Update this list if `claude mcp list` shows a different connector/tool naming.
DISALLOWED_GMAIL_TOOLS = [
    "mcp__gmail__send_message",
    "mcp__gmail__reply",
    "mcp__gmail__forward",
    "mcp__gmail__trash_message",
    "mcp__gmail__trash_thread",
    "mcp__gmail__mark_message_spam",
    "mcp__gmail__mark_thread_spam",
]


def build_prompt(hours: int) -> str:
    return f"""You are the email-triage agent. Follow agents/email-triage.md exactly.

Task for this run:
1. Read agents/email-triage.md, instructions/email-triage.md, and the tail of
   learnings/email-rejections.md.
2. Search Gmail for threads from the last {hours} hours (unread and recently active).
3. Classify each as important/not-important per the current rules.
4. For each important thread that warrants a reply, draft one in the user's voice
   and write it to queue/ as its own markdown file, exactly per the format in
   agents/email-triage.md step 5. Use the repo-relative path queue/<filename>.md.
5. Do not send, reply, forward, trash, or mark-spam anything. Drafting and writing
   the queue file is the entire job.
6. When done, print a one-line summary: threads seen, drafted, skipped.
"""


def main():
    parser = argparse.ArgumentParser(description="Run the email-triage agent headlessly.")
    parser.add_argument("--hours", type=int, default=48, help="Lookback window for Gmail search.")
    parser.add_argument(
        "--unattended",
        action="store_true",
        help="Use acceptEdits permission mode for non-interactive (Task Scheduler) runs. "
        "Omit this for the first several manual runs so you can watch tool calls.",
    )
    args = parser.parse_args()

    queue_dir = REPO_ROOT / "queue"
    queue_dir.mkdir(exist_ok=True)

    prompt = build_prompt(args.hours)

    cmd = [
        "claude",
        "-p",
        prompt,
        "--disallowedTools",
        ",".join(DISALLOWED_GMAIL_TOOLS),
        "--output-format",
        "text",
    ]
    if args.unattended:
        cmd += ["--permission-mode", "acceptEdits"]

    print(f"[{datetime.now(timezone.utc).isoformat()}] Running email-triage agent "
          f"(lookback={args.hours}h, unattended={args.unattended})...")

    result = subprocess.run(cmd, cwd=REPO_ROOT)

    if result.returncode != 0:
        print(f"email-triage run failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    print("Done. Review new drafts with: python scripts/review_queue.py")


if __name__ == "__main__":
    main()
