'use client'

import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import type { User } from '@/types/database.types'

interface HeaderProps {
  user: User
}

export default function Header({ user }: HeaderProps) {
  const router = useRouter()
  const supabase = createClient()

  async function handleLogout() {
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-us-open-blue">
              {user.full_name}
            </h1>
            <p className="text-sm text-gray-600">{user.email}</p>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">
                  {user.credits} créditos
                </span>
                {user.is_vip && (
                  <span className="bg-gradient-to-r from-us-open-yellow to-yellow-500 text-us-open-blue px-2 py-1 rounded text-xs font-bold">
                    VIP
                  </span>
                )}
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="px-4 py-2 text-gray-700 hover:text-us-open-blue hover:bg-gray-100 rounded-lg transition-colors"
            >
              Salir
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
