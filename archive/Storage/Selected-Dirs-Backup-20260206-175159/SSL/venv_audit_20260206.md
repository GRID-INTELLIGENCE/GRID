# Python Virtual Environment Audit Report
**Generated:** 2026-02-06  
**Scope:** `E:\` drive — all project directories  
**System Python:** 3.14.3 (`C:\Users\GRID\AppData\Local\Microsoft\WindowsApps\python.exe`)  
**Old Venvs Python:** 3.13.11 (`C:\Users\irfan\AppData\Local\Programs\Python\Python313\python.exe`) — **ACCESS DENIED**  
**Status:** ✅ **CLEANUP EXECUTED**

---

## Executive Summary

| # | Venv | Size | Project | Has requirements/pyproject | Verdict |
|---|------|------|---------|---------------------------|---------|
| 1 | `E:\.venv` | **1,229 MB** | Root (no project) | None | **DELETE** — orphan, bloated |
| 2 | `E:\Coinbase\.venv` | **76 MB** | Coinbase | `pyproject.toml` | **KEEP** — lean, project-scoped |
| 3 | `E:\grid\.venv` | **1,204 MB** | Grid | `pyproject.toml` + `requirements.txt` | **KEEP** — large but justified |
| 4 | `E:\wellness_studio\.venv` | **1,187 MB** | Wellness Studio | `requirements.txt` + `setup.py` | **RECREATE** — wrong origin path |
| 5 | `E:\SSL\.venv` | **N/A** | SSL/Wireshark Monitor | None | **CREATE** — missing, needed |
| 6 | `E:\security\.venv` | **N/A** | Security | `requirements.txt` | **CREATE** — missing, needed |

**Total current disk usage:** ~3,696 MB (~3.6 GB)  
**Estimated after cleanup:** ~2,467 MB (~2.4 GB) — saves **~1.2 GB**

---

## Detailed Findings

### 1. `E:\.venv` — ROOT VENV ❌ DELETE

- **Origin:** `python -m venv e:\.venv` (created at root level)
- **Python:** 3.13.11 (base interpreter has **Access Denied** — broken)
- **Size:** 1,229 MB
- **Packages:** 130+ packages including torch, transformers, flask, fastapi, locust, kubernetes, mistralai, etc.
- **Problem:** No `requirements.txt`, `pyproject.toml`, or `setup.py` at `E:\` root. This is an orphan "kitchen sink" venv with no project ownership. It duplicates packages already in `E:\grid\.venv` and `E:\wellness_studio\.venv`.
- **Risk:** The base Python path (`C:\Users\irfan\...`) returns Access Denied, making pip operations fail.
- **Action:** **Delete entirely.** No project depends on it.

### 2. `E:\Coinbase\.venv` — ✅ KEEP

- **Origin:** Created by `uv` (v0.9.28), prompt = "Coinbase"
- **Python:** 3.13.11 (CPython)
- **Size:** 76 MB (lean)
- **Packages:** 21 packages — black, ruff, mypy, pytest, pytest-cov, jwt, click, etc.
- **Config:** `E:\Coinbase\pyproject.toml` — well-defined with `click>=8.3.1`, `pyjwt>=2.8.0` + dev/test groups
- **Status:** Healthy, properly scoped, minimal footprint.
- **Action:** **Keep as-is.** No changes needed.

### 3. `E:\grid\.venv` — ✅ KEEP (monitor size)

- **Origin:** `python -m venv E:\grid\.venv`
- **Python:** 3.13.11
- **Size:** 1,204 MB
- **Packages:** 170+ packages — torch, transformers, chromadb, celery, fastapi, sqlalchemy, pandas, numpy, ollama, mcp, etc.
- **Config:** `E:\grid\pyproject.toml` (16 KB) + `E:\grid\requirements.txt` (105 deps) + `E:\grid\requirements-dev.txt`
- **Status:** Large but justified — Grid is the main monorepo with ML, RAG, database, and task queue deps.
- **Action:** **Keep.** Consider periodic `pip cache purge` to reclaim space.

### 4. `E:\wellness_studio\.venv` — ⚠️ RECREATE

- **Origin:** `python -m venv C:\Users\irfan\CascadeProjects\windsurf-project-2\.venv` — **WRONG PATH**
- **Python:** 3.13.11
- **Size:** 1,187 MB
- **Packages:** 95+ packages — torch, whisper, librosa, transformers, sentence-transformers, pdfplumber, etc.
- **Config:** `E:\wellness_studio\requirements.txt` (93 lines) + `E:\wellness_studio\setup.py`
- **Problem:** The `pyvenv.cfg` records the venv was created at `C:\Users\irfan\CascadeProjects\windsurf-project-2\.venv`, then moved/copied to `E:\wellness_studio\.venv`. This can cause subtle path resolution bugs.
- **Action:** **Recreate in-place** at `E:\wellness_studio\.venv` and reinstall from `requirements.txt`.

### 5. `E:\SSL\.venv` — 🆕 CREATE

- **Python files:** `E:\SSL\wireshark-monitor\scripts\parse_traffic.py` (requires `pyshark`)
- **Config:** None — no `requirements.txt` exists
- **Action:** **Create venv + requirements.txt** with `pyshark` and its dependencies.

### 6. `E:\security\.venv` — 🆕 CREATE

- **Python files:** 5 scripts in `E:\security\` (`monitor_network.py`, `network_interceptor.py`, etc.)
- **Config:** `E:\security\requirements.txt` — pyyaml, rich, requests, httpx, aiohttp, pytest
- **Action:** **Create venv** and install from existing `requirements.txt`.

---

## Critical Issue: Broken Base Python

All four existing venvs reference `C:\Users\irfan\AppData\Local\Programs\Python\Python313\python.exe`, which returns **Access Denied**. The current system Python is `3.14.3` at `C:\Users\GRID\AppData\Local\Microsoft\WindowsApps\python.exe`.

This means:
- `pip` commands fail in all existing venvs
- New venvs will use Python 3.14.3 (different minor version)
- Existing venvs with compiled extensions (torch, numpy) may need rebuilding

---

## Recommended Actions (in order)

| Step | Action | Command |
|------|--------|---------|
| 1 | **Delete root orphan venv** | `Remove-Item -Recurse -Force "E:\.venv"` |
| 2 | **Create SSL venv + deps** | `python -m venv "E:\SSL\.venv"` then install pyshark |
| 3 | **Create SSL requirements.txt** | See below |
| 4 | **Create security venv + deps** | `python -m venv "E:\security\.venv"` then install from requirements.txt |
| 5 | **Recreate wellness_studio venv** | Delete old, `python -m venv "E:\wellness_studio\.venv"`, reinstall |
| 6 | **Verify Coinbase & Grid venvs** | Test with `python -c "import click"` etc. |

---

## Files to Create

### `E:\SSL\requirements.txt`
```
# SSL/Wireshark Monitor - Dependencies
# =====================================
# Required by: wireshark-monitor/scripts/parse_traffic.py

