"""
Figaro dashboard: local web app with two views on one page — approval queue and
chat with Figaro. Binds to 127.0.0.1 only by default; see --host if you want LAN
access (e.g. from your phone), but that has no authentication yet, so don't expose
it beyond a trusted home network without adding some first.

Usage:
    python dashboard/server.py [--port 5151] [--host 127.0.0.1]

Queue send/approve/reject mechanics live in scripts/queue_lib.py, shared with
scripts/review_queue.py (the terminal equivalent) so the two UIs can't drift apart
on what "approve" actually does.

Chat is intentionally read-only (Read tool only, no Bash/Write/Edit/MCP tools) —
it can answer questions about the repo, queue state, and learnings, but it cannot
take actions. Building an action-taking dispatcher across all subagents is Phase 5,
deliberately not started yet (see CLAUDE.md) — this chat box is not that.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, jsonify

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import queue_lib as ql

REPO_ROOT = Path(__file__).resolve().parent.parent

# Salsbergs/NASA session-continuity target — see agents/nasa-clear.md "Session
# continuity". Chat questions about this work should be answered from that real
# session's context, not from Figaro's own repo (which knows nothing about it).
AWSRT_DIR = REPO_ROOT.parent / "AWSRT"
AWSRT_SESSION_ID = "6134fed2-8d6f-41dd-9b77-78158c7d239e"
NASA_KEYWORDS = [
    "nasa", "awsrt", "clear repo", "clear project", "pleiades", "igor",
    "salsbergs", "swmf", "magnetogram", "heartbeat", "smart-petsc",
    "space weather", "sofie",
]

app = Flask(__name__)


def is_nasa_related(message: str) -> bool:
    lowered = message.lower()
    return any(kw in lowered for kw in NASA_KEYWORDS)


def learnings_tail(n_entries: int = 5) -> str:
    if not ql.LEARNINGS_FILE.exists():
        return "(learnings/email-rejections.md not found)"
    text = ql.LEARNINGS_FILE.read_text(encoding="utf-8")
    # First chunk is the file's header/format docs, not a real entry.
    real_entries = text.split("\n### ")[1:]
    tail = ["### " + e.strip() for e in real_entries[-n_entries:]]
    return "\n\n".join(tail) if tail else "(no entries yet)"


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/")
def index():
    pending = []
    for path in ql.list_pending():
        meta, body = ql.parse_draft(path)
        pending.append({
            "filename": path.name,
            "subject": meta.get("subject", "?"),
            "from": meta.get("from", "?"),
            "received": meta.get("received", "?"),
            "body": body.strip(),
            "has_thread_id": bool(meta.get("thread_id")),
        })
    return render_template("index.html", pending=pending, recent_learnings=learnings_tail())


@app.route("/queue/<filename>/approve", methods=["POST"])
def approve(filename):
    path = ql.QUEUE_DIR / filename
    if not path.exists():
        return redirect(url_for("index"))
    ok, _msg = ql.approve_draft(path)
    return redirect(url_for("index", sent="1" if ok else "0"))


@app.route("/queue/<filename>/edit", methods=["POST"])
def edit(filename):
    path = ql.QUEUE_DIR / filename
    if not path.exists():
        return redirect(url_for("index"))
    edited_body = request.form.get("body", "")
    summary = request.form.get("summary", "")
    ok, _msg = ql.send_edited_draft(path, edited_body, summary)
    return redirect(url_for("index", sent="1" if ok else "0"))


@app.route("/queue/<filename>/reject", methods=["POST"])
def reject(filename):
    path = ql.QUEUE_DIR / filename
    if not path.exists():
        return redirect(url_for("index"))
    reason = request.form.get("reason", "")
    ql.reject_draft(path, reason)
    return redirect(url_for("index"))


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"reply": ""})

    # Question-first framing matters here: an earlier version led with several
    # sentences of persona/instructions before the actual question, and the model
    # consistently treated that as unfinished system setup rather than a live
    # question to answer, replying "I don't see a question yet" even though it was
    # right there. Leading with the question and keeping the framing short after it
    # fixed this reliably in testing (2026-08-20).
    read_only_note = (
        "(Read-only lookup - you can't write, edit, send, or take actions here. "
        "If the question asks for an action, say so and point to the right "
        "terminal command or interactive session instead.)"
    )

    if is_nasa_related(message):
        # Route to the real AWSRT session instead of Figaro's own repo, which has
        # no visibility into NASA/Salsbergs work at all. Same mechanism verified
        # for Salsbergs in agents/nasa-clear.md "Session continuity".
        prompt = f"Answer this question, using the Read tool to look things up: {message}\n\n{read_only_note}"
        cmd = [ql.CLAUDE_BIN, "--resume", AWSRT_SESSION_ID, "-p", prompt,
               "--allowedTools", "Read", "--output-format", "text"]
        cwd = AWSRT_DIR
        source = "awsrt"
    else:
        prompt = (
            f"Answer this question about the Figaro repo, using the Read tool to "
            f"look things up: {message}\n\n{read_only_note}"
        )
        cmd = [ql.CLAUDE_BIN, "-p", prompt,
               "--allowedTools", "Read", "--output-format", "text"]
        cwd = REPO_ROOT
        source = "figaro"

    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=120
        )
    except subprocess.TimeoutExpired:
        return jsonify({
            "reply": "Timed out after 120s waiting for a response — try a narrower question, "
                     "or this may be the same permission-wall behavior documented in "
                     "scripts/morning_email_run.py if the question needed a tool call that stalled.",
            "source": source,
        })
    except Exception as e:
        return jsonify({"reply": f"Error running the lookup: {e}", "source": source})

    if result.returncode != 0:
        detail = (result.stdout.strip() or result.stderr.strip() or "no output")
        return jsonify({"reply": f"Lookup failed (exit {result.returncode}): {detail}", "source": source})

    reply = result.stdout.strip() or "(no response)"
    return jsonify({"reply": reply, "source": source})


def main():
    parser = argparse.ArgumentParser(description="Run the Figaro dashboard.")
    parser.add_argument("--port", type=int, default=5151)
    parser.add_argument("--host", default="127.0.0.1",
                         help="Use 0.0.0.0 for LAN access (e.g. from your phone) — "
                              "no auth exists yet, only do this on a trusted network.")
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
