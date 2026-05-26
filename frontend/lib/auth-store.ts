import { create } from 'zustand'
import type { UserInfo } from './api'

interface AuthState {
  user: UserInfo | null
  isLoading: boolean
  setUser: (user: UserInfo | null) => void
  login: (accessToken: string, refreshToken: string, user: UserInfo) => void
  logout: () => void
  hydrate: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,

  setUser: (user) => set({ user }),

  login: (accessToken, refreshToken, user) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
    }
    set({ user, isLoading: false })
  },

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
    set({ user: null, isLoading: false })
  },

  hydrate: () => {
    if (typeof window === 'undefined') {
      set({ isLoading: false })
      return
    }
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ isLoading: false })
      return
    }
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error()
        return r.json()
      })
      .then((user) => set({ user, isLoading: false }))
      .catch(() => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, isLoading: false })
      })
  },
}))
