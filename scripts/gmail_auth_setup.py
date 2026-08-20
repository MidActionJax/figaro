"""
One-time OAuth setup for direct Gmail API sending. Run this yourself — it opens
your browser for you to grant access to your own Google account; that consent
step has to come from you, not from an automated call.

Prerequisite: sessions/gmail_client_secret.json must already exist (downloaded
from Google Cloud Console). See docs/gmail-api-setup.md for how to get it.

Usage:
    python scripts/gmail_auth_setup.py
"""

import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gmail_api import CLIENT_SECRET_FILE, SCOPES, TOKEN_FILE


def main():
    if not CLIENT_SECRET_FILE.exists():
        sys.exit(
            f"{CLIENT_SECRET_FILE} not found. Download it from Google Cloud "
            f"Console first — see docs/gmail-api-setup.md."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    print(f"Saved credentials to {TOKEN_FILE}.")
    print("Gmail API sending is now set up. Test with:")
    print('  python -c "import sys; sys.path.insert(0,\'scripts\'); '
          "import gmail_api; print(gmail_api.send_reply('<thread_id>', 'test'))\"")


if __name__ == "__main__":
    main()
