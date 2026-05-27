# AI Film Studio 🎬🤖

**Autonomous Agentic AI Film Production System** - The world's first fully autonomous AI film studio where multiple AI agents collaborate to create complete films from simple text prompts.

## 🌟 Revolutionary Concept

Unlike traditional video tools, AI Film Studio uses **autonomous AI agents** that think, collaborate, and make creative decisions:

- 🎭 **Director Agent**: Develops creative vision and oversees production
- ✍️ **Screenwriter Agent**: Writes scripts and narratives  
- ✂️ **Editor Agent**: Assembles edits with professional pacing
- 🎥 **Cinematographer Agent** (coming): Plans shots and camera work
- 🎵 **Sound Designer Agent** (coming): Creates audio landscapes
- ✨ **VFX Agent** (coming): Adds visual effects

## 🔄 Autonomous Agent Workflow

```
User Input → Director Agent → Screenwriter Agent → Pre-Production Planning
                ↓                    ↓                        ↓
         Creative Vision      Script Development      Shot Planning
                ↓                    ↓                        ↓
         AI Video Generation ← Cinematographer ← Production Coordination
                ↓                    ↓                        ↓
         Editor Agent → Sound Designer → VFX Agent → Final Assembly
                ↓                    ↓                        ↓
         Director Approval → Color Grading → COMPLETED FILM ✅
```

## 🌟 Features

### Fully Autonomous Film Creation
- **From concept to final film** - completely autonomous
- **Multi-agent collaboration** - agents communicate and decide together
- **AI-driven creativity** - each agent uses LLMs to think
- **Production workflow** - follows real film production stages
- **Human oversight** - optional intervention at any stage

### Video Generation
- **Text-to-Video**: Generate videos from text descriptions
- **Image-to-Video**: Animate static images into dynamic videos
- **Script-to-Film**: Convert scripts into complete video productions
- **AI Director**: Automated scene composition and camera angles

### Video Editing
- **Smart Editing**: AI-powered video trimming and arrangement
- **Scene Detection**: Automatic scene boundary detection
- **Transitions**: Intelligent transition suggestions
- **Color Grading**: AI-assisted color correction

### Enhancement
- **Resolution Upscaling**: Enhance video quality with AI
- **Frame Interpolation**: Smooth slow-motion effects
- **Noise Reduction**: AI-powered denoising
- **Audio Enhancement**: Speech enhancement and background music

### Creative Tools
- **Storyboard Generator**: Auto-generate storyboards from scripts
- **Voice Synthesis**: Text-to-speech with multiple voices
- **Subtitle Generation**: Automatic subtitle creation and translation
- **Background Replacement**: AI-powered green screen effects

## 🏗️ Architecture

```
AI-Film-Studio/
├── backend/           # FastAPI backend server
├── frontend/          # React frontend application
├── ai-models/         # AI model integrations
├── storage/           # Media storage
└── docs/              # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (optional)
- CUDA-capable GPU (recommended)

### GitHub Codespaces (Recommended)

Open this repository in GitHub Codespaces for a pre-configured development environment:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new?hide_repo_select=true&ref=main)

The Codespace will automatically:
- Configure git authentication for commits and pushes
- Install all dependencies
- Set up the development environment

See [CODESPACE_SETUP.md](./CODESPACE_SETUP.md) for more details.

### Local Installation

1. **Clone the repository**
```bash
git clone https://github.com/AI-Cloud-Tech-Inc/AI-Film-Studio.git
cd AI-Film-Studio
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

4. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

### Running the Application

#### Development Mode

**Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

#### Docker Mode
```bash
docker-compose up --build
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📚 API Documentation

### Video Generation Endpoints

#### Generate Video from Text
```http
POST /api/v1/generate/text-to-video
Content-Type: application/json

{
  "prompt": "A sunset over the ocean with dolphins jumping",
  "duration": 10,
  "resolution": "1920x1080",
  "style": "cinematic"
}
```

#### Generate Video from Image
```http
POST /api/v1/generate/image-to-video
Content-Type: multipart/form-data

image: <file>
motion_type: "zoom_in"
duration: 5
```

### Video Editing Endpoints

#### Trim Video
```http
POST /api/v1/edit/trim
Content-Type: application/json

{
  "video_id": "uuid",
  "start_time": 5.0,
  "end_time": 15.0
}
```

#### Apply Transitions
```http
POST /api/v1/edit/transitions
Content-Type: application/json

{
  "clips": ["clip1_id", "clip2_id"],
  "transition_type": "fade",
  "duration": 1.0
}
```

## 🔧 Configuration

### Environment Variables

```env
# API Keys
OPENAI_API_KEY=your_openai_key
STABILITY_API_KEY=your_stability_key
REPLICATE_API_KEY=your_replicate_key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/aifilm

# Storage
STORAGE_TYPE=local  # or 's3', 'azure'
STORAGE_PATH=/path/to/storage

# AI Models
MODEL_CACHE_DIR=/path/to/models
USE_GPU=true
GPU_DEVICE=0
```

## 🤖 AI Models

The platform integrates multiple AI models:

- **Stable Video Diffusion** - Text/Image to video generation
- **RIFE** - Frame interpolation
- **Real-ESRGAN** - Video upscaling
- **Whisper** - Audio transcription
- **VITS** - Voice synthesis
- **CLIP** - Scene understanding

## 🎨 Use Cases

1. **Content Creators**: Rapid video prototyping and editing
2. **Marketers**: Product demo videos and advertisements
3. **Educators**: Educational content creation
4. **Film Makers**: Pre-visualization and storyboarding
5. **Game Developers**: Cutscene generation

## 🛠️ Tech Stack

**Backend:**
- FastAPI
- PyTorch
- OpenCV
- FFmpeg
- PostgreSQL
- Redis

**Frontend:**
- React 18
- TypeScript
- Tailwind CSS
- Zustand
- React Query

**AI/ML:**
- Stable Diffusion
- Hugging Face Transformers
- ONNX Runtime
- TensorRT

## 📖 Documentation

- [API Reference](./docs/API.md)
- [Model Integration Guide](./docs/MODELS.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Contributing Guidelines](./docs/CONTRIBUTING.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](./docs/CONTRIBUTING.md).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Stability AI for Stable Diffusion
- OpenAI for GPT models
- Hugging Face for model hosting
- FFmpeg community

## 📞 Support

- 📧 Email: support@ai-cloud-tech.com
- 💬 Discord: [Join our community](https://discord.gg/aifilmstudio)
- 🐛 Issues: [GitHub Issues](https://github.com/AI-Cloud-Tech-Inc/AI-Film-Studio/issues)

## 🗺️ Roadmap

- [x] Basic video generation
- [x] Video editing tools
- [ ] Real-time collaboration
- [ ] Advanced AI effects
- [ ] Mobile app
- [ ] Cloud rendering
- [ ] Marketplace for templates

---

**Made with ❤️ by AI Cloud Tech Inc**
