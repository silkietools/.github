from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from enforce_security_baseline import RepoRecord, include_repo  # noqa: E402


class EnforceSecurityBaselineTests(unittest.TestCase):
    def test_include_repo_filters_visibility(self) -> None:
        public = RepoRecord(name="public-repo", is_private=False)
        private = RepoRecord(name="private-repo", is_private=True)

        self.assertTrue(include_repo(public, "public", set()))
        self.assertFalse(include_repo(private, "public", set()))
        self.assertTrue(include_repo(private, "private", set()))
        self.assertFalse(include_repo(public, "private", set()))
        self.assertTrue(include_repo(public, "all", set()))
        self.assertTrue(include_repo(private, "all", set()))

    def test_include_repo_honors_exclusions(self) -> None:
        public = RepoRecord(name="public-repo", is_private=False)
        self.assertFalse(include_repo(public, "all", {"public-repo"}))


if __name__ == "__main__":
    unittest.main()
