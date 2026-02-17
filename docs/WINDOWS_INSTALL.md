# Quick Installation Guide for Windows

If you encounter Rust compilation errors during installation, follow these steps:

## Option 1: Install Qiskit Only (Recommended for Windows)

```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install core Qiskit packages individually
pip install qiskit
pip install qiskit-ibm-runtime
pip install qiskit-algorithms

# Install other Grid requirements
pip install -r requirements.txt --no-deps
pip install fastapi uvicorn pydantic sqlalchemy click rich loguru pytest openai networkx python-dateutil
```

## Option 2: Use Pre-built Wheels

Download pre-built wheels from:
- https://pypi.org/project/qiskit/#files
- https://pypi.org/project/qiskit-ibm-runtime/#files

Then install:
```bash
pip install downloaded_wheel_file.whl
```

## Option 3: Install Rust (If you need qiskit-optimization)

If you specifically need `qiskit-optimization` which requires Rust:

1. Download Rust from: https://rustup.rs/
2. Run the installer and follow prompts
3. Restart your terminal
4. Verify: `cargo --version`
5. Then: `pip install qiskit-optimization`

## Verify Installation

```bash
python -c "import qiskit; print(qiskit.__version__)"
python -c "from qiskit_ibm_runtime import QiskitRuntimeService; print('Runtime OK')"
```

## Troubleshooting

### Error: "Rust not found"
- Skip qiskit-optimization for now (it's optional for basic quantum workflows)
- Core quantum features work with just qiskit + qiskit-ibm-runtime

### Error: "No matching distribution"
- Ensure you're using Python 3.9-3.12
- Check: `python --version`

### Still Having Issues?
- Try installing in a fresh virtual environment:
  ```bash
  python -m venv venv_quantum
  venv_quantum\Scripts\activate
  pip install qiskit qiskit-ibm-runtime qiskit-algorithms
  ```
