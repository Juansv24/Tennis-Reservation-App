'use client'

import type { User } from '@/types/database.types'

interface UserDetailsBoxProps {
  user: User
}

export default function UserDetailsBox({ user }: UserDetailsBoxProps) {
  return (
    <div className="bg-white border-2 border-us-open-light-blue rounded-lg p-4 shadow-md">
      <div className="space-y-2">
        <div>
          <p className="text-sm text-gray-600">Nombre</p>
          <p className="text-lg font-semibold text-gray-900">{user.full_name}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Email</p>
          <p className="text-base text-gray-900">{user.email}</p>
        </div>
        <div className="pt-2 border-t border-gray-200">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🟠</span>
            <div>
              <p className="text-sm text-gray-600">Créditos disponibles</p>
              <p className="text-xl font-bold text-orange-600">{user.credits}</p>
            </div>
          </div>
        </div>
        {user.is_vip && (
          <div className="bg-gradient-to-r from-us-open-yellow to-yellow-500 text-us-open-blue px-3 py-2 rounded-lg text-center font-bold">
            ⭐ MIEMBRO VIP
          </div>
        )}
      </div>
    </div>
  )
}
