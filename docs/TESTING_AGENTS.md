# Agent Testing

Guide for testing the autonomous AI agents and the Agent Orchestrator in AI Film Studio.

## Agent Architecture Recap

All agents extend `BaseAgent` (in `backend/app/agents/base_agent.py`):

```
BaseAgent (ABC)
├── DirectorAgent        # Creative vision and scene breakdown
├── ScreenwriterAgent    # Script and dialogue generation
├── CinematographerAgent # Shot planning and visual composition
├── SoundDesignerAgent   # Audio design and music planning
└── EditorAgent          # Scene assembly and pacing
```

The `AgentOrchestrator` chains them together into a production pipeline.

Each agent calls Claude via `_ask_claude()` using the Anthropic SDK. Testing agents therefore requires either mocking the LLM call or using a live API key.

## Testing Strategies

### 1. Mock-Based Unit Tests (No API Key Needed)

Patch `_ask_claude` to return deterministic responses. This is the primary approach for CI.

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.director_agent import DirectorAgent

@pytest.mark.asyncio
async def test_director_process_mocked():
    agent = DirectorAgent(anthropic_api_key="fake-key")

    vision_text = "A noir-inspired visual journey through rain-soaked streets."
    scenes_json = '[{"scene_number":1,"description":"Opening shot","duration":10,"shot_type":"wide","mood":"mysterious","visual_prompt":"Dark city street at night"}]'

    with patch.object(agent, "_ask_claude", new_callable=AsyncMock) as mock_ask:
        # First call returns the vision, second returns the scene breakdown
        mock_ask.side_effect = [vision_text, scenes_json]

        result = await agent.process({
            "prompt": "A film noir detective story",
            "style": "cinematic",
            "duration": 30,
        })

    assert result["vision"] == vision_text
    assert len(result["scenes"]) == 1
    assert result["scenes"][0]["shot_type"] == "wide"
    assert result["agent"] == "Director"
    assert mock_ask.call_count == 2
```

### 2. Orchestrator Pipeline Tests

Test the full pipeline by mocking each agent's `process` method:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.orchestrator import AgentOrchestrator

@pytest.mark.asyncio
async def test_orchestrator_pipeline():
    orch = AgentOrchestrator(anthropic_api_key="fake-key")

    director_out = {"vision": "epic vision", "scenes": [{"scene_number": 1}], "style": "cinematic"}
    screenwriter_out = {"script_scenes": [{"scene_number": 1, "dialogue": "Hello"}], "total_scenes": 1}
    cinematographer_out = {"shots": [{"scene_number": 1, "camera": "wide"}]}
    sound_out = {"audio_plan": [{"scene_number": 1, "music": "orchestral"}]}
    editor_out = {"timeline": [{"scene_number": 1, "duration": 10}]}

    with patch.object(orch.director, "process", new_callable=AsyncMock, return_value=director_out), \
         patch.object(orch.screenwriter, "process", new_callable=AsyncMock, return_value=screenwriter_out), \
         patch.object(orch.cinematographer, "process", new_callable=AsyncMock, return_value=cinematographer_out), \
         patch.object(orch.sound_designer, "process", new_callable=AsyncMock, return_value=sound_out), \
         patch.object(orch.editor, "process", new_callable=AsyncMock, return_value=editor_out):

        result = await orch.create_film("A sunrise over the ocean", style="cinematic", duration=30)

    assert "director" in result
    assert "screenwriter" in result
    assert result["status"] == "completed"
```

### 3. Agent Memory Tests

Verify that agents correctly store and retrieve context:

```python
from app.agents.director_agent import DirectorAgent

def test_agent_memory():
    agent = DirectorAgent(anthropic_api_key="fake")
    assert agent.memory == []

    agent.add_to_memory({"vision": "dark and moody"})
    agent.add_to_memory({"scenes": [1, 2, 3]})
    assert len(agent.memory) == 2

    context = agent.get_context(max_items=1)
    assert len(context) == 1
    assert "scenes" in context[0]

    agent.clear_memory()
    assert agent.memory == []
```

