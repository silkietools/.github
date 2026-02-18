#!/usr/bin/env python3
"""Audit repository metadata and README quality rules for an organization."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RepoRecord:
    name: str
    is_private: bool
    description: str
    url: str
    topics: list[str]


@dataclass
class RepoResult:
    name: str
    visibility: str
    url: str
    description_present: bool
    topics: list[str]
    labels: list[str]
    readme_present: bool
    readme_bytes: int
    violations: list[str]
    warnings: list[str]

    @property
    def compliant(self) -> bool:
        return not self.violations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--org", required=True, help="GitHub organization name")
    parser.add_argument(
        "--policy",
        default="config/repo-metadata-policy.json",
        help="Path to JSON policy config",
    )
    parser.add_argument(
        "--visibility",
        choices=("public", "private", "all"),
        default=None,
        help="Repos to audit. Defaults to policy default_visibility.",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional file path for full JSON report",
    )
    return parser.parse_args()


def run_gh(args: list[str]) -> str:
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
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"gh command failed: {' '.join(args)}")
    return proc.stdout


def gh_api(path: str) -> Any:
    return json.loads(run_gh(["api", path]))


def gh_graphql(query: str, variables: dict[str, str]) -> Any:
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args.extend(["-f", f"{key}={value}"])
    return json.loads(run_gh(args))


def load_policy(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fetch_repositories(org: str) -> list[RepoRecord]:
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
            description
            url
            repositoryTopics(first: 100) {
              nodes {
                topic {
                  name
                }
              }
            }
          }
        }
      }
    }
    """.strip()

    repos: list[RepoRecord] = []
    cursor = ""
    while True:
        variables = {"org": org}
        if cursor:
            variables["cursor"] = cursor
        data = gh_graphql(query, variables)
        repo_page = data["data"]["organization"]["repositories"]
        for node in repo_page["nodes"]:
            repos.append(
                RepoRecord(
                    name=node["name"],
                    is_private=bool(node["isPrivate"]),
                    description=node.get("description") or "",
                    url=node["url"],
                    topics=[
                        topic_node["topic"]["name"]
                        for topic_node in node["repositoryTopics"]["nodes"]
                        if topic_node.get("topic") and topic_node["topic"].get("name")
                    ],
                )
            )
        if not repo_page["pageInfo"]["hasNextPage"]:
            break
        cursor = repo_page["pageInfo"]["endCursor"]
    return repos


def fetch_labels(org: str, repo: str) -> list[str]:
    labels = gh_api(f"repos/{org}/{repo}/labels?per_page=100")
    return [label["name"] for label in labels]


