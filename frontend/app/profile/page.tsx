'use client'

import { useState } from 'react'
import { UserCircleIcon, KeyIcon, CheckIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import AuthGuard from '../components/AuthGuard'
import { useAuthStore } from '../../lib/auth-store'
import { authApi } from '../../lib/api'

function ProfileContent() {
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)

  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [username, setUsername] = useState(user?.username ?? '')
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? '')
  const [saving, setSaving] = useState(false)
  const [profileMsg, setProfileMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [pwSaving, setPwSaving] = useState(false)
  const [pwMsg, setPwMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setProfileMsg(null)
    try {
      const updated = await authApi.updateProfile({
        full_name: fullName,
        username,
        avatar_url: avatarUrl || undefined,
      })
      setUser(updated)
      setProfileMsg({ type: 'success', text: 'Profile updated.' })
    } catch (err: unknown) {
      setProfileMsg({ type: 'error', text: (err as Error).message })
    } finally {
      setSaving(false)
    }
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    if (newPw !== confirmPw) {
      setPwMsg({ type: 'error', text: 'Passwords do not match.' })
      return
    }
    setPwSaving(true)
    setPwMsg(null)
    try {
      await authApi.changePassword(currentPw, newPw)
      setPwMsg({ type: 'success', text: 'Password changed.' })
      setCurrentPw('')
      setNewPw('')
      setConfirmPw('')
    } catch (err: unknown) {
      setPwMsg({ type: 'error', text: (err as Error).message })
    } finally {
      setPwSaving(false)
    }
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-0 lg:pl-64">
        <div className="max-w-2xl mx-auto px-4 sm:px-8 py-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-8">Profile Settings</h1>

          {/* Profile Info */}
          <div className="bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl p-6 mb-6">
            <div className="flex items-center gap-3 mb-6">
              <UserCircleIcon className="h-6 w-6 text-purple-400" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Personal Information</h2>
            </div>

            <form onSubmit={handleProfileSave} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                <input
                  type="email"
                  value={user.email}
                  disabled
                  className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400 text-sm cursor-not-allowed"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Avatar URL</label>
                <input
                  type="url"
                  value={avatarUrl}
                  onChange={e => setAvatarUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none placeholder-gray-400"
                />
              </div>

              {profileMsg && (
                <div className={`flex items-center gap-2 text-sm ${profileMsg.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {profileMsg.type === 'success' ? <CheckIcon className="h-4 w-4" /> : <ExclamationCircleIcon className="h-4 w-4" />}
                  {profileMsg.text}
                </div>
              )}

              <button
                type="submit"
                disabled={saving}
                className="px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </form>
          </div>

          {/* Change Password */}
          <div className="bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-6">
              <KeyIcon className="h-6 w-6 text-purple-400" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Change Password</h2>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Current Password</label>
                <input
                  type="password"
                  value={currentPw}
                  onChange={e => setCurrentPw(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">New Password</label>
                <input
                  type="password"
                  value={newPw}
                  onChange={e => setNewPw(e.target.value)}
                  required
                  minLength={8}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPw}
                  onChange={e => setConfirmPw(e.target.value)}
                  required
                  minLength={8}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                />
              </div>

              {pwMsg && (
                <div className={`flex items-center gap-2 text-sm ${pwMsg.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {pwMsg.type === 'success' ? <CheckIcon className="h-4 w-4" /> : <ExclamationCircleIcon className="h-4 w-4" />}
                  {pwMsg.text}
                </div>
              )}

              <button
                type="submit"
                disabled={pwSaving}
                className="px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
              >
                {pwSaving ? 'Changing...' : 'Change Password'}
              </button>
            </form>
          </div>

          {/* Account Info */}
          <div className="mt-6 text-sm text-gray-500 dark:text-gray-400 space-y-1">
            <p>Member since: {new Date(user.created_at).toLocaleDateString()}</p>
            <p>Role: {user.is_admin ? 'Administrator' : 'User'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ProfilePage() {
  return (
    <AuthGuard>
      <ProfileContent />
    </AuthGuard>
  )
}
