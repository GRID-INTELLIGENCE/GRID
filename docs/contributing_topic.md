# Topic branches & `git-topic` guidance

This file contains a minimal contribution policy for topic-oriented work and how to use the PoC.

## Branch naming
- Format: `topic/<theme>-<short>-<issue?>`
- Example: `topic/research-entity-clustering-123`
- Allowed characters are lowercase letters, numbers and hyphens.

## Using the PoC
1. Create branch:
   ```bash
   python scripts/git-topic create --theme research --short "entity clustering" --issue 123 --push
   ```
2. Inspect metadata on your branch:
   ```bash
   python scripts/git-topic info
   ```
3. Create a PR draft:
   ```bash
   python scripts/git-topic finish
   ```

## Git hooks
To enforce branch naming locally, install the PoC commit hook:
```bash
bash scripts/install-hooks.sh
```

## Templates
- Issue template: `.github/ISSUE_TEMPLATE/topic_issue.md`
- PR template: `.github/PULL_REQUEST_TEMPLATE/topic_pr.md`

## Notes for maintainers
- The PoC intentionally avoids automatic GitHub API calls — integration is opt-in.
- Consider adding a GitHub Action to block invalid branch names (see `.github/workflows/validate-topic.yml`).
