import asyncio
import os
import sys

# Add project root to path to allow importing app
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


async def verify_endpoints():
    # Since we can't easily spin up the full complex app in this script without dependencies,
    # we will rely on unit-test style import and direct router invocation if possible,
    # OR assume the user handles the server.
    # But the user asked ME to implement and verify.
    # A better approach is to use FastAPI's TestClient on the router directly.

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from application.resonance.api.performance import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    endpoints = [
        "/performance/sales",
        "/performance/user-behavior",
        "/performance/product-data",
        "/performance/development-data",
    ]

    print("Verifying Performance API Endpoints...")
    all_passed = True

    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...", end=" ")
            response = client.get(endpoint)
            if response.status_code == 200:
                print("OK")
                # print(response.model_dump_json()) # Verbose
            else:
                print(f"FAILED ({response.status_code})")
                print(response.text)
                all_passed = False
        except Exception as e:
            print(f"ERROR: {e}")
            all_passed = False

    if all_passed:
        print("\nAll endpoints verified successfully.")
    else:
        print("\nSome endpoints failed verification.")


if __name__ == "__main__":
    asyncio.run(verify_endpoints())
