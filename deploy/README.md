# Deploying AI Film Studio to GCP

## Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated
2. A GCP project with billing enabled
3. Required APIs enabled:
   - Cloud Run
   - Artifact Registry
   - Cloud Build
   - Cloud SQL (optional — SQLite works for small deployments)

## Quick Deploy (Cloud Run)

### 1. Set environment variables

```bash
export GCP_PROJECT=your-gcp-project-id
export GCP_REGION=us-central1
export GOOGLE_API_KEY=your-gemini-api-key
```

### 2. Deploy the backend

```bash
# Build and push the backend image
cd backend
gcloud builds submit --tag gcr.io/$GCP_PROJECT/ai-film-studio-backend

# Deploy to Cloud Run
gcloud run deploy ai-film-studio-backend \
  --image gcr.io/$GCP_PROJECT/ai-film-studio-backend \
  --platform managed \
  --region $GCP_REGION \
  --allow-unauthenticated \
  --set-env-vars="DATABASE_URL=sqlite:///./ai_film_studio.db,LLM_BACKEND=google,GOOGLE_API_KEY=$GOOGLE_API_KEY,GOOGLE_MODEL=gemini-flash-latest,CORS_ORIGINS=[\"*\"],DEBUG=true" \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --port=8000
```

### 3. Get the backend URL

```bash
BACKEND_URL=$(gcloud run services describe ai-film-studio-backend --region $GCP_REGION --format='value(status.url)')
echo "Backend URL: $BACKEND_URL"
```

### 4. Deploy the frontend

```bash
cd frontend

# Build with backend URL
gcloud builds submit \
  --tag gcr.io/$GCP_PROJECT/ai-film-studio-frontend \
  --build-arg NEXT_PUBLIC_API_URL=$BACKEND_URL

# Deploy to Cloud Run
gcloud run deploy ai-film-studio-frontend \
  --image gcr.io/$GCP_PROJECT/ai-film-studio-frontend \
  --platform managed \
  --region $GCP_REGION \
  --allow-unauthenticated \
  --set-env-vars="NEXT_PUBLIC_API_URL=$BACKEND_URL" \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --port=3000
```

### 5. Access the app

```bash
FRONTEND_URL=$(gcloud run services describe ai-film-studio-frontend --region $GCP_REGION --format='value(status.url)')
echo "App URL: $FRONTEND_URL"
```

## Docker Compose (Local / VM)

For local development or VM deployment:

```bash
# From the project root
cp .env.example .env
# Edit .env with your API keys

docker-compose up -d
```

The app will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## CI/CD Auto-Deploy

The GitHub Actions workflow at `.github/workflows/deploy-gcp.yml` automatically deploys on push to `main` when changes are detected in `backend/`, `frontend/`, or `docker-compose.yml`. You can also trigger manual deploys via the Actions tab.

Required GitHub Secrets:
- `GCP_SA_KEY` — Service account JSON key with Cloud Run Admin and Storage Admin roles
- `GCP_PROJECT_ID` — Your GCP project ID
- `GOOGLE_API_KEY` — Gemini API key for the LLM backend

## Production Considerations

- Use **Cloud SQL** (PostgreSQL) instead of SQLite for persistent storage
- Set up **Cloud Storage** for media files (images, audio)
- Enable **Cloud CDN** for the frontend
- Use **Secret Manager** for API keys instead of environment variables
- Set up a custom domain with **Cloud Load Balancer**
- Enable **Cloud Monitoring** and set up alerts for error rates and latency
