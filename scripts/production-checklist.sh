#!/bin/bash

# Production Readiness Checklist
# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}AI Film Studio - Production Readiness Checklist${NC}"
echo "=================================================="

# Check environment
check_env() {
    local key=$1
    if grep -q "^$key=" .env.production 2>/dev/null; then
        local value=$(grep "^$key=" .env.production | cut -d= -f2)
        if [ -z "$value" ] || [ "$value" = "your-" ] || [[ "$value" == *"your-"* ]]; then
            echo -e "${RED}✗ $key${NC} - NOT CONFIGURED"
            return 1
        else
            echo -e "${GREEN}✓ $key${NC} - configured"
            return 0
        fi
    else
        echo -e "${RED}✗ $key${NC} - NOT SET"
        return 1
    fi
}

echo -e "\n${YELLOW}Environment Variables:${NC}"
check_env "APP_ENV"
check_env "SECRET_KEY"
check_env "DATABASE_URL"
check_env "REDIS_URL"
check_env "OPENAI_API_KEY"
check_env "CORS_ORIGINS"

echo -e "\n${YELLOW}Files:${NC}"
[ -f "DEPLOYMENT.md" ] && echo -e "${GREEN}✓ DEPLOYMENT.md${NC}" || echo -e "${RED}✗ DEPLOYMENT.md${NC}"
[ -f "PRODUCTION_READINESS.md" ] && echo -e "${GREEN}✓ PRODUCTION_READINESS.md${NC}" || echo -e "${RED}✗ PRODUCTION_READINESS.md${NC}"
[ -f "nginx/nginx.conf" ] && echo -e "${GREEN}✓ nginx/nginx.conf${NC}" || echo -e "${RED}✗ nginx/nginx.conf${NC}"
[ -f ".env.production" ] && echo -e "${GREEN}✓ .env.production${NC}" || echo -e "${RED}✗ .env.production${NC}"

echo -e "\n${YELLOW}Docker:${NC}"
[ -f "backend/.dockerignore" ] && echo -e "${GREEN}✓ backend/.dockerignore${NC}" || echo -e "${RED}✗ backend/.dockerignore${NC}"
[ -f "frontend/.dockerignore" ] && echo -e "${GREEN}✓ frontend/.dockerignore${NC}" || echo -e "${RED}✗ frontend/.dockerignore${NC}"

echo -e "\n${YELLOW}Deployment:${NC}"
[ -f "scripts/deploy-azure.sh" ] && echo -e "${GREEN}✓ scripts/deploy-azure.sh${NC}" || echo -e "${RED}✗ scripts/deploy-azure.sh${NC}"
[ -f "scripts/backup-database.sh" ] && echo -e "${GREEN}✓ scripts/backup-database.sh${NC}" || echo -e "${RED}✗ scripts/backup-database.sh${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Fill in all environment variables in .env.production"
echo "2. Run: ./scripts/deploy-azure.sh"
echo "3. Run database migrations"
echo "4. Configure custom domain and SSL"
echo "5. Set up monitoring and alerts"
echo "6. Run: ./scripts/production-checklist.sh (again)"
