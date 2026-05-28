const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface FetchOptions extends RequestInit {
  auth?: boolean
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('access_token')
}

export async function apiFetch<T = unknown>(path: string, opts: FetchOptions = {}): Promise<T> {
  const { auth = false, headers: extra, ...rest } = opts
  const hdrs: Record<string, string> = { 'Content-Type': 'application/json', ...extra as Record<string, string> }

  if (auth) {
    const token = getToken()
    if (token) hdrs['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}/api/v1${path}`, { headers: hdrs, ...rest })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || body.error || `API error ${res.status}`)
  }

  return res.json()
}

export interface AuthResponse {
  user: UserInfo
  tokens: { access_token: string; refresh_token: string; token_type: string }
}

export interface UserInfo {
  id: string
  email: string
  username: string
  full_name: string
  is_active: boolean
  is_admin: boolean
  avatar_url: string | null
  created_at: string
}

export const authApi = {
  register(email: string, username: string, password: string, full_name: string) {
    return apiFetch<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, username, password, full_name }),
    })
  },
  login(email: string, password: string) {
    return apiFetch<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  },
  me() {
    return apiFetch<UserInfo>('/auth/me', { auth: true })
  },
}

export interface Project {
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

export interface Scene {
  scene_number: number
  description: string
  shot_type: string
  mood: string
  duration: number
  visual_prompt: string
  narration: string
  dialogue: { character: string; line: string }[]
  audio_cues: string[]
}

export const projectsApi = {
  list() {
    return apiFetch<Project[]>('/autonomous/projects')
  },
  get(id: string) {
    return apiFetch<ProjectDetail>(`/autonomous/projects/${id}`)
  },
  createFilm(prompt: string, style: string, duration: number, model: string) {
    return apiFetch<{ status: string; project_id: string; message: string }>('/autonomous/create-film', {
      method: 'POST',
      body: JSON.stringify({ prompt, style, duration, model }),
    })
  },
}

export type ProjectSummary = Project

export const api = {
  listProjects() {
    return projectsApi.list()
  },
  getProject(id: string) {
    return projectsApi.get(id)
  },
}

export const mediaApi = {
  generateImage(prompt: string, category = 'storyboard') {
    return apiFetch<{ status: string; path?: string; url?: string; backend: string }>('/media/generate-image', {
      method: 'POST',
      body: JSON.stringify({ prompt, category }),
    })
  },
  generateTTS(text: string, voice = 'neutral', pace = 'normal') {
    return apiFetch<{ status: string; path?: string; backend: string; size_bytes?: number }>('/media/generate-tts', {
      method: 'POST',
      body: JSON.stringify({ text, voice, pace }),
    })
  },
  status() {
    return apiFetch<Record<string, { configured: boolean; backend?: string }>>('/media/status')
  },
}

export const exportsApi = {
  jsonUrl(projectId: string) {
    return `${API_BASE}/api/v1/exports/json/${projectId}`
  },
  pdfUrl(projectId: string) {
    return `${API_BASE}/api/v1/exports/pdf/${projectId}`
  },
  imagesUrl(projectId: string) {
    return `${API_BASE}/api/v1/exports/images/${projectId}`
  },
}

export function mediaUrl(path: string): string {
  if (path.startsWith('http')) return path
  return `${API_BASE}/${path}`
}

export const promptsApi = {
  optimize(prompt: string, style: string, duration: number) {
    return apiFetch<{ optimized_prompt: string; was_optimized: boolean }>('/prompts/optimize', {
      method: 'POST',
      body: JSON.stringify({ prompt, style, duration }),
    })
  },
}
