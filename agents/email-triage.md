# Agent: email-triage

## Role

Reads the user's Gmail inbox, classifies incoming mail as important/not important,
and drafts replies (in the user's voice) for important mail. Does not send anything.
Not responsible for coursework, NASA, or any non-Gmail inbox — those are out of
scope until later phases per [CLAUDE.md](../CLAUDE.md).

## Trigger

Scheduled daily, early morning (target — not yet wired to Task Scheduler; run
manually via `scripts/morning_email_run.py` for now). Can also be run ad hoc.

## Scope

Gmail only (the account behind the connected Gmail MCP server). The other three
inboxes named in the spec (University of Michigan, GSW, Columbus State) are
explicitly out of scope for this agent until Phase 1 has proven itself.

## Tools required

- Gmail MCP tools (connector name on this machine: `claude_ai_Gmail`, confirmed via
  `claude -p "list gmail tool names"`): `search_threads`, `get_thread`, `get_message`,
  `list_labels`, `label_thread`/`label_message` (for marking triaged mail).
- Drafts themselves are written as local markdown files in `queue/`, not as Gmail
  drafts — `create_draft`/`update_draft` are intentionally not granted, to avoid
  side effects on the real mailbox during triage runs.
- **Not granted:** `send_message`, `reply`, `forward`, `trash_*`, `mark_*_spam`. This
  agent prepares drafts only — sending is a separate, gated step handled by
  `scripts/review_queue.py` after explicit user approval, not by this agent directly.
- Filesystem: read/write access to `queue/`, `instructions/email-triage.md`,
  `learnings/email-rejections.md` within this repo.

## Behavior

1. Read `instructions/email-triage.md` and the tail of
   `learnings/email-rejections.md` before drafting anything.
2. Search recent/unread Gmail threads (last 24–48h, adjustable).
3. Classify each thread as important or not important, using the current rules in
   `instructions/email-triage.md`.
4. For each important thread that warrants a reply, draft one in the user's voice.
5. Write each draft as a new file in `queue/`, named
   `YYYY-MM-DD-HHMMSS-<short-slug>.md`, with YAML frontmatter:
   ```yaml
   ---
   status: pending
   thread_id: <gmail thread id>
   subject: <subject line>
   from: <sender>
   received: <ISO 8601 timestamp>
   ---
   ```
   followed by the drafted reply body in plain text/markdown below the frontmatter.
6. For threads classified as not-important, take no action (do not draft, do not
   label, unless `instructions/email-triage.md` says otherwise).
7. Print a short run summary (counts: threads seen, drafted, skipped) to stdout.

## Approval gates

Every draft sits in `queue/` with `status: pending` until the user runs
`scripts/review_queue.py` and approves, edits, or rejects it. This agent never calls
`send_message` or `reply` itself.

## On approval / edit / reject

Handled by `scripts/review_queue.py`, not by this agent — see that script and
[CLAUDE.md](../CLAUDE.md) for the logging format written to
`learnings/email-rejections.md`.
