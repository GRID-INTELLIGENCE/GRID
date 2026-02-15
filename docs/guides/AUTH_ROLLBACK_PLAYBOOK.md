# Auth Deployment Rollback Playbook

## Overview
This playbook provides step-by-step instructions for rolling back the authentication system deployment in case of critical issues.

## Emergency Contacts
- **Lead Developer**: [Contact Info]
- **DevOps**: [Contact Info]
- **Security Team**: [Contact Info]

## Rollback Scenarios

### Scenario 1: Database Migration Issues
**Symptoms**: Migration fails, database corruption, data loss

#### Immediate Actions
1. **Stop all application instances**
   ```bash
   # If using Kubernetes
   kubectl scale deployment grid-api --replicas=0

   # If using Docker Compose
   docker-compose stop grid-api

   # If using systemd
   sudo systemctl stop grid-api
   ```

2. **Create database backup** (if not already done)
   ```bash
   pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > emergency_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Rollback migration**
   ```bash
   # Navigate to project root
   cd /path/to/grid

   # Rollback the user table migration
   alembic downgrade -1

   # Verify rollback
   alembic current
   ```

4. **Restore previous application version**
   ```bash
   # If using git tags
   git checkout v1.0.0  # Previous stable version
   git submodule update --recursive

   # Rebuild and deploy
   docker build -t grid-api:rollback .
   kubectl set image deployment/grid-api grid-api=grid-api:rollback
   ```

5. **Verify rollback**
   - Check application logs for errors
   - Verify database schema matches expected state
   - Test basic functionality (health check, existing endpoints)

### Scenario 2: Authentication Service Failures
**Symptoms**: Login failures, registration errors, token validation issues

#### Immediate Actions
1. **Enable maintenance mode**
   ```bash
   # Set environment variable
   export GRID_MAINTENANCE_MODE=true

   # Restart application
   kubectl rollout restart deployment/grid-api
   ```

2. **Switch to fallback authentication**
   ```bash
   # Temporarily disable new auth system
   export AUTH_SYSTEM_ENABLED=false

   # Restart application
   kubectl rollout restart deployment/grid-api
   ```

3. **Monitor and assess**
   - Check error rates in monitoring dashboard
   - Review authentication logs
   - Verify user impact

### Scenario 3: Rate Limiting Issues
**Symptoms**: Legitimate users blocked, excessive false positives

#### Immediate Actions
1. **Disable rate limiting temporarily**
   ```bash
   export RATE_LIMITING_ENABLED=false
   kubectl rollout restart deployment/grid-api
   ```

2. **Clear Redis cache**
   ```bash
   redis-cli FLUSHDB
   ```

3. **Adjust rate limits**
   ```bash
   # Increase limits temporarily
   export RATE_LIMIT_REQUESTS=200
   export RATE_LIMIT_WINDOW=120
   kubectl rollout restart deployment/grid-api
   ```

### Scenario 4: Security Incident
**Symptoms**: Suspected breach, unauthorized access, data exposure

#### Immediate Actions
1. **Isolate affected systems**
   ```bash
   # Stop all external access
   kubectl scale deployment grid-api --replicas=0

   # Block database access from application
   # (Database-specific firewall rules)
   ```

2. **Rotate secrets immediately**
   ```bash
   # Generate new secret key
   openssl rand -hex 32

   # Update environment variables
   export MOTHERSHIP_SECRET_KEY="new-secret-key"

   # Rotate database credentials if compromised
   ```

3. **Audit and forensics**
   - Preserve all logs
   - Take database snapshots
   - Document incident timeline

## Recovery Steps

### Phase 1: Stabilize (0-2 hours)
- [ ] Stop failing deployment
- [ ] Enable monitoring mode
- [ ] Assess damage scope
- [ ] Notify stakeholders

### Phase 2: Rollback (2-4 hours)
- [ ] Execute appropriate rollback scenario
- [ ] Verify system stability
- [ ] Restore user access
- [ ] Monitor for regressions

### Phase 3: Investigate (4-24 hours)
- [ ] Root cause analysis
- [ ] Code review of changes
- [ ] Update monitoring alerts
- [ ] Document lessons learned

### Phase 4: Redeploy (24+ hours)
- [ ] Fix identified issues
- [ ] Update deployment checklist
- [ ] Gradual rollout with feature flags
- [ ] Extended monitoring period

## Monitoring During Rollback

### Key Metrics to Watch
- Application response times
- Error rates by endpoint
- Database connection pool usage
- Authentication success/failure rates
- User session counts

### Alert Thresholds
- Error rate > 5% for 5 minutes
- Response time > 2 seconds (p95)
- Database connection pool > 80% utilization
- Authentication failures > 10 per minute

## Post-Rollback Checklist

- [ ] All application instances healthy
- [ ] Database schema correct
- [ ] User authentication working
- [ ] Monitoring alerts functioning
- [ ] Stakeholders notified of status
- [ ] Incident report documented
- [ ] Timeline of events recorded
- [ ] Lessons learned documented

## Prevention Measures

### For Future Deployments
1. **Feature Flags**: Implement feature flags for major changes
2. **Gradual Rollout**: Use canary deployments
3. **Automated Testing**: Increase test coverage for auth flows
4. **Monitoring**: Add specific auth-related metrics
5. **Backup Strategy**: Regular database backups with point-in-time recovery

### Emergency Preparedness
1. **Runbook Updates**: Keep rollback procedures current
2. **Team Training**: Regular rollback drills
3. **Tooling**: Automated rollback scripts
4. **Communication**: Clear incident response plan

---

## Quick Reference Commands

```bash
# Check current migration status
alembic current

# Rollback one migration
alembic downgrade -1

# Check application health
curl -f http://localhost:8000/health

# View recent auth logs
kubectl logs -f deployment/grid-api | grep -i auth

# Emergency stop
kubectl scale deployment grid-api --replicas=0
```

---

*Last Updated: 2026-02-13*
*Version: 1.0*
*Review Date: Monthly*
