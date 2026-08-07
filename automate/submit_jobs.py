#!/usr/bin/env python3
"""
Submit multiphysics_amr.sh SLURM jobs for one, several, or all test-case
run directories.

A "run directory" is any directory containing multiphysics_amr.sh (e.g.
3x3_uniform_all_over/0th, 17x17_rodded/0th, ...). The refinement levels
within a case (0th/1st/2nd/3rd) are independent, uniform-refinement runs
-- 1st does not depend on 0th's output etc. -- so there is no submission
order/dependency to respect; everything selected is submitted right away.

Usage:
  python submit_jobs.py                            # dry run, everything under root
  python submit_jobs.py --yes                      # actually submit, everything
  python submit_jobs.py 3x3_uniform_all_over --yes # actually submit, one case (all its run dirs)
  python submit_jobs.py 3x3_uniform_all_over/2nd --yes  # actually submit, one run dir
  python submit_jobs.py 0th --yes                  # actually submit every run dir named "0th" in any case
  python submit_jobs.py --list                     # just show detected run dirs, no submitting
"""

import argparse
import subprocess
import sys
from pathlib import Path

MARKER_FILE = "multiphysics_amr.sh"


def find_run_dirs(root):
    run_dirs = []
    for p in root.rglob(MARKER_FILE):
        run_dirs.append(p.parent)
    return sorted(run_dirs)


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
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_dirs = find_run_dirs(root)

    if args.list:
        for rd in run_dirs:
            print(f"{rd.relative_to(root)}  (job-name={job_name(rd)})")
        return

    selected = [rd for rd in run_dirs if matches_target(rd, root, args.targets)]
    if not selected:
        print("No run directories matched.", file=sys.stderr)
        sys.exit(1)

    print(f"{'Submitting' if args.yes else 'Would submit'} {len(selected)} job(s):")
    failures = 0
    for rd in selected:
        rel = rd.relative_to(root)
        name = job_name(rd)
        if not args.yes:
            print(f"  [dry run] {rel}  (job-name={name})")
            continue
        result = subprocess.run(
            ["sbatch", MARKER_FILE],
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
