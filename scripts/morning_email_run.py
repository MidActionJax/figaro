"""
Phase 1 entry point: run the email-triage agent headlessly against Gmail and
have it write draft replies into queue/.

Usage:
    python scripts/morning_email_run.py [--hours 48]

This shells out to `claude -p` (Claude Code headless mode) rather than talking to
Gmail directly, so the agent gets the same MCP-based Gmail access, the same
CLAUDE.md/agents/instructions context, and the same file tools it would have in an
interactive session.

KNOWN UNRESOLVED ISSUE (as of 2026-08-20) — this script does not reliably work
unattended right now, and it's not a quick fix:

Running the full multi-step triage prompt headlessly (`-p`) reliably hits a
permission wall on the first Gmail tool call, even with `--allowedTools` covering
exactly the tools needed. Ruled out so far, each confirmed by direct testing:
  - Not a tool-naming bug (confirmed the real `mcp__claude_ai_Gmail__*` prefix).
  - Not fixed by `--dangerously-skip-permissions` on the nested process (still
    generates "needs approval" text — the model itself is declining, this isn't
    the CLI's permission dialog).
  - Not fixed by `--continue`/`--resume` into a session with real prior context
    (tried resuming AWSRT-style; the model correctly saw prior context but the
    Gmail tool call was still denied).
  - Chaining two calls in the *same* session — a first call that successfully
    used `search_threads`, then `--continue` into the full prompt in that same
    session — produced real carried-over context (it correctly referenced the
    earlier result) but the *next* Gmail tool call was still denied, and this
    time as an actual permission-system denial, not just the model hesitating.
    That's the strongest signal this is a genuine constraint in how `-p` mode
    handles MCP tool permissions across multiple calls in one session, not
    something fixable by prompt wording or flag choice from the outside.

**Current recommendation: don't rely on this script unattended.** Interactive/
conversational triage (asking Figaro directly, in a normal session, to check
Gmail) works reliably and has been used for real triage runs — see the
`2026-08-20-162723 Coffeee` entry in `learnings/email-rejections.md` for a real
example. Revisit this script if Claude Code's headless permission model changes,
or if there's a way to pre-authorize specific MCP tools for a session that this
investigation didn't find.
"""

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# subprocess.run() doesn't do PATHEXT resolution on Windows the way a shell does, so
# a bare "claude" fails to find claude.cmd even though `where claude` finds it fine.
# Resolve the real path up front instead.
CLAUDE_BIN = shutil.which("claude")
if CLAUDE_BIN is None:
    sys.exit("Could not find 'claude' on PATH. Is Claude Code installed and on PATH?")

# Confirmed on this machine via `claude -p "list gmail tool names"` — the connector
# is named "claude_ai_Gmail", not "gmail". Re-check with the same command if this
# ever stops matching (e.g. after reconnecting the Gmail connector).
GMAIL_PREFIX = "mcp__claude_ai_Gmail__"

# Exactly what agents/email-triage.md scopes this agent to: read + draft, nothing
# that sends or mutates mail state beyond labeling/drafting.
ALLOWED_GMAIL_TOOLS = [
    GMAIL_PREFIX + name
    for name in [
        "search_threads",
        "get_thread",
        "get_message",
        "list_labels",
        "label_thread",
        "label_message",
    ]
]

# Belt-and-suspenders explicit denylist for the sensitive/irreversible ones, even
# though omitting them from ALLOWED_GMAIL_TOOLS already blocks them by default.
DISALLOWED_GMAIL_TOOLS = [
    GMAIL_PREFIX + name
    for name in [
        "send_message",
        "reply",
        "forward",
        "trash_message",
        "trash_thread",
        "mark_message_spam",
        "mark_thread_spam",
    ]
]


def build_prompt(hours: int) -> str:
    return f"""You are the email-triage agent. Follow agents/email-triage.md exactly.

This is an unattended, non-interactive run with no one available to answer
questions — if you ask for confirmation, there is no one to respond and the run
will simply fail. The user already gave their approval by running
scripts/morning_email_run.py themselves; that is the approval for everything this
agent is scoped to do. You are pre-authorized, right now, with no further
confirmation needed, to: search Gmail, read thread/message contents, and write
files under queue/. Call the Gmail search tool immediately as your first action —
do not ask whether you should, do not describe what you're about to do and wait,
just do it. The only thing actually gated behind human approval is sending mail,
and this agent physically cannot do that — send/reply/forward tools are not in its
tool list at all, so there is nothing left here that needs a question asked.

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
        help="Skip the interactive permission dialog for non-interactive (Task Scheduler) "
        "runs, since there's no one there to answer it. Safety boundary is still "
        "--allowedTools/--disallowedTools above (send/reply/forward/trash/spam are never "
        "in the tool list). Omit this for the first several manual runs so you can watch "
        "tool calls before trusting it unattended.",
    )
    args = parser.parse_args()

    queue_dir = REPO_ROOT / "queue"
    queue_dir.mkdir(exist_ok=True)

    prompt = build_prompt(args.hours)

    cmd = [
        CLAUDE_BIN,
        "-p",
        prompt,
        "--allowedTools",
        ",".join(["Read", "Write"] + ALLOWED_GMAIL_TOOLS),
        "--disallowedTools",
        ",".join(DISALLOWED_GMAIL_TOOLS),
        "--output-format",
        "text",
    ]
    if args.unattended:
        cmd += ["--dangerously-skip-permissions"]

    print(f"[{datetime.now(timezone.utc).isoformat()}] Running email-triage agent "
          f"(lookback={args.hours}h, unattended={args.unattended})...")

    result = subprocess.run(cmd, cwd=REPO_ROOT)

    if result.returncode != 0:
        print(f"email-triage run failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    print("Done. Review new drafts with: python scripts/review_queue.py")


if __name__ == "__main__":
    main()
