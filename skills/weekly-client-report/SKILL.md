---
name: weekly-client-report
description: Weekly client report. Use when the user says "write my weekly client report", "weekly status update for my client", "weekly report", "client update email", "what did I do this week", "summarize this week's work for the client", or "weekly progress report". Gathers the week's work from git commits, time-tracking exports (Toggl, Clockify, Harvest CSV) and the user's notes, then writes a short, client-ready report - done, in progress, next week, blockers, hours - as a Markdown file plus a ready-to-send email.
---

# Weekly Client Report

Clients don't read commit logs. Turn a week of raw activity into a 1-minute read that shows progress and makes the next step obvious.

## Steps

1. **Pin down the basics** from the request or conversation (ask once, briefly, only for what's missing):
   - client name (and which project/repo is theirs)
   - period: default the last 7 days ending today; "this week" on a Friday means Monday–today
   - sources: git repo(s), a time-tracking CSV, and/or notes the user pastes
   - **Reuse settings:** if `client-report-profile.json` exists in the current folder, read client, repos, CSV path, tone and recipients from it. After the first report, offer to save one.
2. **Collect** (from this skill's folder; standard library only, needs `git` on PATH for repos):
   ```bash
   python scripts/collect_week.py --repo "path/to/repo" --time-csv "toggl.csv" --client "Acme" --since 2026-09-28 --until 2026-10-03
   ```
   `--author all` includes teammates' commits. Several `--repo` / `--time-csv` flags are fine. If the user has no repo or CSV, skip the script and work from their notes.
3. **Translate activity into outcomes.** Group commits and time entries by feature or goal, not by day. Write in the client's language: "Checkout now supports Vipps" instead of "feat(pay): add vipps adapter". Drop noise (typo fixes, merges, refactors) unless it explains a delay. Never claim something is done that the data shows as in progress.
4. **Write the report** using this structure (keep it under ~250 words unless asked otherwise):

   ```markdown
   # Weekly update – {Client} – week {NN} ({date range})

   **Summary:** one or two sentences: the main progress and whether we're on track.

   ## Done this week
   - outcome-focused bullet (max 6)

   ## In progress
   - item – expected done {day/date}

   ## Next week
   - planned item

   ## Needs from you
   - decision / access / feedback needed, with a date if it blocks us  (omit section if none)

   ## Hours
   {total} h this week · breakdown by project/task if from time tracking  (omit if no time data)
   ```
5. **Save** as `weekly-report-{client-slug}-{YYYY}-W{NN}.md` in the current folder (or where the user asked), and show an **email version** in the reply: subject line + the same content as plain text with a friendly one-line opener and sign-off.
6. **Ask nothing more** unless something important was ambiguous; offer a .docx/PDF version or a shorter Slack version in one line.

## Rules

- Hours come only from time-tracking data or the user. Never estimate hours from commits.
- Keep internal details out (other clients' names, internal tickets, profanity in commit messages, secrets in diffs).
- Match the tone of earlier reports if the user shares one; otherwise friendly, confident, plain English (or the user's language).
