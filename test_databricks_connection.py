#!/usr/bin/env python3
"""Test Databricks connection with environment variables."""

from src.integration.databricks.client import DatabricksClient

def test_connection():
    print('🔍 Testing Databricks SDK client with environment variables...')
    
    try:
        client = DatabricksClient()
        clusters = client.list_clusters()
        print(f'✅ Connection successful! Found {len(clusters)} clusters')
        
        # Show cluster details
        for cluster in clusters[:3]:  # Show first 3
            cluster_name = cluster.get('cluster_name', 'Unknown')
            state = cluster.get('state', 'Unknown')
            print(f'  - {cluster_name} ({state})')
            
        return True
        
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        print('\n💡 To fix this:')
        print('1. Set DATABRICKS_HOST environment variable')
        print('2. Set DATABRICKS_TOKEN environment variable')
        print('3. Optional: Set DATABRICKS_HTTP_PATH for SQL connector')
        return False

if __name__ == "__main__":
    test_connection()
