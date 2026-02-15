# Publish grid-safety to PyPI

Install build tools (optional): `pip install -e ".[publish]"` from the `safety/` directory, or `pip install build twine`.

## Build

From repo root:

```bash
cd safety
python -m build --wheel --sdist
```

Artifacts: `safety/dist/grid_safety-1.0.0-py3-none-any.whl` and `grid_safety-1.0.0.tar.gz`.

## Upload

PyPI recommends using username **`__token__`** with your API token as the password.

1. Create an API token at [PyPI Account → API tokens](https://pypi.org/manage/account/token/).
2. Set it (PowerShell):

   ```powershell
   $env:TWINE_USERNAME = "__token__"
   $env:TWINE_PASSWORD = "<your-pypi-token>"
   ```

3. Upload from repo root:

   ```powershell
   python -m twine upload --skip-existing safety/dist/*
   ```

   Or with token in env:

   ```powershell
   $env:TWINE_USERNAME = "__token__"
   $env:PYPI_API_TOKEN = "<your-pypi-token>"
   $env:TWINE_PASSWORD = $env:PYPI_API_TOKEN
   python -m twine upload --skip-existing safety/dist/*
   ```

For **Test PyPI** first:

```powershell
$env:TWINE_REPOSITORY_URL = "https://test.pypi.org/legacy/"
python -m twine upload --skip-existing safety/dist/*
```
