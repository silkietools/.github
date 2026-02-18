# Org Defaults Template

Org-level defaults repo for contribution/security/support docs, issue/PR templates, and metadata quality automation.

[![YouTube Walkthrough](https://img.shields.io/badge/YouTube-Watch%20walkthrough-FF0000?logo=youtube&logoColor=white)](https://www.youtube.com/watch?v=XWWyVmvqBJ8)
[![shpit.dev Tutorials](https://img.shields.io/badge/shpit.dev-More%20tutorials-0A66C2?logo=googlechrome&logoColor=white)](https://www.shpit.dev/)

## Discovery Model

Use metadata-first discovery instead of README front matter contracts.

- Checklist: `docs/shpit-discovery-checklist.md`
- Policy config: `config/repo-metadata-policy.json`
- Automated audit: `scripts/repo_metadata_audit.py`
- CI workflow: `.github/workflows/repo-metadata-audit.yml`
- Security baseline enforcer: `scripts/enforce_security_baseline.py`
- Security baseline template: `docs/security-baseline-enforcer.md`

This is intentionally config-driven so the same repo structure can be copied to other orgs.

Default policy in this repo:

- Public repos: enforce a minimal README structure (title, badge presence, key sections).
- Public repos: require at least 3 topics.
- Public repos: `shpit` topic/label are warning-only discovery hints (non-blocking).
- Keep deeper content semantics (exact topic taxonomy and label taxonomy) as manual curation.

## Contains

- Org profile: `profile/README.md`
- Discovery checklist: `docs/shpit-discovery-checklist.md`
- Security baseline docs: `docs/security-baseline-enforcer.md`
- Metadata policy config: `config/repo-metadata-policy.json`
- Metadata audit script + tests: `scripts/repo_metadata_audit.py`, `scripts/tests/test_repo_metadata_audit.py`
- Security baseline script + tests: `scripts/enforce_security_baseline.py`, `scripts/tests/test_enforce_security_baseline.py`
- Default docs: contribution, security, support, conduct
- Default templates: issue + pull request

## Reuse In Another Org

1. Clone/copy this `.github` repository into the target org.
2. Update `config/repo-metadata-policy.json` for that org's required topics/labels and exclusions.
3. Run the workflow manually in `.github/workflows/repo-metadata-audit.yml` with target org + visibility.
4. Fix reported repos until the audit passes.

## Security Baseline Template

- Dependabot vulnerability alerts: enforced
- Dependabot security updates: enforced
- Secret scanning + push protection: enforced
- CodeQL default setup: enforced

Use org-level Code Security Configuration defaults for automatic new-repo inheritance.
Use `scripts/enforce_security_baseline.py` only for one-time backfill or manual drift correction.

## Testing and CI

| Layer | Present | Tooling | Runs in CI |
|---|---|---|---|
| unit | yes | `unittest` (Python stdlib) | yes |
| integration | no | none | no |
| e2e api | no | none | no |
| e2e web | no | none | no |

## Notes

- No application runtime code
- Purpose: shared standards and enforceable metadata quality
