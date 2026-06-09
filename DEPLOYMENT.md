# Production Deployment Guide

This guide covers deploying AI Film Studio to Azure Container Apps in production.

## Prerequisites

- Azure subscription with appropriate permissions
- Azure CLI installed (`az` command)
- Docker installed locally
- Git repository cloned
- All configuration values ready (API keys, database credentials, etc.)

## Architecture Overview

```
┌─────────────────────────────────┐
│   Azure Container Registry      │
│   (aifilmstudioacr.azurecr.io)  │
└────────┬────────────────────────┘
         │
    ┌────v─────────────────┬─────────────┐
    │                      │             │
┌───v─────┐        ┌──────v──────┐  ┌──v────┐
│ Backend  │        │  Frontend    │  │ Nginx  │
│  v1.0.0  │        │   v1.0.0     │  │ Proxy  │
└───┬─────┘        └──────┬───────┘  └──┬─────┘
    │                     │             │
    └─────────┬───────────┴─────────────┘
              │
    ┌─────────v──────────┐
    │ Azure Container    │
    │    Apps (ACA)      │
    │   Environment      │
    └──────────┬─────────┘
               │
    ┌──────────┴────────┬─────────────┐
    │                   │             │
┌───v─────────┐  ┌──────v─────┐  ┌──v──────┐
│ PostgreSQL  │  │  Redis      │  │ Celery   │
│  Managed    │  │  Cache      │  │ Workers  │
└─────────────┘  └─────────────┘  └──────────┘
```

## Step 1: Prepare Azure Resources

### 1.1 Create Resource Group

```bash
az group create \
  --name ai-film-studio-rg \
  --location eastus
```

### 1.2 Create Azure Container Registry

```bash
az acr create \
  --resource-group ai-film-studio-rg \
  --name aifilmstudioacr \
  --sku Basic
```

### 1.3 Create Container Apps Environment

```bash
az containerapp env create \
  --name ai-film-studio-env \
  --resource-group ai-film-studio-rg \
  --location eastus
```

### 1.4 Create PostgreSQL Database

```bash
az postgres flexible-server create \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-db \
  --location eastus \
  --admin-user filmstudio \
  --admin-password 'YourSecurePassword123!' \
  --sku-name Standard_B1s \
  --tier Burstable \
  --storage-size 32
```

**Configure firewall rules:**

```bash
az postgres flexible-server firewall-rule create \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-db \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### 1.5 Create Azure Cache for Redis

```bash
az redis create \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-redis \
  --location eastus \
  --sku Basic \
  --vm-size c0
```

### 1.6 Create Azure Key Vault

```bash
az keyvault create \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-kv \
  --location eastus \
  --enable-soft-delete true \
  --soft-delete-retention 90
```

## Step 2: Configure Secrets in Key Vault

Store all sensitive values in Azure Key Vault:

```bash
az keyvault secret set \
  --vault-name ai-film-studio-kv \
  --name SECRET-KEY \
  --value "$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

az keyvault secret set \
  --vault-name ai-film-studio-kv \
  --name DATABASE-URL \
  --value "postgresql://filmstudio:password@host:5432/ai_film_studio"

az keyvault secret set \
  --vault-name ai-film-studio-kv \
  --name REDIS-URL \
  --value "redis://:password@host:6379/0"

# Add API keys
az keyvault secret set \
  --vault-name ai-film-studio-kv \
  --name GOOGLE-API-KEY \
  --value "your-google-api-key"

az keyvault secret set \
  --vault-name ai-film-studio-kv \
  --name ANTHROPIC-API-KEY \
  --value "sk-ant-your-key"

# Add Stripe keys if monetized
az keyvault secret set \
  --vault-name ai-film-studio-kv \
  --name STRIPE-SECRET-KEY \
  --value "sk_live_your-key"
```

## Step 3: Build and Push Docker Images

### 3.1 Authenticate with ACR

```bash
az acr login --name aifilmstudioacr
```

### 3.2 Build Backend Image

```bash
cd backend
docker build -t aifilmstudioacr.azurecr.io/ai-film-studio-backend:1.0.0 .
docker push aifilmstudioacr.azurecr.io/ai-film-studio-backend:1.0.0
```

### 3.3 Build Frontend Image

```bash
cd frontend
docker build \
  --build-arg NEXT_PUBLIC_API_URL="https://backend.yourdomain.com" \
  -t aifilmstudioacr.azurecr.io/ai-film-studio-frontend:1.0.0 .
docker push aifilmstudioacr.azurecr.io/ai-film-studio-frontend:1.0.0
```

## Step 4: Initialize Database

### 4.1 Run Database Migrations

```bash
# Create initial migration
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### 4.2 Seed Initial Data (if needed)

```python
# Create a seed.py script or use Django fixtures
python backend/app/db/seed.py
```

## Step 5: Deploy Backend Service

```bash
az containerapp create \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-backend \
  --environment ai-film-studio-env \
  --image aifilmstudioacr.azurecr.io/ai-film-studio-backend:1.0.0 \
  --registry-server aifilmstudioacr.azurecr.io \
  --registry-identity system \
  --cpu 1.0 \
  --memory 2.0Gi \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    APP_ENV=production \
    DEBUG=False \
    API_VERSION=v1 \
  --secrets \
    SECRET_KEY=secretref:SECRET-KEY \
    DATABASE_URL=secretref:DATABASE-URL \
    REDIS_URL=secretref:REDIS-URL \
    GOOGLE_API_KEY=secretref:GOOGLE-API-KEY \
    ANTHROPIC_API_KEY=secretref:ANTHROPIC-API-KEY \
  --health-probe-path /health \
  --health-probe-protocol http \
  --health-probe-interval 15 \
  --health-probe-timeout 5
```

