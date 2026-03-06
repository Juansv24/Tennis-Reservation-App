// ABOUTME: Client root for the /profile page — manages tab state and profile refresh.
// ABOUTME: Renders Mi Perfil, Comunidad, or Mensajes tab. Fetches unread count for badge.
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import type { User, SuggestedPartner } from '@/types/database.types'
import ProfileForm from './ProfileForm'
import ComunidadTab from './ComunidadTab'
import MessagesTab from './MessagesTab'

interface Props {
  profile: User
  initialTab?: string
  suggestions: SuggestedPartner[]
}

export default function ProfilePageClient({ profile: initialProfile, initialTab, suggestions }: Props) {
  const [profile, setProfile] = useState(initialProfile)
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    fetch('/api/messages')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setUnreadCount(data.totalUnread) })
      .catch(() => {})
  }, [])

  async function handleProfileSaved() {
    const res = await fetch('/api/profile')
    if (res.ok) {
      const data = await res.json()
      setProfile(data.profile)
    }
  }

  const tab = initialTab ?? 'perfil'

  return (
    <div>
      {/* Tab navigation */}
      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {[
          { key: 'perfil', label: 'Mi Perfil', href: '/profile' },
          { key: 'comunidad', label: 'Comunidad', href: '/profile?tab=comunidad' },
          { key: 'mensajes', label: 'Mensajes', href: '/profile?tab=mensajes' },
        ].map(t => (
          <Link
            key={t.key}
            href={t.href}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
              tab === t.key
                ? 'border-us-open-blue text-us-open-blue'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
            {t.key === 'mensajes' && unreadCount > 0 && (
              <span className="bg-us-open-light-blue text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
                {unreadCount}
              </span>
            )}
          </Link>
        ))}
      </div>

      {tab === 'comunidad' && (
        <ComunidadTab suggestions={suggestions} currentUserId={profile.id} />
      )}

      {tab === 'mensajes' && (
        <MessagesTab currentUserId={profile.id} />
      )}

      {tab === 'perfil' && (
        <>
          <div className="bg-blue-50 border-2 border-us-open-light-blue rounded-lg p-5 shadow-sm mb-6">
            <h3 className="text-base font-semibold text-us-open-blue mb-2">¿Para qué sirve completar tu perfil?</h3>
            <ul className="space-y-1.5 text-sm text-gray-700">
              <li>• Aparecerás como <strong>compañero sugerido</strong> para jugadores de tu nivel en la pestaña Comunidad.</li>
              <li>• Podrás <strong>publicar y comentar</strong> en los posts de "Buscando partido" en la pestaña Comunidad para coordinar partidos con otros jugadores registrados.</li>
              <li>• El sistema encontrará jugadores con <strong>niveles y horarios compatibles</strong> con los tuyos basándose en tu historial de reservas.</li>
            </ul>
          </div>
          <ProfileForm user={profile} onSaved={handleProfileSaved} />
        </>
      )}
    </div>
  )
}
