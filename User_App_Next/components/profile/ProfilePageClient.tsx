// ABOUTME: Client root for the /profile page — manages tab state and profile refresh.
// ABOUTME: Renders Mi Perfil or Comunidad tab based on initialTab prop.
'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { User, SuggestedPartner } from '@/types/database.types'
import ProfileForm from './ProfileForm'
import ComunidadTab from './ComunidadTab'

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

  const isComunidad = initialTab === 'comunidad'

  return (
    <div>
      <div className="mb-6">
        <Link href="/" className="text-sm text-us-open-light-blue hover:underline">
          ← Volver al inicio
        </Link>
      </div>

      {isComunidad ? (
        <ComunidadTab suggestions={suggestions} currentUserId={profile.id} />
      ) : (
        <>
          <h2 className="text-2xl font-bold text-us-open-blue mb-6">Mi Perfil</h2>
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
