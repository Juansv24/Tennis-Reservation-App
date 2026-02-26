// ABOUTME: Client root for the /profile page — manages tab state and profile refresh.
// ABOUTME: Currently renders only the Mi Perfil tab. Comunidad and Mensajes come in a later task.
'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { User } from '@/types/database.types'
import ProfileForm from './ProfileForm'

interface Props {
  profile: User
}

export default function ProfilePageClient({ profile: initialProfile }: Props) {
  const [profile, setProfile] = useState(initialProfile)

  async function handleProfileSaved() {
    const res = await fetch('/api/profile')
    if (res.ok) {
      const data = await res.json()
      setProfile(data.profile)
    }
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <Link
          href="/"
          className="text-sm text-us-open-light-blue hover:underline"
        >
          ← Volver al inicio
        </Link>
      </div>

      <h2 className="text-2xl font-bold text-us-open-blue mb-6">Mi Perfil</h2>

      <ProfileForm user={profile} onSaved={handleProfileSaved} />
    </div>
  )
}
