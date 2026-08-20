# Learnings: email-rejections

Raw log, one entry per approve/edit/reject event, oldest first. Appended by
`scripts/review_queue.py`. Periodically consolidated into
[instructions/email-triage.md](../instructions/email-triage.md) by
`scripts/consolidate_learnings.py` — do not hand-prune this file, the consolidation
job is what keeps it from growing unbounded in influence (raw history stays here for
audit purposes even after consolidation).

## Entry format

```
### YYYY-MM-DD-HHMMSS <slug>
- action: approve | edit | reject
- subject: <subject line>
- reason: <user-given reason, or "not given">
- diff/summary: <for edits, a short natural-language summary of what changed>
```

---

### 2026-08-20-162723 Coffeee
- action: reject
- subject: Coffeee
- reason: we dont need to respond to these coffee things
