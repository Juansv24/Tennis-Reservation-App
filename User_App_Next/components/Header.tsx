// ABOUTME: Site-wide header component — displays user name, credits, lock code, and Salir button.
// ABOUTME: Renders a tab bar (Reservas / Mi Perfil / Comunidad / Mensajes) for app navigation.
'use client'

import { createClient } from '@/lib/supabase/client'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import type { User } from '@/types/database.types'

const ALL_TABS = [
  { label: 'Reservas',  href: '/',                       key: 'reservas'  },
  { label: 'Mi Perfil', href: '/profile',                key: 'perfil'    },
  { label: 'Comunidad', href: '/profile?tab=comunidad',  key: 'comunidad' },
  { label: 'Mensajes',  href: '/profile?tab=mensajes',   key: 'mensajes'  },
]

interface HeaderProps {
  user: User
  lockCode?: string
  hasReservations?: boolean
}

export default function Header({ user, lockCode, hasReservations }: HeaderProps) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const supabase = createClient()
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    fetch('/api/messages')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setUnreadCount(data.totalUnread) })
      .catch(() => {})
  }, [])

  async function handleLogout() {
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  const onProfilePage = pathname.startsWith('/profile')
  const currentTab = searchParams.get('tab')

  function isActive(key: string) {
    if (key === 'reservas')  return pathname === '/'
    if (key === 'perfil')    return onProfilePage && currentTab === null
    if (key === 'comunidad') return onProfilePage && currentTab === 'comunidad'
    if (key === 'mensajes')  return onProfilePage && currentTab === 'mensajes'
    return false
  }

  return (
    <header className="bg-gradient-to-r from-us-open-blue to-us-open-light-blue text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-start justify-between">
          {/* Left section: Reservando como, Name and Credits */}
          <div>
            <p className="text-xs md:text-sm text-white opacity-75 mb-4 uppercase tracking-wide">
              Reservando como:
            </p>
            <h1 className="text-2xl md:text-3xl font-bold">
              {user.full_name}
              {user.is_vip && <span className="text-base md:text-lg ml-1">⭐</span>}
            </h1>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-lg md:text-xl">🪙</span>
              <p className="text-base md:text-lg opacity-90">Créditos disponibles: {user.credits}</p>
            </div>
          </div>

          {/* Right section: Salir button and Lock code */}
          <div className="flex flex-col items-end gap-2">
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg transition-colors font-semibold"
            >
              Salir
            </button>
            {hasReservations && lockCode && (
              <div className="flex items-center gap-2 text-white">
                <p className="text-base opacity-90">Código de candado:</p>
                <p className="text-2xl font-light tracking-widest">{lockCode}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex gap-1">
          {ALL_TABS.map(tab => (
            <Link
              key={tab.key}
              href={tab.href}
              className={`px-5 py-2 text-base font-semibold rounded-t-lg transition-colors ${
                isActive(tab.key)
                  ? 'bg-white text-us-open-blue'
                  : 'text-white opacity-80 hover:opacity-100 hover:bg-white hover:bg-opacity-10'
              }`}
            >
              <span className="flex items-center gap-1.5">
                {tab.label}
                {tab.key === 'perfil' && !user.profile_completed && (
                  <span className="w-3 h-3 bg-us-open-yellow rounded-full inline-block" aria-label="Perfil incompleto" />
                )}
                {tab.key === 'mensajes' && unreadCount > 0 && (
                  <span className="w-3 h-3 bg-us-open-yellow rounded-full inline-block" aria-label="Mensajes nuevos" />
                )}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </header>
  )
}
