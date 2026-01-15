'use client'

export default function InstructionsSection() {
  return (
    <div className="bg-blue-50 border-2 border-us-open-light-blue rounded-lg p-6 shadow-sm">
      <h2 className="text-2xl font-bold text-us-open-blue mb-4">Cómo Reservar</h2>
      <ol className="space-y-3 list-decimal list-inside">
        <li className="text-gray-800">
          <span className="font-semibold">Revisa que estés en los horarios de reserva</span> disponibles (6:00 AM - 8:00 PM)
        </li>
        <li className="text-gray-800">
          <span className="font-semibold">Selecciona los horarios disponibles</span> que desees reservar (máximo 2 horas consecutivas)
        </li>
        <li className="text-gray-800">
          <span className="font-semibold">Confirma tu reserva</span> y revisa el código del candado
        </li>
        <li className="text-gray-800">
          <span className="font-semibold">Te llegará una confirmación</span> y podrás usar el código para acceder a la cancha
        </li>
      </ol>
      <div className="mt-4 p-3 bg-us-open-yellow bg-opacity-20 rounded-lg">
        <p className="text-sm text-gray-700">
          <strong>Nota:</strong> Las reservas utilizan 1 crédito por hora. Los miembros VIP reservan gratis.
        </p>
      </div>
    </div>
  )
}
