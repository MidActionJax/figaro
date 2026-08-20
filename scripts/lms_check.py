"""
Reads a school's D2L Brightspace homepage (courses, announcements, upcoming
calendar events) using the session state saved by scripts/lms_login.py. Runs
headless — no visible window needed to just read, and headed browser launches
aren't reliable in every execution context (confirmed 2026-08-20: a real
"spawn UNKNOWN" failure when launched non-interactively vs. fine when the user
runs it themselves). If the session's expired, this can't show you a login
page (it's headless) — it just says so clearly and tells you to re-run
scripts/lms_login.py <school> yourself, same as the first-time setup.

This is a first pass: it reads the homepage, which already surfaces upcoming
deadlines (Brightspace's calendar widget) and the course list. Going deeper
into each individual course's assignment/dropbox pages to extract per-
assignment due dates is real follow-up work — course page layouts vary enough
that scraping them generically needs iterating against actual course content,
not something to guess at generically here.

Usage:
    python scripts/lms_check.py gsw
    python scripts/lms_check.py colstate
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent

SCHOOLS = {
    "gsw": {"home_url": "https://gsw.view.usg.edu/d2l/home"},
    "colstate": {"home_url": "https://colstate.view.usg.edu/d2l/home"},
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in SCHOOLS:
        sys.exit(f"Usage: python {sys.argv[0]} <{'|'.join(SCHOOLS)}>")

    school = sys.argv[1]
    config = SCHOOLS[school]
    state_file = REPO_ROOT / "sessions" / f"lms_{school}_state.json"

    if not state_file.exists():
        sys.exit(f"No saved session for {school} — run: python scripts/lms_login.py {school}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(state_file))
        page = context.new_page()
        page.goto(config["home_url"])
        page.wait_for_load_state("load")
        # D2L/SSO does a brief client-side redirect dance after "load" fires —
        # checking page.url immediately can catch it mid-redirect and wrongly
        # look like an expired session. A short wait avoids that false negative.
        page.wait_for_timeout(2000)

        if "login.microsoftonline.com" in page.url or "/d2l/login" in page.url:
            browser.close()
            sys.exit(
                f"Session expired for {school}. This runs headless, so "
                f"it can't show you a login page — re-run this yourself instead:\n"
                f"  python scripts/lms_login.py {school}"
            )

        print(f"\n=== {school} homepage content ===\n")
        print(page.inner_text("body"))

        browser.close()


if __name__ == "__main__":
    main()
