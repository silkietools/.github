# Silkie Tools Org Defaults

Org-wide defaults for `silkietools` repositories.

[![YouTube Walkthrough](https://img.shields.io/badge/YouTube-Watch%20walkthrough-FF0000?logo=youtube&logoColor=white)](https://www.youtube.com/watch?v=XWWyVmvqBJ8)
[![shpit.dev Tutorials](https://img.shields.io/badge/shpit.dev-More%20tutorials-0A66C2?logo=googlechrome&logoColor=white)](https://www.shpit.dev/)

## Mission

Build tech behind [silkie.tools](https://silkie.tools/) so SMB retail teams can run faster in thin-margin markets.

## Multi-Org Featured Content Contract (for shpit.dev)

Use this contract to ingest content from many orgs and include only featured repos based on README front matter.

- Spec: `docs/shpit-content-contract.md`
- Parser target: root `README.md` front matter in each repo
- Include rule: `shpit.include: true`
- Featured rule: `shpit.featured: true`
- Display description source: `shpit.display.description` (fallback to GitHub repo description)

## Contains

- Org profile: `profile/README.md`
- Content import contract: `docs/shpit-content-contract.md`
- Default docs: contribution, security, support, conduct
- Default templates: issue + pull request

## Testing and CI

| Layer | Present | Tooling | Runs in CI |
|---|---|---|---|
| unit | no | none | no |
| integration | no | none | no |
| e2e api | no | none | no |
| e2e web | no | none | no |

No CI configuration is defined in this repository.

## Notes

- No runtime code
- Purpose: shared standards, not app logic
