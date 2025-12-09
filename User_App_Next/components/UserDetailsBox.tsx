'use client'

import type { User } from '@/types/database.types'

interface UserDetailsBoxProps {
  user: User
}

export default function UserDetailsBox({ user }: UserDetailsBoxProps) {
  return (
    <div className="bg-white border-2 border-us-open-light-blue rounded-lg p-4 shadow-md">
      <div>
        <p className="text-sm text-gray-600">Email</p>
        <p className="text-base text-gray-900">{user.email}</p>
      </div>
    </div>
  )
}
