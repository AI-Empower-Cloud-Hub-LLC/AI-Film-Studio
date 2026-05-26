'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  description: string;
  parallel_group?: string;
}

interface GraphEdge {
  from: string;
  to: string;
  type: string;
  label?: string;
}

interface GraphStructure {
  nodes: GraphNode[];
  edges: GraphEdge[];
  features: string[];
}

interface WorkflowStep {
  agent: string;
  status: string;
  detail: string;
}

interface FilmResult {
  status: string;
  project_id?: string;
  message?: string;
  data?: {
    scene_count?: number;
    total_duration?: number;
    workflow_steps?: WorkflowStep[];
    node_timings?: Record<string, number>;
    revision_count?: number;
  };
}

const NODE_STATUS_COLORS: Record<string, string> = {
  pending: 'border-gray-600 bg-gray-700 text-gray-400',
  running: 'border-indigo-400 bg-indigo-900/50 text-indigo-300 ring-2 ring-indigo-400/30',
  completed: 'border-green-500 bg-green-900/30 text-green-300',
  error: 'border-red-500 bg-red-900/30 text-red-300',
  revision: 'border-yellow-500 bg-yellow-900/30 text-yellow-300',
};

const STATUS_ICONS: Record<string, string> = {
  pending: '○',
  running: '◉',
  completed: '✓',
  error: '✗',
  revision: '↺',
};

