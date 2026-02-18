#!/usr/bin/env python3
"""Enable security baseline controls across repositories in a GitHub organization."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RepoRecord:
    name: str
    is_private: bool


@dataclass
class RepoRun:
    name: str
    visibility: str
    success: bool
    details: list[str]
    warnings: list[str]
    errors: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--org", required=True, help="GitHub organization name")
    parser.add_argument(
        "--visibility",
        choices=("public", "private", "all"),
        default="all",
        help="Repositories to target.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Repository name to skip (repeatable).",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional output path for full run report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any repository fails baseline application.",
    )
    return parser.parse_args()


def run_gh(args: list[str]) -> tuple[int, str, str]:
    env = os.environ.copy()
    if "GH_TOKEN" not in env and "GITHUB_TOKEN" in env:
        env["GH_TOKEN"] = env["GITHUB_TOKEN"]
    proc = subprocess.run(
        ["gh", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def gh_json(args: list[str]) -> Any:
    code, out, err = run_gh(args)
    if code != 0:
        raise RuntimeError(err.strip() or f"gh command failed: {' '.join(args)}")
    return json.loads(out)


def list_repos(org: str) -> list[RepoRecord]:
    query = """
    query($org: String!, $cursor: String) {
      organization(login: $org) {
        repositories(first: 100, after: $cursor, orderBy: {field: NAME, direction: ASC}) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            name
            isPrivate
          }
        }
      }
    }
    """.strip()

    repos: list[RepoRecord] = []
    cursor = ""
    while True:
        args = ["api", "graphql", "-f", f"query={query}", "-f", f"org={org}"]
        if cursor:
            args.extend(["-f", f"cursor={cursor}"])
        data = gh_json(args)
        page = data["data"]["organization"]["repositories"]
        for node in page["nodes"]:
            repos.append(RepoRecord(name=node["name"], is_private=bool(node["isPrivate"])))
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return repos


def include_repo(repo: RepoRecord, visibility: str, excluded: set[str]) -> bool:
    if repo.name in excluded:
        return False
    if visibility == "all":
        return True
    if visibility == "public":
        return not repo.is_private
    if visibility == "private":
        return repo.is_private
    raise ValueError(f"Unsupported visibility: {visibility}")


def api_call(method: str, path: str, fields: list[str] | None = None) -> tuple[bool, str, str]:
    args = ["api", "-X", method, path, "-H", "Accept: application/vnd.github+json"]
    for field in fields or []:
        args.extend(["-f", field])
    code, out, err = run_gh(args)
    return (code == 0, out.strip(), err.strip())


def enable_dependabot(repo_full: str, run: RepoRun) -> None:
    ok, _, err = api_call("PUT", f"repos/{repo_full}/vulnerability-alerts")
    if ok:
        run.details.append("vulnerability_alerts=enabled")
    else:
        run.errors.append(f"vulnerability_alerts_failed:{err}")
        return

    ok, _, err = api_call("PUT", f"repos/{repo_full}/automated-security-fixes")
    if not ok and "Vulnerability alerts must be enabled" in err:
        time.sleep(1)
        ok, _, err = api_call("PUT", f"repos/{repo_full}/automated-security-fixes")
    if ok:
        run.details.append("dependabot_security_updates=enabled")
    else:
        run.errors.append(f"automated_security_fixes_failed:{err}")


def enable_secret_scanning(repo_full: str, is_private: bool, run: RepoRun) -> None:
    fields = [
        "security_and_analysis[dependabot_security_updates][status]=enabled",
        "security_and_analysis[secret_scanning][status]=enabled",
        "security_and_analysis[secret_scanning_push_protection][status]=enabled",
        "security_and_analysis[secret_scanning_non_provider_patterns][status]=enabled",
    ]
    if is_private:
        fields.append("security_and_analysis[code_security][status]=enabled")

    ok, _, err = api_call("PATCH", f"repos/{repo_full}", fields)
    if ok:
        run.details.append("security_and_analysis_baseline=applied")
    else:
        run.errors.append(f"security_and_analysis_failed:{err}")


def enable_codeql_default_setup(repo_full: str, run: RepoRun) -> None:
    ok, _, err = api_call(
        "PATCH",
        f"repos/{repo_full}/code-scanning/default-setup",
        fields=["state=configured"],
    )
    if ok:
        run.details.append("codeql_default_setup=configured")
    else:
        run.errors.append(f"codeql_default_setup_failed:{err}")


def apply_repo(org: str, repo: RepoRecord) -> RepoRun:
    repo_full = f"{org}/{repo.name}"
    visibility = "private" if repo.is_private else "public"
    run = RepoRun(name=repo.name, visibility=visibility, success=True, details=[], warnings=[], errors=[])

    enable_dependabot(repo_full, run)
    enable_secret_scanning(repo_full, repo.is_private, run)
    enable_codeql_default_setup(repo_full, run)

    run.success = not run.errors
    return run


def print_report(org: str, results: list[RepoRun]) -> None:
    print(f"Org: {org}")
    print("")
    print("repo\tvisibility\tsuccess\terrors\twarnings")
    for run in results:
        errors = ",".join(run.errors) if run.errors else "-"
        warnings = ",".join(run.warnings) if run.warnings else "-"
        print(f"{run.name}\t{run.visibility}\t{'yes' if run.success else 'no'}\t{errors}\t{warnings}")


def main() -> int:
    args = parse_args()
    repos = list_repos(args.org)
    targets = [r for r in repos if include_repo(r, args.visibility, set(args.exclude))]

    results: list[RepoRun] = []
    for repo in targets:
        results.append(apply_repo(args.org, repo))

    print_report(args.org, results)

    payload = {
        "org": args.org,
        "visibility": args.visibility,
        "checked_repositories": len(results),
        "failed_repositories": [r.name for r in results if not r.success],
        "results": [
            {
                "name": r.name,
                "visibility": r.visibility,
                "success": r.success,
                "details": r.details,
                "warnings": r.warnings,
                "errors": r.errors,
            }
            for r in results
        ],
    }
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.strict and payload["failed_repositories"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
