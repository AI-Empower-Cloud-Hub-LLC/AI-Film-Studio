# Testing the Autonomous Agentic AI System 🤖🎬

## Quick Start Testing

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy development config
copy ..\env.dev .env

# Add your OpenAI API key
# Edit .env and set: OPENAI_API_KEY=sk-your-key-here
```

### 3. Start the Server
```bash
python main.py
```

Server starts at: http://localhost:8000

### 4. Test Autonomous Film Creation

#### Option A: Using the API Docs (Easiest)
1. Open http://localhost:8000/docs
2. Find **POST /api/v1/autonomous/create-film**
3. Click "Try it out"
4. Use this test request:
```json
{
  "user_input": "Create a 30-second inspirational video about a person overcoming challenges to achieve their dreams",
  "duration": 30,
  "style": "cinematic",
  "quality": "high"
}
```
5. Click "Execute"

#### Option B: Using cURL
```bash
curl -X POST http://localhost:8000/api/v1/autonomous/create-film \
  -H "Content-Type: application/json" \
  -d "{
    \"user_input\": \"Create a 30-second inspirational video about a person overcoming challenges\",
    \"duration\": 30,
    \"style\": \"cinematic\"
  }"
```

#### Option C: Using PowerShell
```powershell
$headers = @{
    "Content-Type" = "application/json"
}
$body = @{
    user_input = "Create a 30-second inspirational video about overcoming challenges"
    duration = 30
    style = "cinematic"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/autonomous/create-film" `
    -Method Post -Headers $headers -Body $body
```

### 5. Monitor Agent Activity

#### Check Agent Status
```bash
# See what agents are doing
curl http://localhost:8000/api/v1/autonomous/status
```

Response shows:
- Current workflow stage
- Each agent's status (idle, thinking, working)
- Agent memory sizes
- Project state

#### List All Agents
```bash
curl http://localhost:8000/api/v1/autonomous/agents
```

### 6. Watch the Autonomous Workflow

When you trigger film creation, watch the logs to see agents working:

```
INFO: Director Agent: Developing creative vision...
INFO: Director thinking: "Interpret this user request into a creative vision..."
INFO: Screenwriter Agent: Writing script...
INFO: Screenwriter thinking: "Write a 30-second screenplay for..."
INFO: Director Agent: Reviewing script...
INFO: Editor Agent: Assembling edit...
INFO: Director Agent: Final approval...
```

## What the Agents Do Autonomously

### Stage 1: Concept Development (Director)
```
User: "Create inspirational video about overcoming challenges"
  ↓
Director Agent:
- Analyzes user input
- Determines tone: Inspirational, uplifting
- Sets visual style: Cinematic, high-quality
- Defines pacing: Dynamic with emotional beats
- Creates creative vision document
```

### Stage 2: Script Development (Screenwriter + Director)
```
Screenwriter Agent:
- Writes complete screenplay
- Breaks down into scenes
- Adds visual notes
- Includes timing estimates
  ↓
Director Agent:
- Reviews script
- Provides feedback
- Approves or requests revisions
```

### Stage 3: Pre-Production (Director)
```
Director Agent:
- Plans shot list
- Determines camera angles
- Sets composition requirements
- Creates production brief
```

### Stage 4: Production (AI Generation)
```
AI Generator:
- Generates all required shots
- Applies style guidelines
- Creates visual assets
(Currently placeholder - real AI integration next)
```

### Stage 5: Post-Production (Editor + Sound + VFX)
```
Editor Agent:
- Selects best shots
- Determines pacing
- Creates Edit Decision List (EDL)
- Assembles rough cut
  ↓
Sound Designer: (Coming soon)
- Adds music
- Creates sound effects
  ↓
VFX Agent: (Coming soon)
- Applies effects
- Enhances visuals
```

### Stage 6: Finalization (Director)
```
Director Agent:
- Reviews final cut
- Checks against creative vision
- Approves or requests changes
- Delivers final film
```

## Testing Individual Agents

### Test Director Agent
```bash
curl -X POST http://localhost:8000/api/v1/autonomous/agents/director/task \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"develop_vision\",
    \"user_input\": \"A dramatic sunset scene\"
  }"
```

### Test Screenwriter Agent
```bash
curl -X POST http://localhost:8000/api/v1/autonomous/agents/screenwriter/task \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"write_script\",
    \"brief\": \"Write a 15-second scene about friendship\",
    \"duration\": 15
  }"
```

### Test Editor Agent
```bash
curl -X POST http://localhost:8000/api/v1/autonomous/agents/editor/task \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"determine_pacing\",
    \"sequence\": \"3 shots: wide, medium, close-up\",
    \"target_emotion\": \"tension\"
  }"
