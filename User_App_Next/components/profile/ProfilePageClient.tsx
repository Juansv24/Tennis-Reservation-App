// ABOUTME: Client root for the /profile page — manages tab content and profile refresh.
// ABOUTME: Renders Mi Perfil, Comunidad, or Mensajes content based on initialTab prop.
'use client'

import { useState } from 'react'
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

  async function handleProfileSaved() {
    const res = await fetch('/api/profile')
    if (res.ok) {
      const data = await res.json()
      setProfile(data.profile)
    }
  }

  const tab = initialTab ?? 'perfil'

  if (tab === 'comunidad') {
    return <ComunidadTab suggestions={suggestions} currentUserId={profile.id} />
  }

  if (tab === 'mensajes') {
    return <MessagesTab currentUserId={profile.id} />
  }

  // Default: Mi Perfil
  return (
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
  )
}