function PipelineGraph({ graph, steps }: { graph: GraphStructure | null; steps: WorkflowStep[] }) {
  if (!graph) return null;

  const stepsByAgent: Record<string, WorkflowStep> = {};
  for (const s of steps) {
    stepsByAgent[s.agent] = s;
  }

  const getNodeStatus = (node: GraphNode): string => {
    const step = stepsByAgent[node.label];
    return step?.status || 'pending';
  };

  const orderedNodes: (GraphNode | GraphNode[])[] = [];
  const parallelGroupAdded = new Set<string>();

  const nodeOrder = ['director', 'screenwriter', 'cinematographer', 'editor', 'review'];
  for (const id of nodeOrder) {
    const node = graph.nodes.find(n => n.id === id);
    if (!node) continue;
    if (node.parallel_group && !parallelGroupAdded.has(node.parallel_group)) {
      parallelGroupAdded.add(node.parallel_group);
      orderedNodes.push(graph.nodes.filter(n => n.parallel_group === node.parallel_group));
    } else if (!node.parallel_group) {
      orderedNodes.push(node);
    }
  }

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-lg font-bold text-indigo-400">LangGraph Pipeline</h3>
        <div className="flex gap-1 ml-auto">
          {graph.features.map(f => (
            <span key={f} className="text-[10px] px-1.5 py-0.5 bg-indigo-900/50 text-indigo-300 rounded border border-indigo-700">
              {f.replace('_', ' ')}
            </span>
          ))}
        </div>
      </div>

      <div className="flex flex-col items-center gap-2">
        {orderedNodes.map((item, idx) => (
          <div key={idx} className="w-full">
            {Array.isArray(item) ? (
              <div>
                <div className="text-center text-xs text-gray-500 mb-1">parallel execution</div>
                <div className="flex gap-3 justify-center">
                  {item.map(node => (
                    <NodeCard key={node.id} node={node} status={getNodeStatus(node)} step={stepsByAgent[node.label]} />
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex justify-center">
                <NodeCard node={item} status={getNodeStatus(item)} step={stepsByAgent[item.label]} />
              </div>
            )}
            {idx < orderedNodes.length - 1 && (
              <div className="flex justify-center my-1">
                <span className="text-gray-500 text-lg">↓</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function NodeCard({ node, status, step }: { node: GraphNode; status: string; step?: WorkflowStep }) {
  return (
    <div className={`flex-1 max-w-xs px-4 py-3 rounded-lg border transition-all duration-300 ${NODE_STATUS_COLORS[status] || NODE_STATUS_COLORS.pending}`}>
      <div className="flex items-center gap-2">
        <span className="text-lg font-mono">
          {status === 'running' ? (
            <span className="inline-block animate-spin">◉</span>
          ) : (
            STATUS_ICONS[status] || STATUS_ICONS.pending
          )}
        </span>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm">{node.label}</div>
          <div className="text-xs opacity-70 truncate">{step?.detail || node.description}</div>
        </div>
        {node.type === 'decision' && (
          <span className="text-[10px] px-1 py-0.5 bg-yellow-800/50 text-yellow-300 rounded">decision</span>
        )}
      </div>
    </div>
  );
}

export default function CreateFilm() {
  const [formData, setFormData] = useState({
    prompt: '',
    style: 'cinematic',
    duration: 30,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FilmResult | null>(null);
  const [graph, setGraph] = useState<GraphStructure | null>(null);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/autonomous/graph')
      .then(r => r.json())
      .then(setGraph)
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setSteps([]);

    try {
      const response = await fetch('http://localhost:8000/api/v1/autonomous/create-film', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: formData.prompt,
          style: formData.style,
          duration: formData.duration,
        }),
      });

      const data = await response.json();
      setResult(data);
      if (data.data?.workflow_steps) {
        setSteps(data.data.workflow_steps);
      }
    } catch (error) {
      console.error('Error:', error);
      setResult({ status: 'error', message: 'Failed to connect to backend' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="container mx-auto">
          <Link href="/" className="text-indigo-400 hover:text-indigo-300 mb-2 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold">🎬 Create Your Film</h1>
          <p className="text-gray-400 mt-2">Transform your vision into reality with autonomous AI agents</p>
        </div>
      </header>

      <main className="container mx-auto p-6 max-w-4xl">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Form column */}
          <div className="lg:col-span-3">
            <form onSubmit={handleSubmit} className="bg-gray-800 p-8 rounded-lg border border-gray-700">
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">
                  Film Concept <span className="text-red-400">*</span>
                </label>
                <textarea
                  value={formData.prompt}
                  onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                  placeholder="Describe your film idea... (e.g., 'A cyberpunk city at night with neon lights and flying vehicles')"
                  rows={4}
                  required
                  disabled={loading}
                  className="w-full p-3 bg-gray-700 border border-gray-600 rounded focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Visual Style</label>
                  <select
                    value={formData.style}
                    onChange={(e) => setFormData({ ...formData, style: e.target.value })}
                    disabled={loading}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="cinematic">Cinematic</option>
                    <option value="documentary">Documentary</option>
                    <option value="anime">Anime</option>
                    <option value="cartoon">Cartoon</option>
                    <option value="realistic">Realistic</option>
                    <option value="sci-fi">Sci-Fi</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Duration (seconds)</label>
                  <input
                    type="number"
                    value={formData.duration}
                    onChange={(e) => setFormData({ ...formData, duration: parseInt(e.target.value) })}
                    min="10"
                    max="300"
                    step="10"
                    disabled={loading}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">AI Backend</label>
                <div className="w-full p-3 bg-gray-700 border border-gray-600 rounded text-gray-300">
                  Ollama (Local LLM) — Free, no API key needed
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Powered by Mistral via Ollama. Or set GOOGLE_API_KEY for Google AI.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || !formData.prompt}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 text-white font-bold py-4 rounded-lg text-lg transition"
              >
                {loading ? '🎬 Creating Film...' : '🚀 Create Film'}
              </button>
            </form>

            {/* Result section */}
            {result && result.status === 'success' && (
              <div className="mt-6 bg-gray-800 p-6 rounded-lg border border-green-500">
                <h3 className="text-xl font-bold mb-4 text-green-400">Film Created Successfully!</h3>
                <div className="space-y-2 text-sm">
                  <p><span className="text-gray-400">Project ID:</span> {result.project_id}</p>
                  <p><span className="text-gray-400">Scenes:</span> {result.data?.scene_count}</p>
                  <p><span className="text-gray-400">Duration:</span> {result.data?.total_duration}s</p>
                  {result.data?.revision_count ? (
                    <p><span className="text-gray-400">Revisions:</span> {result.data.revision_count}</p>
                  ) : null}
                  {result.data?.node_timings && (
                    <div className="mt-3 pt-3 border-t border-gray-700">
                      <p className="text-gray-400 mb-1">Pipeline Timings:</p>
                      <div className="grid grid-cols-2 gap-1">
                        {Object.entries(result.data.node_timings).map(([node, time]) => (
                          <div key={node} className="flex justify-between text-xs">
                            <span className="text-gray-500">{node}</span>
                            <span className="text-indigo-300">{time}s</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {result && result.status === 'error' && (
              <div className="mt-6 bg-gray-800 p-6 rounded-lg border border-red-500">
                <h3 className="text-xl font-bold mb-2 text-red-400">Pipeline Error</h3>
                <p className="text-sm text-gray-300">{result.message || 'An error occurred during film creation'}</p>
              </div>
            )}
          </div>

          {/* Pipeline visualization column */}
          <div className="lg:col-span-2">
            <PipelineGraph graph={graph} steps={steps} />
          </div>
        </div>
      </main>
    </div>
  );
}
