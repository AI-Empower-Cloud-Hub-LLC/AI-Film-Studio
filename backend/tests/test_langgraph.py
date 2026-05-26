"""
Tests for the advanced LangGraph orchestrator features.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.orchestrator import AgentOrchestrator, PipelineState


@pytest.fixture
def orchestrator():
    """Create an orchestrator with mock LLM that returns demo content."""
    return AgentOrchestrator()


def test_graph_structure(orchestrator):
    """Graph introspection returns correct topology."""
    structure = orchestrator.get_graph_structure()

    assert "nodes" in structure
    assert "edges" in structure
    assert "features" in structure

    node_ids = {n["id"] for n in structure["nodes"]}
    assert node_ids == {
        "director", "screenwriter", "screenplay_refinement",
        "cinematographer", "sound_designer", "cast_selection", "location_research",
        "vfx_planning", "mood_board",
        "editor", "review",
    }

    assert "parallel_execution" in structure["features"]
    assert "error_retry" in structure["features"]
    assert "state_checkpointing" in structure["features"]
    assert "quality_review_loop" in structure["features"]


def test_graph_has_parallel_group(orchestrator):
    """Production and post-production nodes are in parallel groups."""
    structure = orchestrator.get_graph_structure()
    parallel_nodes = [n for n in structure["nodes"] if n.get("parallel_group")]
    assert len(parallel_nodes) == 6
    groups = {n["parallel_group"] for n in parallel_nodes}
    assert groups == {"production", "post_production"}
    production_ids = {n["id"] for n in parallel_nodes if n["parallel_group"] == "production"}
    assert production_ids == {"cinematographer", "sound_designer", "cast_selection", "location_research"}


def test_graph_has_review_decision_node(orchestrator):
    """Review node is typed as 'decision' for conditional routing."""
    structure = orchestrator.get_graph_structure()
    review = next(n for n in structure["nodes"] if n["id"] == "review")
    assert review["type"] == "decision"


def test_graph_has_conditional_edges(orchestrator):
    """Review has conditional edges (approved → END, revision → screenwriter)."""
    structure = orchestrator.get_graph_structure()
    review_edges = [e for e in structure["edges"] if e["from"] == "review"]
    assert len(review_edges) == 2
    labels = {e.get("label") for e in review_edges}
    assert "approved" in labels
    assert "revision needed" in labels


def test_graph_has_fan_out_edges(orchestrator):
    """Screenplay refinement fans out to production nodes."""
    structure = orchestrator.get_graph_structure()
    fan_out_edges = [e for e in structure["edges"] if e["type"] == "fan_out"]
    assert len(fan_out_edges) == 4
    targets = {e["to"] for e in fan_out_edges}
    assert targets == {"cinematographer", "sound_designer", "cast_selection", "location_research"}


def test_run_history_empty_initially(orchestrator):
    """Run history is empty before any pipelines execute."""
    assert orchestrator.get_run_history() == []


@pytest.mark.asyncio
async def test_create_film_returns_workflow_steps(orchestrator):
    """Pipeline returns workflow_steps with all agents."""
    result = await orchestrator.create_film(
        user_prompt="A sunset over the ocean with dramatic waves",
        style="cinematic",
        duration=30,
    )
    assert result["status"] == "success"
    steps = result.get("workflow_steps", [])
    agent_names = [s["agent"] for s in steps]
    assert "Director" in agent_names
    assert "Screenwriter" in agent_names
    assert "Screenplay Refinement" in agent_names
    assert "Cinematographer" in agent_names
    assert "Sound Designer" in agent_names
    assert "Cast Selection" in agent_names
    assert "Location Research" in agent_names
    assert "VFX Planning" in agent_names
    assert "Mood Board" in agent_names
    assert "Editor" in agent_names
    assert "Quality Review" in agent_names


@pytest.mark.asyncio
async def test_create_film_returns_node_timings(orchestrator):
    """Pipeline returns timing data for each node."""
    result = await orchestrator.create_film(
        user_prompt="A forest at dawn with morning mist",
        style="documentary",
        duration=20,
    )
    assert result["status"] == "success"
    timings = result.get("node_timings", {})
    assert "director" in timings
    assert "screenwriter" in timings
    assert "parallel_production" in timings
    assert "editor" in timings
    assert "review" in timings
    for v in timings.values():
        assert isinstance(v, float)
        assert v >= 0


@pytest.mark.asyncio
async def test_create_film_updates_run_history(orchestrator):
    """After a pipeline run, run history contains the record."""
    assert len(orchestrator.get_run_history()) == 0
    await orchestrator.create_film(
        user_prompt="Neon cityscape at night",
        style="sci-fi",
        duration=30,
    )
    history = orchestrator.get_run_history()
    assert len(history) == 1
    assert history[0]["prompt"] == "Neon cityscape at night"
    assert history[0]["status"] == "success"
    assert "node_timings" in history[0]


@pytest.mark.asyncio
async def test_create_film_parallel_produces_both_outputs(orchestrator):
    """Parallel node produces both cinematography and sound outputs."""
    result = await orchestrator.create_film(
        user_prompt="A dancer on a moonlit stage",
        style="cinematic",
        duration=30,
    )
    assert result["status"] == "success"
    assert "cinematography" in result
    assert "sound" in result
    assert "cast" in result
    assert "locations" in result
    assert result["cinematography"].get("agent") == "Cinematographer"
    assert result["sound"].get("agent") == "SoundDesigner"
