'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  FilmIcon,
  ArrowLeftIcon,
  ClockIcon,
  SparklesIcon,
  CpuChipIcon,
  VideoCameraIcon,
  MusicalNoteIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline'
import { CheckCircleIcon } from '@heroicons/react/24/solid'

interface Scene {
  scene_number: number
  description: string
  shot_type: string
  mood: string
  duration: number
  visual_prompt: string
  narration: string
  dialogue: string[]
  audio_cues: string[]
}

interface Project {
  id: string
  title: string
  prompt: string
  style: string
  duration: number
  model: string
  status: string
  director_vision: string
  created_at: string
  scenes: Scene[]
  script: Scene[]
}

const SHOT_COLORS: Record<string, string> = {
  wide: 'from-blue-500 to-cyan-500',
  medium: 'from-purple-500 to-pink-500',
  close: 'from-orange-500 to-red-500',
  'close-up': 'from-orange-500 to-red-500',
  aerial: 'from-green-500 to-teal-500',
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'scenes' | 'script'>('scenes')

  useEffect(() => {
    if (!id) return
    fetch(`http://localhost:8000/api/v1/autonomous/projects/${id}`)
      .then(r => {
        if (!r.ok) throw new Error(`Server error ${r.status}`)
        return r.json()
      })
      .then(setProject)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-900 flex items-center justify-center text-gray-400">
        <div className="animate-spin h-8 w-8 border-2 border-purple-400 border-t-transparent rounded-full mr-3" />
        Loading project…
      </main>
    )
  }

  if (error || !project) {
    return (
      <main className="min-h-screen bg-gray-900 flex flex-col items-center justify-center text-center gap-3">
        <FilmIcon className="h-12 w-12 text-gray-600" />
        <p className="text-red-400 font-medium">{error ?? 'Project not found'}</p>
        <Link href="/projects" className="text-purple-400 hover:text-purple-300 text-sm">
          ← Back to projects
        </Link>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black">
      {/* Header */}
      <header className="border-b border-gray-800/60 backdrop-blur-sm sticky top-0 z-10 bg-gray-900/80">
        <div className="container mx-auto px-4 py-4 flex items-center gap-4">
          <Link href="/projects" className="flex items-center gap-1.5 text-gray-400 hover:text-white transition-colors text-sm">
            <ArrowLeftIcon className="h-4 w-4" />
            Projects
          </Link>
          <span className="text-gray-700">/</span>
          <span className="text-white font-medium truncate">{project.title}</span>
        </div>
      </header>

      <div className="container mx-auto px-4 py-10 max-w-5xl">
        {/* Hero */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircleIcon className="h-5 w-5 text-green-400" />
            <span className="text-green-400 text-sm font-medium capitalize">{project.status}</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-4 leading-tight">
            {project.title}
          </h1>
          <div className="flex flex-wrap gap-3 text-sm text-gray-400">
            <span className="flex items-center gap-1.5 px-3 py-1 bg-gray-800 rounded-full">
              <SparklesIcon className="h-4 w-4" /> {project.style}
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 bg-gray-800 rounded-full">
              <ClockIcon className="h-4 w-4" /> {project.duration}s
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 bg-gray-800 rounded-full">
              <CpuChipIcon className="h-4 w-4" /> {project.model}
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 bg-gray-800 rounded-full">
              <FilmIcon className="h-4 w-4" /> {project.scenes.length} scenes
            </span>
          </div>
        </motion.div>

        {/* Director Vision */}
        {project.director_vision && (
          <motion.section
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8 p-6 bg-purple-500/5 border border-purple-500/20 rounded-2xl"
          >
            <h2 className="text-purple-300 font-semibold mb-3 flex items-center gap-2">
              <VideoCameraIcon className="h-5 w-5" />
              Director&apos;s Vision
            </h2>
            <p className="text-gray-300 leading-relaxed whitespace-pre-line">{project.director_vision}</p>
          </motion.section>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-800/50 p-1 rounded-xl w-fit">
          {(['scenes', 'script'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all capitalize ${
                activeTab === tab
                  ? 'bg-purple-600 text-white shadow'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab === 'scenes' ? (
                <span className="flex items-center gap-1.5"><FilmIcon className="h-4 w-4" /> Scenes</span>
              ) : (
                <span className="flex items-center gap-1.5"><DocumentTextIcon className="h-4 w-4" /> Script</span>
              )}
            </button>
          ))}
        </div>

        {/* Scenes Tab */}
        {activeTab === 'scenes' && (
          <div className="space-y-4">
            {project.scenes.map((scene, i) => {
              const gradient = SHOT_COLORS[scene.shot_type] ?? 'from-purple-500 to-blue-500'
              return (
                <motion.div
                  key={scene.scene_number}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="bg-gray-900/80 border border-gray-800 rounded-2xl overflow-hidden"
                >
                  {/* Scene header bar */}
                  <div className={`h-1 bg-gradient-to-r ${gradient}`} />
                  <div className="p-6">
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div className="flex items-center gap-3">
                        <span className={`flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-r ${gradient} flex items-center justify-center text-white text-xs font-bold`}>
                          {scene.scene_number}
                        </span>
                        <div className="flex gap-2 flex-wrap">
                          <span className="px-2 py-0.5 text-xs bg-gray-800 text-gray-300 rounded-full capitalize">
                            {scene.shot_type} shot
                          </span>
                          <span className="px-2 py-0.5 text-xs bg-gray-800 text-gray-300 rounded-full capitalize">
                            {scene.mood}
                          </span>
                          <span className="px-2 py-0.5 text-xs bg-gray-800 text-gray-300 rounded-full flex items-center gap-1">
                            <ClockIcon className="h-3 w-3" />{scene.duration}s
                          </span>
                        </div>
                      </div>
                    </div>

                    <p className="text-gray-200 mb-4 leading-relaxed">{scene.description}</p>

                    {scene.visual_prompt && (
                      <div className="mb-4 p-3 bg-gray-800/60 rounded-lg border-l-2 border-purple-500">
                        <p className="text-xs text-purple-300 font-medium mb-1 uppercase tracking-wide">Visual Prompt</p>
                        <p className="text-gray-400 text-sm leading-relaxed">{scene.visual_prompt}</p>
                      </div>
                    )}

                    {scene.narration && (
                      <div className="mb-4">
                        <p className="text-xs text-blue-300 font-medium mb-1 uppercase tracking-wide flex items-center gap-1">
                          <MusicalNoteIcon className="h-3 w-3" /> Narration
                        </p>
                        <p className="text-gray-400 text-sm italic">&ldquo;{scene.narration}&rdquo;</p>
                      </div>
                    )}

                    {scene.audio_cues && scene.audio_cues.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {scene.audio_cues.map((cue, j) => (
                          <span key={j} className="px-2 py-0.5 text-xs bg-blue-500/10 text-blue-300 border border-blue-500/20 rounded-full">
                            {cue}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

        {/* Script Tab */}
        {activeTab === 'script' && (
          <div className="space-y-4">
            {project.script.length === 0 ? (
              <div className="text-center py-16 text-gray-500">No script data available.</div>
            ) : (
              project.script.map((scene, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="bg-gray-900/80 border border-gray-800 rounded-2xl p-6"
                >
                  <div className="flex items-center gap-2 mb-4">
                    <span className="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center text-gray-300 text-xs font-bold">
                      {scene.scene_number}
                    </span>
                    <span className="text-gray-400 text-sm">Scene {scene.scene_number}</span>
                  </div>

                  {scene.narration && (
                    <div className="mb-4">
                      <p className="text-xs text-purple-300 font-medium uppercase tracking-wide mb-2">Narration</p>
                      <p className="text-gray-300 leading-relaxed italic">&ldquo;{scene.narration}&rdquo;</p>
                    </div>
                  )}

                  {scene.dialogue && scene.dialogue.length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs text-green-300 font-medium uppercase tracking-wide mb-2">Dialogue</p>
                      <div className="space-y-2">
                        {scene.dialogue.map((line, j) => (
                          <p key={j} className="text-gray-300 text-sm pl-4 border-l-2 border-green-500/30">{line}</p>
                        ))}
                      </div>
                    </div>
                  )}

                  {scene.audio_cues && scene.audio_cues.length > 0 && (
                    <div>
                      <p className="text-xs text-blue-300 font-medium uppercase tracking-wide mb-2">Audio Cues</p>
                      <div className="flex flex-wrap gap-2">
                        {scene.audio_cues.map((cue, j) => (
                          <span key={j} className="px-2 py-0.5 text-xs bg-blue-500/10 text-blue-300 border border-blue-500/20 rounded-full">
                            {cue}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              ))
            )}
          </div>
        )}
      </div>
    </main>
  )
}
