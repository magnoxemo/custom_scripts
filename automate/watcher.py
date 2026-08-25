#!/usr/bin/env python3

import argparse
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta

STATE_DIR = os.environ.get("SLURM_WATCHER_DIR", os.path.expanduser("~/.slurm_watcher"))
STATE_FILE = os.path.join(STATE_DIR, "state.json")
ACTIVITY_LOG = os.path.join(STATE_DIR, "activity.log")
FAILED_LOG = os.path.join(STATE_DIR, "failed_jobs.log")
ERROR_LOG = os.path.join(STATE_DIR, "watcher_errors.log")

USER = os.environ.get("USER") or getpass.getuser()

TERMINAL_STATES = {
    "COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL",
    "OUT_OF_MEMORY", "PREEMPTED", "BOOT_FAIL", "DEADLINE", "REVOKED",
}
FAILURE_STATES = TERMINAL_STATES - {"COMPLETED"}


def parse_slurm_time(s):
    """Parse a squeue/sacct time-ish string into seconds. Returns None
    for unbounded/unknown values (UNLIMITED, NOT_SET, INVALID, empty)."""
    if not s:
        return None
    s = s.strip()
    if s in ("UNLIMITED", "NOT_SET", "INVALID", "N/A", ""):
        return None
    days = 0
    if "-" in s:
        day_part, s = s.split("-", 1)
        days = int(day_part)
    parts = s.split(":")
    parts = [int(p) for p in parts]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, sec = parts[-3], parts[-2], parts[-1]
    return days * 86400 + h * 3600 + m * 60 + sec


