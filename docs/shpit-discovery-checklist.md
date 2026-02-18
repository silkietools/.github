# Repo Discovery Checklist (Metadata-First)

Use GitHub metadata + README content as the source of truth.
Do not require README front matter contracts.

## Goal

Keep discovery simple across public repos/orgs while maintaining high-quality cards/lists.
Default discovery topic in this repo is `shpit`, but this is configurable via `config/repo-metadata-policy.json`.

## Discovery Inputs (Source of Truth)

1. GitHub repository description
2. GitHub topics/tags (include the configured discovery topic when a repo should be imported)
3. Root `README.md`
4. Repository primary language from GitHub metadata

Notes:
- Language should come from GitHub API metadata, not manual README text.
- Badges can still communicate stack/tooling in README.

## Required Repo Metadata

Each public repo that should be imported must have:

- [ ] A non-empty GitHub description (1 clear sentence, outcome-focused)
- [ ] Required discovery topic/tag (default: `shpit`)
- [ ] A root `README.md`

Recommended for discovery (warning-level in automation, not hard fail):

- [ ] Topic/tag `shpit`
- [ ] Label `shpit`

Cross-org metadata baseline (applies to all repos):

- [ ] Public repos meet minimum README structure (title, badges, key sections)
- [ ] Labels stay useful for triage/workflow (not repo-name repetition)

## README Checklist (Recommended)

Use this checklist to keep repo pages consistent and crawl-friendly:

- [ ] Clear title + one-line summary near the top
- [ ] Short "what it does" bullets
- [ ] Badge block for stack/tooling/CI where relevant
- [ ] Quick start or usage section (if runnable)
- [ ] Testing + CI status section (explicit even when missing)
- [ ] Links to docs/demo/tutorial if applicable

## Visual Asset / Icon (Optional but Useful)

For repos that should stand out in cards, include at least one of:

- `assets/icon.*` (project icon)
- `assets/cover.*` or `assets/preview.*` (card/hero visual)
- Open Graph/social preview image configured via repo docs/site

If present, crawler/UI can prioritize these visuals for richer cards.

## Recommended Import Behavior

1. Query public repos for each target org.
2. Keep public repos containing the configured discovery topic.
3. Fetch GitHub metadata (name, description, topics, primary language, updated_at).
4. Fetch root `README.md` when available.
5. Build cards from metadata first; enrich with README badges/links.
6. Sort by your chosen featured logic, then `updated_at` desc.

## Content Quality Workflow

Use the `readme-maintainer` skill to standardize README quality across repos.
Use `scripts/repo_metadata_audit.py` for org-level enforcement of metadata + README checks.

Minimum expectation per imported repo:

- description set
- configured discovery tag set
- README updated with concise summary + key badges + usage context
