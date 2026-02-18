from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repo_metadata_audit import RepoRecord, evaluate_repo, include_repo  # noqa: E402


class RepoMetadataAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = {
            "required_repo_description": False,
            "required_readme": False,
            "required_topics": [],
            "required_labels": [],
            "public_min_topics": 3,
            "public_required_readme": True,
            "public_warn_topics": ["shpit"],
            "public_readme_minimum": {
                "require_title": True,
                "min_badges": 1,
                "required_section_groups": [
                    ["what it does", "overview", "what is"],
                    ["quick start", "usage", "getting started"],
                    ["testing", "testing and ci", "quality"],
                ],
                "min_required_groups_matched": 2,
            },
        }

    def test_include_repo_respects_visibility_and_exclusions(self) -> None:
        public = RepoRecord("demo", False, "desc", "https://example.com/demo", [])
        private = RepoRecord("internal", True, "desc", "https://example.com/internal", [])

        self.assertTrue(include_repo(public, "public", set()))
        self.assertFalse(include_repo(private, "public", set()))
        self.assertTrue(include_repo(private, "private", set()))
        self.assertFalse(include_repo(public, "private", set()))
        self.assertFalse(include_repo(public, "all", {"demo"}))

    def test_public_repo_without_readme_fails_and_missing_shpit_warns(self) -> None:
        record = RepoRecord("demo", False, "", "https://example.com/demo", [])
        result = evaluate_repo(
            record=record,
            labels=[],
            readme_present=False,
            readme_text="",
            policy=self.policy,
        )
        self.assertFalse(result.compliant)
        self.assertIn("missing_readme", result.violations)
        self.assertIn("missing_topic_warning:shpit", result.warnings)

    def test_public_repo_readme_minimum_enforced(self) -> None:
        record = RepoRecord("demo", False, "", "https://example.com/demo", ["shpit"])
        readme = "\n".join(["# Demo", "## Notes"])
        result = evaluate_repo(
            record=record,
            labels=["bug"],
            readme_present=True,
            readme_text=readme,
            policy=self.policy,
        )
        self.assertFalse(result.compliant)
        self.assertIn("readme_badges_below_min:0<1", result.violations)
        self.assertIn("readme_section_groups_below_min:0<2", result.violations)

    def test_compliant_public_repo_passes(self) -> None:
        record = RepoRecord("demo", False, "", "https://example.com/demo", ["shpit"])
        readme = "\n".join(
            [
                "# Demo",
                "[![Node](https://img.shields.io/badge/Node-20-blue)](https://nodejs.org/)",
                "## What it does",
                "## Quick Start",
                "## Testing and CI",
            ]
        )
        result = evaluate_repo(
            record=record,
            labels=["bug"],
            readme_present=True,
            readme_text=readme,
            policy=self.policy,
        )
        self.assertFalse(result.compliant)
        self.assertIn("public_topics_below_min:1<3", result.violations)

    def test_public_repo_with_three_topics_passes_min_topic_rule(self) -> None:
        record = RepoRecord(
            "demo",
            False,
            "",
            "https://example.com/demo",
            ["shpit", "demo", "template"],
        )
        readme = "\n".join(
            [
                "# Demo",
                "[![Node](https://img.shields.io/badge/Node-20-blue)](https://nodejs.org/)",
                "## What it does",
                "## Quick Start",
                "## Testing and CI",
            ]
        )
        result = evaluate_repo(
            record=record,
            labels=["bug"],
            readme_present=True,
            readme_text=readme,
            policy=self.policy,
        )
        self.assertTrue(result.compliant)
        self.assertEqual([], result.violations)

    def test_private_repo_not_forced_into_public_rules(self) -> None:
        record = RepoRecord("internal", True, "", "https://example.com/internal", [])
        result = evaluate_repo(
            record=record,
            labels=["bug"],
            readme_present=False,
            readme_text="",
            policy=self.policy,
        )
        self.assertTrue(result.compliant)
        self.assertEqual([], result.warnings)


if __name__ == "__main__":
    unittest.main()
