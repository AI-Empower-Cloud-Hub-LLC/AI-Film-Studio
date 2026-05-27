'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { FilmIcon, CheckCircleIcon, ClockIcon } from '@heroicons/react/24/outline'
import { api, FilmRequest, FilmResult } from '@/lib/api'

// ── Pipeline step definitions ────────────────────────────────────────────────
const PIPELINE_STEPS = [
  { agent: 'Director', label: 'Crafting vision & scene breakdown', delay: 0 },
  { agent: 'Screenwriter', label: 'Writing script & dialogue', delay: 8000 },
  { agent: 'Cinematographer', label: 'Planning shots & visual style', delay: 16000 },
  { agent: 'SoundDesigner', label: 'Designing audio landscape', delay: 24000 },
  { agent: 'Editor', label: 'Assembling timeline', delay: 32000 },
]

type Tab = 'overview' | 'script' | 'cinematography' | 'sound' | 'timeline'

// ── Sub-components ───────────────────────────────────────────────────────────

function PipelineProgress({ activeStep }: { activeStep: number }) {
  return (
    <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-6 mt-6">
      <h3 className="text-lg font-semibold text-purple-300 mb-4">Production Pipeline</h3>
      <div className="space-y-3">
        {PIPELINE_STEPS.map((step, i) => {
          const done = i < activeStep
          const active = i === activeStep
          return (
            <div key={step.agent} className="flex items-center gap-3">
              {done ? (
                <CheckCircleIcon className="h-5 w-5 text-green-400 shrink-0" />
              ) : active ? (
                <div className="h-5 w-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin shrink-0" />
              ) : (
                <ClockIcon className="h-5 w-5 text-gray-600 shrink-0" />
              )}
              <div>
                <span className={`font-medium ${done ? 'text-green-400' : active ? 'text-purple-300' : 'text-gray-500'}`}>
                  {step.agent}
                </span>
                <span className={`text-sm ml-2 ${done ? 'text-gray-400' : active ? 'text-gray-300' : 'text-gray-600'}`}>
                  — {step.label}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function SceneCard({ scene, shotPlan, audioPlan }: {
  scene: { scene_number: number; description: string; shot_type: string; mood: string; duration: number; visual_prompt?: string }
  shotPlan?: { camera_movement: string; lens: string; lighting: string; color_palette: string[] }
  audioPlan?: { music_genre: string; voiceover_tone: string }
}) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 hover:border-purple-500/50 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs font-bold text-purple-400 bg-purple-400/10 px-2 py-1 rounded">
          SCENE {scene.scene_number}
        </span>
        <span className="text-xs text-gray-500">{scene.duration}s</span>
      </div>
      <p className="text-gray-200 text-sm mb-3">{scene.description}</p>
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="bg-gray-700 text-gray-300 px-2 py-1 rounded">{scene.shot_type}</span>
        <span className="bg-gray-700 text-gray-300 px-2 py-1 rounded">{scene.mood}</span>
        {shotPlan && <span className="bg-blue-900/50 text-blue-300 px-2 py-1 rounded">{shotPlan.lighting}</span>}
        {audioPlan && <span className="bg-green-900/50 text-green-300 px-2 py-1 rounded">{audioPlan.music_genre}</span>}
      </div>
      {scene.visual_prompt && (
        <p className="mt-3 text-xs text-gray-500 italic line-clamp-2">{scene.visual_prompt}</p>
      )}
    </div>
  )
}

function ResultsTabs({ data }: { data: FilmResult }) {
  const [tab, setTab] = useState<Tab>('overview')
  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'script', label: 'Script' },
    { id: 'cinematography', label: 'Cinematography' },
    { id: 'sound', label: 'Sound' },
    { id: 'timeline', label: 'Timeline' },
  ]

  const scenes = data.director?.scenes ?? []
  const shotPlans = data.cinematography?.shot_plans ?? []
  const audioPlan = data.sound?.audio_plans ?? []
  const scriptScenes = data.script?.script_scenes ?? []
  const timeline = data.final_timeline?.timeline ?? []

  return (
    <div className="mt-8">
      {/* Tab bar */}
      <div className="flex gap-1 p-1 bg-gray-800 rounded-xl border border-gray-700 mb-6 overflow-x-auto">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 min-w-max px-4 py-2 text-sm font-medium rounded-lg transition-all ${
              tab === t.id
                ? 'bg-purple-600 text-white shadow'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
        >
          {/* Overview */}
          {tab === 'overview' && (() => {
            const shotByNum = new Map(
              shotPlans.filter((p: any) => p?.scene_number != null).map((p: any) => [p.scene_number, p])
            )
            const audioByNum = new Map(
              audioPlan.filter((p: any) => p?.scene_number != null).map((p: any) => [p.scene_number, p])
            )
            return (
              <div className="space-y-6">
                {data.director?.vision && (
                  <div className="bg-gray-800 border border-purple-500/30 rounded-xl p-6">
                    <h4 className="text-sm font-semibold text-purple-400 uppercase tracking-wider mb-3">Director's Vision</h4>
                    <p className="text-gray-200 leading-relaxed">{data.director.vision}</p>
                  </div>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {scenes.map((scene) => (
                    <SceneCard
                      key={scene.scene_number}
                      scene={scene}
                      shotPlan={shotByNum.get(scene.scene_number)}
                      audioPlan={audioByNum.get(scene.scene_number)}
                    />
                  ))}
                </div>
              </div>
            )
          })()}

          {/* Script */}
          {tab === 'script' && (
            <div className="space-y-4">
              {scriptScenes.length === 0 && (
                <p className="text-gray-500 text-center py-8">No script data available.</p>
              )}
              {scriptScenes.map((s: any) => (
                <div key={s.scene_number} className="bg-gray-800 border border-gray-700 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-xs font-bold text-purple-400 bg-purple-400/10 px-2 py-1 rounded">SCENE {s.scene_number}</span>
                    <span className="text-sm text-gray-400">{s.mood} · {s.duration}s</span>
                  </div>
                  {s.narration && (
                    <div className="mb-4">
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Narration</p>
                      <p className="text-gray-200 italic">{s.narration}</p>
                    </div>
                  )}
                  {s.dialogue?.length > 0 && (
                    <div className="mb-4 space-y-2">
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Dialogue</p>
                      {s.dialogue.map((d: any, i: number) => (
                        <div key={i} className="flex gap-3">
                          <span className="text-purple-400 font-semibold text-sm w-28 shrink-0">{d.character}</span>
                          <span className="text-gray-300 text-sm">{d.line}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {s.audio_cues?.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {s.audio_cues.map((cue: string, i: number) => (
                        <span key={i} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">{cue}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Cinematography */}
          {tab === 'cinematography' && (
            <div className="space-y-4">
              {shotPlans.length === 0 && (
                <p className="text-gray-500 text-center py-8">No cinematography data available.</p>
              )}
              {shotPlans.map((sp: any) => (
                <div key={sp.scene_number} className="bg-gray-800 border border-gray-700 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-xs font-bold text-blue-400 bg-blue-400/10 px-2 py-1 rounded">SCENE {sp.scene_number}</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    {[
                      { label: 'Camera', value: sp.camera_movement },
                      { label: 'Lens', value: sp.lens },
                      { label: 'Lighting', value: sp.lighting },
                      { label: 'Depth of Field', value: sp.depth_of_field },
                    ].map(item => (
                      <div key={item.label}>
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{item.label}</p>
                        <p className="text-gray-200 font-medium capitalize">{item.value}</p>
                      </div>
                    ))}
                  </div>
                  {sp.color_palette?.length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Color Palette</p>
                      <div className="flex flex-wrap gap-2">
                        {sp.color_palette.map((c: string, i: number) => (
                          <span key={i} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {sp.image_generation_prompt && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Image Generation Prompt</p>
                      <p className="text-gray-400 text-sm italic bg-gray-900 rounded-lg p-3">{sp.image_generation_prompt}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Sound */}
          {tab === 'sound' && (
            <div className="space-y-4">
              {audioPlan.length === 0 && (
                <p className="text-gray-500 text-center py-8">No sound design data available.</p>
              )}
              {audioPlan.map((ap: any) => (
                <div key={ap.scene_number} className="bg-gray-800 border border-gray-700 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-xs font-bold text-green-400 bg-green-400/10 px-2 py-1 rounded">SCENE {ap.scene_number}</span>
                    <span className="text-sm text-gray-400">{ap.music_genre} · {ap.music_tempo}</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                    {[
                      { label: 'Voiceover Tone', value: ap.voiceover_tone },
                      { label: 'Voiceover Pace', value: ap.voiceover_pace },
                      { label: 'Voice ID', value: ap.elevenlabs_voice_id },
                    ].map(item => (
                      <div key={item.label}>
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{item.label}</p>
                        <p className="text-gray-200 font-medium capitalize">{item.value}</p>
                      </div>
                    ))}
                  </div>
                  {ap.music_instruments?.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Instruments</p>
                      <div className="flex flex-wrap gap-2">
                        {ap.music_instruments.map((inst: string, i: number) => (
                          <span key={i} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">{inst}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {ap.sound_effects?.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Sound Effects</p>
                      <div className="flex flex-wrap gap-2">
                        {ap.sound_effects.map((sfx: string, i: number) => (
                          <span key={i} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">{sfx}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {ap.mixing_notes && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Mixing Notes</p>
                      <p className="text-gray-400 text-sm">{ap.mixing_notes}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Timeline */}
          {tab === 'timeline' && (
            <div className="space-y-3">
              {timeline.length === 0 && (
                <p className="text-gray-500 text-center py-8">No timeline data available.</p>
              )}
              {timeline.map((entry: any) => (
                <div key={entry.scene_number} className="bg-gray-800 border border-gray-700 rounded-xl p-5 flex items-center gap-6">
                  <div className="text-center shrink-0 w-16">
                    <p className="text-xs text-gray-500">SCENE</p>
                    <p className="text-2xl font-bold text-gray-200">{entry.scene_number}</p>
                  </div>
                  <div className="h-10 w-px bg-gray-700 shrink-0" />
                  <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-xs text-gray-500">Start</p>
                      <p className="text-gray-200">{Number(entry.start_time ?? 0).toFixed(1)}s</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">End</p>
                      <p className="text-gray-200">{Number(entry.end_time ?? 0).toFixed(1)}s</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Duration</p>
                      <p className="text-gray-200">{entry.duration}s</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Transition</p>
                      <p className="text-gray-200 capitalize">{entry.transition_out ?? '—'}</p>
                    </div>
                  </div>
                </div>
              ))}
              {data.final_timeline?.total_duration != null && (
                <div className="flex justify-end pt-2">
                  <span className="text-sm text-gray-400">
                    Total: <strong className="text-white">{data.final_timeline.total_duration}s</strong>
                  </span>
                </div>
              )}
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function CreateFilm() {
  const [formData, setFormData] = useState<FilmRequest>({
    prompt: '',
    style: 'cinematic',
    duration: 30,
    model: 'claude-opus-4-6',
  })
  const [useCrew, setUseCrew] = useState(false)
  const [loading, setLoading] = useState(false)
  const [activeStep, setActiveStep] = useState(-1)
  const [result, setResult] = useState<FilmResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  const clearTimers = () => {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    setError(null)
    setActiveStep(0)
    clearTimers()

    // Advance pipeline step indicator on a timer
    PIPELINE_STEPS.forEach((step, i) => {
      if (i === 0) return
      const t = setTimeout(() => setActiveStep(i), step.delay)
      timersRef.current.push(t)
    })

    try {
      const resp = useCrew
        ? await api.createFilmCrew(formData)
        : await api.createFilm(formData)
      clearTimers()
      setActiveStep(PIPELINE_STEPS.length) // all done
      setResult(resp.data)
    } catch (err: any) {
      clearTimers()
      setError(err.message ?? 'Film creation failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => () => clearTimers(), [])

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-900/80 border-b border-gray-800 sticky top-0 z-10 backdrop-blur">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FilmIcon className="h-6 w-6 text-purple-400" />
            <h1 className="text-xl font-bold">AI Film Studio</h1>
          </div>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/" className="text-gray-400 hover:text-white transition-colors">Home</Link>
            <Link href="/projects" className="text-gray-400 hover:text-white transition-colors">Projects</Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-6 py-10 max-w-4xl">
        {/* Page title */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">Create Your Film</h2>
          <p className="text-gray-400">Five AI agents collaborate to turn your idea into a complete film plan.</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-gray-800 border border-gray-700 rounded-2xl p-8 space-y-6">
          {/* Prompt */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Film Concept <span className="text-red-400">*</span>
            </label>
            <textarea
              value={formData.prompt}
              onChange={e => setFormData({ ...formData, prompt: e.target.value })}
              placeholder="e.g. A lone astronaut discovers signs of life on Europa and must decide whether to tell humanity…"
              rows={4}
              required
              disabled={loading}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-600 rounded-xl text-gray-100 placeholder-gray-500 focus:border-purple-500 focus:outline-none resize-none transition-colors"
            />
          </div>

          {/* Style + Duration */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Visual Style</label>
              <select
                value={formData.style}
                onChange={e => setFormData({ ...formData, style: e.target.value })}
                disabled={loading}
                className="w-full px-4 py-3 bg-gray-900 border border-gray-600 rounded-xl text-gray-100 focus:border-purple-500 focus:outline-none transition-colors"
              >
                {['cinematic', 'documentary', 'anime', 'cartoon', 'realistic', 'sci-fi', 'noir', 'horror'].map(s => (
                  <option key={s} value={s} className="capitalize">{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Duration — {formData.duration}s
              </label>
              <input
                type="range"
                min={10} max={300} step={10}
                value={formData.duration}
                onChange={e => setFormData({ ...formData, duration: parseInt(e.target.value) })}
                disabled={loading}
                className="w-full accent-purple-500 mt-3"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>10s</span><span>300s</span>
              </div>
            </div>
          </div>

          {/* Model + Pipeline */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">AI Model</label>
              <select
                value={formData.model}
                onChange={e => setFormData({ ...formData, model: e.target.value })}
                disabled={loading}
                className="w-full px-4 py-3 bg-gray-900 border border-gray-600 rounded-xl text-gray-100 focus:border-purple-500 focus:outline-none transition-colors"
              >
                <option value="claude-opus-4-6">Claude Opus 4.6 — Most powerful</option>
                <option value="claude-sonnet-4-6">Claude Sonnet 4.6 — Balanced</option>
                <option value="claude-haiku-4-5">Claude Haiku 4.5 — Fastest</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Pipeline</label>
              <div className="flex rounded-xl overflow-hidden border border-gray-600">
                <button type="button" onClick={() => setUseCrew(false)} disabled={loading}
                  className={`flex-1 py-3 text-sm font-medium transition-colors ${!useCrew ? 'bg-purple-600 text-white' : 'bg-gray-900 text-gray-400 hover:text-gray-200'}`}>
                  Custom Agents
                </button>
                <button type="button" onClick={() => setUseCrew(true)} disabled={loading}
                  className={`flex-1 py-3 text-sm font-medium transition-colors ${useCrew ? 'bg-purple-600 text-white' : 'bg-gray-900 text-gray-400 hover:text-gray-200'}`}>
                  CrewAI
                </button>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !formData.prompt.trim()}
            className="w-full py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:from-gray-700 disabled:to-gray-700 text-white font-semibold rounded-xl text-lg transition-all hover:shadow-lg hover:shadow-purple-500/30"
          >
            {loading ? 'Producing…' : 'Create Film'}
          </button>
        </form>

        {/* Progress */}
        <AnimatePresence>
          {loading && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <PipelineProgress activeStep={activeStep} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error */}
        {error && (
          <div className="mt-6 bg-red-900/30 border border-red-500/50 rounded-xl p-4 text-red-300">
            {error}
          </div>
        )}

        {/* Results */}
        <AnimatePresence>
          {result && !loading && (
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
              {/* Success banner */}
              <div className="mt-8 bg-green-900/30 border border-green-500/40 rounded-xl p-4 flex items-center justify-between">
                <div>
                  <p className="text-green-400 font-semibold">Film pipeline complete</p>
                  <p className="text-gray-400 text-sm mt-0.5">
                    {result.scene_count} scenes · {result.total_duration}s total
                    {result.framework === 'crewai' && <span className="ml-2 text-purple-400">(CrewAI)</span>}
                  </p>
                </div>
                <Link href="/projects" className="text-sm text-purple-400 hover:text-purple-300 transition-colors">
                  View all projects →
                </Link>
              </div>
              <ResultsTabs data={result} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}
