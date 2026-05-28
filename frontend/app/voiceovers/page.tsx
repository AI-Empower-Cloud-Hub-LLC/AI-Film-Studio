'use client'

import { useEffect, useState, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  MicrophoneIcon,
  MusicalNoteIcon,
  SpeakerWaveIcon,
  PlayIcon,
  PauseIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import AuthGuard from '../components/AuthGuard'
import ErrorBoundary from '../components/ErrorBoundary'
import { projectsApi, mediaApi, mediaUrl } from '../../lib/api'
import type { Project, Scene } from '../../lib/api'

function VoiceoversContent() {
  const [projects, setProjects] = useState<Project[]>([])
  const [narrations, setNarrations] = useState<Scene[]>([])
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [generatingScene, setGeneratingScene] = useState<number | null>(null)
  const [audioUrls, setAudioUrls] = useState<Record<number, string>>({})
  const [playingScene, setPlayingScene] = useState<number | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadNarrations = async (id: string) => {
    setSelectedProject(id)
    setAudioUrls({})
    setPlayingScene(null)
    try {
      const detail = await projectsApi.get(id)
      setNarrations(detail.scenes.filter((s) => s.narration))
    } catch {
      setNarrations([])
    }
  }

  const generateVoiceover = async (scene: Scene) => {
    if (!scene.narration) return
    setGeneratingScene(scene.scene_number)
    try {
      const result = await mediaApi.generateTTS(scene.narration)
      if (result.status === 'completed' && result.path) {
        setAudioUrls(prev => ({ ...prev, [scene.scene_number]: mediaUrl(result.path!) }))
      }
    } catch (err) {
      console.error('TTS failed:', err)
    } finally {
      setGeneratingScene(null)
    }
  }

  const generateAll = async () => {
    for (const scene of narrations) {
      await generateVoiceover(scene)
    }
  }

  const togglePlay = (sceneNumber: number, url: string) => {
    if (playingScene === sceneNumber) {
      audioRef.current?.pause()
      setPlayingScene(null)
      return
    }
    if (audioRef.current) {
      audioRef.current.pause()
    }
    const audio = new Audio(url)
    audio.onended = () => setPlayingScene(null)
    audio.play()
    audioRef.current = audio
    setPlayingScene(sceneNumber)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-0 lg:pl-64">
        <div className="px-8 py-8">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">Voiceovers</h1>
              <p className="text-gray-400">AI-generated narration and dialogue audio tracks</p>
            </div>
            {narrations.length > 0 && (
              <button
                onClick={generateAll}
                disabled={generatingScene !== null}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 rounded-lg text-sm font-medium text-gray-900 dark:text-white transition-colors"
              >
                <SparklesIcon className="h-4 w-4" />
                Generate All Voiceovers
              </button>
            )}
          </div>

          {/* Project selector */}
          <div className="flex gap-3 mb-6 flex-wrap">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => loadNarrations(p.id)}
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
              <MicrophoneIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <p className="text-gray-400">Select a project to view voiceover narrations</p>
            </div>
          ) : narrations.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-gray-400">No narrations found for this project.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {narrations.map((scene, i) => (
                <motion.div
                  key={scene.scene_number}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className="bg-white dark:bg-gray-800/40 border border-gray-200 dark:border-gray-700/50 shadow-sm dark:shadow-none rounded-xl p-5"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-green-500/10 rounded-xl flex-shrink-0">
                      <SpeakerWaveIcon className="h-6 w-6 text-green-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">Scene {scene.scene_number}</span>
                        <span className="px-2 py-0.5 bg-gray-700 text-gray-400 text-xs rounded-full">{scene.mood}</span>
                        <span className="text-xs text-gray-500">{scene.duration}s</span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{scene.narration}</p>

                      {/* Audio controls */}
                      <div className="flex items-center gap-3 mb-3">
                        {audioUrls[scene.scene_number] ? (
                          <button
                            onClick={() => togglePlay(scene.scene_number, audioUrls[scene.scene_number])}
                            className="flex items-center gap-2 px-3 py-1.5 bg-green-600/20 border border-green-500/30 rounded-lg text-green-400 text-xs font-medium hover:bg-green-600/30 transition-colors"
                          >
                            {playingScene === scene.scene_number ? (
                              <><PauseIcon className="h-4 w-4" /> Pause</>
                            ) : (
                              <><PlayIcon className="h-4 w-4" /> Play Voiceover</>
                            )}
                          </button>
                        ) : (
                          <button
                            onClick={() => generateVoiceover(scene)}
                            disabled={generatingScene !== null}
                            className="flex items-center gap-2 px-3 py-1.5 bg-purple-600/20 border border-purple-500/30 rounded-lg text-purple-400 text-xs font-medium hover:bg-purple-600/30 disabled:opacity-50 transition-colors"
                          >
                            {generatingScene === scene.scene_number ? (
                              <><div className="animate-spin h-3 w-3 border-2 border-purple-400 border-t-transparent rounded-full" /> Generating...</>
                            ) : (
                              <><SparklesIcon className="h-4 w-4" /> Generate Voiceover</>
                            )}
                          </button>
                        )}
                      </div>

                      {scene.audio_cues && scene.audio_cues.length > 0 && (
                        <div className="flex items-center gap-2 flex-wrap">
                          <MusicalNoteIcon className="h-3.5 w-3.5 text-gray-500 flex-shrink-0" />
                          {scene.audio_cues.map((cue, ci) => (
                            <span key={ci} className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded-full">
                              {cue}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
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

export default function VoiceoversPage() {
  return (
    <AuthGuard>
      <ErrorBoundary>
        <VoiceoversContent />
      </ErrorBoundary>
    </AuthGuard>
  )
}
