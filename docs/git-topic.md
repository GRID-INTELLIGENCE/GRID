# git-topic PoC

This documents the `git-topic` proof-of-concept included in `scripts/`.

Summary
- Purpose: make topic/theme oriented work easier by scaffolding branches, storing metadata, and creating PR drafts.
- PoC location: `scripts/git-topic` (Python script).

Usage examples

- Create a new topic branch:

  ```bash
  python scripts/git-topic create --theme research --short "entity clustering" --issue 123 --push
  ```

- Show metadata for current branch:

  ```bash
  python scripts/git-topic info
  ```

- Draft a PR for the current branch:

  ```bash
  python scripts/git-topic finish
  ```

Branch naming policy (PoC)
- Branches should follow `topic/<theme>-<short>-<issue?>` where theme and short use lowercase, hyphens, and numbers.

Integration notes
- Automatic issue/PR creation with GitHub/GitLab is intentionally not implemented in the PoC.
- CI validations, hooks, and full GitHub API integration can be added as opt-in features.

Next steps
- Add robust CLI (entrypoints), tests that exercise git commands in ephemeral repos, and CI workflows to validate branch names.
