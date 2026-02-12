# Git Repositories and Worktrees (D:\ and F:\)

Summary of Git repos and worktrees found on D:\ (and F:\ when available). Last scan: 2026-02-07.

---

## D:\ — Full Git repositories (four)

All under `D:\Build`; each has a `.git` directory.

| Repo path | Branch | Last commit | Remote |
|-----------|--------|-------------|--------|
| D:\Build\Coinbase | main | `8f25eee` — "git save progress" | none |
| D:\Build\GRID | main | `c9d1308` — "docs: add Git and branch best practices..." | origin → `https://github.com/caraxesthebloodwyrm02/GRID.git` |
| D:\Build\GRID-main | main | `c9d1308` — same as GRID | origin → `https://github.com/caraxesthebloodwyrm02/GRID.git` |
| D:\Build\wellness_studio | main | `4ac66f9` — "safety checkpoint" | none |

- **GRID** and **GRID-main** are both the same remote and same commit; they are two clones of the same repo. Consider using one and archiving the other to avoid confusion (see [Deduplication](#deduplication) below).
- **Coinbase** and **wellness_studio** have no remotes (local-only or not set).

---

## D:\ — Git worktrees (two)

Both under `D:\Build\.worktrees`. Each has a `.git` **file** (not a directory) pointing to the main repo on **E:\**.

| Worktree path | Points to (main repo worktree dir) |
|---------------|-------------------------------------|
| D:\Build\.worktrees\copilot-worktree-2026-02-01T20-18-14 | `E:/.git/worktrees/copilot-worktree-2026-02-01T20-18-14` |
| D:\Build\.worktrees\copilot-worktree-2026-02-07T01-40-39 | `E:/.git/worktrees/copilot-worktree-2026-02-07T01-40-39` |

Git data (commits, refs) for these worktrees live on E:\. When E:\ is available, run from E:\: `git status`, `git worktree list`, `git log -1 --oneline`.

---

## Other D:\Build locations

- **D:\Build\grid.worktrees** — exists, empty (no worktrees).
- **D:\Build\GRID-main.old** — backup from earlier restore.
- **D:\Build\user_context** — no `.git` (not a Git repo).
- **D:\Storage** — no `.git` found (scan depth 6).

---

## E:\ and F:\

- **E:\** — Main repo for the two worktrees above. If E:\ is mounted, run: `git -C E:\ status`, `git -C E:\ worktree list`, `git -C E:\ log -1 --oneline`. At last check (implementation time), E:\ was not accessible (e.g. drive not mounted).
- **F:\** — Not present or not accessible at last check. When F:\ is available, run the same `.git` search (directories and files) as on D:\ to list repos and worktrees.

---

## Deduplication

**GRID** and **GRID-main** on D:\ are duplicate clones (same remote, same commit). To simplify:

- Prefer one as the primary (e.g. `D:\Build\GRID-main` for consistency with RESTORE.md).
- Archive or remove the other (e.g. rename to `GRID-archive` or delete after confirming the primary is up to date).

No automatic change was made; update this doc after you consolidate.
