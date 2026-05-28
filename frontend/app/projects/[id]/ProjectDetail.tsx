'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  ArrowLeftIcon,
  ClockIcon,
  SparklesIcon,
  DocumentTextIcon,
  VideoCameraIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline'
import { exportsApi } from '../../../lib/api'

interface Scene {
  scene_number: number
  description: string
  shot_type: string
  mood: string
  duration: number
  visual_prompt: string
}

interface Script {
  scene_number: number
  narration: string
  dialogue: { character: string; line: string }[]
  audio_cues: string[]
}

interface ProjectData {
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
  script: Script[]
}

export default function ProjectDetail() {
  const params = useParams()
  const id = params?.id as string
  const [project, setProject] = useState<ProjectData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'scenes' | 'scripts'>('scenes')

  useEffect(() => {
    if (!id) return
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${apiUrl}/api/v1/autonomous/projects/${id}`)
      .then((r) => r.json())
      .then(setProject)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-purple-400 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">Project not found</p>
          <Link href="/projects" className="text-purple-400 hover:text-purple-300">Back to Projects</Link>
        </div>
      </div>
    )
  }

  const statusColor: Record<string, string> = {
    completed: 'bg-green-500/10 text-green-400 border-green-500/30',
    processing: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    pending: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    failed: 'bg-red-500/10 text-red-400 border-red-500/30',
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link href="/projects" className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors">
            <ArrowLeftIcon className="h-5 w-5" />
          </Link>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-white">{project.title}</h1>
            <div className="flex items-center gap-3 mt-1">
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${statusColor[project.status] || 'bg-gray-500/10 text-gray-400 border-gray-500/30'}`}>
                {project.status}
              </span>
              <span className="text-sm text-gray-500 flex items-center gap-1">
                <SparklesIcon className="h-3.5 w-3.5" /> {project.style}
              </span>
              <span className="text-sm text-gray-500 flex items-center gap-1">
                <ClockIcon className="h-3.5 w-3.5" /> {project.duration}s
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <a
              href={exportsApi.pdfUrl(project.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 bg-red-600/20 border border-red-500/30 rounded-lg text-red-400 text-xs font-medium hover:bg-red-600/30 transition-colors"
            >
              <ArrowDownTrayIcon className="h-4 w-4" /> PDF
            </a>
            <a
              href={exportsApi.jsonUrl(project.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 bg-blue-600/20 border border-blue-500/30 rounded-lg text-blue-400 text-xs font-medium hover:bg-blue-600/30 transition-colors"
            >
              <ArrowDownTrayIcon className="h-4 w-4" /> JSON
            </a>
            <a
              href={exportsApi.imagesUrl(project.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 bg-green-600/20 border border-green-500/30 rounded-lg text-green-400 text-xs font-medium hover:bg-green-600/30 transition-colors"
            >
              <ArrowDownTrayIcon className="h-4 w-4" /> Images ZIP
            </a>
          </div>
        </div>

        {/* Director Vision */}
        {project.director_vision && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-6 bg-purple-500/5 border border-purple-500/20 rounded-xl"
          >
            <h2 className="text-sm font-semibold text-purple-400 mb-2">Director&apos;s Vision</h2>
            <p className="text-gray-300 leading-relaxed">{project.director_vision}</p>
          </motion.div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-800/60 p-1 rounded-lg w-fit">
          <button
            onClick={() => setActiveTab('scenes')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'scenes' ? 'bg-purple-500/20 text-purple-400' : 'text-gray-400 hover:text-white'
            }`}
          >
            <VideoCameraIcon className="h-4 w-4" /> Scenes ({project.scenes.length})
          </button>
          <button
            onClick={() => setActiveTab('scripts')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'scripts' ? 'bg-purple-500/20 text-purple-400' : 'text-gray-400 hover:text-white'
            }`}
          >
            <DocumentTextIcon className="h-4 w-4" /> Scripts ({project.script.length})
          </button>
        </div>

        {/* Content */}
        {activeTab === 'scenes' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {project.scenes.map((scene, i) => (
              <motion.div
                key={scene.scene_number}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-5"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-white">Scene {scene.scene_number}</span>
                  <span className="px-2 py-0.5 bg-gray-700 text-gray-400 text-xs rounded-full">{scene.duration}s</span>
                </div>
                <p className="text-sm text-gray-300 mb-3">{scene.description}</p>
                <div className="flex gap-2">
                  <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded-full">{scene.shot_type}</span>
                  <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 text-xs rounded-full">{scene.mood}</span>
                </div>
                {scene.visual_prompt && (
                  <p className="mt-3 text-xs text-gray-500 italic border-l-2 border-gray-700 pl-3">{scene.visual_prompt}</p>
                )}
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {project.script.map((script, i) => (
              <motion.div
                key={script.scene_number}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-5"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs font-medium rounded-full">
                    Scene {script.scene_number}
                  </span>
                </div>
                {script.narration && (
                  <p className="text-sm text-gray-300 mb-3 italic border-l-2 border-purple-500/50 pl-3">
                    {script.narration}
                  </p>
                )}
                {script.dialogue && script.dialogue.length > 0 && (
                  <div className="space-y-2">
                    {script.dialogue.map((d, di) => (
                      <div key={di} className="pl-4">
                        <span className="text-xs font-semibold text-blue-400 uppercase">{d.character}</span>
                        <p className="text-sm text-gray-300">{d.line}</p>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
