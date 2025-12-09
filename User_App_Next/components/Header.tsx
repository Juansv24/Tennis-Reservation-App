'use client'

import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import type { User } from '@/types/database.types'

interface HeaderProps {
  user: User
  lockCode?: string
  hasReservations?: boolean
}

export default function Header({ user, lockCode, hasReservations }: HeaderProps) {
  const router = useRouter()
  const supabase = createClient()

  async function handleLogout() {
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  return (
    <header className="bg-gradient-to-r from-us-open-blue to-us-open-light-blue text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-start justify-between">
          {/* Left section: Name and Credits */}
          <div>
            <h1 className="text-3xl font-bold">
              {user.full_name} {user.is_vip && '⭐'}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xl">🪙</span>
              <p className="text-lg opacity-90">Créditos disponibles: {user.credits}</p>
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
    </header>
  )
}
