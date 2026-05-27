# 🎬 Autonomous Agentic AI Film Studio

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109-green.svg)](https://fastapi.tiangolo.com/)

**The world's first fully autonomous AI film studio powered by collaborative AI agents.**

AI 🤖 The Agent Crew

Meet the autonomous AI agents that create your films:

### 🎭 Director Agent
**The Creative Visionary**
- Interprets your concept into a cohesive creative vision
- Makes high-level artistic decisions autonomously
- Coordinates all other agents like a real film director
- Reviews and approves final output

### ✍️ Screenwriter Agent
**The Storyteller**
- Writes complete scripts with dialogue and scene descriptions
- Develops character arcs and narrative structure
- Revises based on director feedback autonomously
- Maintains narrative consistency

### 🎥 Cinematographer Agent
**The Visual Artist**
- Plans camera angles, movements, and compositions
- Determines lighting and visual style
- Creates detailed shot lists
- Ensures visual continuity across scenes

### ✂️ Editor Agent
**The Pacing Expert**
- Assembles scenes into cohesive narrative
- Determines optimal timing and rhythm
- Applies transitions intelligently
- Makes autonomous cut decisions

### 🎵 Sound Designer Agent
**The Audio Architect**
- Selects or generates background music
- Creates immersive soundscapes
- Mixes audio levels autonomously
- Synchronizes sound with visual beats

### ✨ VFX Agent
**The Enhancement Specialist**
- Identifies enhancement opportunities
- Applies visual effects and color grading
- Integrates CGI elements seamlessly
- Ensures technical quality

👉 **Learn more**: [Agent Architecture](./AGENT_ARCHITECTURE.md)human micromanagement
- **📈 Continuous Learning**: System improves from every film produced

## ✨ Features

- **🤖 AI Scriptwriting** - Generate professional video scripts using GPT-4
- **🎨 Smart Storyboarding** - Automatic visual planning from scripts
- **🎬 Scene Generation** - AI-powered video scene creation
- **🎤 Voice Synthesis** - Natural voiceovers in multiple languages
- **✂️ Auto Editing** - Intelligent video compilation and editing
- **🎯 Multi-Format** - Support for landscape, portrait, and square videos

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/AI-Cloud-Tech-Inc/AI-Film-Studio.git
cd AI-Film-Studio

# Setup environment variables
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# Add your API keys to backend/.env
# OPENAI_API_KEY=sk-your-key-here

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Using GitHub Codespaces

This repository is fully configured for GitHub Codespaces with automatic setup:

1. **Create a Codespace** from the repository
2. **Wait for automatic setup** - The devcontainer will:
   - Configure git authentication using GitHub CLI
   - Install Python and Node.js dependencies
   - Set up the development environment
3. **Start developing** - All git operations (commit, push, pull) work automatically!

**Git authentication is pre-configured** - no manual setup needed!

📖 For troubleshooting or manual setup: [CODESPACE_SETUP.md](./CODESPACE_SETUP.md)

## 📚 Documentation

- **[Getting Started Guide](docs/GETTING_STARTED.md)** - Detailed setup instructions
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and components
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (after starting backend)

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and task queue
- **Celery** - Background job processing
- **OpenAI GPT-4** - Script generation
- **ElevenLabs** - Voice synthesis
- **Stability AI** - Image generation

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Query** - Data fetching
- **Framer Motion** - Animations

## 📦 Project Structure

```
AI-Film-Studio/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── services/ # Business logic
│   │   ├── tasks/    # Celery tasks
│   │   └── core/     # Configuration
│   └── main.py       # Application entry
├── frontend/         # Next.js frontend
│   ├── app/         # Pages and layouts
│   ├── components/  # React components
│   └── lib/         # Utilities
├── docs/            # Documentation
└── docker-compose.yml
```

## 🎯 Workflow

1. **Create Project** → Define video parameters
2. **Generate Script** → AI creates the narrative
3. **Storyboard** → Visual scene planning
4. **Generate Scenes** → AI creates video clips
5. **Add Voiceover** → Synthesize narration
6. **Compile** → Assemble final video
7. **Export** → Download your video

## 🔑 Required API Keys

- **OpenAI** (Required) - [Get API Key](https://platform.openai.com)
- **ElevenLabs** (Optional) - [Get API Key](https://elevenlabs.io)
- **Stability AI** (Optional) - [Get API Key](https://stability.ai)

Add these to `backend/.env` file.

## 🧑‍💻 Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## 📊 API Endpoints

- `POST /api/v1/projects/` - Create new project
- `POST /api/v1/scripts/generate` - Generate script
- `POST /api/v1/storyboards/generate` - Create storyboard
- `POST /api/v1/scenes/generate` - Generate video scene
- `POST /api/v1/voiceovers/generate` - Create voiceover
- `POST /api/v1/videos/compile` - Compile final video

Full API documentation: http://localhost:8000/docs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4
- ElevenLabs for voice synthesis
- Stability AI for image generation
- All contributors to this project

## 📧 Contact

- **GitHub**: [AI-Cloud-Tech-Inc](https://github.com/AI-Cloud-Tech-Inc)
- **Issues**: [Report a bug](https://github.com/AI-Cloud-Tech-Inc/AI-Film-Studio/issues)

---

Made with ❤️ by AI Cloud Tech Inc
