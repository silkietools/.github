# Security Baseline Template

Use this for any new org to avoid per-repo manual setup.

## Baseline Controls

- Dependabot vulnerability alerts
- Dependabot security updates
- Secret scanning
- Secret scanning push protection
- Secret scanning non-provider patterns
- CodeQL default setup

## New Org Setup (Automatic For New Repos)

1. List available org security configurations:

```bash
gh api orgs/<org>/code-security/configurations -H 'Accept: application/vnd.github+json'
```

2. Set the chosen configuration as default for new repos:

```bash
gh api -X PUT orgs/<org>/code-security/configurations/<config_id>/defaults \
  -H 'Accept: application/vnd.github+json' \
  -f default_for_new_repos=all
```

3. Verify defaults:

```bash
gh api orgs/<org>/code-security/configurations/defaults -H 'Accept: application/vnd.github+json'
```

## Existing Repo Backfill (One-Time / Manual)

Use the local script:

```bash
python3 scripts/enforce_security_baseline.py \
  --org <org> \
  --visibility all \
  --exclude .github \
  --output-json /tmp/security-baseline-report.json \
  --strict
```

No repo-stored org admin token is required for this model; run it from a trusted local admin session when needed.

## Plan / Licensing Notes

- Public repositories: baseline security features are generally available without paid add-ons.
- Private/internal repositories: code scanning and advanced secret scanning protections require paid GitHub security licensing (GitHub Code Security / GitHub Secret Protection, formerly GHAS entitlements).
- Team plan alone does not automatically grant all private-repo advanced security features.
