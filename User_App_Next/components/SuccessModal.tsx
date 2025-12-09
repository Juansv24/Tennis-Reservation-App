'use client'

interface SuccessModalProps {
  isOpen: boolean
  userName: string
  date: string
  hours: number[]
  creditsUsed: number
  creditsRemaining: number
  onMakeAnotherReservation: () => void
}

export default function SuccessModal({
  isOpen,
  userName,
  date,
  hours,
  creditsUsed,
  creditsRemaining,
  onMakeAnotherReservation,
}: SuccessModalProps) {
  if (!isOpen) return null

  // Format date in Spanish
  const dateObj = new Date(date + 'T00:00:00')
  const daysEs = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']
  const monthsEs = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
  const dayName = daysEs[dateObj.getDay()]
  const monthName = monthsEs[dateObj.getMonth()]
  const dateStr = `${dayName}, ${dateObj.getDate()} de ${monthName} de ${dateObj.getFullYear()}`
  // Capitalize only first letter
  const formattedDate = dateStr.charAt(0).toUpperCase() + dateStr.slice(1).toLowerCase()

  // Format times
  const sortedHours = [...hours].sort((a, b) => a - b)
  const startTime = `${sortedHours[0].toString().padStart(2, '0')}:00`
  const endTime = `${(sortedHours[sortedHours.length - 1] + 1).toString().padStart(2, '0')}:00`

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-md transform transition-all">
        {/* Success Header */}
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-t-lg p-6">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-4xl">✅</span>
            <h2 className="text-2xl font-bold text-green-800">¡Reserva Confirmada!</h2>
          </div>
          <p className="text-green-700 text-sm">
            Tu reserva ha sido procesada exitosamente
          </p>
        </div>

        {/* Details */}
        <div className="p-6 space-y-3">
          <div className="flex justify-between items-center border-b border-gray-200 pb-2">
            <span className="text-gray-600 font-medium">Nombre:</span>
            <span className="text-gray-900 font-semibold">{userName}</span>
          </div>

          <div className="flex justify-between items-center border-b border-gray-200 pb-2">
            <span className="text-gray-600 font-medium">Fecha:</span>
            <span className="text-gray-900 font-semibold text-right">{formattedDate}</span>
          </div>

          <div className="flex justify-between items-center border-b border-gray-200 pb-2">
            <span className="text-gray-600 font-medium">Hora:</span>
            <span className="text-gray-900 font-semibold">{startTime} - {endTime}</span>
          </div>

          <div className="flex justify-between items-center border-b border-gray-200 pb-2">
            <span className="text-gray-600 font-medium">Duración:</span>
            <span className="text-gray-900 font-semibold">{hours.length} hora(s)</span>
          </div>

          <div className="flex justify-between items-center border-b border-gray-200 pb-2">
            <span className="text-gray-600 font-medium">💰 Créditos usados:</span>
            <span className="text-gray-900 font-semibold">{creditsUsed}</span>
          </div>

          <div className="flex justify-between items-center bg-blue-50 p-3 rounded-lg">
            <span className="text-blue-900 font-bold">💳 Créditos restantes:</span>
            <span className="text-blue-900 font-bold text-xl">{creditsRemaining}</span>
          </div>
        </div>

        {/* Action Button */}
        <div className="px-6 pb-6">
          <button
            onClick={onMakeAnotherReservation}
            className="w-full py-3 bg-gradient-to-r from-us-open-blue to-us-open-light-blue text-white rounded-lg font-semibold hover:from-us-open-light-blue hover:to-us-open-blue transition-all shadow-md hover:shadow-lg"
          >
            Hacer otra reserva
          </button>
        </div>
      </div>
    </div>
  )
}
