# UV Usage Guide (Quick)

**UV is the official Python venv/package manager for this repo.** All virtual environment and package operations should use UV—not `python -m venv` or `pip`. This ensures consistent dependency resolution and faster installs.

## Global
- Ensure `C:\Users\irfan\.local\bin` is on PATH (already set).
- Python pinned: 3.13.

## Main project (root)
```powershell
Set-Location e:\grid
uv venv --python 3.13 --clear
.\.venv\Scripts\Activate.ps1
uv sync --group dev --group test
```

## Departments
- **light_of_the_seven**
  ```powershell
  Set-Location e:\grid\light_of_the_seven
  uv venv --python 3.13 --clear
  .\.venv\Scripts\Activate.ps1
  uv pip sync requirements.txt
  ```
- **data**
  ```powershell
  Set-Location e:\grid\data
  uv venv --python 3.13 --clear
  .\.venv\Scripts\Activate.ps1
  uv pip sync requirements.txt
  ```
- **docs**
  ```powershell
  Set-Location e:\grid\docs
  uv venv --python 3.13 --clear
  .\.venv\Scripts\Activate.ps1
  uv pip sync requirements.txt
  ```
- **datakit**
  ```powershell
  Set-Location e:\grid\datakit
  uv venv --python 3.13 --clear
  .\.venv\Scripts\Activate.ps1
  uv pip sync requirements-core.txt
  uv pip sync requirements-ml.txt
  uv pip sync requirements-viz.txt
  ```
- **Arena/the_chase/python**
  ```powershell
  Set-Location e:\grid\Arena\the_chase\python
  uv venv --python 3.13 --clear
  .\.venv\Scripts\Activate.ps1
  uv sync
  ```

## Sanity checks (run inside each venv)
```powershell
uv --version
python --version
uvx ruff --version
uv run python -c "import requests; print('OK')"
```

## Notes
- If you see hardlink warnings, set `UV_LINK_MODE=copy` (or `--link-mode=copy`).
- Use `--clear` to skip the venv replace prompt.
- For `.in` → `.txt` flows, specify the department and we can add them.
