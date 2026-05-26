'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/solid'
import {
  SparklesIcon,
} from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import AuthGuard from '../components/AuthGuard'
import ErrorBoundary from '../components/ErrorBoundary'
import { projectsApi } from '../../lib/api'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const AGENTS = ['Director', 'Screenwriter', 'Cinematographer', 'SoundDesigner', 'Editor']

interface AgentProgress {
  step: number
  total_steps: number
  agent: string
  status: string
  detail: string
}

function AgentIcon({ status }: { status: 'pending' | 'running' | 'completed' | 'error' }) {
  if (status === 'completed') return <CheckCircleIcon className="h-5 w-5 text-green-400" />
  if (status === 'error') return <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
  if (status === 'running') {
    return <div className="h-5 w-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
  }
  return <div className="h-5 w-5 border-2 border-gray-600 rounded-full" />
}

function CreateFilmContent() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    prompt: '',
    style: 'cinematic',
    duration: 30,
    model: 'claude-opus-4-6',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [agentStates, setAgentStates] = useState<Record<string, { status: string; detail: string }>>({})
  const wsRef = useRef<WebSocket | null>(null)

  const cleanupWs = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  useEffect(() => {
    return cleanupWs
  }, [cleanupWs])

  const connectWebSocket = useCallback((projectId: string) => {
    const wsUrl = API_BASE.replace(/^http/, 'ws')
    const ws = new WebSocket(`${wsUrl}/ws/projects/${projectId}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data: AgentProgress = JSON.parse(event.data)
      if (data.agent && data.status) {
        setAgentStates((prev) => ({
          ...prev,
          [data.agent]: { status: data.status, detail: data.detail || '' },
        }))
      }
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setAgentStates({})

    try {
      const result = await projectsApi.createFilm(
        formData.prompt,
        formData.style,
        formData.duration,
        formData.model,
      )

      if (result.project_id) {
        connectWebSocket(result.project_id)
      }

      AGENTS.forEach((a) =>
        setAgentStates((prev) => ({ ...prev, [a]: { status: 'completed', detail: '' } })),
      )

      setTimeout(() => {
        router.push(`/projects/${result.project_id}`)
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create film')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black">
      <Sidebar />

      <div className="pl-0 lg:pl-64">
        <div className="px-8 py-8 max-w-3xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-1">Create Film</h1>
            <p className="text-gray-400">Transform your vision into reality with autonomous AI agents</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Film Concept <span className="text-red-400">*</span>
                </label>
                <textarea
                  value={formData.prompt}
                  onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                  placeholder="Describe your film idea... (e.g., 'A cyberpunk city at night with neon lights and flying vehicles')"
                  rows={4}
                  required
                  disabled={loading}
                  className="w-full p-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none text-white placeholder-gray-500 transition-colors"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Visual Style</label>
                  <select
                    value={formData.style}
                    onChange={(e) => setFormData({ ...formData, style: e.target.value })}
                    disabled={loading}
                    className="w-full p-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:border-purple-500 focus:outline-none text-white transition-colors"
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
                  <label className="block text-sm font-medium text-gray-300 mb-2">Duration (seconds)</label>
                  <input
                    type="number"
                    value={formData.duration}
                    onChange={(e) => setFormData({ ...formData, duration: parseInt(e.target.value) || 30 })}
                    min="10"
                    max="300"
                    step="10"
                    disabled={loading}
                    className="w-full p-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:border-purple-500 focus:outline-none text-white transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">AI Model</label>
                <select
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  disabled={loading}
                  className="w-full p-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:border-purple-500 focus:outline-none text-white transition-colors"
                >
                  <option value="claude-opus-4-6">Claude Opus 4.6 — Most Powerful</option>
                  <option value="claude-sonnet-4-6">Claude Sonnet 4.6 — Balanced</option>
                  <option value="claude-haiku-4-5">Claude Haiku 4.5 — Fastest</option>
                  <option value="gpt-4">GPT-4 (OpenAI)</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !formData.prompt || formData.prompt.length < 10}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:from-gray-700 disabled:to-gray-700 text-white font-bold py-4 rounded-xl text-lg transition-all hover:shadow-lg hover:shadow-purple-500/30 disabled:cursor-not-allowed"
            >
              <SparklesIcon className="h-6 w-6" />
              {loading ? 'Creating Film...' : 'Create Film'}
            </button>
          </form>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="mt-6 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl p-4 flex items-start gap-3"
              >
                <ExclamationCircleIcon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium">Film creation failed</p>
                  <p className="text-sm mt-1 text-red-300">{error}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 bg-gray-800/60 border border-gray-700/50 rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Production Pipeline</h3>
              <div className="space-y-3">
                {AGENTS.map((agent, i) => {
                  const state = agentStates[agent]
                  const status = (state?.status || (i === 0 && loading ? 'running' : 'pending')) as 'pending' | 'running' | 'completed' | 'error'
                  return (
                    <motion.div
                      key={agent}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                        status === 'running'
                          ? 'bg-purple-500/10 border border-purple-500/20'
                          : status === 'completed'
                          ? 'bg-green-500/5'
                          : ''
                      }`}
                    >
                      <AgentIcon status={status} />
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium ${
                          status === 'completed' ? 'text-green-400' :
                          status === 'running' ? 'text-purple-400' :
                          'text-gray-500'
                        }`}>
                          Step {i + 1}: {agent}
                        </p>
                        {state?.detail && (
                          <p className="text-xs text-gray-500 mt-0.5 truncate">{state.detail}</p>
                        )}
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function CreateFilmPage() {
  return (
    <AuthGuard>
      <ErrorBoundary>
        <CreateFilmContent />
      </ErrorBoundary>
    </AuthGuard>
  )
}
