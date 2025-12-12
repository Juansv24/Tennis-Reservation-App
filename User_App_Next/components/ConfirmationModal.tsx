'use client'

import { formatDateFull } from '@/lib/constants'

interface ConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  date: string
  hours: number[]
  credits: number
  isLoading?: boolean
}

export default function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  date,
  hours,
  credits,
  isLoading = false,
}: ConfirmationModalProps) {
  if (!isOpen) return null

  const totalHours = hours.length
  const cost = totalHours // All users pay 1 credit per hour
  const remainingCredits = credits - cost

  // Format time range
  const timeRange = hours.length === 1
    ? `${hours[0]}:00 - ${hours[0] + 1}:00`
    : `${Math.min(...hours)}:00 - ${Math.max(...hours) + 1}:00`

  // Capitalize only first letter of date
  const formattedDate = formatDateFull(date)
  const dateWithFirstCapital = formattedDate.charAt(0).toUpperCase() + formattedDate.slice(1).toLowerCase()

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 transition-opacity duration-300 ease-in-out"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-2xl w-full max-w-md mx-4 transform transition-all duration-300 ease-in-out scale-100 relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-gray-100 bg-opacity-75 rounded-lg flex items-center justify-center z-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-us-open-blue mx-auto mb-3"></div>
              <p className="text-gray-700 font-semibold">Procesando...</p>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="bg-gradient-to-r from-us-open-blue to-us-open-light-blue text-white px-6 py-4 rounded-t-lg">
          <h2 className="text-2xl font-bold">Confirmar Reserva</h2>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Date */}
          <div className="border-b border-gray-200 pb-3">
            <p className="text-sm text-gray-600 uppercase tracking-wide mb-1">
              Fecha
            </p>
            <p className="text-lg font-semibold text-gray-900">
              {dateWithFirstCapital}
            </p>
          </div>

          {/* Time Slot */}
          <div className="border-b border-gray-200 pb-3">
            <p className="text-sm text-gray-600 uppercase tracking-wide mb-1">
              Horario
            </p>
            <p className="text-lg font-semibold text-gray-900">
              {timeRange}
            </p>
            {totalHours > 1 && (
              <p className="text-sm text-gray-600 mt-1">
                ({totalHours} horas)
              </p>
            )}
          </div>

          {/* Cost */}
          <div className="border-b border-gray-200 pb-3">
            <p className="text-sm text-gray-600 uppercase tracking-wide mb-1">
              Costo
            </p>
            <p className="text-lg font-semibold text-gray-900">
              {cost} crédito{cost > 1 ? 's' : ''}
            </p>
          </div>

          {/* Remaining Balance */}
          <div>
            <p className="text-sm text-gray-600 uppercase tracking-wide mb-1">
              Saldo Restante
            </p>
            <p className="text-lg font-semibold text-gray-900">
              {remainingCredits} crédito{remainingCredits !== 1 ? 's' : ''}
            </p>
          </div>
        </div>

        {/* Buttons */}
        <div className="px-6 pb-6 flex gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-us-open-blue to-us-open-light-blue text-white rounded-lg font-semibold hover:from-us-open-light-blue hover:to-us-open-blue transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Confirmar Reserva
          </button>
        </div>
      </div>
    </div>
  )
}
