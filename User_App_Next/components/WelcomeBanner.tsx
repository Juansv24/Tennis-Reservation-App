'use client'

import type { User } from '@/types/database.types'

interface WelcomeBannerProps {
  user: User
}

export default function WelcomeBanner({ user }: WelcomeBannerProps) {
  return (
    <div className="bg-green-100 border-l-4 border-green-500 text-green-900 p-4 rounded-lg shadow-sm">
      <p className="text-lg font-semibold">
        ¡Bienvenido de vuelta, {user.full_name}! 👋
      </p>
    </div>
  )
}
