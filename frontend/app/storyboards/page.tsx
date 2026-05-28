'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  PhotoIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import AuthGuard from '../components/AuthGuard'
import ErrorBoundary from '../components/ErrorBoundary'
import { projectsApi, mediaApi, mediaUrl } from '../../lib/api'
import type { Project, Scene } from '../../lib/api'

function StoryboardsContent() {
  const [projects, setProjects] = useState<Project[]>([])
  const [frames, setFrames] = useState<Scene[]>([])
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [generatingFrame, setGeneratingFrame] = useState<number | null>(null)
  const [frameImages, setFrameImages] = useState<Record<number, string>>({})

  useEffect(() => {
    projectsApi.list({ per_page: 100 }).then(r => setProjects(r.items)).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadFrames = async (id: string) => {
    setSelectedProject(id)
    setFrameImages({})
    try {
      const detail = await projectsApi.get(id)
      setFrames(detail.scenes)
    } catch {
      setFrames([])
    }
  }

  const generateImage = async (scene: Scene) => {
    const prompt = scene.visual_prompt || scene.description
    if (!prompt) return
    setGeneratingFrame(scene.scene_number)
    try {
      const result = await mediaApi.generateImage(prompt, 'storyboard')
      const url = result.url || (result.path ? mediaUrl(result.path) : null)
      if (url) {
        setFrameImages(prev => ({ ...prev, [scene.scene_number]: url }))
      }
    } catch (err) {
      console.error('Image gen failed:', err)
    } finally {
      setGeneratingFrame(null)
    }
  }

  const generateAll = async () => {
    for (const frame of frames) {
      await generateImage(frame)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-0 lg:pl-64">
        <div className="px-8 py-8">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">Storyboards</h1>
              <p className="text-gray-400">Visual planning frames derived from scene breakdowns</p>
            </div>
            {frames.length > 0 && (
              <button
                onClick={generateAll}
                disabled={generatingFrame !== null}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg text-sm font-medium text-gray-900 dark:text-white transition-colors"
              >
                <SparklesIcon className="h-4 w-4" />
                Generate All Images
              </button>
            )}
          </div>

          {/* Project selector */}
          <div className="flex gap-3 mb-6 flex-wrap">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => loadFrames(p.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
                  selectedProject === p.id
                    ? 'bg-purple-500/10 border-purple-500/30 text-purple-400'
                    : 'bg-gray-100 dark:bg-gray-800/40 border-gray-200 dark:border-gray-700/50 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-800/70'
                }`}
              >
                {p.title.slice(0, 40)}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-400">
              <div className="animate-spin h-6 w-6 border-2 border-purple-400 border-t-transparent rounded-full mr-3" />
              Loading...
            </div>
          ) : !selectedProject ? (
            <div className="text-center py-20">
              <PhotoIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <p className="text-gray-400">Select a project to view storyboard frames</p>
            </div>
          ) : frames.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-gray-400">No storyboard frames for this project yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {frames.map((frame, i) => (
                <motion.div
                  key={frame.scene_number}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.06 }}
                  className="bg-white dark:bg-gray-800/40 border border-gray-200 dark:border-gray-700/50 shadow-sm dark:shadow-none rounded-xl overflow-hidden"
                >
                  {/* Frame visual */}
                  <div className="aspect-video bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center relative overflow-hidden">
                    {frameImages[frame.scene_number] ? (
                      <img
                        src={frameImages[frame.scene_number]}
                        alt={`Frame ${frame.scene_number}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <button
                        onClick={() => generateImage(frame)}
                        disabled={generatingFrame !== null}
                        className="flex flex-col items-center gap-2 text-gray-500 hover:text-purple-400 transition-colors"
                      >
                        {generatingFrame === frame.scene_number ? (
                          <div className="animate-spin h-8 w-8 border-2 border-purple-400 border-t-transparent rounded-full" />
                        ) : (
                          <>
                            <SparklesIcon className="h-8 w-8" />
                            <span className="text-xs">Generate Image</span>
                          </>
                        )}
                      </button>
                    )}
                    <div className="absolute top-3 left-3 px-2 py-0.5 bg-black/60 text-white text-xs font-medium rounded">
                      Frame {frame.scene_number}
                    </div>
                    <div className="absolute bottom-3 right-3 px-2 py-0.5 bg-black/60 text-gray-600 dark:text-gray-300 text-xs rounded">
                      {frame.shot_type}
                    </div>
                  </div>

                  <div className="p-4">
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-2 line-clamp-2">{frame.description}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded-full">{frame.mood}</span>
                      <span>{frame.duration}s</span>
                    </div>
                    {frame.visual_prompt && (
                      <p className="mt-2 text-xs text-gray-500 line-clamp-2 italic">
                        Prompt: {frame.visual_prompt}
                      </p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function StoryboardsPage() {
  return (
    <AuthGuard>
      <ErrorBoundary>
        <StoryboardsContent />
      </ErrorBoundary>
    </AuthGuard>
  )
}
