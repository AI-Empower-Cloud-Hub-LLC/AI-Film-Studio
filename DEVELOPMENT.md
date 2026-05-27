# AI Film Studio - Development Setup

## Quick Start (Development)

### Prerequisites
```bash
# Install Python 3.9+
python --version

# Install Node.js 18+
node --version

# Install FFmpeg
ffmpeg -version
```

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.dev .env

# Run the backend
python main.py
```

Backend will run on: http://localhost:8000
API Docs: http://localhost:8000/docs

### 2. Frontend Setup (Coming Soon)

```bash
cd frontend
npm install
npm run dev
```

### 3. Test the API

**Upload a video:**
```bash
curl -X POST "http://localhost:8000/api/v1/video/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-video.mp4" \
  -F "title=Test Video"
```

**Generate video from text:**
```bash
curl -X POST "http://localhost:8000/api/v1/generate/text-to-video" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean",
    "duration": 5,
    "resolution": "1920x1080"
  }'
```

## Project Structure

```
AI-Film-Studio/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core config
│   │   ├── db/           # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   ├── main.py           # Entry point
│   └── requirements.txt  # Python dependencies
├── frontend/             # React frontend (TBD)
├── storage/              # Local file storage
├── .env.dev              # Development environment
└── README.md             # Main documentation
```

## Development Notes

- **Database**: SQLite for development (auto-created)
- **Storage**: Local filesystem (`./storage`)
- **API Keys**: Optional for basic features, required for AI generation
- **GPU**: Not required, but speeds up AI processing

## Next Steps

1. Get API keys (optional): OpenAI, Stability AI, Replicate
2. Test video upload and basic operations
3. Integrate AI models when ready
4. Build frontend interface

## Troubleshooting

**FFmpeg not found:**
- Windows: Download from https://ffmpeg.org
- macOS: `brew install ffmpeg`
- Linux: `sudo apt-get install ffmpeg`

**Port already in use:**
- Change `APP_PORT` in `.env.dev`

**Database errors:**
- Delete `aifilm.db` and restart
