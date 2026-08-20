# Instructions: nasa-clear

*Rewritten periodically from `learnings/nasa-notes.md` as real patterns emerge —
currently a lean starting point with no consolidated learnings yet.*

## Engineering standards

- Match each repo's existing conventions (commit style, code structure, build
  system) rather than importing habits from elsewhere. AWSRT and CLEAR are
  different codebases with different conventions — don't assume one's patterns
  apply to the other.
- Prefer editing existing files/patterns to introducing new abstractions, unless
  the task genuinely calls for something new.
- Write commit messages that explain why, not just what.
- Flag genuine ambiguity (unclear requirements, a design decision with real
  tradeoffs) rather than silently picking an approach and hoping it's right.

## Things not to do

- Do not commit or push without going through the approval gate in
  `agents/nasa-clear.md`, regardless of how the task itself was triggered.
- Do not assume CLEAR's build/install process works like a standalone repo — it
  installs into a parent SWMF directory via `make install`/`make uninstall`. Check
  `CLEAR/README.md` before assuming otherwise.
- Do not scaffold a new repo for a task that belongs in AWSRT or CLEAR.
