# Figaro — Personal Chief-of-Staff Agent System

## Project Overview

Figaro is a personally-built, locally-run multi-agent automation system. It acts as a single point of interaction ("chief of staff") that delegates work to specialized subagents, learns from user corrections over time, and never takes irreversible action (sending, submitting, publishing) without explicit human approval.

**Core philosophy:**
- Figaro coordinates; he does not personally execute domain work.
- Every subagent operates in its own scoped context (its own instructions file, its own tools) so unrelated domains never bleed into each other.
- Nothing is sent, submitted, committed-and-pushed, or marked complete without explicit user approval, *except* where the user has explicitly pre-approved a specific action type.
- The system improves itself: every rejection or edit the user makes is logged and periodically folded back into that subagent's instructions, so accuracy increases over time without the user re-explaining preferences.
- Run entirely on the user's own machine — no paid server/VPS. Scheduling via OS-level task scheduler (Windows Task Scheduler or cron/WSL), not an always-on cloud host.

## User Context (for the agent's own grounding — do not treat as generic defaults)

- Student at GSW; transient student at Columbus State University.
- Working with the CLEAR Center on a NASA project with a recurring task list that changes based on incoming email.
- Checks 4 email accounts each morning: Gmail (personal), University of Michigan, GSW, Columbus State.
- Most GSW/Columbus State coursework is written documents; some is online interactive tasks (e.g. zyBooks participation activities).
- GSW and Columbus State portals require MFA — full headless login automation is not reliable; system should support persistent authenticated sessions with manual re-auth as fallback.
- Has an existing library of past coursework files that should be used to ground tone/format for new drafts.
- Longer-term goal (not in initial build scope): once schoolwork/NASA automation is stable, extend the same pattern to a small B2B outreach business (contacting SBIR Phase 2 award winners about contract rates). Business does not exist yet — do not build this layer until explicitly requested.

## High-Level Architecture

```
figaro/
├── CLAUDE.md                  # Master context file, read by every session
├── agents/                    # One definition file per subagent
│   ├── email-triage.md
│   ├── coursework-gsw.md
│   ├── coursework-columbus.md
│   ├── nasa-clear.md
│   ├── zybooks.md
│   └── _template.md           # Used when Figaro creates a new agent on demand
├── instructions/               # Per-domain behavioral rules, self-updating
│   ├── email-triage.md
│   ├── coursework.md
│   ├── nasa-clear.md
│   └── zybooks.md
├── learnings/                  # Raw logs of every rejection/edit, per domain
│   ├── email-rejections.md
│   ├── coursework-edits.md
│   └── nasa-notes.md
├── dashboard/                  # Local web app — approval queue + chat interface
│   ├── server.py               # or Node equivalent
│   └── static/
├── scripts/
│   ├── morning_email_run.py    # Cron/Task Scheduler entry point
│   ├── weekly_coursework_run.py
│   └── consolidate_learnings.py  # Monthly rewrite of instructions from learnings
├── sessions/                    # Auth/session persistence for browser-based agents
│   └── (stored cookies/session state per portal)
└── data/
    └── old-coursework/          # User's existing files, used for tone grounding
```

## Engine / Tooling Choices

