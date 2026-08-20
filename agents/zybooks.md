# Agent: zybooks

## Role

Browser/computer-use capable agent for zyBooks: summarizing what's due (read-only)
and, once armed, actually completing participation activities. Academic-integrity
question is resolved — the user confirmed (2026-08-20) that automating zyBooks
participation-activity completion doesn't violate GSW/Columbus State policy. That
clears the *policy* blocker; the *tool-grant* gate below is separate and still
applies, per the global rule that no agent gets browser/computer-use control
without explicit approval.

## Trigger

Part of the weekly coursework pass (flagged by `agents/coursework-gsw.md` /
`agents/coursework-columbus.md`), or ad hoc ("what's due on zyBooks").

## Scope

zyBooks only. Read/summarize is available now. Completion capability is
documented here but **not yet armed** — see Tools required.

## Tools required

- **Read/summarize (available now):** browser/computer-use tooling, read-only —
  navigate to zyBooks, read assignment/activity listings and due dates, do not
  interact with any activity content.
- **Completion (documented, not yet armed):** the same browser/computer-use
  tooling with permission to actually click through and complete participation
  activities. Even though the academic-integrity question is settled, granting
  live click/type/submit control to an agent is exactly the kind of sensitive
  tool grant the global rules require explicit approval for — and completing a
  graded participation activity is hard to cleanly undo. **Before the first real
  completion run:** confirm with the user, in the moment, that this specific run
  should proceed — a standing "policy is fine" answer authorizes building the
  capability, not running it unsupervised the first time.
- **Auth:** persistent authenticated browser session (saved after manual login),
  same pattern as the coursework agents — GSW/Columbus State MFA rules out
  reliable headless login. If the session is invalid/expired, flag clearly rather
  than failing silently or attempting credential guesses.

## Behavior

**Read/summarize mode (default):**
1. Read `instructions/zybooks.md` before doing anything.
2. Use the saved session in `sessions/` to navigate to zyBooks (flag clearly if no
   valid session exists — do not attempt fresh login).
3. Read what's due, by when, and current completion status.
4. Report back — this is enough for "what's due" style requests; no queue entry
   needed unless the user wants it tracked alongside coursework drafts.

**Completion mode (once armed for a specific run):**
1. All of the above, plus: for the specific activity(ies) the user has asked to be
   completed, click through and complete them.
2. Report back exactly what was completed, so there's a record even though
   there's no "approval queue" step before the action (the approval already
   happened by the user asking for this specific run).

## Approval gates

- Read/summarize: no gate, always available.
- Completion: gated per-run as described above, not just at build time.

## On approval / edit / reject

Not really applicable in the approve/edit/reject sense (no draft is produced) —
if a completion run goes wrong (wrong activity, mis-clicked something), log what
happened to a new `learnings/zybooks-notes.md` if this becomes a recurring need;
not created yet since it doesn't exist until there's a first real entry to put in
it.
