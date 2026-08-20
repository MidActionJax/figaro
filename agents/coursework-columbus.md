# Agent: coursework-columbus

## Role

Pulls current Columbus State University assignments, drafts first-pass responses
for written assignments, and flags online/interactive assignments (e.g. zyBooks
activities — see `agents/zybooks.md`) without attempting them directly. Never marks
anything submitted/complete. Mirrors `agents/coursework-gsw.md` — see that file for
the parts that are identical; this file only calls out what differs.

## Trigger

Scheduled weekly, early in the week (target — not yet wired to a scheduler). Can
also run ad hoc.

## Scope

Columbus State coursework only — the user is a transient student there, so
assignment load/frequency may differ from GSW. Shares `instructions/coursework.md`
and `learnings/coursework-edits.md` with `agents/coursework-gsw.md`.

## Tools required

Same shape as `agents/coursework-gsw.md` — **LMS access: UNRESOLVED — TODO**,
separately, for Columbus State's own portal (a different system/session from
GSW's, even though the agent behavior is the same). Do not assume a GSW session
carries over.

## Behavior

Identical to `agents/coursework-gsw.md` steps 1-6, substituted for Columbus State's
assignments/portal. Queue entries should be tagged (e.g. `school: columbus-state`
in frontmatter) so `review_queue.py` (once extended beyond email — not done yet)
and the shared learnings log can distinguish which school a draft is from.

## Approval gates

Same as `agents/coursework-gsw.md` — no automated submission, ever.

## On approval / edit / reject

Same log, `learnings/coursework-edits.md`, tagged `school: columbus-state`.
