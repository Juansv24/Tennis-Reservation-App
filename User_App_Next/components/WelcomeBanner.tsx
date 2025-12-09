'use client'

import { useState, useEffect } from 'react'
import type { User } from '@/types/database.types'

interface WelcomeBannerProps {
  user: User
}

export default function WelcomeBanner({ user }: WelcomeBannerProps) {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false)
    }, 5000) // Hide after 5 seconds

    return () => clearTimeout(timer)
  }, [])

  if (!isVisible) return null

  return (
    <div className="bg-green-100 border-l-4 border-green-500 text-green-900 p-4 rounded-lg shadow-sm animate-in fade-in duration-300">
      <p className="text-lg font-semibold">
        ¡Bienvenido de vuelta, {user.full_name}! 👋
      </p>
    </div>
  )
}
