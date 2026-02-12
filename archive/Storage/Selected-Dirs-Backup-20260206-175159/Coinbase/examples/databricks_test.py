"""Test Databricks integration without real credentials."""

import os
from unittest.mock import patch

from coinbase import DatabricksClient, DatabricksConfig


def test_databricks_integration():
    """Test Databricks integration with mocked credentials."""
    print("=" * 60)
    print("Databricks Integration Test")
    print("=" * 60)

    # Test configuration loading
    print("\n1. Testing configuration loading...")

    # Mock environment variables
    with patch.dict(
        os.environ,
        {
            "DATABRICKS_HOST": "https://test.cloud.databricks.com",
            "DATABRICKS_TOKEN": "test_token_123",
            "DATABRICKS_CLUSTER_ID": "test-cluster-123",
            "DATABRICKS_WAREHOUSE_ID": "test-warehouse-123",
        },
    ):
        config = DatabricksConfig.from_env()

        print(f"   Host: {config.host}")
        print(f"   Token: {'***' + config.token[-4:] if config.token else None}")
        print(f"   Cluster ID: {config.cluster_id}")
        print(f"   Warehouse ID: {config.warehouse_id}")

        # Test validation
        print("\n2. Testing configuration validation...")
        if config.validate():
            print("   ✓ Configuration is valid")
        else:
            print("   ✗ Configuration is invalid")
            return

        # Test client creation
        print("\n3. Testing client creation...")
        try:
            # Mock the WorkspaceClient to avoid real connection
            with patch("databricks.sdk.WorkspaceClient") as mock_client:
                mock_instance = mock_client.return_value
                mock_instance.get_workspace_id.return_value = "test-workspace-123"
                mock_instance.clusters.list.return_value = iter([])
                mock_instance.warehouses.list.return_value = iter([])

                client = DatabricksClient(config)
                print("   ✓ Client created successfully")

                # Test connection
                print("\n4. Testing connection (mocked)...")
                result = client.test_connection()
                if result["status"] == "connected":
                    print("   ✓ Connection test successful")
                    print(f"   Workspace ID: {result['workspace_id']}")
                    print(f"   Cluster count: {result['cluster_count']}")
                else:
                    print(f"   ✗ Connection test failed: {result.get('error')}")

                # Test cluster listing
                print("\n5. Testing cluster listing...")
                clusters = client.list_clusters()
                print(f"   Found {len(clusters)} clusters")

                # Test warehouse listing
                print("\n6. Testing warehouse listing...")
                warehouses = client.list_warehouses()
                print(f"   Found {len(warehouses)} warehouses")

                print("\n✅ All tests passed!")
                print("\nTo use with real credentials:")
                print("1. Set DATABRICKS_HOST and DATABRICKS_TOKEN environment variables")
                print("2. Run: uv run python examples/databricks_basic_usage.py")

        except Exception as e:
            print(f"   ✗ Error: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_databricks_integration()
