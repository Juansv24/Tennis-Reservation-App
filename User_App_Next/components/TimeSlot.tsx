'use client'

import { formatHour } from '@/lib/constants'
import type { SlotStatus } from '@/types/database.types'

interface TimeSlotProps {
  hour: number
  status: SlotStatus
  onClick?: () => void
  ownerName?: string
}

export default function TimeSlot({ hour, status, onClick, ownerName }: TimeSlotProps) {
  const isClickable = status === 'available' || status === 'selected'

  const statusStyles = {
    available: 'bg-white border-2 border-us-open-light-blue text-us-open-blue hover:bg-blue-50 cursor-pointer',
    selected: 'bg-blue-100 border-4 border-us-open-light-blue text-us-open-blue cursor-pointer shadow-lg scale-105',
    'my-reservation': 'bg-[#052c90] text-[#ffd400] border-2 border-[#001b59]',
    taken: 'bg-blue-50 border-2 border-blue-200 text-gray-600',
    past: 'bg-gray-100 border border-gray-200 text-gray-400 cursor-not-allowed opacity-60',
    maintenance: 'bg-orange-100 border-2 border-orange-400 text-orange-700',
  }

  const statusLabels = {
    available: 'Disponible',
    selected: 'Seleccionado',
    'my-reservation': 'Tu Reserva',
    taken: ownerName ? ownerName : 'Escuela de Tenis',
    past: 'Pasado',
    maintenance: 'Mantenimiento',
  }

  return (
    <button
      onClick={isClickable ? onClick : undefined}
      disabled={!isClickable}
      className={`
        w-full p-4 rounded-lg transition-all duration-200 font-semibold text-center
        ${statusStyles[status]}
      `}
    >
      <div className="flex items-center justify-center">
        <div>
          <div className="text-xl font-bold">{formatHour(hour)}</div>
          <div className="text-sm mt-1">{statusLabels[status]}</div>
        </div>
        {status === 'selected' && (
          <div className="text-2xl ml-3">✓</div>
        )}
      </div>
    </button>
  )
}
