'use client'

import { useEffect, useState } from 'react'
import { UserGroupIcon, PlusIcon, EnvelopeIcon, TrashIcon } from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import AuthGuard from '../components/AuthGuard'
import { teamsApi, type TeamInfo } from '../../lib/api'

function TeamsContent() {
  const [teams, setTeams] = useState<TeamInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    teamsApi.list().then(setTeams).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleCreate = async () => {
    if (!name.trim()) return
    setCreating(true)
    try {
      const res = await teamsApi.create(name.trim(), desc.trim() || undefined)
      setTeams([...teams, { id: res.id, name: name.trim(), description: desc.trim() || null, owner_id: '', member_count: 1, created_at: new Date().toISOString() }])
      setName('')
      setDesc('')
      setShowCreate(false)
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to create team')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this team?')) return
    try {
      await teamsApi.delete(id)
      setTeams(teams.filter(t => t.id !== id))
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to delete team')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-0 lg:pl-64">
        <div className="px-8 py-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">Teams</h1>
              <p className="text-gray-500 dark:text-gray-400">Collaborate on film projects with your team</p>
            </div>
            <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-semibold rounded-lg transition-all">
              <PlusIcon className="h-5 w-5" />
              New Team
            </button>
          </div>

          {showCreate && (
            <div className="bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Create Team</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Team Name</label>
                  <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g., Production Team" className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900/60 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                  <input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Optional description" className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900/60 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white" />
                </div>
                <div className="flex gap-3">
                  <button onClick={handleCreate} disabled={creating} className="px-5 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium disabled:opacity-50">
                    {creating ? 'Creating...' : 'Create Team'}
                  </button>
                  <button onClick={() => setShowCreate(false)} className="px-5 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg">Cancel</button>
                </div>
              </div>
            </div>
          )}

          {loading ? (
            <div className="text-center py-20 text-gray-400">Loading teams...</div>
          ) : teams.length === 0 ? (
            <div className="text-center py-20">
              <UserGroupIcon className="h-16 w-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400 text-lg">No teams yet</p>
              <p className="text-gray-400 dark:text-gray-500 text-sm mt-1">Create a team to collaborate on projects</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {teams.map(team => (
                <div key={team.id} className="bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl p-6 hover:border-purple-500/30 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg">
                      <UserGroupIcon className="h-5 w-5 text-white" />
                    </div>
                    <button onClick={() => handleDelete(team.id)} className="p-1 text-gray-400 hover:text-red-500 transition-colors">
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">{team.name}</h3>
                  {team.description && <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">{team.description}</p>}
                  <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span>{team.member_count} member{team.member_count !== 1 ? 's' : ''}</span>
                    <span>{new Date(team.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function TeamsPage() {
  return <AuthGuard><TeamsContent /></AuthGuard>
}
