# Security Baseline Enforcer

Automated org-wide security baseline:

- Dependabot vulnerability alerts
- Dependabot security updates
- Secret scanning
- Secret scanning push protection
- Secret scanning non-provider patterns
- CodeQL default setup

## Files

- Script: `scripts/enforce_security_baseline.py`
- Workflow: `.github/workflows/security-baseline-enforcer.yml`

## Local Run

```bash
python3 scripts/enforce_security_baseline.py \
  --org silkietools \
  --visibility all \
  --exclude .github \
  --output-json /tmp/security-baseline-report.json \
  --strict
```

## Workflow Secret

Set `ORG_ADMIN_TOKEN` in the `.github` repository (or org-level actions secrets) with permissions that can administer all target repositories.