- **Primary execution engine:** Claude Code in headless mode (`claude -p`), invoked from Python scripts. This gives file access, shell/git access, and structured JSON output without an interactive terminal.
- **Browser/desktop-interactive tasks** (zyBooks, portal navigation): a separate subagent using computer-use tooling (Claude's computer-use capability via the Agent SDK, or Claude in Chrome), invoked directly from the same orchestration scripts — not via the Cowork desktop app, which currently has no API/programmatic bridge.
- **Do not attempt to integrate with the Cowork app directly.** Cowork and Claude Code are isolated products with no documented bridge as of this writing. All "cowork-style" browser/desktop capability should be built with direct computer-use tools instead.
- **Scheduling:** OS-native (Windows Task Scheduler or cron under WSL/Linux). Use a wake timer if early-morning runs are desired; alternatively trigger on user login/unlock as a more reliable fallback.
- **Version control:** the whole `figaro/` directory is a git repo. Every instruction-file update, every learning-log append, and every commit Figaro makes to other projects (e.g. NASA repo) should be tracked, giving a full audit trail.
- **Dashboard:** a lightweight local web app (Flask/FastAPI + simple frontend, or similar), bound to localhost, exposed via a bookmarkable URL the user can hit from their phone on the same network. Two primary views:
  1. **Approval queue** — pending drafts/actions, each with Approve / Edit / Reject.
  2. **Chat with Figaro** — free-text box for ad hoc commands ("go find out X," "handle Y with NASA").

## Subagent Specifications

### 1. Email Triage Agent
- **Trigger:** scheduled daily (target: early morning, adjustable).
- **Scope:** reads all 4 inboxes (IMAP or provider API where available).
- **Behavior:**
  1. Read `instructions/email-triage.md` and the tail of `learnings/email-rejections.md` before drafting anything.
  2. Classify incoming mail as important/not important.
  3. For important mail, draft a reply in the user's voice.
  4. Write all drafts to the approval queue. **Send nothing automatically.**
- **On approval:** send as-is.
- **On edit:** send edited version; log the diff + a short natural-language summary of what changed to `learnings/email-rejections.md`.
- **On reject:** do not send; log the reason (if given) or a best-guess reason to `learnings/email-rejections.md`.

### 2. Coursework Agents (GSW / Columbus State)
- **Trigger:** scheduled weekly, early in the week.
- **Scope:** pulls current assignments (via LMS API if available — check for Canvas/Blackboard API tokens first, before resorting to browser scraping), reads assignment requirements and any linked material, drafts a first-pass response for written assignments.
- **Behavior:**
  1. Cross-reference this week's assignments against recent emails for any changes/updates.
  2. Separate assignments into "written doc — can draft" vs. "online/interactive — flag only, do not attempt."
  3. Use `data/old-coursework/` for tone and formatting grounding.
  4. Produce a first-pass draft per written assignment; queue for approval. **Never mark complete or submit automatically.**
- **On edit/reject:** log what was wrong (structure, tone, missed requirement, etc.) to `learnings/coursework-edits.md`.
- **Auth:** use a persistent authenticated browser session (saved after manual login) rather than automating MFA. If the session is invalid/expired, flag it clearly rather than failing silently or attempting credential guesses.

### 3. Salsbergs — General Coding Agent
Salsbergs is Figaro's general-purpose coding specialist — the subagent that handles any task requiring real code/git work. He should be instructed and framed as the most senior-level engineer in the system: expected to write production-quality code, exercise strong independent judgment on implementation decisions, follow good engineering practices (clear commits, sensible structure, not just "make it work"), and flag genuine ambiguity rather than guessing on anything consequential. He is not NASA-exclusive by design; he currently operates on the NASA/CLEAR codebase because that's the primary coding-heavy workload right now, but should be built so any future coding task (including eventual business tooling) can be routed to Salsbergs rather than spinning up a separate coding agent.
*(backing files: `agents/nasa-clear.md` and `instructions/nasa-clear.md` for now — may be generalized to `agents/coding.md` if/when a second coding workload is added)*
- **Trigger:** ad hoc, invoked via the dashboard chat (e.g., "go handle X with NASA").
- **Scope:** operates directly inside the user's **existing** NASA/CLEAR codebase/repo — do not scaffold a new repo. This existing repo already contains substantial project context (prior code, structure, conventions) that the agent should read and work within, not duplicate or replace. The exact repo path/location should be confirmed with the user during Phase 0 setup and configured accordingly. The agent has git/`gh` CLI tools scoped to this repo.
- **Behavior:**
  1. Maintains and updates the NASA task list, checked weekly against new emails for changes.
  2. On a specific ad hoc request, completes the requested work and prepares the changes.
  3. Presents a summary of the completed work (diff/changes) to the dashboard approval queue. **Does not commit or open a PR automatically.**
  4. On approval, commits the changes and opens the pull request, then reports back with the PR link.
  5. On reject, holds the work for the user to review/discuss further without committing anything.
- **Approval model:** even though the task itself is user-triggered ("go do X"), the commit + PR step is a separate, explicit approval gate — the agent completing the work does not imply authorization to commit/push it.

### 4. zyBooks / Interactive Coursework Agent
- **Trigger:** part of the weekly coursework pass, or ad hoc.
- **Scope:** browser/computer-use capable — navigates zyBooks, completes participation activities.
- **Important constraint:** before enabling this agent to actually complete graded participation activities, the user should confirm this doesn't violate their school's academic integrity policy. Build this agent's read/summarize capabilities first (e.g., "tell me what's due") and gate the "actually click through and complete" capability separately.
- **Auth:** same persistent-session pattern as coursework agents.

### 5. Meta-Agent Creation (Figaro's own capability)
- **Trigger:** whenever a user request doesn't map to an existing agent/instruction file.
- **Behavior:**
  1. Figaro recognizes no existing agent covers the request.
  2. Drafts a new agent definition (using `agents/_template.md` as a starting structure) — name, scope, required tools, starter instructions.
  3. **Surfaces this to the user for approval before granting any sensitive tool access** (sending, git push, browser control, credentials).
  4. On approval, saves the new agent file and hands off the current task to it.
  5. The new agent persists for future use.

## The Learning Loop (core differentiator)

1. Every domain has a `learnings/*.md` file that accumulates raw entries: what was drafted, what the user did (approve/edit/reject), and why (explicit reason if given, inferred pattern if not).
2. A monthly (or every-N-entries) consolidation job (`scripts/consolidate_learnings.py`) reads the accumulated raw entries for a domain and **rewrites** that domain's `instructions/*.md` file to reflect the patterns found — not just appending forever.
3. This keeps each instructions file lean (a set of current rules) while `learnings/` serves as the historical record/audit trail.
4. Every subagent reads its instructions file at the start of every run, before doing any work.

## Approval & Safety Rules (apply globally)

- No email is sent without approval (edit counts as implicit approval to send the edited version).
- No assignment is marked submitted/complete without user action.
- No new agent gets sensitive tool access (send, push, browser control) without explicit approval.
- No NASA/CLEAR work is committed or turned into a pull request without explicit approval — the agent may complete the work and prepare changes ad hoc, but committing/opening a PR is always a separate, gated step.
- zyBooks/graded-activity completion is gated separately from read/summarize access, pending the user's confirmation on academic integrity policy.

## Runtime / Background Execution Requirement

The system must run without requiring the user to keep a terminal window open. It should start automatically on machine startup and run silently in the background.

**Development/beta phase:** run directly from Python source (no packaging step). Use a background service approach even at this stage so testing reflects real usage:
- **Windows:** background service (e.g. via NSSM) or Task Scheduler with an "At startup" trigger and "Run whether user is logged on or not"; launch with `pythonw.exe` (not `python.exe`) so no console window appears.
- **Linux/WSL (if applicable):** a `systemd` user/system service — starts on boot, runs in background, restarts on failure.

**Production packaging (once the core loop is stable):** package into a single `.exe` using PyInstaller (`pyinstaller figaro.py --onefile --noconsole`). This is a one-command build step, not a rewrite. To keep re-packaging rare and painless:
- All frequently-changed content — `instructions/*.md`, `learnings/*.md`, `agents/*.md`, and any config — must be **external files read at runtime**, never baked into the packaged executable. Editing behavior (tweaking instructions, adding a new agent definition) should never require rebuilding the exe.
- Only genuine code/logic changes require rerunning the PyInstaller build.
- The background service/startup task should point at the packaged `.exe` once it exists; swapping in a newly-built exe is just replacing the file the service points to.

The dashboard remains reachable at all times via its local URL in a browser regardless of dev or production mode; the user should never need to open a terminal for day-to-day use, only for initial setup, active development, or troubleshooting.

## Build Order (recommended phases)

1. **Phase 0 — Foundation:** repo scaffold, git init, Claude Code + Agent SDK setup, task scheduler configured, old coursework files imported into `data/`.
2. **Phase 1 — Email triage:** full loop working (draft → approval queue → send/edit/reject → learnings log). Run for 1–2 weeks before proceeding.
3. **Phase 2 — Weekly coursework pass:** LMS access resolved (API preferred, persistent session fallback), draft generation, approval loop, learnings log.
4. **Phase 3 — NASA/CLEAR agent:** repo access, git/PR workflow, ad hoc dashboard trigger.
5. **Phase 4 — zyBooks agent:** browser/computer-use subagent, read-only first, completion capability gated behind explicit user go-ahead.
6. **Phase 5 — Figaro dispatcher + meta-agent creation:** routing logic across all subagents, ad hoc request handling, new-agent creation with approval gating, monthly learnings consolidation.
7. **Later, on request only:** business-outreach agent for the SBIR B2B work, following the same instructions/learnings/approval pattern established above.

## What to build first if starting fresh

Start with Phase 0 + Phase 1 only. Do not build Phases 2–5 until the email triage loop has been running successfully for at least a week and the approval/learning mechanism has proven itself trustworthy in practice.
