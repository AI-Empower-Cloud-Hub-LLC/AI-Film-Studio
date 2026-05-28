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

export interface CastCharacter {
  character_name: string
  role_type: string
  description: string
  physical_description: string
  personality_traits: string[]
  suggested_actors: string[]
  estimated_salary_range: string
  image_prompt: string
}

export interface CastData {
  characters: CastCharacter[]
  total_characters: number
  casting_sheet: {
    total_characters: number
    leads: number
    supporting: number
    extras: number
    estimated_total_budget: string
  }
}

export interface LocationData {
  locations: {
    scene_number: number
    location_name: string
    type: string
    geographic_description: string
    visual_description: string
    image_prompt: string
    city_country: string
    permit_required: boolean
    estimated_cost: string
    logistics: string
    alternatives: string[]
    weather_considerations: string
  }[]
  total_locations: number
  logistics_summary: {
    total_locations: number
    interior_count: number
    exterior_count: number
    permits_needed: number
    estimated_total_cost: string
  }
}

export interface VFXData {
  vfx_shots: {
    scene_number: number
    vfx_needed: boolean
    techniques: string[]
    description: string
    complexity: string
    estimated_cost: string
    render_time_estimate: string
    software_recommended: string[]
    notes: string
  }[]
  total_vfx_shots: number
  vfx_summary: {
    total_scenes: number
    scenes_with_vfx: number
    complexity_breakdown: Record<string, number>
    estimated_total_cost: string
  }
}

export interface MoodBoardData {
  mood_images: {
    id: number
    title: string
    category: string
    description: string
    image_prompt: string
    color_hex_codes: string[]
    reference_notes: string
  }[]
  style_guide: {
    primary_colors: string[]
    accent_colors: string[]
    typography_style: string
    lighting_approach: string
    texture_keywords: string[]
    composition_rules: string[]
    reference_films: string[]
    overall_tone: string
  }
  total_images: number
}

export interface RefinedScreenplay {
  refined_scenes: {
    scene_number: number
    slug_line: string
    action_lines: string
    dialogue: { character: string; parenthetical?: string; line: string }[]
    camera_directions: string[]
    transitions: string
    production_notes: string[]
    polished_narration: string
  }[]
  total_scenes: number
  format: string
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
  refined_screenplay?: RefinedScreenplay
  cast?: CastData
  locations?: LocationData
  vfx_plan?: VFXData
  mood_board?: MoodBoardData
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
  update(id: string, data: { title?: string; style?: string; duration?: number }) {
    return apiFetch<{ id: string; title: string; style: string; duration: number; status: string }>(`/autonomous/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },
  delete(id: string) {
    return apiFetch<{ status: string; project_id: string }>(`/autonomous/projects/${id}`, {
      method: 'DELETE',
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
  screenplayUrl(projectId: string) {
    return `${API_BASE}/api/v1/exports/screenplay/${projectId}`
  },
  castUrl(projectId: string) {
    return `${API_BASE}/api/v1/exports/cast/${projectId}`
  },
  locationsUrl(projectId: string) {
    return `${API_BASE}/api/v1/exports/locations/${projectId}`
  },
  vfxUrl(projectId: string) {
    return `${API_BASE}/api/v1/exports/vfx/${projectId}`
  },
  moodBoardUrl(projectId: string) {
    return `${API_BASE}/api/v1/exports/mood-board/${projectId}`
  },
  zipUrl(projectId: string) {
    return `${API_BASE}/api/v1/exports/zip/${projectId}`
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

export interface AttachmentInfo {
  id: string
  filename: string
  size: number
  content_type: string
  category: string
  created_at: string
}

export const attachmentsApi = {
  list(projectId: string) {
    return apiFetch<AttachmentInfo[]>(`/attachments/${projectId}`)
  },
  async upload(projectId: string, file: File, category = 'general'): Promise<AttachmentInfo> {
    const form = new FormData()
    form.append('file', file)
    form.append('category', category)
    const res = await fetch(`${API_BASE}/api/v1/attachments/${projectId}`, {
      method: 'POST',
      body: form,
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `Upload failed ${res.status}`)
    }
    return res.json()
  },
  downloadUrl(projectId: string, attachmentId: string) {
    return `${API_BASE}/api/v1/attachments/${projectId}/${attachmentId}/download`
  },
  async remove(projectId: string, attachmentId: string) {
    return apiFetch<{ status: string; id: string }>(`/attachments/${projectId}/${attachmentId}`, {
      method: 'DELETE',
    })
  },
}
