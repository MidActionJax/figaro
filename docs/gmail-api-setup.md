# Gmail API setup (one-time, for real sending)

This is separate from the Gmail connector Claude Code already uses for reading/
searching (that keeps working as-is, no change needed). This setup is only for
the mechanical "send this exact reply" step — see `scripts/gmail_api.py` for why
that needed a different mechanism than the rest of the system.

You need to do the Google Cloud Console steps yourself — they require signing in
with your own Google account and granting consent, which isn't something Figaro
does on your behalf.

## 1. Create (or reuse) a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com/).
2. Create a new project (top-left project picker → "New Project"), or use an
   existing one if you already have one you're fine reusing. Name doesn't
   matter — e.g. "figaro".

## 2. Enable the Gmail API

1. In the left sidebar (or search bar), go to **APIs & Services → Library**.
2. Search for "Gmail API" and click **Enable**.

## 3. Configure the OAuth consent screen

1. **APIs & Services → OAuth consent screen**.
2. User type: **External** (unless you have a Google Workspace account and want
   Internal — External is fine and simpler for personal Gmail).
3. Fill in the required fields (app name — e.g. "Figaro" — and your own email for
   support/developer contact). You don't need to fill in optional fields.
4. On the "Test users" step, add your own Gmail address
   (`jaxonjdoolittle@gmail.com`) as a test user. This keeps the app in "Testing"
   mode, which is fine for personal use — you don't need to submit it for
   Google's verification review.

## 4. Create an OAuth Client ID

1. **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. Application type: **Desktop app**.
3. Name it whatever (e.g. "figaro-desktop").
4. Click **Create**, then **Download JSON** on the credential that appears.

## 5. Save the credential file

Save the downloaded JSON as:

```
C:\Users\jaxon\OneDrive\Desktop\Github\figaro\sessions\gmail_client_secret.json
```

This file is already covered by `.gitignore` (everything under `sessions/` is
excluded except `.gitkeep`) — it will never get committed.

## 6. Run the one-time auth flow

```bash
python scripts/gmail_auth_setup.py
```

This opens your browser to Google's consent screen. Sign in, approve the two
requested scopes (send mail, read mail metadata), and it'll save a token to
`sessions/gmail_token.json` — also gitignored. That token auto-refreshes itself
after this; you shouldn't need to redo this step unless you revoke access or the
refresh token expires from long disuse.

## Done

Once `sessions/gmail_token.json` exists, `scripts/gmail_api.py`'s `send_reply()`
will work — the dashboard's Approve/Edit-and-send buttons and
`scripts/review_queue.py`'s approve/edit paths all route through it.