def fetch_readme(org: str, repo: str) -> tuple[bool, str]:
    env = os.environ.copy()
    if "GH_TOKEN" not in env and "GITHUB_TOKEN" in env:
        env["GH_TOKEN"] = env["GITHUB_TOKEN"]
    proc = subprocess.run(
        ["gh", "api", f"repos/{org}/{repo}/readme"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        if "404" in proc.stderr:
            return (False, "")
        raise RuntimeError(proc.stderr.strip())
    payload = json.loads(proc.stdout)
    content = (payload.get("content") or "").replace("\n", "")
    decoded = base64.b64decode(content).decode("utf-8", errors="replace") if content else ""
    return (True, decoded)


def include_repo(record: RepoRecord, visibility: str, excluded: set[str]) -> bool:
    if record.name in excluded:
        return False
    if visibility == "all":
        return True
    if visibility == "public":
        return not record.is_private
    if visibility == "private":
        return record.is_private
    raise ValueError(f"Unsupported visibility mode: {visibility}")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def readme_minimum_violations(readme_text: str, minimum: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    lines = [line.strip() for line in readme_text.splitlines()]
    non_empty = [line for line in lines if line]

    if minimum.get("require_title", False):
        first_line = non_empty[0] if non_empty else ""
        if not first_line.startswith("# "):
            violations.append("readme_missing_title")

    min_badges = int(minimum.get("min_badges", 0) or 0)
    if min_badges > 0:
        badge_count = len(
            re.findall(
                r"!\[[^\]]*]\(\s*(?:https?:)?//img\.shields\.io/[^)]+\)",
                readme_text,
                flags=re.IGNORECASE,
            )
        )
        if badge_count < min_badges:
            violations.append(f"readme_badges_below_min:{badge_count}<{min_badges}")

    required_groups = minimum.get("required_section_groups", []) or []
    if required_groups:
        normalized_headings: list[str] = []
        for line in readme_text.splitlines():
            match = re.match(r"^#{2,6}\s+(.+?)\s*$", line.strip())
            if match:
                normalized_headings.append(normalize_text(match.group(1)))

        matched_groups = 0
        for group in required_groups:
            group_matched = False
            for candidate in group:
                normalized_candidate = normalize_text(candidate)
                if any(normalized_candidate in heading for heading in normalized_headings):
                    group_matched = True
                    break
            if group_matched:
                matched_groups += 1

        min_groups = int(minimum.get("min_required_groups_matched", len(required_groups)))
        if matched_groups < min_groups:
            violations.append(f"readme_section_groups_below_min:{matched_groups}<{min_groups}")

    return violations


def evaluate_repo(
    record: RepoRecord,
    labels: list[str],
    readme_present: bool,
    readme_text: str,
    policy: dict[str, Any],
) -> RepoResult:
    required_topics = list(policy.get("required_topics", []))
    required_labels = list(policy.get("required_labels", []))
    warn_topics = list(policy.get("warn_topics", []))
    warn_labels = list(policy.get("warn_labels", []))

    if not record.is_private:
        required_topics.extend(policy.get("public_required_topics", []))
        required_labels.extend(policy.get("public_required_labels", []))
        warn_topics.extend(policy.get("public_warn_topics", []))
        warn_labels.extend(policy.get("public_warn_labels", []))

    violations: list[str] = []
    warnings: list[str] = []

    if policy.get("required_repo_description", False) and not record.description.strip():
        violations.append("missing_description")

    for topic in sorted(set(required_topics)):
        if topic not in record.topics:
            violations.append(f"missing_topic:{topic}")

    for topic in sorted(set(warn_topics)):
        if topic not in record.topics:
            warnings.append(f"missing_topic_warning:{topic}")

    for label in sorted(set(required_labels)):
        if label not in labels:
            violations.append(f"missing_label:{label}")

    for label in sorted(set(warn_labels)):
        if label not in labels:
            warnings.append(f"missing_label_warning:{label}")

    require_readme = bool(policy.get("required_readme", False))
    if not record.is_private and policy.get("public_required_readme", False):
        require_readme = True

    if require_readme and not readme_present:
        violations.append("missing_readme")

    if readme_present:
        for needle in policy.get("required_readme_contains", []) or []:
            if needle not in readme_text:
                violations.append(f"readme_missing_text:{needle}")

        minimum = policy.get("readme_minimum", {}) or {}
        if not record.is_private:
            public_minimum = policy.get("public_readme_minimum", {}) or {}
            if public_minimum:
                minimum = public_minimum
        if minimum:
            violations.extend(readme_minimum_violations(readme_text, minimum))

    visibility = "private" if record.is_private else "public"
    return RepoResult(
        name=record.name,
        visibility=visibility,
        url=record.url,
        description_present=bool(record.description.strip()),
        topics=sorted(record.topics),
        labels=sorted(labels),
        readme_present=readme_present,
        readme_bytes=len(readme_text.encode("utf-8")) if readme_present else 0,
        violations=sorted(set(violations)),
        warnings=sorted(set(warnings)),
    )


def print_report(org: str, policy_name: str, visibility: str, results: list[RepoResult]) -> None:
    print(f"Org: {org}")
    print(f"Policy: {policy_name}")
    print(f"Visibility: {visibility}")
    print("")
    print("repo\tvisibility\tcompliant\tviolations\twarnings")
    for result in results:
        status = "yes" if result.compliant else "no"
        issues = ",".join(result.violations) if result.violations else "-"
        warnings = ",".join(result.warnings) if result.warnings else "-"
        print(f"{result.name}\t{result.visibility}\t{status}\t{issues}\t{warnings}")


def main() -> int:
    args = parse_args()
    policy = load_policy(args.policy)
    visibility = args.visibility or policy.get("default_visibility", "public")
    excluded = set(policy.get("exclude_repositories", []))

    records = fetch_repositories(args.org)
    targets = [record for record in records if include_repo(record, visibility, excluded)]
    results: list[RepoResult] = []

    for record in targets:
        labels = fetch_labels(args.org, record.name)
        readme_present, readme_text = fetch_readme(args.org, record.name)
        results.append(evaluate_repo(record, labels, readme_present, readme_text, policy))

    print_report(args.org, policy.get("policy_name", "unknown"), visibility, results)

    payload = {
        "org": args.org,
        "policy_name": policy.get("policy_name", "unknown"),
        "visibility": visibility,
        "checked_repositories": len(results),
        "non_compliant_count": sum(1 for result in results if not result.compliant),
        "warning_count": sum(len(result.warnings) for result in results),
        "results": [
            {
                "name": result.name,
                "visibility": result.visibility,
                "url": result.url,
                "description_present": result.description_present,
                "topics": result.topics,
                "labels": result.labels,
                "readme_present": result.readme_present,
                "readme_bytes": result.readme_bytes,
                "violations": result.violations,
                "warnings": result.warnings,
            }
            for result in results
        ],
    }
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return 1 if payload["non_compliant_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
