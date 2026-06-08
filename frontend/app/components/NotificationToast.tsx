'use client'

import { useState, useEffect, useCallback } from 'react'
import { CheckCircleIcon, XCircleIcon, InformationCircleIcon, XMarkIcon } from '@heroicons/react/24/outline'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'info'
  title: string
  message?: string
  timestamp: number
}

const STORAGE_KEY = 'aifs_notifications'

function loadNotifications(): Notification[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

function saveNotifications(items: Notification[]) {
  if (typeof window === 'undefined') return
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, 50)))
}

let listeners: ((n: Notification[]) => void)[] = []

export function addNotification(type: Notification['type'], title: string, message?: string) {
  const n: Notification = { id: Date.now().toString(), type, title, message, timestamp: Date.now() }
  const all = [n, ...loadNotifications()]
  saveNotifications(all)
  listeners.forEach(fn => fn(all))
}

export function useNotifications() {
  const [items, setItems] = useState<Notification[]>([])

  useEffect(() => {
    setItems(loadNotifications())
    listeners.push(setItems)
    return () => { listeners = listeners.filter(l => l !== setItems) }
  }, [])

  const dismiss = useCallback((id: string) => {
    const updated = items.filter(n => n.id !== id)
    saveNotifications(updated)
    setItems(updated)
  }, [items])

  const clearAll = useCallback(() => {
    saveNotifications([])
    setItems([])
  }, [])

  return { items, dismiss, clearAll }
}

export function NotificationToast({ notification, onDismiss }: { notification: Notification; onDismiss: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 6000)
    return () => clearTimeout(t)
  }, [onDismiss])

  const icons = {
    success: <CheckCircleIcon className="h-5 w-5 text-green-400" />,
    error: <XCircleIcon className="h-5 w-5 text-red-400" />,
    info: <InformationCircleIcon className="h-5 w-5 text-blue-400" />,
  }

  const borders = {
    success: 'border-green-500/30',
    error: 'border-red-500/30',
    info: 'border-blue-500/30',
  }

  return (
    <div className={`flex items-start gap-3 bg-white dark:bg-gray-800 border ${borders[notification.type]} rounded-xl p-4 shadow-lg max-w-sm animate-slide-in`}>
      {icons[notification.type]}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white">{notification.title}</p>
        {notification.message && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{notification.message}</p>}
      </div>
      <button onClick={onDismiss} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
        <XMarkIcon className="h-4 w-4" />
      </button>
    </div>
  )
}

export default function NotificationContainer() {
  const [visible, setVisible] = useState<Notification[]>([])

  useEffect(() => {
    const handler = (all: Notification[]) => {
      if (all.length > 0 && all[0]) {
        setVisible(prev => [all[0], ...prev].slice(0, 3))
      }
    }
    listeners.push(handler as (n: Notification[]) => void)
    return () => { listeners = listeners.filter(l => l !== handler) }
  }, [])

  const dismiss = (id: string) => setVisible(v => v.filter(n => n.id !== id))

  if (visible.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {visible.map(n => (
        <NotificationToast key={n.id} notification={n} onDismiss={() => dismiss(n.id)} />
      ))}
    </div>
  )
}
