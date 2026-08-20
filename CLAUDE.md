# Figaro — Master Context

This file is read by every Claude Code session (interactive or headless `claude -p`)
that operates inside this repo. Full project spec: [docs/figaro-project-spec.md](docs/figaro-project-spec.md).

## What Figaro is

A personally-built, locally-run chief-of-staff agent. Figaro coordinates; subagents
(defined in `agents/`) do the domain work. Nothing irreversible (send, submit,
commit+push) happens without explicit human approval, except where the user has
pre-approved a specific action type in writing.

## Current build phase

**Phase 0 + Phase 1 only: Email triage (Gmail).** Per the spec's own recommendation,
do not build coursework, NASA/CLEAR, zyBooks, or the dispatcher/meta-agent until the
email loop has run successfully for at least a week. Don't add scaffolding for later
phases speculatively.

## Decisions made so far (supersede anything in the spec doc that conflicts)

- **Email scope for Phase 1: Gmail only.** The other three inboxes (University of
  Michigan, GSW, Columbus State) are out of scope until Gmail triage is proven out.
- **No web dashboard for Phase 1.** The spec's original dashboard (Flask/FastAPI +
  browser UI) is deferred. Approval queue is file-based: drafts land as markdown
  files in `queue/`, reviewed via `scripts/review_queue.py` in a terminal the user
  keeps open. Revisit a real web dashboard once the email loop is trustworthy.

## How the email triage loop works right now

1. `scripts/morning_email_run.py` is the entry point (run manually for now, or via
   Windows Task Scheduler later — not yet wired up).
2. It invokes `claude -p` headless, pointing it at `agents/email-triage.md` and
   `instructions/email-triage.md`, with Gmail MCP tools available.
3. The agent reads unread/recent Gmail, classifies importance, and for important
   mail drafts a reply in the user's voice — grounded in `instructions/email-triage.md`
   and the tail of `learnings/email-rejections.md`.
4. Drafts are written as individual markdown files in `queue/`, one per draft, with
   YAML frontmatter (`status: pending`). **No email is ever sent automatically.**
5. The user reviews with `scripts/review_queue.py` (approve / edit / reject).
   - Approve → sends as-is via Gmail MCP, moves file to `queue/done/`.
   - Edit → opens the draft in the user's editor, sends the edited version, logs a
     diff summary to `learnings/email-rejections.md`.
   - Reject → does not send, logs the reason to `learnings/email-rejections.md`.

## Rules that apply to every subagent, always

- No email is sent without approval (editing counts as approval of the edited text).
- No new agent gets sensitive tool access (send, push, browser control) without the
  user explicitly approving it first.
- If something doesn't map to an existing agent, say so — don't improvise a new
  capability silently.
- Read the relevant `instructions/*.md` file and the tail of the relevant
  `learnings/*.md` file before doing any work in that domain.

## User grounding

See "User Context" in [docs/figaro-project-spec.md](docs/figaro-project-spec.md) for
who this is being built for and why. Treat it as real grounding, not generic defaults.
