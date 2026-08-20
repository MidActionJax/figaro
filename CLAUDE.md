# Figaro — Master Context

This file is read by every Claude Code session (interactive or headless `claude -p`)
that operates inside this repo. Full project spec: [docs/figaro-project-spec.md](docs/figaro-project-spec.md).

## What Figaro is

A personally-built, locally-run chief-of-staff agent. Figaro coordinates; subagents
(defined in `agents/`) do the domain work. Nothing irreversible (send, submit,
commit+push) happens without explicit human approval, except where the user has
pre-approved a specific action type in writing.

## Current build phase

**Interface-first, as of 2026-08-20.** Earlier the same day the user chose to start
Phase 2-4 agent scaffolding ahead of the spec's recommended pace (see the agent
files under `agents/` for GSW/Columbus coursework, Salsbergs/NASA, zyBooks) — then,
later that day, explicitly paused expanding to *more* agent domains. Current
priority: build out the dashboard interface and perfect the existing (email
triage) agent before "hiring" more agents. Read this as the current priority
ordering, not a reversal — the Phase 2-4 scaffolding still exists and is still
correct, it's just not being extended further (e.g. no new agents, no chasing the
LMS-access TODO) until the interface and Phase 1 are solid. Phase 5 (Figaro
dispatcher + meta-agent creation) remains deliberately held.

Phase 1 (email triage) remains the only domain with a proven approval/learning
loop (one real cycle: draft → reject → instructions updated) — treat the other
domains' instructions files as unvalidated starting points until they've been
through real use.

## Decisions made so far (supersede anything in the spec doc that conflicts)

- **Email scope for Phase 1: Gmail only.** The other three inboxes (University of
  Michigan, GSW, Columbus State) are out of scope until Gmail triage is proven out.
- **Web dashboard built 2026-08-20** (`dashboard/server.py`, Flask). User chose to
  pause expanding into more agent domains and instead build out the interface and
  perfect the current (email) agent first, before "hiring" more agents. Two views
  on one page: approval queue (approve/edit/reject, wired to the same
  `scripts/queue_lib.py` the terminal `review_queue.py` uses, so the two UIs can't
  drift apart) and a chat box. Binds to `127.0.0.1` only by default — no auth
  exists yet, so don't bind `0.0.0.0`/LAN without adding some first, even though
  the spec wants phone access eventually. `scripts/review_queue.py` (terminal)
  still works and isn't deprecated — same underlying logic, different UI.
- **Dashboard chat is read-only by design**, not the Phase 5 dispatcher. It has
  the `Read` tool only (no Bash/Write/Edit/MCP), so it can answer questions about
  the repo/queue/learnings but can't take actions. Prompt structure matters here:
  leading with the actual question and keeping instructional framing short and
  *after* it is what made this reliable — an earlier version led with several
  sentences of persona-setup before the question and the model consistently
  treated the real question as not-yet-arrived ("I don't see a question yet"),
  even though it was right there in the same message. See the comment in
  `dashboard/server.py`'s `chat()` if this regresses.
- **Salsbergs' NASA repo scope: both `AWSRT` and `CLEAR`, not a single hardcoded
  path.** Found at `C:\Users\jaxon\OneDrive\Desktop\Github\AWSRT` (real-time
  forecasting pipeline; already has a `.claude/` dir from prior use) and
  `C:\Users\jaxon\OneDrive\Desktop\Github\CLEAR` (literally "the CLEAR project"
  repo, matches spec naming). Both are under the `SWMFsoftware` GitHub org. Salsbergs
  determines which repo a task applies to from the request itself rather than
  assuming one.
- **zyBooks academic-integrity gate: confirmed clear by the user (2026-08-20).**
  Both read/summarize and completion-automation capability are in scope for
  `agents/zybooks.md` — see that file for how completion access is still granted
  narrowly (computer-use/browser control is a sensitive tool per the global rules
  below, so first real use still gets a human go-ahead even though the policy
  question itself is settled).
- **Coursework LMS access (GSW/Columbus State): resolved 2026-08-20.** Both
  schools run D2L Brightspace under USG's shared infrastructure; confirmed
  neither offers students a self-service API token, so both use a persistent
  Playwright session — `scripts/lms_login.py <gsw|colstate>` (user-run, needs
  real desktop/MFA) + `scripts/lms_check.py <gsw|colstate>` (headless-safe,
  reads the saved session). See `agents/coursework-gsw.md` "Tools required"
  for the full mechanism and what was ruled out along the way (persistent
  browser *profile* directories had a session-cookie quirk with this SSO flow
  that explicit `storage_state` export/import sidesteps). Currently reads the
  homepage only (course list, announcements, calendar) — going deeper into
  individual courses for specific assignment due dates is real follow-up work.

