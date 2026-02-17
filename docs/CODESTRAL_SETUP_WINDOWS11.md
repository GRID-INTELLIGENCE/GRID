# Codestral Client Setup for Windows 11

This guide will help you set up the Codestral client on Windows 11 for secure and efficient usage
of the API.

## Prerequisites

- Windows 11 (64-bit)
- Internet connection
- Administrator privileges (for software installation)

## Setup Instructions

### 1. Install Python

1. Download the latest Python 3.11+ installer from
[python.org](https://www.python.org/downloads/windows/)
2. Run the installer
3. Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation by opening PowerShell and running:
   ```powershell
   python --version
   ```

### 2. Set Up Project Directory

1. Open PowerShell as Administrator
2. Create a project directory:
   ```powershell
   mkdir ~\codestral-project
   cd ~\codestral-project
   ```

### 3. Set Environment Variable for API Key

For security, we'll set the API key as a system environment variable:

#### Option A: Using PowerShell (Current Session Only)
```powershell
$env:gridstral_code_api_key = "your_api_key_here"
```

#### Option B: Permanent User-level Setting (recommended)
1. Press `Win + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "System variables", click "New"
5. Variable name: `gridstral_code_api_key`
6. Variable value: `your_api_key_here`
7. Click OK to save

### 4. Create and Activate Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate the environment
.\.venv\Scripts\Activate.ps1
```

### 5. Install Required Packages

Install the minimal Codestral dependencies from the dedicated manifest:

```powershell
pip install -r requirements.codestral.txt
```

### 6. Create the Client Script

Create a file named `codestral_client.py` in the `src/grid/` package (the project already contains `src/grid/codestral_client.py`) and use it from your scripts. The client reads `gridstral_code_api_key` by default.

### 7. Verification

Create a test script `test_codestral.py`:

```python
from grid.codestral_client import get_codestral_client

def main():
    try:
        client = get_codestral_client()
        print("Client initialized successfully!")

        # Test code generation
        response = client.generate_code(
            prompt="Write a function that calculates factorial in Python",
            language="python"
        )
        print("\nGenerated code:")
        print(response)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
```
