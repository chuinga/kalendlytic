# Kalendlytic - Deployment Scripts

This directory contains deployment automation scripts for the Kalendlytic infrastructure.

## Scripts Overview

### Core Deployment Scripts

- **`deploy.sh`** - Main deployment script with environment-specific configurations
- **`deploy.ps1`** - PowerShell version for Windows environments
- **`bootstrap.sh`** - CDK bootstrap script for initial setup
- **`rollback.sh`** - Rollback and disaster recovery script
- **`manage-secrets.sh`** - Environment variables and secrets management

### Configuration Files

- **`config.sh`** - Shared configuration and utility functions
- **`../config/environments/`** - Environment-specific configuration files

## Prerequisites

1. **AWS CLI** - Configured with appropriate credentials
2. **AWS CDK** - Installed globally (`npm install -g aws-cdk`)
3. **Node.js** - Version 18 or higher
4. **jq** - For JSON processing (required for secrets management)

## Quick Start

### 1. Bootstrap CDK (First Time Setup)

```bash
# Bootstrap for development environment
./scripts/bootstrap.sh -e dev -r eu-west-1

# Bootstrap for production with specific profile
./scripts/bootstrap.sh -e prod -r eu-west-1 -p production-profile
```

### 2. Deploy Infrastructure

```bash
# Deploy to development
./scripts/deploy.sh -e dev

# Deploy to production with confirmation
./scripts/deploy.sh -e prod -p production-profile

# Dry run to see what would be deployed
./scripts/deploy.sh -e staging --dry-run
```

### 3. Manage Secrets

```bash
# Initialize default secrets for environment
./scripts/manage-secrets.sh init -e dev

# List all secrets
./scripts/manage-secrets.sh list -e prod

# Set a specific secret
./scripts/manage-secrets.sh set BEDROCK_API_KEY "your-api-key" -e dev

# Export secrets to .env file
./scripts/manage-secrets.sh export -e dev
```

## Environment Configuration

Each environment has its own configuration file in `config/environments/`:

- **`dev.json`** - Development environment (minimal resources, debug logging)
- **`staging.json`** - Staging environment (production-like, testing features)
- **`prod.json`** - Production environment (high availability, security hardened)

### Configuration Structure

```json
{
  "environment": "dev",
  "region": "eu-west-1",
  "stackPrefix": "meeting-scheduling-agent-dev",
  "tags": { ... },
  "core": {
    "dynamodb": { ... },
    "cognito": { ... },
    "kms": { ... }
  },
  "api": {
    "lambda": { ... },
    "apiGateway": { ... }
  },
  "web": {
    "s3": { ... },
    "cloudFront": { ... }
  },
  "monitoring": { ... },
  "security": { ... }
}
```

## Deployment Strategies

### Development Environment

- Pay-per-request billing
- Minimal security features
- Debug logging enabled
- No backup retention
- Fast deployment for iteration

```bash
./scripts/deploy.sh -e dev --force
```

### Staging Environment

- Production-like configuration
- Security features enabled
- Automated testing integration
- Backup and monitoring

```bash
./scripts/deploy.sh -e staging
```

### Production Environment

- High availability setup
- Full security hardening
- Comprehensive monitoring
- Disaster recovery enabled
- Multi-region backup

```bash
./scripts/deploy.sh -e prod -p production-profile
```

## Rollback Procedures

### Quick Rollback

```bash
# Rollback entire environment
./scripts/rollback.sh -e dev

# Rollback with backup creation
./scripts/rollback.sh -e prod --backup

# Dry run to see what would be rolled back
./scripts/rollback.sh -e staging --dry-run
```

### Disaster Recovery

For production environments, the rollback script supports:

1. **Changeset Rollback** - Rollback to specific CloudFormation changeset
2. **Complete Destroy** - Full environment teardown
3. **Cross-Region Recovery** - Restore from backup region

```bash
# Rollback to specific changeset
./scripts/rollback.sh -e prod -v changeset-123

# Complete disaster recovery
./scripts/rollback.sh -e prod --disaster-recovery
```

## Secrets Management

### Secret Types

The system manages several types of secrets:

- **API Keys** - Bedrock, external services
- **JWT Secrets** - Authentication tokens
- **Encryption Keys** - Data encryption
- **Webhook Secrets** - External integrations

### Secret Rotation

```bash
# Rotate a specific secret
./scripts/manage-secrets.sh rotate JWT_SECRET -e prod

# Rotate all secrets (use with caution)
./scripts/manage-secrets.sh rotate-all -e dev
```

### Environment Variables

Secrets are stored in AWS Systems Manager Parameter Store and can be exported to `.env` files for local development:

```bash
# Export all secrets to .env.dev
./scripts/manage-secrets.sh export -e dev

# Import secrets from file
./scripts/manage-secrets.sh import .env.local -e dev
```

## Monitoring and Logging

### Deployment Logs

All deployment activities are logged to `logs/deployment_{environment}.log`:

```bash
# View recent deployment logs
tail -f logs/deployment_prod.log

# Search for errors
grep ERROR logs/deployment_prod.log
```

### Stack Status Monitoring

```bash
# Check all stack statuses
./scripts/deploy.sh -e prod --status-only

# Monitor specific stack
aws cloudformation describe-stacks --stack-name meeting-scheduling-agent-prod-api
```

## Troubleshooting

### Common Issues

1. **CDK Not Bootstrapped**
   ```bash
   ./scripts/bootstrap.sh -e dev --force
   ```

2. **Stack in Failed State**
   ```bash
   ./scripts/rollback.sh -e dev
   ./scripts/deploy.sh -e dev --force
   ```

3. **Secrets Not Found**
   ```bash
   ./scripts/manage-secrets.sh init -e dev
   ```

4. **Permission Denied on Scripts**
   ```bash
   chmod +x scripts/*.sh
   ```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
./scripts/deploy.sh -e dev --verbose
./scripts/manage-secrets.sh list -e dev --verbose
```

## Security Considerations

### Production Deployments

- Always use dedicated AWS profiles for production
- Enable MFA for production AWS accounts
- Use least-privilege IAM policies
- Regularly rotate secrets and access keys
- Monitor CloudTrail for deployment activities

### Secret Management

- Never commit secrets to version control
- Use AWS Systems Manager Parameter Store for secret storage
- Enable automatic secret rotation where possible
- Audit secret access regularly

## NPM Scripts

The following NPM scripts are available for convenience:

```bash
# Development
npm run deploy:dev
npm run bootstrap:dev
npm run secrets:init:dev

# Staging
npm run deploy:staging
npm run rollback:staging
npm run secrets:list:staging

# Production
npm run deploy:prod
npm run secrets:export:prod
```

## Support

For issues with deployment scripts:

1. Check the deployment logs in `logs/`
2. Verify AWS credentials and permissions
3. Ensure all prerequisites are installed
4. Review environment configuration files
5. Contact the DevOps team for production issues