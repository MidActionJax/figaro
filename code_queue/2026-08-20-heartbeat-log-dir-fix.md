---
status: pending
repo_name: CLEAR
repo_path: C:/Users/jaxon/OneDrive/Desktop/Github/CLEAR
base_branch: jax
new_branch: fix/heartbeat-log-dir
files: RealTimeSW/heartbeat_check.sh
pr_title: Fix heartbeat_check.sh dying when log directory doesn't exist yet
---
## Summary

`heartbeat_check.sh`'s log directory wasn't guaranteed to exist. Under
`set -euo pipefail`, if it didn't (first deployment before
`heartbeat_write.sh` has ever run, or a transient mount issue), the first
`log()` call inside `send_alert()` would fail via `tee` and kill the entire
monitoring loop — dying exactly at the moment it was trying to report the
outage it exists to catch.

**Fix:** added `mkdir -p "$(dirname "$LOGFILE")"` right after `LOGFILE` is
computed, so the log directory is guaranteed to exist from script startup,
not created lazily on first use.

## Test plan

- [x] Reproduced the bug: sourced the pre-fix code against a missing log
      directory, confirmed it died with `tee: ... No such file or directory`,
      exit code 1, never reaching the lines after the failure.
- [x] Confirmed the fix: same missing-directory scenario against the patched
      script, `do_check()` returned exit code 0, correctly logged the alert,
      and the directory existed afterward.
- [x] Full regression suite (`test_heartbeat_check.sh`, all four original
      scenarios) still passes against the fixed script.
