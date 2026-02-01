import sys

import httpx

url = "http://localhost:11434/api/tags"
print(f"Testing {url}...")
try:
    r = httpx.get(url, timeout=10.0)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"Failed: {type(e).__name__}: {e}")
    sys.exit(1)
