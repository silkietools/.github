# Repo Metadata Audit

Automated policy checks for org repositories live in:

- Policy config: `config/repo-metadata-policy.json`
- Audit CLI: `scripts/repo_metadata_audit.py`
- CI workflow: `.github/workflows/repo-metadata-audit.yml`

## What It Enforces

- Public repo README exists
- Public repo README has a minimal structure (title, at least one badge, key sections)
- Public repos have at least 3 topics
- Optional discovery hints as warnings (default: missing `shpit` topic/label)

## Local Usage

```bash
python3 scripts/repo_metadata_audit.py \
  --org silkietools \
  --visibility public \
  --policy config/repo-metadata-policy.json \
  --output-json /tmp/metadata-audit-report.json
```

`gh` must be authenticated. For private repo audits (`--visibility private|all`), use a token with access to those repositories.

## Policy Shape

```json
{
  "policy_name": "public-discovery-and-readme-minimums",
  "default_visibility": "all",
  "exclude_repositories": [".github"],
  "required_repo_description": false,
  "required_readme": false,
  "required_topics": [],
  "required_labels": [],
  "public_min_topics": 3,
  "public_required_topics": [],
  "public_required_labels": [],
  "public_warn_topics": ["shpit"],
  "public_warn_labels": ["shpit"],
  "public_required_readme": true,
  "public_readme_minimum": {
    "require_title": true,
    "min_badges": 1,
    "required_section_groups": [
      ["what it does", "overview", "what is", "summary"],
      ["quick start", "usage", "getting started", "installation"],
      ["testing", "testing and ci", "quality"]
    ],
    "min_required_groups_matched": 2
  }
}
```

## Cloning For Another Org

1. Copy this `.github` repo into the target org.
2. Update the policy values for that org.
3. Run the workflow manually to validate.
4. Fix non-compliant repos until the workflow passes.
