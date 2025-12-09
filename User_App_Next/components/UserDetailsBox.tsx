'use client'

import type { User } from '@/types/database.types'

interface UserDetailsBoxProps {
  user: User
}

export default function UserDetailsBox({ user }: UserDetailsBoxProps) {
  return (
    <div className="bg-white border-2 border-us-open-light-blue rounded-lg p-4 shadow-md">
      <div className="flex gap-4">
        {/* Left section: Name and Email */}
        <div className="flex-1 space-y-2">
          <div>
            <p className="text-sm text-gray-600">Nombre</p>
            <p className="text-lg font-semibold text-gray-900">
              {user.full_name} {user.is_vip && '⭐'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Email</p>
            <p className="text-base text-gray-900">{user.email}</p>
          </div>
        </div>

        {/* Vertical separator */}
        <div className="border-l border-gray-200"></div>

        {/* Right section: Credits */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">🪙</span>
          <div>
            <p className="text-lg font-semibold text-gray-900">Créditos disponibles</p>
            <p className="text-xl font-bold text-us-open-blue">{user.credits}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
