#!/usr/bin/env python3
"""Fail-closed release verifier for the do-Shapley reproduction."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FINAL_REMOTE = "https://github.com/MachineLearning-Nerd/icml26-do-shapley"
CANONICAL_NAME = "MachineLearning-Nerd"
CANONICAL_EMAIL = "MachineLearning-Nerd@users.noreply.github.com"


def fail(message: str) -> None:
    raise SystemExit(f"VERIFY_FAIL: {message}")


def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        fail(f"command failed: {' '.join(args)}\n{result.stdout}{result.stderr}")
    return result.stdout.strip()


def require_files() -> None:
    required = [
        "README.md",
        "STATUS.md",
        "CLAIM_EVIDENCE.md",
        "SOURCE_MANIFEST.md",
        "BRANCH_AUDIT.md",
        "CITATION.cff",
        "requirements.txt",
        "docs/paper.txt",
        "repro/src/doshapley.py",
        "repro/src/scm.py",
        "repro/src/estimator.py",
        "repro/src/run_claims.py",
        "repro/tests/test_doshapley.py",
        "repro/tests/test_smoke.py",
        "outputs/c1_exact_large.csv",
        "outputs/c1_exact_vs_brute.csv",
        "outputs/c1_linearity.csv",
        "outputs/c1_r_range.csv",
        "outputs/c2_convergence.csv",
        "outputs/summary.json",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")


def check_docs() -> None:
    readme = (ROOT / "README.md").read_text()
    evidence = (ROOT / "CLAIM_EVIDENCE.md").read_text()
    manifest = (ROOT / "SOURCE_MANIFEST.md").read_text()
    branch_audit = (ROOT / "BRANCH_AUDIT.md").read_text()
    citation = (ROOT / "CITATION.cff").read_text()
    for marker in (
        "Exactly Computing do-Shapley Values",
        "R. Teal Witter",
        "Álvaro Parafita",
        "NOT_REPRODUCED",
        "clean-room",
        "No official source code",
    ):
        if marker not in readme:
            fail(f"README is missing marker: {marker}")
    for marker in ("C1", "C2", "BoundarySampler", "brute_shapley", "NOT_REPRODUCED"):
        if marker not in evidence:
            fail(f"claim evidence is missing marker: {marker}")
    for marker in ("docs/paper.txt", "run_claims.py", "clean-room"):
        if marker not in manifest:
            fail(f"source manifest is missing marker: {marker}")
    for marker in ("main", "master", "MachineLearning-Nerd", "No `orx`"):
        if marker not in branch_audit:
            fail(f"branch audit is missing marker: {marker}")
    for marker in ("repository-code:", "10.48550/arXiv.2602.07203", "Rosenblatt"):
        if marker not in citation:
            fail(f"citation file is missing marker: {marker}")
    if (ROOT / "requirements.txt").read_text().splitlines() != [
        "numpy==2.3.1",
        "pytest==8.4.1",
    ]:
        fail("requirements.txt is not pinned to the audited environment")


def check_git_state() -> None:
    if run("git", "branch", "--show-current") != "main":
        fail("current branch is not main")
    remote = run("git", "remote", "get-url", "origin").removesuffix(".git")
    if remote != FINAL_REMOTE:
        fail(f"origin is {remote!r}, expected {FINAL_REMOTE!r}")
    if run("git", "status", "--porcelain"):
        fail("working tree is not clean")
    refs = run("git", "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes").splitlines()
    if any(ref.endswith("/master") or ref.endswith("/orx") for ref in refs):
        fail(f"retired/generated branch remains: {refs}")
    if "refs/heads/main" not in refs:
        fail("refs/heads/main is missing")
    if any("repro-Peim0KY6ty" in ref for ref in refs):
        fail(f"old repository slug remains in refs: {refs}")

    records = run(
        "git",
        "log",
        "--all",
        "--format=%H%x00%an%x00%ae%x00%cn%x00%ce",
    ).splitlines()
    if not records:
        fail("no reachable commits")
    for record in records:
        fields = record.split("\x00")
        if len(fields) != 5:
            fail(f"malformed commit record: {record}")
        _, author, author_email, committer, committer_email = fields
        if (author, author_email, committer, committer_email) != (
            CANONICAL_NAME,
            CANONICAL_EMAIL,
            CANONICAL_NAME,
            CANONICAL_EMAIL,
        ):
            fail(f"non-canonical commit identity: {record}")


def read_rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def check_outputs() -> None:
    summary = json.loads((ROOT / "outputs/summary.json").read_text())
    c1 = summary["claims"]["C1_exact_computation_linear_in_r"]
    c2 = summary["claims"]["C2_estimator_convergence"]
    if (c1["cases"], c1["verified"]) != (60, 60):
        fail(f"C1 case count is {c1['cases']}/{c1['verified']}")
    if not c1["all_machine_precision"] or c1["worst_abs_err"] >= 2e-10:
        fail(f"C1 error threshold failed: {c1}")
    if c1["corr_exact_time_vs_r"] <= 0.99 or c1["max_speedup_vs_brute"] <= 10:
        fail(f"C1 scaling thresholds failed: {c1}")
    if c1["exact_handles_d_up_to"] != 25 or not c1["all_in_range"]:
        fail(f"C1 large/r-range thresholds failed: {c1}")
    if (c2["cases"], c2["all_exact_at_r"]) != (4, True):
        fail(f"C2 case/exactness threshold failed: {c2}")
    if c2["max_gap_orders_of_magnitude"] <= 10:
        fail(f"C2 gap threshold failed: {c2}")
    if c2["max_gap_at"] != "d=11, m=81, r=81":
        fail(f"C2 maximum-gap case changed: {c2}")

    exact_rows = read_rows("outputs/c1_exact_vs_brute.csv")
    linearity_rows = read_rows("outputs/c1_linearity.csv")
    large_rows = read_rows("outputs/c1_exact_large.csv")
    range_rows = read_rows("outputs/c1_r_range.csv")
    convergence_rows = read_rows("outputs/c2_convergence.csv")
    if [len(rows) for rows in (exact_rows, linearity_rows, large_rows, range_rows, convergence_rows)] != [60, 11, 6, 3, 24]:
        fail("committed CSV row counts do not match the audited producer run")
    if any(row["verified"] != "True" for row in exact_rows):
        fail("a C1 exact-vs-brute row is not verified")
    exact_c2 = [row for row in convergence_rows if int(row["m"]) >= int(row["r"])]
    if len(exact_c2) != 8 or any(int(row["boundary_distinct"]) != int(row["r"]) for row in exact_c2):
        fail("C2 m>=r rows do not cover every class")
    if max(float(row["boundary_err"]) for row in exact_c2) >= 1e-10:
        fail("C2 m>=r numerical error exceeds threshold")


def check_tests() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "repro/tests/test_doshapley.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode:
        fail(f"focused tests failed:\n{output}")
    if "28 passed" not in output:
        fail(f"focused test count changed:\n{output}")


def main() -> None:
    require_files()
    check_docs()
    check_git_state()
    check_outputs()
    check_tests()
    print("FINAL_VERIFICATION_PASS")
    print(f"repository={FINAL_REMOTE}")
    print("branch=main")
    print(f"reachable_commits={len(run('git', 'rev-list', '--all').splitlines())}")
    print("commit_identity=canonical")
    print("claim_boundaries=PASS")
    print("focused_tests=PASS")


if __name__ == "__main__":
    main()
