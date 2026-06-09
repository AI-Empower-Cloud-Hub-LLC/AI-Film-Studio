# Production Setup Guide

This guide walks you through configuring your application for production deployment.

## Prerequisites

Before starting, gather the following information:

### 1. Domain Information
- [ ] Production domain (e.g., `aifilmstudio.com`)
- [ ] Email for SSL certificates (e.g., `admin@yourdomain.com`)

### 2. Azure Resources
- [ ] Azure subscription ID
- [ ] Azure region (e.g., `eastus`)
- [ ] Resource group name (e.g., `ai-film-studio-rg`)

### 3. Database
- [ ] PostgreSQL admin username
- [ ] PostgreSQL admin password
- [ ] Database name (default: `ai_film_studio`)

### 4. Redis Cache
- [ ] Redis connection URL or host:port
- [ ] Redis password (if required)

### 5. API Keys & Secrets
These are required for the AI features:

#### LLM Services (Pick one or more)
- [ ] **OpenAI**: API key from https://platform.openai.com
  - Cost: ~$0.03-0.10 per 1K tokens
  - Quality: Very high
  
- [ ] **Anthropic Claude**: API key from https://console.anthropic.com
  - Cost: ~$0.003-0.024 per 1K tokens
  - Quality: Very high
  
- [ ] **Google Gemini**: API key from https://ai.google.dev
  - Cost: Free tier available
  - Quality: Good

#### Voice Generation
- [ ] **ElevenLabs**: API key from https://elevenlabs.io
  - Cost: Free tier or ~$0.30 per 1K characters
  - Quality: Excellent

#### Video Generation (Optional)
- [ ] **Replicate**: API token from https://replicate.com
  - For Stable Video Diffusion
  - Cost: ~$0.025-0.10 per video

- [ ] **Runway ML**: API key from https://app.runwayml.com
  - Advanced video generation
  - Cost: Premium service

#### Image Generation (Optional)
- [ ] **Stability AI**: API key from https://stability.ai
  - For fallback image generation

### 6. Email Service
- [ ] **SendGrid** API key from https://sendgrid.com
  - OR use your preferred SMTP server
  - Cost: Free tier available (100 emails/day)

### 7. Error Monitoring
- [ ] **Sentry** DSN from https://sentry.io
  - For error tracking and monitoring
  - Cost: Free tier available

### 8. Azure Storage (Optional)
- [ ] Azure Storage account name
- [ ] Azure Storage connection string
- [ ] Container name (default: `media`)

---

## Step 1: Fill in Environment Variables

Edit `.env.production` with your values:

```bash
nano .env.production
```

Replace all `YOUR_*` placeholders with actual values:

```env
# Application
SECRET_KEY=<generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'>
APP_ENV=production

# Database
DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST:5432/ai_film_studio

# Redis
REDIS_URL=redis://:PASSWORD@HOST:6379/0

# Domain
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# LLM (Choose one)
OPENAI_API_KEY=sk_...                    # OpenAI
# OR
ANTHROPIC_API_KEY=sk-ant-...             # Anthropic Claude
# OR
GOOGLE_API_KEY=...                       # Google Gemini

# Voice Generation
ELEVENLABS_API_KEY=...

# Email Service
SMTP_PASSWORD=sg_...                     # SendGrid or your email provider

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
```

### Generate Secret Key

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Copy the output and paste it as `SECRET_KEY` value.

---

## Step 2: Set Up Azure Resources

### Option A: Manual Setup (Azure Portal)

1. Create PostgreSQL database
2. Create Redis cache
3. Create Key Vault
4. Create Container Registry

### Option B: Automated Setup (Recommended)

```bash
./scripts/deploy-azure.sh
```

This script will:
- ✅ Create resource group
- ✅ Create container registry
- ✅ Create container apps environment
- ✅ Create key vault
- ✅ Store secrets securely
- ✅ Build and push Docker images

---

## Step 3: Configure Environment

Update these settings in `.env.production`:

### Azure Resources
```env
RESOURCE_GROUP=ai-film-studio-rg
LOCATION=eastus
ACR_NAME=aifilmstudioacr
```

### Domain Configuration
```env
# Update these to your domain
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
FRONTEND_URL=https://yourdomain.com
```

### Database Connection
```env
# PostgreSQL Managed Database
DATABASE_URL=postgresql://filmstudio:PASSWORD@ai-film-studio-db.postgres.database.azure.com:5432/ai_film_studio
```

### Redis Connection
```env
# Azure Cache for Redis
REDIS_URL=redis://:PASSWORD@ai-film-studio-redis.redis.cache.windows.net:6380/0?ssl=True
```

---

## Step 4: Verify Configuration

Run the production checklist:

```bash
./scripts/production-checklist.sh
```

Expected output:
```
✓ APP_ENV
✓ SECRET_KEY
✓ DATABASE_URL
✓ REDIS_URL
✓ OPENAI_API_KEY (or your chosen LLM)
✓ CORS_ORIGINS
✓ All files present
✓ Docker configurations ready
✓ Deployment scripts ready
```

---

## Step 5: Deploy Infrastructure

```bash
./scripts/deploy-azure.sh
```

