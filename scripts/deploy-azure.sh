#!/bin/bash
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}AI Film Studio - Azure Deployment Script${NC}"
echo "==========================================="

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"
command -v az >/dev/null 2>&1 || { echo -e "${RED}Azure CLI not found. Install it first.${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker not found. Install it first.${NC}"; exit 1; }

# Load environment variables from .env.production
if [ ! -f ".env.production" ]; then
    echo -e "${RED}Error: .env.production not found${NC}"
    exit 1
fi

source .env.production

# Extract configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-ai-film-studio-rg}"
LOCATION="${LOCATION:-eastus}"
ACR_NAME="${ACR_NAME:-aifilmstudioacr}"
CONTAINER_ENV="${CONTAINER_ENV:-ai-film-studio-env}"
DB_SERVER="${DB_SERVER:-ai-film-studio-db}"
KV_NAME="${KV_NAME:-ai-film-studio-kv}"

echo -e "${GREEN}Configuration:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  ACR: $ACR_NAME"
echo "  Key Vault: $KV_NAME"

# Step 1: Create Resource Group
echo -e "\n${YELLOW}Step 1: Creating Resource Group${NC}"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" 2>/dev/null || echo "Resource group already exists"

# Step 2: Create Container Registry
echo -e "\n${YELLOW}Step 2: Creating Container Registry${NC}"
az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    2>/dev/null || echo "ACR already exists"

# Step 3: Create Container Apps Environment
echo -e "\n${YELLOW}Step 3: Creating Container Apps Environment${NC}"
az containerapp env create \
    --name "$CONTAINER_ENV" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    2>/dev/null || echo "Container Apps environment already exists"

# Step 4: Create Key Vault
echo -e "\n${YELLOW}Step 4: Creating Key Vault${NC}"
az keyvault create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$KV_NAME" \
    --location "$LOCATION" \
    --enable-soft-delete true \
    2>/dev/null || echo "Key Vault already exists"

# Step 5: Store secrets in Key Vault
echo -e "\n${YELLOW}Step 5: Storing secrets in Key Vault${NC}"
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
fi

az keyvault secret set --vault-name "$KV_NAME" --name "SECRET-KEY" --value "$SECRET_KEY" > /dev/null
az keyvault secret set --vault-name "$KV_NAME" --name "DATABASE-URL" --value "$DATABASE_URL" > /dev/null
az keyvault secret set --vault-name "$KV_NAME" --name "REDIS-URL" --value "$REDIS_URL" > /dev/null
az keyvault secret set --vault-name "$KV_NAME" --name "OPENAI-API-KEY" --value "$OPENAI_API_KEY" > /dev/null
echo -e "${GREEN}✓ Secrets stored${NC}"

# Step 6: Build and push images
echo -e "\n${YELLOW}Step 6: Building and pushing Docker images${NC}"
az acr login --name "$ACR_NAME"

echo "Building backend image..."
docker build -t "$ACR_NAME.azurecr.io/ai-film-studio-backend:1.0.0" ./backend
docker push "$ACR_NAME.azurecr.io/ai-film-studio-backend:1.0.0"

echo "Building frontend image..."
docker build \
    --build-arg NEXT_PUBLIC_API_URL="https://api.yourdomain.com" \
    -t "$ACR_NAME.azurecr.io/ai-film-studio-frontend:1.0.0" ./frontend
docker push "$ACR_NAME.azurecr.io/ai-film-studio-frontend:1.0.0"

echo -e "${GREEN}✓ Images pushed to ACR${NC}"

echo -e "\n${GREEN}==========================================="
echo "Deployment preparation complete!"
echo "==========================================${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Update your domain in the Container Apps configuration"
echo "2. Run: az containerapp create ... (see DEPLOYMENT.md)"
echo "3. Configure custom domain and SSL"
echo "4. Run database migrations"
echo "5. Monitor: az containerapp logs show -n <app-name> -g $RESOURCE_GROUP"
