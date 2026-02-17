# shpit.dev Content Contract (v1)

Use this schema to programmatically pull relevant content across many GitHub orgs and include only featured repos.

## Goal

Standardize a front matter contract in each repo's root `README.md` so `shpit.dev` can:

- discover repos across 7+ orgs
- filter to featured repos
- render a clean title + description for cards/lists

## Required Front Matter

Place this at the top of each repository `README.md`:

```yaml
---
shpit:
  include: true
  featured: true
  display:
    title: "Repo Title for shpit.dev"
    description: "One clear sentence about what this repo helps you build or learn."
---
```

## Optional Fields

```yaml
---
shpit:
  org: "silkietools"
  priority: 100
  tags:
    - scraping
    - compute
    - workflows
  links:
    docs: "https://github.com/org/repo#readme"
    tutorial: "https://www.shpit.dev/"
---
```

## Field Semantics

- `shpit.include`: hard gate for import. If false or missing, skip repo.
- `shpit.featured`: controls featured sections on `shpit.dev`.
- `shpit.display.title`: stable UI title for imported cards.
- `shpit.display.description`: user-facing summary shown on `shpit.dev`.
- `shpit.priority`: sort descending when multiple featured repos exist.

## Description Guidance

`shpit.display.description` should:

- be 90 to 180 characters
- describe outcome/value, not internal implementation details
- read cleanly as standalone UI text

Good example:
"TypeScript scraper starter showing robust pagination, retries, and normalized output for marketplace-style data ingestion."

## Import Behavior (Recommended)

1. Query target org repos.
2. Keep repos marked as featured (GitHub metadata) or parse all repos if you prefer contract-only filtering.
3. Fetch root `README.md` from each repo.
4. Parse front matter and keep repos where `shpit.include: true`.
5. Use `shpit.display.description` for site cards; fallback to GitHub repo description if missing.
6. Sort by `shpit.priority` (high to low), then `updated_at` (newest first).