### 4. Integration Tests with Live API (Optional)

These tests call the real Anthropic API and are marked `slow`. They require `ANTHROPIC_API_KEY` to be set.

```python
import os
import pytest
from app.agents.director_agent import DirectorAgent

@pytest.mark.slow
@pytest.mark.asyncio
async def test_director_live_api():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = DirectorAgent(anthropic_api_key=api_key)
    result = await agent.process({
        "prompt": "A heartwarming story about a dog finding its way home",
        "style": "cinematic",
        "duration": 30,
    })

    assert isinstance(result["vision"], str)
    assert len(result["vision"]) > 20
    assert isinstance(result["scenes"], list)
    assert len(result["scenes"]) >= 3
```

Run only slow tests:

```bash
pytest -m slow
```

### 5. Prompt Optimizer Tests

The `PromptOptimizer` uses LangChain + Claude. When no API key is set, it falls back to passthrough mode:

```python
import pytest
from app.services.prompt_optimizer import PromptOptimizer

@pytest.mark.asyncio
async def test_optimizer_passthrough():
    optimizer = PromptOptimizer()
    result = await optimizer.optimize("A sunset over mountains", "cinematic", 30)
    assert result["optimized_prompt"] == "A sunset over mountains"
    assert result["was_optimized"] is False
```

## Agent Test Checklist

When adding a new agent or modifying an existing one, verify:

- [ ] `process()` returns the expected dictionary structure
- [ ] LLM responses are parsed correctly (especially JSON responses)
- [ ] Invalid or empty LLM responses are handled gracefully
- [ ] Memory is updated after processing
- [ ] The agent integrates correctly with the orchestrator pipeline
- [ ] Logging output is informative (check with `caplog` fixture)

## Mocking Tips

### Mocking `_ask_claude` with `side_effect`

Use `side_effect` when an agent makes multiple LLM calls in one `process()` invocation (e.g. Director calls `_create_vision` then `_break_down_scenes`):

```python
mock_ask.side_effect = [
    "vision text",      # first _ask_claude call
    '[{"scene": 1}]',   # second _ask_claude call
]
```

### Mocking at the Anthropic SDK Level

For deeper tests, mock the `AsyncAnthropic` client:

```python
from unittest.mock import AsyncMock, MagicMock

mock_client = MagicMock()
mock_client.messages.create = AsyncMock(return_value=MagicMock(
    content=[MagicMock(type="text", text="mocked response")]
))
agent._client = mock_client
```

### Handling JSON Parse Errors

Test that agents handle malformed LLM output:

```python
@pytest.mark.asyncio
async def test_director_handles_bad_json():
    agent = DirectorAgent(anthropic_api_key="fake")

    with patch.object(agent, "_ask_claude", new_callable=AsyncMock) as mock_ask:
        mock_ask.side_effect = ["good vision", "not valid json"]

        with pytest.raises(Exception):
            await agent.process({"prompt": "test prompt", "style": "cinematic", "duration": 30})
```

## File Reference

| File | Contains |
|---|---|
| `backend/app/agents/base_agent.py` | `BaseAgent` ABC, `_ask_claude`, memory methods |
| `backend/app/agents/director_agent.py` | `DirectorAgent` &mdash; vision and scene breakdown |
| `backend/app/agents/screenwriter_agent.py` | `ScreenwriterAgent` &mdash; script generation |
| `backend/app/agents/cinematographer_agent.py` | `CinematographerAgent` &mdash; shot planning |
| `backend/app/agents/sound_designer_agent.py` | `SoundDesignerAgent` &mdash; audio design |
| `backend/app/agents/editor_agent.py` | `EditorAgent` &mdash; scene assembly |
| `backend/app/agents/orchestrator.py` | `AgentOrchestrator` &mdash; pipeline coordinator |
| `backend/app/services/prompt_optimizer.py` | `PromptOptimizer` &mdash; LangChain prompt enhancement |
