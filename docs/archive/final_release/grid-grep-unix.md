# GRID: Unix & WSL Integration (Grep & Git)
**Bridging Environments for High-Performance Search**

This guide details how to leverage Unix-style tools (`grep`, `sed`, `awk`) and `git` within the GRID ecosystem, specifically for users operating in Hybrid Windows/WSL2 environments.

---

## 🐚 Git Operations (Windows/WSL2)

### 1. Cross-Environment Git Config
To avoid line-ending issues and permission mismatch:
```bash
git config --global core.autocrlf true
git config --global core.filemode false
```

### 2. Fast Staging (P1 Priority)
For high-speed commits during sprint cycles:
```powershell
# In PowerShell:
git add . ; git commit -m "STABILIZATION: [Module Name]" ; git push --no-verify
```

---

## 🔍 Advanced Search (`grid-grep-unix`)
The `grid-grep` core utilizes `ripgrep`, which behaves like Unix `grep` but at multi-thread speeds.

### Unix Equivalents in GRID:
| Goal | Unix Command | GRID (`grid-grep`) Equivalent |
|------|--------------|------------------------------|
| Search for string | `grep -r "pattern" .` | `grid-grep.exe "pattern"` |
| Regex search | `grep -E "pattern" .` | `grid-grep.exe -e "pattern"` |
| Filter by file type | `grep --include="*.py"` | `grid-grep.exe -t py "pattern"` |
| Count matches | `grep -c "pattern"` | `grid-grep.exe -c "pattern"` |

### Pipe & Process Examples:
To count instances of `ClusteringService` in `legacy_src`:
```bash
# WSL/Unix Terminal:
grep -r "ClusteringService" legacy_src | wc -l
```

---

## 🛠️ Performance Tuning for WSL
If running GRID inside WSL2, ensure the project is on the Linux filesystem (`/home/...`) rather than the mounted Windows drive (`/mnt/e/...`) for P99 disk latency improvements.

---

**Authorized by**: GRID DevOps
**Last Updated**: 2026-01-06
