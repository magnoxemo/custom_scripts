#!/usr/bin/env python3
"""
Submit multiphysics_amr.sh SLURM jobs for one, several, or all test-case
run directories.
"""

import argparse
import subprocess
import sys
from pathlib import Path

MARKER_FILE = "multiphysics_amr.sh"
TIMEOUT_MARKER = "DUE TO TIME LIMIT"


def find_run_dirs(root):
    run_dirs = []
    for p in root.rglob(MARKER_FILE):
        run_dirs.append(p.parent)
    return sorted(run_dirs)


def needs_recovery(run_dir):
    """True if this run dir's most recent SLURM .err file shows a wall-time kill."""
    err_files = list(run_dir.glob("*.err"))
    if not err_files:
        return False
    latest = max(err_files, key=lambda p: p.stat().st_mtime)
    try:
        return TIMEOUT_MARKER in latest.read_text(errors="ignore")
    except OSError:
        return False


def matches_target(run_dir, root, targets):
    if not targets:
        return True
    rel = run_dir.relative_to(root).as_posix()
    name = run_dir.name
    for t in targets:
        t = t.rstrip("/")
        if t == name or t == rel:
            return True
        if rel.startswith(t + "/"):
            return True
    return False


def job_name(run_dir):
    for line in (run_dir / MARKER_FILE).read_text().splitlines():
        line = line.strip()
        if line.startswith("#SBATCH --job-name="):
            return line.split("=", 1)[1]
    return "?"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("targets", nargs="*", help="case and/or run-dir names/paths to restrict to (default: all)")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent), help="hpc_debug root to search (default: this script's directory)")
    parser.add_argument("--yes", action="store_true", help="actually submit (default is a dry run)")
    parser.add_argument("--list", action="store_true", help="just list detected run directories and exit")
    parser.add_argument(
        "--recover",
        action="store_true",
        help="restrict to run dirs whose latest job was killed by the wall-time limit, "
        "and submit them as `sbatch multiphysics_amr.sh recover` (resume from the latest "
        "checkpoint instead of a fresh run)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_dirs = find_run_dirs(root)
    if args.recover:
        run_dirs = [rd for rd in run_dirs if needs_recovery(rd)]

    if args.list:
        if not run_dirs:
            print("No run directories need recovering." if args.recover else "No run directories found.")
        for rd in run_dirs:
            print(f"{rd.relative_to(root)}  (job-name={job_name(rd)})")
        return

    selected = [rd for rd in run_dirs if matches_target(rd, root, args.targets)]
    if not selected:
        print(
            "No run directories matched." if not args.recover else "No run directories need recovering.",
            file=sys.stderr,
        )
        sys.exit(1)

    sbatch_args = [MARKER_FILE, "recover"] if args.recover else [MARKER_FILE]
    verb = "recovering" if args.recover else "submitting"
    print(f"{'Submitting' if args.yes else 'Would submit'} {len(selected)} job(s) ({verb}):")
    failures = 0
    for rd in selected:
        rel = rd.relative_to(root)
        name = job_name(rd)
        if not args.yes:
            print(f"  [dry run] {rel}  (job-name={name})")
            continue
        result = subprocess.run(
            ["sbatch", *sbatch_args],
            cwd=rd,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  {rel}  (job-name={name})  ->  {result.stdout.strip()}")
        else:
            failures += 1
            print(f"  {rel}  (job-name={name})  ->  FAILED: {result.stderr.strip()}")

    if not args.yes:
        print("\nDry run only -- re-run with --yes to actually submit via sbatch.")
    elif failures:
        print(f"\n{failures} submission(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
