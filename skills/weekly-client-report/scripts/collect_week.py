#!/usr/bin/env python3
"""Collect a week's work (git commits + time-tracking exports) as JSON for a client report.

Usage:
    python collect_week.py [--repo PATH ...] [--time-csv FILE ...] [--client NAME]
                           [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--author EMAIL|all]

Defaults: the last 7 days, the current folder as repo (if it is a git repo), and
commits by your own git user.email. Time CSVs from Toggl, Clockify, Harvest and
similar tools are detected by their column names. Standard library only.
"""
import argparse
import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

DURATION_COLS = ("duration (decimal)", "time (decimal)", "hours", "duration (h)", "duration", "time")
DATE_COLS = ("start date", "date", "spent date", "day")
PROJECT_COLS = ("project",)
CLIENT_COLS = ("client",)
DESC_COLS = ("description", "notes", "task", "activity")


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    return result.stdout.strip() if result.returncode == 0 else None


def collect_commits(repo, since, until, author):
    if git(repo, "rev-parse", "--is-inside-work-tree") != "true":
        return None
    if author is None:
        author = git(repo, "config", "user.email")
    args = ["log", "--all", "--no-merges", f"--since={since}T00:00:00",
            f"--until={until}T23:59:59", "--date=short", "--pretty=format:%ad\x1f%an\x1f%s"]
    if author and author != "all":
        args.append(f"--author={author}")
    out = git(repo, *args) or ""
    commits = []
    for line in out.splitlines():
        day, name, subject = (line.split("\x1f") + ["", ""])[:3]
        commits.append({"date": day, "author": name, "subject": subject})
    return {"repo": Path(repo).resolve().name, "author_filter": author or "all", "commits": commits}


def find_col(header, names):
    lowered = {h.strip().lower(): h for h in header}
    for name in names:
        if name in lowered:
            return lowered[name]
    return None


def parse_hours(value):
    value = (value or "").strip()
    if not value:
        return 0.0
    if ":" in value:
        parts = [int(p) for p in value.split(":")]
        while len(parts) < 3:
            parts.append(0)
        h, m, s = parts[:3]
        return h + m / 60 + s / 3600
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return 0.0


def parse_day(value):
    value = (value or "").strip()[:10]
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def collect_time(path, since, until, client):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        reader = csv.DictReader(fh, dialect=dialect)
        header = reader.fieldnames or []
        cols = {k: find_col(header, names) for k, names in (
            ("hours", DURATION_COLS), ("date", DATE_COLS), ("project", PROJECT_COLS),
            ("client", CLIENT_COLS), ("desc", DESC_COLS))}
        if not cols["hours"]:
            return {"file": str(path), "error": f"no duration column found in {header}"}
        by_project = defaultdict(lambda: {"hours": 0.0, "tasks": defaultdict(float)})
        total, skipped = 0.0, 0
        for row in reader:
            day = parse_day(row.get(cols["date"])) if cols["date"] else None
            if day and not (since <= day <= until):
                continue
            haystack = " ".join(str(row.get(cols[k]) or "") for k in ("client", "project"))
            if client and client.lower() not in haystack.lower():
                skipped += 1
                continue
            hours = parse_hours(row.get(cols["hours"]))
            project = (row.get(cols["project"]) if cols["project"] else None) or "(no project)"
            desc = (row.get(cols["desc"]) if cols["desc"] else None) or "(no description)"
            by_project[project]["hours"] += hours
            by_project[project]["tasks"][desc.strip()] += hours
            total += hours
    projects = [{"project": p, "hours": round(v["hours"], 2),
                 "tasks": [{"task": t, "hours": round(h, 2)}
                           for t, h in sorted(v["tasks"].items(), key=lambda x: -x[1])]}
                for p, v in sorted(by_project.items(), key=lambda x: -x[1]["hours"])]
    return {"file": str(path), "total_hours": round(total, 2), "projects": projects,
            "rows_filtered_out_by_client": skipped}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", action="append", default=[], help="Git repo to scan (repeatable)")
    ap.add_argument("--time-csv", action="append", default=[], help="Time-tracking CSV export (repeatable)")
    ap.add_argument("--client", help="Only time entries whose client/project contains this text")
    ap.add_argument("--since", help="Start date YYYY-MM-DD (default: 6 days before --until)")
    ap.add_argument("--until", help="End date YYYY-MM-DD (default: today)")
    ap.add_argument("--author", help="Commit author email, or 'all' (default: your git user.email)")
    args = ap.parse_args()

    try:
        until = date.fromisoformat(args.until) if args.until else date.today()
        since = date.fromisoformat(args.since) if args.since else until - timedelta(days=6)
    except ValueError as exc:
        sys.exit(f"Dates must be YYYY-MM-DD: {exc}")
    if since > until:
        sys.exit("--since must be on or before --until")

    repos = args.repo or (["."] if git(".", "rev-parse", "--is-inside-work-tree") == "true" else [])
    result = {
        "period": {"since": since.isoformat(), "until": until.isoformat(),
                   "iso_week": f"{until.isocalendar()[0]}-W{until.isocalendar()[1]:02d}"},
        "git": [], "time": [], "warnings": [],
    }
    for repo in repos:
        data = collect_commits(repo, since.isoformat(), until.isoformat(), args.author)
        if data is None:
            result["warnings"].append(f"{repo}: not a git repository")
        else:
            result["git"].append(data)
    for path in args.time_csv:
        if not Path(path).is_file():
            result["warnings"].append(f"{path}: file not found")
            continue
        try:
            result["time"].append(collect_time(path, since, until, args.client))
        except (csv.Error, UnicodeDecodeError) as exc:
            result["warnings"].append(f"{path}: could not parse CSV ({exc})")
    if not repos and not args.time_csv:
        result["warnings"].append("no sources: pass --repo and/or --time-csv, or ask the user for notes")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
