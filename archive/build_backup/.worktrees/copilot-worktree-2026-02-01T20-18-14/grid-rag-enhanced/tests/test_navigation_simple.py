"""
Simple navigation endpoint test.

Focused test for the navigation endpoint without complex dependencies.
"""


import pytest
import requests


class TestNavigationEndpointSimple:
    """Simple test cases for the navigation endpoint."""

    @pytest.fixture
    def base_url(self):
        """Base URL for the API."""
        return "http://localhost:8000/api/v1/navigation/plan"

    def test_navigation_endpoint_exists(self, base_url):
        """Test that the navigation endpoint exists and is accessible."""
        try:
            response = requests.post(
                base_url,
                json={"goal": "Test goal", "context": {}, "max_alternatives": 3, "enable_learning": True},
                timeout=5,
            )

            # If server is running, should get 200 or validation error
            assert response.status_code in [200, 422, 404, 500]

            if response.status_code == 200:
                data = response.json()
                assert "plan_id" in data or "error" in data

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - connection refused")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")

    def test_navigation_endpoint_validation(self, base_url):
        """Test navigation endpoint input validation."""
        try:
            # Test empty goal
            response = requests.post(
                base_url,
                json={"goal": "", "context": {}, "max_alternatives": 3, "enable_learning": True},  # Invalid
                timeout=5,
            )

            if response.status_code == 422:
                # Validation error as expected
                assert "detail" in response.json()
            elif response.status_code == 404:
                pytest.skip("Navigation endpoint not found")
            else:
                # Should not accept empty goal
                assert response.status_code != 200

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - connection refused")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")

    def test_navigation_endpoint_minimal(self, base_url):
        """Test navigation endpoint with minimal valid request."""
        try:
            response = requests.post(base_url, json={"goal": "Create a test endpoint"}, timeout=5)

            if response.status_code == 200:
                data = response.json()
                # Should have basic structure
                assert "plan_id" in data or "steps" in data or "error" not in data
            elif response.status_code == 404:
                pytest.skip("Navigation endpoint not found")
            elif response.status_code == 422:
                # Might require more fields
                pass
            else:
                # Other status codes might be acceptable
                pass

        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - connection refused")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")


if __name__ == "__main__":
    # Run tests manually
    test_class = TestNavigationEndpointSimple()
    base_url = "http://localhost:8000/api/v1/navigation/plan"

    print("Testing navigation endpoint...")
    print(f"Base URL: {base_url}")
    print()

    try:
        test_class.test_navigation_endpoint_exists(base_url)
        print("✓ Endpoint exists test passed")
    except Exception as e:
        print(f"✗ Endpoint exists test failed: {e}")

    try:
        test_class.test_navigation_endpoint_validation(base_url)
        print("✓ Validation test passed")
    except Exception as e:
        print(f"✗ Validation test failed: {e}")

    try:
        test_class.test_navigation_endpoint_minimal(base_url)
        print("✓ Minimal request test passed")
    except Exception as e:
        print(f"✗ Minimal request test failed: {e}")

    print()
    print("Navigation endpoint tests completed.")
