# Azure DevOps Setup Guide

This guide walks through setting up Azure DevOps CI/CD pipelines for the AI Film Studio project.

## Prerequisites

- Azure DevOps organization (free tier available at https://dev.azure.com)
- Azure subscription with appropriate permissions
- Azure Container Registry (ACR) created
- Azure Container Apps environment set up

## Step 1: Create Azure DevOps Project

1. Go to https://dev.azure.com
2. Create a new project (e.g., "ai-film-studio")
3. Select "Git" as version control
4. Click "Create"

## Step 2: Import Repository

### Option A: Import from GitHub

1. In Azure DevOps, go to **Repos**
2. Click the repository dropdown
3. Select **Import a repository**
4. Choose **Git**
5. Enter the GitHub repository URL: `https://github.com/AI-Empower-Cloud-Hub-LLC/AI-Film-Studio.git`
6. Click **Import**

### Option B: Set up as a Mirror

If you prefer to keep the primary repo on GitHub and mirror to Azure DevOps:

```bash
git clone --mirror https://github.com/AI-Empower-Cloud-Hub-LLC/AI-Film-Studio.git
cd AI-Film-Studio.git
git push --mirror https://dev.azure.com/your-org/ai-film-studio/_git/ai-film-studio
```

## Step 3: Create Service Connection

1. Go to **Project Settings** → **Service connections**
2. Click **New service connection**
3. Select **Azure Resource Manager**
4. Choose **Service principal (automatic)**
5. Fill in:
   - **Scope level**: Subscription
   - **Subscription**: Select your Azure subscription
   - **Resource group**: `ai-film-studio-rg`
6. Name it: `AzureResourceManager`
7. Click **Save**

For the ACR, also create:
1. **New service connection** → **Docker Registry**
2. Choose **Azure Container Registry**
3. Select your subscription and ACR
4. Name it: `aifilmstudioacr`
5. Click **Save**

## Step 4: Create Variables

1. Go to **Pipelines** → **Library** → **Variable groups**
2. Click **+ Variable group**
3. Name it: `ai-film-studio-prod`
4. Add variables:
   - `AZURE_SUBSCRIPTION`: Your Azure subscription name
   - `DOCKER_BUILDKIT`: `1`
5. Click **Save**

For secrets, use Azure Key Vault:
1. Create an **Azure Key Vault** variable group linked to your Key Vault
2. Add secrets:
   - Database connection strings
   - API keys (OpenAI, Anthropic, Google, etc.)
   - Stripe keys
   - Other sensitive configuration

## Step 5: Create the Pipeline

1. Go to **Pipelines** → **Create Pipeline**
2. Select **Azure Repos Git** (or GitHub if using mirror)
3. Select the repository
4. Choose **Existing Azure Pipelines YAML file**
5. Select **azure-pipelines.yml**
6. Click **Continue**
7. Review and **Run**

## Step 6: Configure Pipeline Settings

After the pipeline is created:

1. Go to the pipeline settings
2. Click **...** → **Settings**
3. Configure:
   - **Agent pool**: Default
   - **Demands**: None (uses pool defaults)
   - **Timeout**: 360 minutes (for long deployments)

## Step 7: Set Deployment Environment

1. Go to **Pipelines** → **Environments**
2. Click **Create environment**
3. Name it: `Production`
4. Set up approvals (optional):
   - Click **⋮** → **Approvals and checks**
   - Add **Approval** check if desired
   - Add users/groups who can approve deployments

## Step 8: Update Azure Pipeline YAML

Update the `azure-pipelines.yml` file with your specific values:

```yaml
variables:
  ACR_NAME: 'your-acr-name'           # Your ACR name
  RESOURCE_GROUP: 'your-rg-name'      # Your resource group
  BACKEND_APP: 'your-backend-name'    # Your Container App name
  FRONTEND_APP: 'your-frontend-name'  # Your Container App name
  AZURE_SUBSCRIPTION: 'YourServiceConnection'  # Service connection name
```

## Step 9: Secrets and Configuration

### Using Azure Key Vault

Reference secrets in the pipeline:

```yaml
variables:
  - group: ai-film-studio-kv  # Your Key Vault variable group
```

### Docker Build Arguments

Environment variables are passed during build:

```yaml
script: |
  docker build \
    --build-arg NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    -t $(FRONTEND_IMAGE):latest \
    ./frontend
```

## Step 10: Enable Multi-Branch Triggering

The pipeline triggers on:
- Push to `main`
- Push to `develop`
- Manual trigger (via "Run pipeline")

Modify the `trigger` section if needed:

```yaml
trigger:
  branches:
    include:
    - main
    - develop
    - feature/*  # Optional: include feature branches
```

## Monitoring and Troubleshooting

### View Pipeline Runs

1. Go to **Pipelines**
2. Click the pipeline name
3. View run history and logs

### Check Agent Logs

If the pipeline fails:
1. Click the failed run
2. Click the job
3. View the logs for detailed error messages

### Common Issues

| Issue | Solution |
|-------|----------|
| ACR authentication fails | Verify the Docker Registry service connection and ACR credentials |
| Container Apps update fails | Check the resource group name and container app names |
| Python/Node dependencies timeout | Increase timeout in pipeline settings |
| Deployment verification fails | Ensure Container Apps have network access and health endpoints are correct |

## CI/CD Best Practices

1. **Use branch policies**: Require pull request reviews before merging to main
2. **Enable status checks**: Require pipeline to pass before merge
3. **Use approval gates**: For production deployments
4. **Monitor costs**: Azure Container Apps charges per vCore-hour
5. **Set up alerts**: In Application Insights for application errors

## Next Steps

1. Update the pipeline with your Azure resources
2. Configure branch policies in your repo
3. Set up notifications for pipeline failures
4. Document your deployment process for your team

## References

- [Azure DevOps Documentation](https://docs.microsoft.com/en-us/azure/devops)
- [Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps)
- [YAML Schema Reference](https://docs.microsoft.com/en-us/azure/devops/pipelines/yaml-schema)