pyshark>=0.6
pyyaml>=6.0.1
```

---

## .gitignore Status

`E:\.gitignore` already contains `.venv/` and `venv/` — all venvs are properly excluded from git.

---

## Disk Space Summary

| State | Total venv size |
|-------|----------------|
| **Before cleanup** | ~3,696 MB |
| After deleting `E:\.venv` | ~2,467 MB |
| After recreating wellness_studio | ~2,467 MB (same, rebuilt) |
| After adding SSL + security venvs | ~2,480 MB (minimal additions) |

---

## Execution Log (2026-02-06)

### ✅ Completed Actions

| # | Action | Result |
|---|--------|--------|
| 1 | **Deleted `E:\.venv`** | Removed 1,229 MB orphan venv |
| 2 | **Created `E:\SSL\.venv`** | Python 3.14.3, pyshark + pyyaml installed, verified ✅ |
| 3 | **Created `E:\SSL\requirements.txt`** | Dependency manifest for `parse_traffic.py` |
| 4 | **Created `E:\security\.venv`** | Python 3.14.3, all deps from requirements.txt installed, verified ✅ |
| 5 | **Recreated `E:\wellness_studio\.venv`** | Python 3.14.3, correct origin path, 91 packages installed |

### ⚠️ Known Issue: Torch on Wellness Studio

`torch` fails to load with `OSError: [WinError 126]` because **Microsoft Visual C++ Redistributable** is not installed.
- **Fix:** Download and install from https://aka.ms/vs/17/release/vc_redist.x64.exe
- **Impact:** `torch`, `whisper`, `transformers`, `sentence-transformers` won't work until VC++ is installed
- **Non-torch deps:** All verified working (pandas, numpy, pydantic, sklearn, librosa, rich, click)

### ⚠️ Known Issue: Grid & Coinbase Venvs (Python 3.13)

`E:\grid\.venv` and `E:\Coinbase\.venv` still reference Python 3.13.11 at `C:\Users\irfan\...` (Access Denied).
- **Impact:** `pip install/uninstall` will fail in these venvs
- **Fix:** Recreate when ready: `python -m venv E:\grid\.venv` + reinstall from `requirements.txt`
- **Note:** Grid venv is 1.2 GB with 170+ packages — recreating takes significant time and bandwidth

### Final Venv State

| Venv | Python | Origin | Status |
|------|--------|--------|--------|
| `E:\SSL\.venv` | 3.14.3 | Correct | ✅ Fresh, working |
| `E:\security\.venv` | 3.14.3 | Correct | ✅ Fresh, working |
| `E:\wellness_studio\.venv` | 3.14.3 | Correct | ⚠️ Working (except torch — needs VC++ Redist) |
| `E:\Coinbase\.venv` | 3.13.11 | Stale user path | ⚠️ Kept — pip broken, packages still usable |
| `E:\grid\.venv` | 3.13.11 | Stale user path | ⚠️ Kept — pip broken, packages still usable |
| `E:\.venv` | — | — | ❌ Deleted |
