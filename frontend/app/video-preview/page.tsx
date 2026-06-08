'use client'

import { useEffect, useState } from 'react'
import { PlayIcon, PauseIcon, ForwardIcon, BackwardIcon, SpeakerWaveIcon, FilmIcon } from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import AuthGuard from '../components/AuthGuard'
import { projectsApi, type ProjectDetail, type Scene } from '../../lib/api'

function VideoPreviewContent() {
  const [projects, setProjects] = useState<{ id: string; title: string; status: string }[]>([])
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null)
  const [currentScene, setCurrentScene] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    projectsApi.list({ per_page: 50 }).then(res => {
      setProjects(res.items.filter(p => p.status === 'completed'))
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadProject = async (id: string) => {
    try {
      const detail = await projectsApi.get(id)
      setSelectedProject(detail)
      setCurrentScene(0)
      setIsPlaying(false)
    } catch { /* ignore */ }
  }

  useEffect(() => {
    if (!isPlaying || !selectedProject) return
    const timer = setInterval(() => {
      setCurrentScene(prev => {
        if (prev >= selectedProject.scenes.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 4000)
    return () => clearInterval(timer)
  }, [isPlaying, selectedProject])

  const scene: Scene | undefined = selectedProject?.scenes?.[currentScene]

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-0 lg:pl-64">
        <div className="px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">Video Preview</h1>
            <p className="text-gray-500 dark:text-gray-400">Preview your generated films scene by scene</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Project selector */}
            <div className="lg:col-span-1">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-3">Completed Films</h3>
              {loading ? (
                <p className="text-gray-400 text-sm">Loading...</p>
              ) : projects.length === 0 ? (
                <p className="text-gray-400 text-sm">No completed films</p>
              ) : (
                <div className="space-y-2">
                  {projects.map(p => (
                    <button key={p.id} onClick={() => loadProject(p.id)} className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${selectedProject?.id === p.id ? 'border-purple-500 bg-purple-500/10 text-purple-400' : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-purple-500/30'}`}>
                      <p className="font-medium text-sm truncate">{p.title}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Preview area */}
            <div className="lg:col-span-3">
              {!selectedProject ? (
                <div className="flex flex-col items-center justify-center py-32 bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl">
                  <FilmIcon className="h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400 text-lg">Select a film to preview</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Video viewport */}
                  <div className="relative aspect-video bg-black rounded-xl overflow-hidden border border-gray-700">
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-white p-8">
                      <div className="absolute top-4 left-4 bg-black/50 px-3 py-1 rounded-full text-xs">
                        Scene {currentScene + 1} / {selectedProject.scenes.length}
                      </div>
                      {scene && (
                        <>
                          <div className="text-center max-w-2xl">
                            <h3 className="text-2xl font-bold mb-3">{scene.description?.slice(0, 100)}</h3>
                            <p className="text-gray-300 text-sm mb-4">{scene.visual_prompt || scene.narration || ''}</p>
                            <div className="flex gap-3 justify-center text-xs text-gray-400">
                              <span className="bg-white/10 px-2 py-1 rounded">{scene.shot_type}</span>
                              <span className="bg-white/10 px-2 py-1 rounded">{scene.mood}</span>
                              <span className="bg-white/10 px-2 py-1 rounded">{scene.duration}s</span>
                            </div>
                          </div>
                          {scene.narration && (
                            <div className="absolute bottom-16 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6">
                              <p className="text-center text-sm italic text-gray-200">&ldquo;{scene.narration}&rdquo;</p>
                            </div>
                          )}
                        </>
                      )}
                    </div>

                    {/* Progress bar */}
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-800">
                      <div className="h-full bg-purple-500 transition-all" style={{ width: `${((currentScene + 1) / selectedProject.scenes.length) * 100}%` }} />
                    </div>
                  </div>

                  {/* Controls */}
                  <div className="flex items-center justify-center gap-4">
                    <button onClick={() => setCurrentScene(Math.max(0, currentScene - 1))} className="p-2 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600">
                      <BackwardIcon className="h-5 w-5" />
                    </button>
                    <button onClick={() => setIsPlaying(!isPlaying)} className="p-3 rounded-full bg-purple-600 hover:bg-purple-500 text-white">
                      {isPlaying ? <PauseIcon className="h-6 w-6" /> : <PlayIcon className="h-6 w-6" />}
                    </button>
                    <button onClick={() => setCurrentScene(Math.min(selectedProject.scenes.length - 1, currentScene + 1))} className="p-2 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600">
                      <ForwardIcon className="h-5 w-5" />
                    </button>
                  </div>

                  {/* Scene timeline */}
                  <div className="bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl p-4">
                    <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-3">Scene Timeline</h3>
                    <div className="flex gap-2 overflow-x-auto pb-2">
                      {selectedProject.scenes.map((s, i) => (
                        <button key={i} onClick={() => { setCurrentScene(i); setIsPlaying(false) }} className={`flex-shrink-0 px-4 py-2 rounded-lg text-xs font-medium transition-colors ${i === currentScene ? 'bg-purple-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-purple-500/10'}`}>
                          Scene {s.scene_number}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Scene details */}
                  {scene && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {scene.dialogue && scene.dialogue.length > 0 && (
                        <div className="bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl p-4">
                          <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Dialogue</h4>
                          {scene.dialogue.map((d, i) => (
                            <div key={i} className="mb-2">
                              <span className="font-medium text-purple-400">{d.character}:</span>
                              <span className="text-gray-700 dark:text-gray-300 ml-2 text-sm">{d.line}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {scene.audio_cues && scene.audio_cues.length > 0 && (
                        <div className="bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl p-4">
                          <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2 flex items-center gap-1">
                            <SpeakerWaveIcon className="h-4 w-4" /> Audio Cues
                          </h4>
                          <ul className="space-y-1">
                            {scene.audio_cues.map((cue, i) => (
                              <li key={i} className="text-sm text-gray-600 dark:text-gray-400">{cue}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function VideoPreviewPage() {
  return <AuthGuard><VideoPreviewContent /></AuthGuard>
}