## Step 6: Deploy Frontend Service

```bash
az containerapp create \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-frontend \
  --environment ai-film-studio-env \
  --image aifilmstudioacr.azurecr.io/ai-film-studio-frontend:1.0.0 \
  --registry-server aifilmstudioacr.azurecr.io \
  --registry-identity system \
  --cpu 0.5 \
  --memory 1.0Gi \
  --target-port 3000 \
  --ingress external \
  --env-vars \
    NODE_ENV=production \
    NEXT_PUBLIC_API_URL="https://backend.yourdomain.com"
```

## Step 7: Deploy Celery Worker

```bash
az containerapp create \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-celery \
  --environment ai-film-studio-env \
  --image aifilmstudioacr.azurecr.io/ai-film-studio-backend:1.0.0 \
  --registry-server aifilmstudioacr.azurecr.io \
  --registry-identity system \
  --cpu 2.0 \
  --memory 4.0Gi \
  --env-vars \
    APP_ENV=production \
  --secrets \
    DATABASE_URL=secretref:DATABASE-URL \
    REDIS_URL=secretref:REDIS-URL \
  --command "celery" "-A" "app.tasks.celery" "worker" "--loglevel=info"
```

## Step 8: Configure SSL/TLS with Custom Domain

### 8.1 Add Custom Domain

```bash
az containerapp hostname bind \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-backend \
  --hostname backend.yourdomain.com
```

### 8.2 Set Up Azure Front Door for HTTPS

```bash
az network front-door create \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-afd \
  --backend-pool-settings \
    --backend-pool-name backend-pool
```

## Step 9: Configure CI/CD

The repository includes `azure-pipelines.yml` for automated deployment:

1. Go to Azure DevOps
2. Create a new pipeline pointing to `azure-pipelines.yml`
3. Configure variables and secrets
4. Trigger on commits to `main` branch

## Step 10: Post-Deployment Verification

### 10.1 Check Health Endpoints

```bash
curl -s https://backend.yourdomain.com/health | jq
curl -s https://yourdomain.com | head -20
```

### 10.2 View Application Logs

```bash
az containerapp logs show \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-backend
```

### 10.3 Monitor with Application Insights

```bash
# Create Application Insights instance
az monitor app-insights component create \
  --app ai-film-studio-insights \
  --location eastus \
  --resource-group ai-film-studio-rg
```

## Scaling Configuration

### Auto-scaling Backend

```bash
az containerapp update \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-backend \
  --min-replicas 2 \
  --max-replicas 10
```

### Auto-scaling Rules

```bash
az containerapp update \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-backend \
  --min-replicas 2 \
  --max-replicas 10 \
  --cpu-threshold 80 \
  --memory-threshold 80
```

## Backup & Disaster Recovery

### 1. Database Backups

PostgreSQL Managed creates automatic backups. Configure retention:

```bash
az postgres flexible-server parameter set \
  --resource-group ai-film-studio-rg \
  --server-name ai-film-studio-db \
  --name backup_retention_days \
  --value 30
```

### 2. Restore from Backup

```bash
az postgres flexible-server restore \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-db-restored \
  --source-server ai-film-studio-db \
  --restore-time "2024-01-15T15:00:00"
```

## Monitoring & Alerts

### Set Up Alerts

```bash
# High CPU usage
az monitor metrics alert create \
  --resource-group ai-film-studio-rg \
  --name HighCPUUsage \
  --scopes "/subscriptions/SUBSCRIPTION_ID/resourceGroups/ai-film-studio-rg" \
  --condition "avg cpu > 80" \
  --description "Alert when CPU exceeds 80%"

# Database connection failures
az monitor metrics alert create \
  --resource-group ai-film-studio-rg \
  --name DatabaseConnectionFailed \
  --scopes "/subscriptions/SUBSCRIPTION_ID/resourceGroups/ai-film-studio-rg" \
  --condition "total connections < 1" \
  --description "Alert when database is unreachable"
```

## Troubleshooting

### Backend won't start

```bash
# Check logs
az containerapp logs show -n ai-film-studio-backend -g ai-film-studio-rg --follow

# Common issues:
# - Missing API keys in Key Vault
# - Database connection string invalid
# - Redis unreachable
```

### High latency

```bash
# Check resource utilization
az containerapp show -n ai-film-studio-backend -g ai-film-studio-rg --query properties.template.scale

# Scale up if needed
az containerapp update -n ai-film-studio-backend -g ai-film-studio-rg --min-replicas 3
```

### Database quota exceeded

```bash
# Check current usage
az postgres flexible-server show \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-db

# Scale up storage
az postgres flexible-server update \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-db \
  --storage-size 128
```

## Cost Optimization

1. **Right-size resources**: Start with smaller vCore allocation, scale as needed
2. **Use spot instances**: For non-critical workloads
3. **Reserved instances**: If committed to 1-3 year terms
4. **Monitor costs**: `az cost management query list --resource-group ai-film-studio-rg`

## Security Hardening

1. **Enable Azure Policy**: Enforce compliance standards
2. **Configure network isolation**: Use Private Endpoints for databases
3. **Enable audit logging**: Track all resource changes
4. **Implement WAF rules**: Protect against common attacks
5. **Regular security scanning**: Container vulnerability scanning

## Next Steps

- [ ] Set up monitoring and alerting
- [ ] Configure backup retention policies
- [ ] Implement disaster recovery testing
- [ ] Set up log aggregation
- [ ] Configure automated updates
- [ ] Set up team notifications

---

**Last Updated**: 2026-06-09
**Version**: 1.0
