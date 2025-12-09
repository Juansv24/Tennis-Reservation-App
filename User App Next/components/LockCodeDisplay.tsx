'use client'

interface LockCodeDisplayProps {
  lockCode: string
  hasReservations: boolean
}

export default function LockCodeDisplay({ lockCode, hasReservations }: LockCodeDisplayProps) {
  if (!hasReservations || !lockCode) return null

  return (
    <div className="text-right">
      <div
        className="inline-block bg-gradient-to-r from-us-open-blue to-us-open-light-blue text-white rounded-lg px-4 py-3 shadow-md"
      >
        <p className="text-xs uppercase tracking-wide opacity-90 mb-1">
          🔐 Código de Candado
        </p>
        <p className="text-2xl font-bold tracking-wider">
          {lockCode}
        </p>
      </div>
    </div>
  )
}
