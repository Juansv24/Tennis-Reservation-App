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
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-4xl">🎾</span>
            <div>
              <h1 className="text-3xl font-bold">Reservas de Cancha de Tenis</h1>
              <p className="text-lg opacity-90">{process.env.NEXT_PUBLIC_COURT_NAME}</p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg transition-colors font-semibold"
            >
              Salir
            </button>
            {hasReservations && lockCode && (
              <div className="text-white text-right">
                <p className="text-xs opacity-75 tracking-wide">Código de Candado</p>
                <p className="text-2xl font-light tracking-widest">{lockCode}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