```

## Test Scenarios

### 1. Simple Inspirational Video
```json
{
  "user_input": "Create an uplifting 20-second video about new beginnings",
  "duration": 20,
  "style": "bright and hopeful"
}
```

### 2. Dramatic Story
```json
{
  "user_input": "A 45-second dramatic story about a person finding courage in a difficult moment",
  "duration": 45,
  "style": "cinematic drama"
}
```

### 3. Product Showcase
```json
{
  "user_input": "Create a sleek 30-second product video for a new smartphone, emphasizing innovation and design",
  "duration": 30,
  "style": "modern and minimal"
}
```

### 4. Nature Documentary Style
```json
{
  "user_input": "A 60-second nature video showcasing the beauty of mountains and wildlife",
  "duration": 60,
  "style": "documentary"
}
```

### 5. Music Video Concept
```json
{
  "user_input": "Create a 90-second music video concept with vibrant colors and dynamic movement",
  "duration": 90,
  "style": "vibrant and energetic"
}
```

## Debugging Agent Behavior

### Check Agent Memory
Agents store their decision history in memory:
```python
# In agent code:
agent.memory  # List of all decisions and actions
```

### View Agent Context
```python
# Current working context:
agent.context  # Dict of current project info
```

### Enable Debug Logging
```bash
# In .env
AGENT_LOGGING_LEVEL=DEBUG
LOG_LEVEL=DEBUG
```

### Watch LLM Prompts
The agents log their "thinking" prompts:
```
DEBUG: Director thinking: "As an AI film director, develop creative vision for: [user input]..."
```

## Common Issues & Solutions

### Issue: "OpenAI API key not found"
**Solution:** Add your key to `.env`:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### Issue: Agents timing out
**Solution:** Increase timeouts in `.env`:
```
AGENT_ORCHESTRATOR_TIMEOUT=7200
WORKFLOW_STAGE_TIMEOUT_PRODUCTION=3600
```

### Issue: "Agent not found" error
**Solution:** Check agent is enabled:
```
DIRECTOR_AGENT_ENABLED=true
SCREENWRITER_AGENT_ENABLED=true
EDITOR_AGENT_ENABLED=true
```

### Issue: Want faster testing
**Solution:** Use GPT-3.5-Turbo:
```
AGENT_LLM_MODEL=gpt-3.5-turbo
```

## Next Steps

### 1. Integrate Real LLMs
Currently agents use placeholder responses. Connect actual LLMs:
```python
# In base_agent.py _call_llm()
import openai
response = await openai.ChatCompletion.acreate(...)
```

### 2. Add More Agents
- Cinematographer Agent
- Sound Designer Agent
- VFX Artist Agent
- Color Grader Agent

### 3. Integrate AI Video Generation
Connect to:
- Stable Diffusion Video
- Runway ML
- Pika Labs
- Other AI video generators

### 4. Build Frontend
Create React UI to:
- Submit film requests
- Monitor agent activity in real-time
- View agent decisions
- Manual intervention controls

### 5. Add Learning
Implement agent learning from:
- Human feedback
- Successful patterns
- User preferences

## Performance Metrics

Track these metrics:
- **Time per stage**: How long each workflow stage takes
- **Iteration count**: How many revisions needed
- **Approval rate**: How often director approves first draft
- **User satisfaction**: Feedback on final films
- **Agent efficiency**: Token usage, API calls

## Advanced Testing

### Test Multi-Agent Collaboration
```python
# Send message between agents
orchestrator.send_message_between_agents(
    from_role=AgentRole.EDITOR,
    to_role=AgentRole.DIRECTOR,
    message={
        "type": "request_approval",
        "work_type": "rough_cut",
        "data": edit_data
    }
)
```

### Test Human Intervention
```python
# Pause for human review
orchestrator.pause_for_review(stage="script")

# Override agent decision
orchestrator.override_decision(
    agent=AgentRole.DIRECTOR,
    decision="creative_vision",
    override_value=custom_vision
)
```

### Load Testing
```bash
# Test multiple concurrent film creations
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/autonomous/create-film \
    -H "Content-Type: application/json" \
    -d "{\"user_input\": \"Test film $i\", \"duration\": 30}" &
done
```

## Success Criteria

Your autonomous system works when:
- ✅ Agents complete all 6 workflow stages
- ✅ Director creates meaningful creative vision
- ✅ Screenwriter produces coherent scripts
- ✅ Editor makes logical pacing decisions
- ✅ Agents collaborate (request feedback, iterate)
- ✅ Final output aligns with user intent
- ✅ No manual intervention required (unless configured)

## Get Help

- Check [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md) for system design
- Review agent logs for decision trail
- Monitor `/api/v1/autonomous/status` during runs
- Join community for agent development tips

**Happy Autonomous Filmmaking! 🎬🤖**