## How the email triage loop works right now

**`scripts/morning_email_run.py` (unattended headless triage) does not reliably
work yet — this is a real, investigated dead end, not just "untested."** Full
writeup of what was ruled out is in that file's docstring. Short version: the
first Gmail tool call in a headless `-p` run reliably hits a permission wall that
survives correct tool naming, `--dangerously-skip-permissions`, and session
resume/continuity — including a test where a prior call in the *same* session had
already used the tool successfully. This looks like a genuine constraint in how
`-p` mode handles MCP tool permissions, not something fixable from outside the
CLI. **Interactive triage works reliably instead** — just ask Figaro directly, in
a normal session, to check Gmail. That's the supported path for now; see
`learnings/email-rejections.md` for a real example (the "Coffeee" entry).

1. `scripts/morning_email_run.py` is the entry point for unattended runs (not
   currently reliable — see above). Interactive triage (asking directly) is the
   supported path today.
2. It invokes `claude -p` headless, pointing it at `agents/email-triage.md` and
   `instructions/email-triage.md`, with Gmail MCP tools available.
3. The agent reads unread/recent Gmail, classifies importance, and for important
   mail drafts a reply in the user's voice — grounded in `instructions/email-triage.md`
   and the tail of `learnings/email-rejections.md`.
4. Drafts are written as individual markdown files in `queue/`, one per draft, with
   YAML frontmatter (`status: pending`). **No email is ever sent automatically.**
5. The user reviews with `scripts/review_queue.py` or the dashboard (approve /
   edit / reject).
   - Approve → sends as-is, moves file to `queue/done/`.
   - Edit → opens the draft (editor for the terminal script, a textarea for the
     dashboard), sends the edited version, logs a diff summary to
     `learnings/email-rejections.md`.
   - Reject → does not send, logs the reason to `learnings/email-rejections.md`.

**The actual send step is direct Gmail API, not Claude Code** —
`scripts/gmail_api.py`, set up once via `python scripts/gmail_auth_setup.py`
(see `docs/gmail-api-setup.md`). This changed 2026-08-20 after real testing
found the original design (`claude -p` with the Gmail MCP reply tool) unreliable
in the same way as the headless-triage issue above: a `-p` call could exit 0
looking successful while having sent nothing, because the underlying MCP tool
call was silently denied by what looks like a built-in Claude Code safety
classifier for sensitive actions. Reading/searching Gmail through the MCP
connector is unaffected and still works fine — only the mechanical "send this"
step moved. If `sessions/gmail_token.json` doesn't exist yet, sending will fail
with a clear `GmailNotAuthorized` message pointing at the setup doc.

## Running the dashboard

The dashboard now auto-starts at login (set up 2026-08-20), matching the
original spec's "no terminal needed for daily use" goal:

- `scripts/start_dashboard.bat` (tracked in this repo) checks whether something
  is already listening on port 5151 and exits immediately if so — this exists
  specifically to prevent the duplicate-process bug found during send-path
  testing (two servers bound to the same port, requests routed unpredictably
  between old and new code). If nothing's listening, it launches
  `pythonw.exe dashboard/server.py` via PowerShell's `Start-Process` (not a bare
  invocation — a real test found that plain `cmd /c` invocations of a background
  process didn't reliably detach in this environment's tooling; `Start-Process`
  is the Windows-correct mechanism and worked cleanly every time it was tested).
- A stub at
  `C:\Users\jaxon\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\figaro-dashboard.bat`
  (outside this repo, per-machine, not git-tracked) just calls the real script
  above. Windows runs anything in that Startup folder automatically at login.
- Verified working via manual invocation (both the "not running, start it" and
  "already running, skip" paths, run repeatedly). **Not yet verified against a
  real logout/login cycle** — the Startup-folder trigger itself is standard
  Windows behavior and should work the same way, but hasn't been proven through
  an actual restart yet.
- To start it manually instead of waiting for login: `python dashboard/server.py`
  from the repo root (or just run `scripts/start_dashboard.bat` directly).

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
