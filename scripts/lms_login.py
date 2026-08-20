"""
Opens a real, visible browser window against a school's D2L Brightspace portal.
Log in (MFA included), then press Enter in THIS terminal once you're actually
looking at the school's homepage (course tiles) — not right after the
Microsoft login step. That timing matters: closing right after Microsoft auth
but before the SAML redirect back to D2L finishes means D2L's own session
cookie never gets set, even though it looks like you're "done." Confirmed by
two failed attempts (2026-08-20) where cookies existed for Microsoft's SSO
domains but never for the school's own domain.

Session state is captured explicitly via Playwright's storage_state export at
the moment you press Enter — not relied on implicitly from the browser
profile directory, which turned out to have its own persistence quirks with
this SSO flow (session-lifetime cookies not surviving between browser
launches even in a "persistent" profile).

Usage:
    python scripts/lms_login.py gsw
    python scripts/lms_login.py colstate
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent

SCHOOLS = {
    "gsw": {
        "login_url": "https://login.microsoftonline.com/e21eed1c-1f72-4ad4-84ab-a7ae53ab95c2/saml2?SAMLRequest=jdE9a8MwEAbgvdD%2fYLRbclTZsoUdCO0SSJek7dClKPLFMdiSq5OT%2fvwqDaEdu90HLzzc1as5HO0WPmfAkKyfGoJ6HPy1%2fxB5LkFoaUSZi8WhrAqpNdcLU0Fm%2bD4jyRt47J1tCKexWyPOsLYYtA1xlPEizcqUZy88U3mlFoLKUkjJxTtJVojgQ8w%2bOovzCH4H%2ftQbeN1uGnIMYULFWIdneurhTGfsKLQza%2fnAhonpqGaD63rLLt7NpaJxR5KvcbDYkNlb5TT2qKweAVUward63qjIVJN3wRk3kOX9XZLUP2j%2fn6C%2bkcnyBmwreeCyeEgzXkEq9tykOi9kKlojBEBhAEoawMaDIN37vjsGnLQBatz4S6%2fZFRFBNfv7keU3&RelayState=%2fd2l%2fhome",
    },
    "colstate": {
        "login_url": "https://colstate.view.usg.edu/d2l/home",
    },
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in SCHOOLS:
        sys.exit(f"Usage: python {sys.argv[0]} <{'|'.join(SCHOOLS)}>")

    school = sys.argv[1]
    config = SCHOOLS[school]
    state_file = REPO_ROOT / "sessions" / f"lms_{school}_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(config["login_url"])

        print(
            "Log in (including MFA) in the window that just opened. "
            "IMPORTANT: wait until you actually SEE the school's homepage "
            "(course tiles, not the Microsoft sign-in page) before doing "
            "anything here. Once you're looking at the real homepage, come "
            "back to this terminal and press Enter."
        )
        input()

        context.storage_state(path=str(state_file))
        browser.close()

    print(f"Session saved to {state_file}.")


if __name__ == "__main__":
    main()