This will:
1. Create Azure resource group
2. Create Container Registry
3. Create Container Apps environment
4. Create Key Vault
5. Store secrets securely
6. Build and push Docker images

---

## Step 6: Configure Database

### Run Migrations

```bash
# SSH into backend container
docker exec ai-film-studio-backend bash

# Run Alembic migrations
cd /app
alembic upgrade head

# Verify migration
alembic current
```

Or use Azure Container Instances:

```bash
az containerapp exec \
  --name ai-film-studio-backend \
  --resource-group ai-film-studio-rg \
  --command "alembic upgrade head"
```

---

## Step 7: Configure SSL/TLS

### Option A: Let's Encrypt (Automated)

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Request certificate
certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Certificate location:
# /etc/letsencrypt/live/yourdomain.com/
```

### Option B: Azure Front Door

1. Create Azure Front Door
2. Add your domain
3. Set up SSL certificate
4. Configure backend endpoints

---

## Step 8: Deploy Application

### Via Azure DevOps Pipeline

1. Push to `main` branch:
   ```bash
   git push origin main
   ```

2. Pipeline will automatically:
   - Run tests
   - Build Docker images
   - Push to ACR
   - Deploy to Container Apps
   - Run health checks

### Via Azure CLI

```bash
# Deploy backend
az containerapp create \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-backend \
  --environment ai-film-studio-env \
  --image acr.azurecr.io/backend:1.0.0 \
  --env-vars APP_ENV=production

# Deploy frontend
az containerapp create \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-frontend \
  --environment ai-film-studio-env \
  --image acr.azurecr.io/frontend:1.0.0 \
  --env-vars NODE_ENV=production
```

---

## Step 9: Verify Deployment

```bash
# Check backend health
curl https://api.yourdomain.com/health

# Check frontend
curl https://yourdomain.com
```

Expected responses:
- Backend: `{"status": "healthy", "services": {...}}`
- Frontend: HTML page with React app

---

## Step 10: Set Up Monitoring

### Application Insights

```bash
# Enable monitoring
az monitor app-insights component create \
  --app ai-film-studio-insights \
  --location eastus \
  --resource-group ai-film-studio-rg
```

### Sentry (Error Tracking)

1. Create account at https://sentry.io
2. Create project for Python/FastAPI
3. Copy DSN
4. Add to `.env.production`:
   ```env
   SENTRY_DSN=https://YOUR_DSN@sentry.io/PROJECT_ID
   ```

### Health Monitoring

```bash
# Create alert for backend health
az monitor metrics alert create \
  --resource-group ai-film-studio-rg \
  --name "Backend Health Alert" \
  --scopes "/subscriptions/SUBSCRIPTION_ID/resourceGroups/ai-film-studio-rg" \
  --condition "avg cpu > 80"
```

---

## Step 11: Configure Backups

### Database Backup

```bash
# Run backup script
./scripts/backup-database.sh

# Verify backup
ls -lh backups/
```

### Automated Daily Backup

```bash
# Add to crontab
0 2 * * * cd /path/to/ai-film-studio && ./scripts/backup-database.sh
```

---

## Step 12: Final Verification

Run final checklist:

```bash
./scripts/production-checklist.sh
```

All items should show ✅ green.

---

## Post-Deployment

### 1. Monitor Logs

```bash
# View backend logs
az containerapp logs show \
  --name ai-film-studio-backend \
  --resource-group ai-film-studio-rg \
  --follow
```

### 2. Check Performance

Monitor in Application Insights:
- Response times
- Error rates
- Database performance
- Resource utilization

### 3. Verify Security

```bash
# Check SSL/TLS
curl -I https://yourdomain.com

# Verify headers
curl -I https://yourdomain.com | grep -E "Strict-Transport-Security|X-Frame"
```

### 4. Test Critical Flows

- [ ] User registration
- [ ] User login
- [ ] Create project
- [ ] Generate script
- [ ] Create scenes
- [ ] Generate video

---

## Troubleshooting

### Database Connection Failed
```bash
# Verify connection
psql postgresql://user:pass@host/db

# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group ai-film-studio-rg \
  --server-name ai-film-studio-db
```

### Redis Connection Failed
```bash
# Test Redis
redis-cli -h HOST -p 6379 ping

# Check connection string
REDIS_URL=redis://:PASSWORD@HOST:6379/0
```

### API Returns 503
```bash
# Check container health
az containerapp show \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-backend

# View logs
az containerapp logs show \
  --resource-group ai-film-studio-rg \
  --name ai-film-studio-backend
```

---

## Support Resources

- **Azure Documentation**: https://docs.microsoft.com/en-us/azure/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Next.js**: https://nextjs.org/docs
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/documentation
- **Docker**: https://docs.docker.com/

---

## Checklist

- [ ] Domain configured
- [ ] Azure resources created
- [ ] Environment variables filled
- [ ] Docker images built
- [ ] Database migrated
- [ ] SSL/TLS configured
- [ ] Application deployed
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backups enabled
- [ ] Security verified
- [ ] Performance acceptable

---

**Ready to deploy? Run:**

```bash
./scripts/production-checklist.sh
```

Then:

```bash
./scripts/deploy-azure.sh
```

Good luck! 🚀
