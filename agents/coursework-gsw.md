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

- **LMS access: UNRESOLVED — TODO.** Neither a Canvas/Blackboard API token nor a
  persistent authenticated browser session has been set up for GSW yet. Do not
  attempt browser automation against a live MFA-protected portal without a saved
  session already in place; check `sessions/` first and flag clearly (per the
  global "flag clearly rather than fail silently" rule) if nothing usable is there.
- Filesystem read access to `data/old-coursework/` for tone/format grounding.
- Filesystem read/write access to `queue/`, `instructions/coursework.md`,
  `learnings/coursework-edits.md`.
- **Not granted:** any "mark submitted/complete" action on the GSW portal, under
  any circumstance — this is a hard global rule, not just a default.

## Behavior

1. Read `instructions/coursework.md` and the tail of `learnings/coursework-edits.md`
   before drafting anything.
2. Pull this week's GSW assignments (method TBD — see Tools required).
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
