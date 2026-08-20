# Agent: {{name}}

*(Copy this file to `agents/{{name}}.md` when creating a new subagent. Fill in every
section. Do not grant sensitive tools — send, push, browser control, credentials —
without the user explicitly approving that grant first; see
[docs/figaro-project-spec.md](../docs/figaro-project-spec.md) §5, Meta-Agent Creation.)*

## Role

One paragraph: what this agent is responsible for, and what it is explicitly *not*
responsible for.

## Trigger

Scheduled (cron/Task Scheduler) or ad hoc (dashboard/CLI request)? If scheduled, how
often?

## Scope

What files, repos, inboxes, or systems can this agent touch? Be specific — this is
also the boundary that keeps this domain from bleeding into others.

## Tools required

List each tool/MCP server this agent needs and why. Flag anything sensitive
(send-capable, push-capable, browser/computer-use, credential access) explicitly —
these require the approval step above before this file is considered "live."

## Behavior

Step-by-step, in the order the agent should actually execute:

1. Read `instructions/{{name}}.md` and the tail of `learnings/{{name}}-*.md` before
   doing anything else.
2. ...

## Approval gates

What does this agent draft/prepare vs. what requires explicit user approval before
it happens? Be explicit — "prepares X, never does Y without approval."

## On approval / edit / reject

How does user feedback get logged back to `learnings/{{name}}-*.md`? What's the
raw entry format?
