# Databricks Configuration Guide

## Runtime Version Requirements

### Minimum Runtime Version
- **Required**: Databricks Runtime 11.3 LTS or higher
- **Recommended**: Latest LTS version for security patches
- **Python Version**: Python 3.9+ (3.13 recommended for Coinbase)

### Runtime Selection
```python
# In Databricks cluster configuration:
Runtime: 11.3 LTS ML (or higher)
Python: 3.9+
```

## Access Modes

### Standard Access Mode
- **Description**: Shared cluster with isolated compute
- **Use Case**: Development and testing
- **Limitations**: 
  - No access to cluster root
  - Limited system libraries
  - Shared resources

### Dedicated Access Mode
- **Description**: Dedicated cluster with full access
- **Use Case**: Production workloads
- **Benefits**:
  - Full cluster access
  - Custom system libraries
  - Better isolation
  - Higher performance

### Recommendation
- **Development**: Standard access mode
- **Production**: Dedicated access mode

## Unity Catalog Configuration

### Catalog Setup
```sql
-- Create catalog
CREATE CATALOG IF NOT EXISTS coinbase;

-- Create schema
CREATE SCHEMA IF NOT EXISTS coinbase.portfolio;

-- Grant permissions
GRANT CREATE ON CATALOG coinbase TO `coinbase_users`;
GRANT ALL ON SCHEMA coinbase.portfolio TO `coinbase_users`;
```

### Managed Tables
- All tables are managed Delta Lake tables
- ACID transactions guaranteed
- Time Travel enabled (default 7 days)
- Automatic optimization

### Naming Constraints
- **Tables**: Lowercase with underscores (e.g., `portfolio_positions`)
- **Columns**: Lowercase with underscores (e.g., `user_id_hash`)
- **No spaces or dots** in names
- **No special characters** except underscores

## Cluster Configuration

### Minimum Cluster Specs
- **Workers**: 2-4 (development), 4+ (production)
- **Memory**: 16GB+ per worker
- **Storage**: DBFS or Unity Catalog Volumes
- **Node Type**: Memory-optimized

### Example Configuration
```json
{
  "cluster_name": "coinbase-analytics",
  "spark_version": "11.3.x-scala2.12",
  "node_type_id": "i3.xlarge",
  "num_workers": 4,
  "autotermination_minutes": 30,
  "data_security_mode": "SINGLE_USER",
  "runtime_version": "11.3"
}
```

## Connection Configuration

### Environment Variables
```bash
export DATABRICKS_HOST="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your_warehouse_id"
export DATABRICKS_TOKEN="your_token"
```

### Connection Parameters
```python
connection_params = {
    "server_hostname": os.getenv("DATABRICKS_HOST"),
    "http_path": os.getenv("DATABRICKS_HTTP_PATH"),
    "access_token": os.getenv("DATABRICKS_TOKEN")
}
```

## Security Configuration

### Token Management
- Use personal access tokens (PATs)
- Rotate tokens regularly (90 days recommended)
- Store tokens securely (environment variables, secret management)

### Network Security
- Enable VPC peering for private connectivity
- Use IP access lists for workspace access
- Enable TLS 1.3 for all connections

### Data Encryption
- **At Rest**: Managed by Databricks (AES-256)
- **In Transit**: TLS 1.3
- **Customer-Managed Keys**: Available for enterprise plans

## Performance Optimization

### Delta Lake Features
- **Auto Optimize**: Automatic file compaction
- **Z-Ordering**: Improved query performance
- **Vacuum**: Remove old snapshot files

### Query Optimization
```sql
-- Z-order by frequently queried columns
OPTIMIZE portfolio_positions ZORDER BY (symbol);

-- Vacuum old files (7-day retention)
VACUUM portfolio_positions RETAIN 7 HOURS;
```

### Cluster Autoscaling
```json
{
  "autoscale": {
    "min_workers": 2,
    "max_workers": 8
  }
}
```

## Monitoring & Logging

### Cluster Metrics
- CPU utilization
- Memory usage
- Disk I/O
- Network throughput

### Query History
- Enable query history tracking
- Monitor slow queries (> 30s)
- Set up alerts for failures

### Audit Logs
- Enable audit logging for all access
- Track data modifications
- Monitor privileged operations

## Best Practices

### Development
1. Use standard access mode
2. Enable auto-termination (30 min)
3. Use spot instances for cost savings
4. Test with sample data before production

### Production
1. Use dedicated access mode
2. Enable high concurrency mode
3. Set up monitoring and alerting
4. Implement backup and recovery

### Security
1. Rotate access tokens regularly
2. Use least privilege access
3. Enable IP access lists
4. Monitor audit logs

### Performance
1. Use Delta Lake for all tables
2. Enable auto-optimize
3. Z-order by frequently queried columns
4. Vacuum old files regularly

## Troubleshooting

### Connection Issues
- Verify workspace URL and HTTP path
- Check token validity
- Ensure network connectivity
- Verify firewall rules

### Performance Issues
- Check cluster resource usage
- Review query plans
- Optimize table layouts
- Increase cluster size if needed

### Data Quality Issues
- Validate data types
- Check for NULL values
- Verify referential integrity
- Run data quality checks

## References

- [Databricks Runtime Release Notes](https://docs.databricks.com/release-notes/runtime/)
- [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Delta Lake Documentation](https://docs.databricks.com/delta/index.html)
- [Cluster Configuration](https://docs.databricks.com/clusters/configure/)
