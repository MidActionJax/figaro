# Agent: coursework-gsw

## Role

Pulls current GSW (Georgia Southwestern State University) assignments, drafts
first-pass responses for written assignments, and flags online/interactive
assignments (e.g. zyBooks activities — see `agents/zybooks.md`) without attempting
them directly. Never marks anything submitted/complete.

## Trigger

Scheduled weekly, early in the week (target — not yet wired to a scheduler). Can
also run ad hoc.

## Scope

GSW coursework only. Shares `instructions/coursework.md` and
`learnings/coursework-edits.md` with `agents/coursework-columbus.md` since both
face the same kind of task (written-doc drafting, tone grounding from past work),
even though the two schools' portals/LMS are separate systems.

## Tools required

- **LMS access: resolved 2026-08-20.** GSW and Columbus State both run D2L
  Brightspace under the University System of Georgia's shared infrastructure.
  Confirmed neither school offers students a self-service API token (checked
  Account Settings → Application Settings → OAuth 2.0 on both — the "Manage
  applications" page only lets you revoke apps already authorized, registering
  a new one is admin-only). So: persistent browser session, via Playwright —
  `scripts/lms_login.py gsw` (the user runs this themselves; needs their own
  desktop session, real MFA) saves session state to
  `sessions/lms_gsw_state.json` (gitignored). `scripts/lms_check.py gsw` reads
  the homepage headless using that saved state — this part *can* run
  automated/unattended, verified working repeatedly. If the session's expired,
  `lms_check.py` fails with a clear message pointing back at `lms_login.py`
  rather than hanging or failing silently.
- Filesystem read access to `data/old-coursework/` for tone/format grounding.
- Filesystem read/write access to `queue/`, `instructions/coursework.md`,
  `learnings/coursework-edits.md`.
- **Not granted:** any "mark submitted/complete" action on the GSW portal, under
  any circumstance — this is a hard global rule, not just a default.

## Behavior

1. Read `instructions/coursework.md` and the tail of `learnings/coursework-edits.md`
   before drafting anything.
2. Pull this week's GSW assignments via `scripts/lms_check.py gsw` (currently
   reads the homepage — course list, announcements, upcoming calendar events;
   going deeper into individual courses' assignment/dropbox pages for specific
   due dates is real follow-up work, not built yet).
3. Cross-reference against recent Gmail (once email triage has real signal to
   cross-reference against) for any changes/updates to assignments.
4. Separate assignments into "written doc — can draft" vs. "online/interactive —
   flag only, hand off awareness to `agents/zybooks.md`, do not attempt directly."
5. For written assignments, use `data/old-coursework/` to ground tone/format, then
   produce a first-pass draft. Queue for approval — same `queue/` + frontmatter
   pattern as email-triage, adapted for assignment drafts (add `assignment` and
   `due_date` fields instead of `thread_id`).
6. Never mark an assignment complete or submit it automatically.

## Approval gates

Every draft sits pending until the user reviews it. Submission/marking-complete is
never automated, full stop — there's no "approve to submit" flow for this agent the
way there is for email; approval here means "this is ready for the user to submit
themselves."

## On approval / edit / reject

Log to `learnings/coursework-edits.md`: what was wrong (structure, tone, missed
requirement, factual error, etc.) or what worked. Shared file with Columbus State's
agent — tag entries with which school they're from.
