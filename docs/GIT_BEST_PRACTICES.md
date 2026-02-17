# Git & Branch Best Practices

Guidance for working with Git and branches in the GRID repository.

## Source of truth

- **`main`** is the single source of truth.
- All production-ready work lives on `main`. Feature and topic branches are for short-lived work, then merged or discarded.
- Keep `main` always runnable: green tests, passing lint, no broken imports.

## Branch strategy

| Branch type | Purpose | Lifecycle |
|-------------|---------|-----------|
| **main** | Production-ready code; default branch | Permanent |
| **feature/\*** | New features, kept small and mergeable | Merge to main, then delete |
| **fix/\*** | Bugfixes | Merge to main, then delete |
| **chore/\*** | Tooling, config, docs | Merge to main, then delete |
| **cascade/\*** | Snapshot/worktree branches | Archive or delete after sync |

## Best practices

### 1. Work from main

- Create feature branches from **current** `main`:  
  `git checkout main && git pull && git checkout -b feature/your-thing`
- Avoid long-lived branches; merge back frequently so history stays related.

### 2. Avoid unrelated histories

- **Do not** force-push a different history to `main` (e.g. from another fork or after a full rewrite). That makes existing branches “unrelated” and blocks normal merges.
- If you must replace history (e.g. squash migration), coordinate with the team and treat old branches as obsolete; re-branch from the new `main` for new work.

### 3. Merging into main

- Prefer **merge** (or squash-merge in the UI) so main gains the branch commits.
- Only use `--allow-unrelated-histories` in rare cases (e.g. merging a separate repo); expect many conflicts and resolve carefully.
- Before merging: run tests and lint on the branch.

### 4. Commits

- Use **`-m`** for commit messages:  
  `git commit -m "Your message"`  
  Without `-m`, Git treats the next argument as a path, not a message.
- Write clear, present-tense messages: “Add X”, “Fix Y”, “Refactor Z”.
- Commit often; push when the branch is in a good state for others (or CI).

### 5. Remotes and push

- Know which remote `main` tracks:  
  `git status -sb` or `git branch -vv`
- Push main explicitly if you have multiple remotes:  
  `git push origin2 main` (replace `origin2` with your main remote).

### 6. Local branch hygiene

- **List branches:**  
  `git branch -v`  
  `git branch -a` (includes remotes)
- **Delete merged branches** (optional):  
  - Merged into current branch:  
    `git branch --merged`  
  - Delete local only:  
    `git branch -d <name>`  
  - Delete remote:  
    `git push origin --delete <name>`
- Keep only branches you’re actively using; delete or archive the rest to avoid confusion.

### 7. When branches can’t merge

- If Git reports **“refusing to merge unrelated histories”**, the branch and `main` don’t share a common ancestor (e.g. after a history rewrite).
- **Options:**  
  - **Prefer:** Treat `main` as truth; re-apply only the changes you need (cherry-pick or manual copy), then delete the old branch.  
  - **Rare:** Merge with `--allow-unrelated-histories` and resolve many conflicts by hand (not recommended for many branches at once).

### 8. Configuration

- Prefer **global** config for identity and defaults:  
  `git config --global user.name "..."`  
  `git config --global user.email "..."`
- Use **local** config only for repo-specific overrides (e.g. remote URLs, branch defaults). Avoid duplicating identity in every repo.

## Quick reference

```powershell
# Ensure you're on main and up to date
git checkout main
git pull origin2 main   # or your main remote

# New feature
git checkout -b feature/short-name
# ... work, commit ...
git checkout main
git merge feature/short-name --no-edit
git push origin2 main
git branch -d feature/short-name

# Commit with message (PowerShell)
git add -A
git commit -m "Descriptive message"
git push origin2 main
```

## Related docs

- `docs/DEVELOPMENT_GUIDE.md` – Build, test, and run commands
- `docs/SECURITY_MAINTAINABILITY.md` – Security and maintenance
