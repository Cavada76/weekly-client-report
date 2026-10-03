# Weekly Client Report for Claude

Stop writing the Friday status email by hand. Ask Claude to

> write my weekly client report for Acme

and it gathers the week's work from your **git commits**, **time tracking** (Toggl, Clockify, Harvest CSV exports) and your notes, then writes a short, client-ready update: done, in progress, next week, what you need from the client, and hours. You get a Markdown file plus a ready-to-send email.

## Install

**Claude Code**
```
/plugin marketplace add Cavada76/weekly-client-report
/plugin install weekly-client-report@weekly-client-report
```

**Claude.ai / Claude desktop:** download `weekly-client-report-skill.zip` from Releases, then Settings → Capabilities → Skills → Upload, and paste your notes or upload your time export.

## Why it reads well

- Commits become outcomes ("Checkout now supports Vipps"), noise is dropped
- Hours come only from your time data, never guessed
- Saves client, repos and tone in `client-report-profile.json` so next week is one sentence

Python standard library only; `git` for commit history.

MIT licensed.
