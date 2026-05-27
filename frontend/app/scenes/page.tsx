'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  VideoCameraIcon,
  EyeIcon,
} from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import { projectsApi } from '../../lib/api'
import type { Project, Scene } from '../../lib/api'

const SHOT_COLORS: Record<string, string> = {
  wide: 'from-blue-500 to-cyan-500',
  medium: 'from-purple-500 to-pink-500',
  close: 'from-orange-500 to-red-500',
  'close-up': 'from-orange-500 to-red-500',
  'extreme-close-up': 'from-red-500 to-rose-500',
  aerial: 'from-green-500 to-teal-500',
}

export default function ScenesPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [scenes, setScenes] = useState<Scene[]>([])
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadScenes = async (id: string) => {
    setSelectedProject(id)
    try {
      const detail = await projectsApi.get(id)
      setScenes(detail.scenes)
    } catch {
      setScenes([])
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black">
      <Sidebar />
      <div className="pl-64">
        <div className="px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-1">Scenes</h1>
            <p className="text-gray-400">Visual breakdowns and shot compositions from your films</p>
          </div>

          {/* Project selector */}
          <div className="flex gap-3 mb-6 flex-wrap">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => loadScenes(p.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
                  selectedProject === p.id
                    ? 'bg-purple-500/10 border-purple-500/30 text-purple-400'
                    : 'bg-gray-800/40 border-gray-700/50 text-gray-400 hover:text-white hover:bg-gray-800/70'
                }`}
              >
                {p.title.slice(0, 40)}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-400">
              <div className="animate-spin h-6 w-6 border-2 border-purple-400 border-t-transparent rounded-full mr-3" />
              Loading…
            </div>
          ) : !selectedProject ? (
            <div className="text-center py-20">
              <VideoCameraIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <p className="text-gray-400">Select a project above to view its scenes</p>
            </div>
          ) : scenes.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-gray-400">No scenes found for this project.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {scenes.map((scene, i) => {
                const gradient = SHOT_COLORS[scene.shot_type] || 'from-gray-500 to-gray-600'
                return (
                  <motion.div
                    key={scene.scene_number}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.06 }}
                    className="bg-gray-800/40 border border-gray-700/50 rounded-xl overflow-hidden"
                  >
                    {/* Scene header */}
                    <div className={`h-2 bg-gradient-to-r ${gradient}`} />
                    <div className="p-5">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-semibold text-white">Scene {scene.scene_number}</span>
                        <span className="px-2 py-0.5 bg-gray-700 text-gray-400 text-xs rounded-full">
                          {scene.duration}s
                        </span>
                      </div>

                      <p className="text-sm text-gray-300 mb-3 line-clamp-3">{scene.description}</p>

                      <div className="flex flex-wrap gap-2 mb-3">
                        <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded-full">{scene.shot_type}</span>
                        <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 text-xs rounded-full">{scene.mood}</span>
                      </div>

                      {scene.visual_prompt && (
                        <div className="p-3 bg-gray-700/30 rounded-lg">
                          <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
                            <EyeIcon className="h-3 w-3" /> Visual Prompt
                          </div>
                          <p className="text-xs text-gray-400 line-clamp-3">{scene.visual_prompt}</p>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
