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
  const isClickable = status === 'available'

  const statusStyles = {
    available: 'bg-white border-2 border-available-green border-l-4 text-available-green hover:bg-green-50 hover:border-us-open-yellow cursor-pointer slot-hover',
    'my-reservation': 'bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-us-open-light-blue border-l-4 border-l-us-open-blue text-us-open-blue shadow-md',
    taken: 'bg-gray-50 border-2 border-gray-200 text-taken-gray cursor-not-allowed opacity-70',
    past: 'bg-white border border-dashed border-gray-200 text-gray-400 cursor-not-allowed opacity-50',
    maintenance: 'bg-orange-50 border-2 border-maintenance-orange border-l-4 border-l-orange-600 text-orange-700',
  }

  const statusLabels = {
    available: 'Disponible',
    'my-reservation': 'Tu Reserva',
    taken: 'Reservado',
    past: 'Pasado',
    maintenance: 'Mantenimiento',
  }

  return (
    <button
      onClick={isClickable ? onClick : undefined}
      disabled={!isClickable}
      className={`
        p-4 rounded-lg slot-transition font-semibold text-center
        ${statusStyles[status]}
      `}
    >
      <div className="text-lg mb-1">{formatHour(hour)}</div>
      <div className="text-sm font-medium">{statusLabels[status]}</div>
      {status === 'taken' && ownerName && (
        <div className="text-xs mt-1 opacity-75">{ownerName}</div>
      )}
    </button>
  )
}
