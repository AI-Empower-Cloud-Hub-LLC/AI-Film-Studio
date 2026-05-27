const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const V1 = `${BASE}/api/v1/autonomous`

export interface FilmRequest {
  prompt: string
  style: string
  duration: number
  model: string
}

export interface WorkflowStep {
  agent: string
  status: string
  framework?: string
}

export interface Scene {
  scene_number: number
  description: string
  shot_type: string
  mood: string
  duration: number
  visual_prompt?: string
  narration?: string
  dialogue?: { character: string; line: string }[]
  audio_cues?: string[]
}

export interface ShotPlan {
  scene_number: number
  camera_movement: string
  lens: string
  lighting: string
  color_palette: string[]
  image_generation_prompt: string
  depth_of_field: string
}

export interface AudioPlan {
  scene_number: number
  music_genre: string
  music_tempo: string
  music_instruments: string[]
  sound_effects: string[]
  voiceover_tone: string
  voiceover_pace: string
  mixing_notes: string
  elevenlabs_voice_id: string
}

export interface TimelineEntry {
  scene_number: number
  start_time: number
  end_time: number
  duration: number
  transition_out: string
  effects?: Record<string, unknown>
}

export interface FilmResult {
  project_id: string
  framework?: string
  prompt: string
  style: string
  duration: number
  scene_count: number
  total_duration: number
  director: {
    vision: string
    scenes: Scene[]
    agent: string
  }
  script: {
    script_scenes: Scene[]
    total_scenes: number
    agent: string
  }
  cinematography: {
    shot_plans: ShotPlan[]
    agent: string
  }
  sound: {
    audio_plans: AudioPlan[]
    agent: string
  }
  final_timeline: {
    timeline: TimelineEntry[]
    total_duration: number
    scenes_count: number
  }
  media_assets: {
    video_clips: string[]
    audio_files: string[]
    scene_count: number
  }
  workflow_steps: WorkflowStep[]
}

export interface FilmResponse {
  status: string
  project_id: string
  message: string
  persisted: boolean
  data: FilmResult
}

export interface ProjectSummary {
  id: string
  title: string
  style: string
  duration: number
  status: string
  scene_count: number
  created_at: string
}

export interface ProjectDetail {
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

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${V1}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const detail = err.detail
    const message = Array.isArray(detail)
      ? detail.map((d: any) => d?.msg ?? JSON.stringify(d)).join('; ')
      : (typeof detail === 'string' ? detail : JSON.stringify(detail) ?? 'Request failed')
    throw new Error(message)
  }
  return res.json()
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${V1}${path}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const detail = err.detail
    const message = Array.isArray(detail)
      ? detail.map((d: any) => d?.msg ?? JSON.stringify(d)).join('; ')
      : (typeof detail === 'string' ? detail : JSON.stringify(detail) ?? 'Request failed')
    throw new Error(message)
  }
  return res.json()
}

export const api = {
  createFilm: (req: FilmRequest) => post<FilmResponse>('/create-film', req),
  createFilmCrew: (req: FilmRequest) => post<FilmResponse>('/create-film-crew', req),
  listProjects: (skip = 0, limit = 20) =>
    get<ProjectSummary[]>(`/projects?skip=${skip}&limit=${limit}`),
  getProject: (id: string) => get<ProjectDetail>(`/projects/${id}`),
}