def seconds_to_str(total):
    if total is None:
        return "-"
    sign = "-" if total < 0 else ""
    total = abs(int(total))
    d, rem = divmod(total, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return f"{sign}{d}-{h:02d}:{m:02d}:{s:02d}"
    return f"{sign}{h:02d}:{m:02d}:{s:02d}"


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# state persistence
# --------------------------------------------------------------------------

def ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_poll": None, "jobs": {}}
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    ensure_state_dir()
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    os.replace(tmp, STATE_FILE)


def log_line(path, line):
    ensure_state_dir()
    with open(path, "a") as f:
        f.write(f"[{now_iso()}] {line}\n")

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def query_squeue():
    """Live jobs (pending/running/etc) for the current user, keyed by job id."""
    fmt = "%i|%j|%T|%M|%l|%Z|%P|%R"
    try:
        out = run(["squeue", "-u", USER, "-h", "-o", fmt])
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log_line(ERROR_LOG, f"squeue query failed: {e}")
        return {}

    jobs = {}
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        fields = line.split("|")
        if len(fields) != 8:
            continue
        jobid, name, state, elapsed, timelimit, workdir, partition, reason = fields
        jobs[jobid] = {
            "name": name,
            "state": state,
            "elapsed_s": parse_slurm_time(elapsed),
            "timelimit_s": parse_slurm_time(timelimit),
            "workdir": workdir,
            "partition": partition,
            "reason": reason,
        }
    return jobs


def query_sacct(since):
    """Jobs (any state, including finished) submitted/active since `since`
    (datetime). Keyed by base job id (array-task ids kept, step ids dropped)."""
    fields = ["JobID", "JobName", "State", "ExitCode", "Start", "End", "Elapsed", "Partition", "WorkDir"]
    since_str = since.strftime("%Y-%m-%dT%H:%M:%S")
    base_cmd = ["sacct", "-u", USER, "-n", "-P", "-S", since_str]

    def try_query(fields):
        cmd = base_cmd + ["--format=" + ",".join(fields)]
        out = run(cmd)
        return out, fields

    try:
        out, used_fields = try_query(fields)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # WorkDir isn't available on some older Slurm builds - retry without it.
        fields_no_workdir = [f for f in fields if f != "WorkDir"]
        try:
            out, used_fields = try_query(fields_no_workdir)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            log_line(ERROR_LOG, f"sacct query failed: {e}")
            return {}

    has_workdir = "WorkDir" in used_fields
    jobs = {}
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        fields_v = line.split("|")
        if len(fields_v) != len(used_fields):
            continue
        row = dict(zip(used_fields, fields_v))
        jobid = row["JobID"]
        if "." in jobid:
            continue  # skip .batch / .extern / step entries
        jobs[jobid] = {
            "name": row.get("JobName", ""),
            "state": row.get("State", ""),
            "exitcode": row.get("ExitCode", ""),
            "start": row.get("Start", ""),
            "end": row.get("End", ""),
            "elapsed": row.get("Elapsed", ""),
            "partition": row.get("Partition", ""),
            "workdir": row.get("WorkDir", "") if has_workdir else "",
        }
    return jobs


# --------------------------------------------------------------------------
# poll: update state, log transitions
# --------------------------------------------------------------------------

def poll(lookback_days):
    state = load_state()
    jobs = state.setdefault("jobs", {})

    if state.get("last_poll"):
        since = datetime.fromisoformat(state["last_poll"]) - timedelta(minutes=10)
    else:
        since = datetime.now() - timedelta(days=lookback_days)

    live = query_squeue()
    history = query_sacct(since)

    all_ids = set(live) | set(history)
    new_failures = []
    new_completions = []
    new_starts = []

    for jobid in all_ids:
        prev = jobs.get(jobid, {})
        is_live = jobid in live

        if is_live:
            l = live[jobid]
            workdir = l["workdir"] or prev.get("workdir", "")
            entry = {
                "name": l["name"],
                "workdir": workdir,
                "partition": l["partition"],
                "state": l["state"],
                "elapsed_s": l["elapsed_s"],
                "timelimit_s": l["timelimit_s"],
                "reason": l["reason"],
                "first_seen": prev.get("first_seen", now_iso()),
                "logged_terminal": False,
            }
            if prev.get("state") != "RUNNING" and l["state"] == "RUNNING":
                new_starts.append((jobid, entry))
            jobs[jobid] = entry
            continue

        # not live -> either finished, or only known from sacct history
        h = history.get(jobid)
        if h is None:
            # was live before, vanished, no sacct record yet (race) - leave as-is
            continue

        base_state = h["state"].split()[0] if h["state"] else ""
        workdir = h["workdir"] or prev.get("workdir", "") or "UNKNOWN"
        entry = dict(prev)
        entry.update({
            "name": h["name"] or prev.get("name", ""),
            "workdir": workdir,
            "partition": h["partition"] or prev.get("partition", ""),
            "state": base_state,
            "exitcode": h["exitcode"],
            "start": h["start"],
            "end": h["end"],
            "elapsed_s": parse_slurm_time(h["elapsed"]),
            "first_seen": prev.get("first_seen", now_iso()),
        })

        already_logged = prev.get("logged_terminal", False)
        if base_state in TERMINAL_STATES and not already_logged:
            entry["logged_terminal"] = True
            if base_state in FAILURE_STATES:
                new_failures.append((jobid, entry))
            else:
                new_completions.append((jobid, entry))
        jobs[jobid] = entry

    for jobid, e in new_starts:
        log_line(ACTIVITY_LOG, f"STARTED  job {jobid} '{e['name']}' in {e['workdir']}")

    for jobid, e in new_completions:
        log_line(ACTIVITY_LOG, f"DONE     job {jobid} '{e['name']}' in {e['workdir']} (state={e['state']})")

    for jobid, e in new_failures:
        msg = (f"job {jobid} '{e['name']}' FAILED (state={e['state']}, "
               f"exit={e.get('exitcode', '?')}) in {e['workdir']}")
        log_line(ACTIVITY_LOG, msg)
        log_line(FAILED_LOG, msg)

    # prune old terminal jobs so state.json doesn't grow forever
    cutoff = datetime.now() - timedelta(days=14)
    for jobid in list(jobs.keys()):
        e = jobs[jobid]
        if e.get("logged_terminal"):
            try:
                seen = datetime.fromisoformat(e.get("first_seen", now_iso()))
            except ValueError:
                seen = datetime.now()
            if seen < cutoff:
                del jobs[jobid]

    state["last_poll"] = now_iso()
    save_state(state)

    if new_failures:
        print(f"{len(new_failures)} job(s) newly failed - see {FAILED_LOG}")
    if new_completions:
        print(f"{len(new_completions)} job(s) newly completed.")
    if new_starts:
        print(f"{len(new_starts)} job(s) newly started running.")
    if not (new_failures or new_completions or new_starts):
        print("No new job state changes.")


# --------------------------------------------------------------------------
# status: live table
# --------------------------------------------------------------------------

def print_table(rows, headers):
    widths = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(str(c)))
    fmt = "  ".join("{:<%d}" % w for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for r in rows:
        print(fmt.format(*r))


def status():
    live = query_squeue()
    if not live:
        print("No pending or running jobs.")
        return
    rows = []
    for jobid, l in sorted(live.items(), key=lambda kv: kv[0]):
        elapsed = l["elapsed_s"]
        limit = l["timelimit_s"]
        remaining = (limit - elapsed) if (limit is not None and elapsed is not None) else None
        rows.append([
            jobid,
            l["name"],
            l["state"],
            os.path.basename(l["workdir"].rstrip("/")) or l["workdir"],
            seconds_to_str(elapsed),
            seconds_to_str(limit),
            seconds_to_str(remaining),
            l["partition"],
            l["reason"] if l["state"] != "RUNNING" else "",
        ])
    print_table(rows, ["JOBID", "NAME", "STATE", "DIR", "ELAPSED", "LIMIT", "REMAINING", "PART", "REASON"])


def failures(last_n, today_only):
    if not os.path.exists(FAILED_LOG):
        print("No failures logged yet.")
        return
    with open(FAILED_LOG) as f:
        lines = f.readlines()
    if today_only:
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [l for l in lines if l.startswith(f"[{today}")]
    if last_n:
        lines = lines[-last_n:]
    if not lines:
        print("No matching failures.")
        return
    sys.stdout.write("".join(lines))


def clean(target, backup, yes):
    log_map = {"failures": FAILED_LOG, "activity": ACTIVITY_LOG}
    targets = log_map.items() if target == "all" else [(target, log_map[target])]

    for name, path in targets:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            print(f"{name} log already empty ({path}).")
            continue
        if not yes:
            resp = input(f"Clear {path}? [y/N] ").strip().lower()
            if resp != "y":
                print(f"Skipped {name} log.")
                continue
        if backup:
            bak = f"{path}.bak-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy(path, bak)
            print(f"Backed up to {bak}")
        open(path, "w").close()
        print(f"Cleared {name} log ({path}).")


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Watch your Slurm jobs: running time, time left, failures.")
    sub = p.add_subparsers(dest="command", required=True)

    poll_p = sub.add_parser("poll", help="Update state and log any job start/finish/failure events. Run this from cron.")
    poll_p.add_argument("--lookback-days", type=int, default=1,
                         help="On first run only, how far back to check sacct history (default: 1 day).")

    sub.add_parser("status", help="Show a live table of your pending/running jobs with elapsed/remaining time.")

    fail_p = sub.add_parser("failures", help="Show logged job failures.")
    fail_p.add_argument("-n", "--last", type=int, default=20, help="Show the last N failures (default: 20).")
    fail_p.add_argument("--today", action="store_true", help="Only show failures from today.")

    clean_p = sub.add_parser("clean", help="Clear logged failure/activity history (does not affect job tracking).")
    clean_p.add_argument("target", nargs="?", default="failures", choices=["failures", "activity", "all"],
                          help="Which log to clear (default: failures).")
    clean_p.add_argument("--backup", action="store_true", help="Save a timestamped backup before clearing.")
    clean_p.add_argument("-y", "--yes", action="store_true", help="Don't prompt for confirmation.")

    args = p.parse_args()

    if args.command == "poll":
        poll(args.lookback_days)
    elif args.command == "status":
        status()
    elif args.command == "failures":
        failures(args.last, args.today)
    elif args.command == "clean":
        clean(args.target, args.backup, args.yes)


if __name__ == "__main__":
    main()
