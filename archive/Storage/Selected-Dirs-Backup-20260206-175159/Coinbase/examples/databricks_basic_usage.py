"""Basic usage example for Databricks integration."""

from coinbase import DatabricksClient, DatabricksConfig


def main():
    """Demonstrate basic Databricks usage."""
    print("=" * 60)
    print("Databricks Basic Usage Example")
    print("=" * 60)

    # Load configuration from environment variables
    print("\n1. Loading configuration from environment variables...")
    config = DatabricksConfig.from_env()

    print(f"   Host: {config.host}")
    print(f"   Cluster ID: {config.cluster_id}")
    print(f"   Warehouse ID: {config.warehouse_id}")
    print(f"   Account ID: {config.account_id}")

    # Validate configuration
    print("\n2. Validating configuration...")
    if config.validate():
        print("   ✓ Configuration is valid")
    else:
        print("   ✗ Configuration is invalid")
        print("   Required: DATABRICKS_HOST and DATABRICKS_TOKEN")
        return

    # Create client
    print("\n3. Creating Databricks client...")
    try:
        client = DatabricksClient(config)
        print("   ✓ Client created successfully")
    except Exception as e:
        print(f"   ✗ Failed to create client: {e}")
        return

    # Test connection
    print("\n4. Testing connection...")
    result = client.test_connection()

    if result["status"] == "connected":
        print("   ✓ Connection successful")
        print(f"   Workspace ID: {result['workspace_id']}")
        print(f"   Available clusters: {result['cluster_count']}")
    else:
        print(f"   ✗ Connection failed: {result.get('error')}")
        return

    # List clusters
    print("\n5. Listing available clusters...")
    clusters = client.list_clusters()
    print(f"   Found {len(clusters)} clusters:")
    for cluster in clusters[:3]:  # Show first 3
        cluster_name = cluster.get("cluster_name", "Unknown")
        cluster_state = cluster.get("state", "Unknown")
        print(f"   - {cluster_name} ({cluster_state})")

    # List warehouses
    print("\n6. Listing available SQL warehouses...")
    warehouses = client.list_warehouses()
    print(f"   Found {len(warehouses)} warehouses:")
    for warehouse in warehouses[:3]:  # Show first 3
        warehouse_name = warehouse.get("name", "Unknown")
        warehouse_state = warehouse.get("state", "Unknown")
        print(f"   - {warehouse_name} ({warehouse_state})")

    print("\n7. Basic usage routine complete!")
    print("\nNext steps:")
    print("   - Use client.run_sql_query() to execute SQL queries")
    print("   - Use client.list_clusters() to explore clusters")
    print("   - Use client.list_warehouses() to explore warehouses")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
