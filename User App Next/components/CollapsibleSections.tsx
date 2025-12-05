'use client'

import { useState } from 'react'

export default function CollapsibleSections() {
  const [rulesOpen, setRulesOpen] = useState(false)
  const [creditsOpen, setCreditsOpen] = useState(false)

  return (
    <div className="space-y-4">
      {/* Cómo Reservar - Always visible */}
      <div className="bg-white rounded-lg border-2 border-us-open-light-blue p-6">
        <h2 className="text-xl font-bold text-us-open-blue mb-4">Cómo Reservar</h2>
        <ol className="space-y-2 text-gray-700">
          <li>1. Revisa que estés en los <strong>horarios de reserva</strong> y que tengas <strong>créditos disponibles!</strong></li>
          <li>2. <strong>Selecciona los horarios disponibles</strong> que desees entre hoy y mañana (hasta 2 horas por día)</li>
          <li>3. <strong>Confirma tu reserva</strong> con un click</li>
          <li>4. Te llegará una <strong>confirmación a tu correo registrado</strong></li>
        </ol>
      </div>

      {/* Reglas de Reserva - Expandable */}
      <div className="bg-white rounded-lg border border-gray-300">
        <button
          onClick={() => setRulesOpen(!rulesOpen)}
          className="w-full p-4 text-left flex items-center gap-2 hover:bg-gray-50"
        >
          <span>📋</span>
          <span className="font-semibold text-gray-800">Reglas de Reserva</span>
          <span className="ml-auto">{rulesOpen ? '▼' : '▶'}</span>
        </button>
        {rulesOpen && (
          <div className="p-4 pt-0 text-gray-700">
            <ul className="space-y-2">
              <li>• Horario: 6:00 AM - 9:00 PM</li>
              <li>• Máximo 2 horas consecutivas por reserva</li>
              <li>• Cada reserva cuesta 1 crédito por hora</li>
              <li>• Usuarios VIP tienen créditos ilimitados</li>
              <li>• Código del candado se muestra al confirmar</li>
            </ul>
          </div>
        )}
      </div>

      {/* Cómo Adquirir Créditos - Expandable */}
      <div className="bg-white rounded-lg border border-gray-300">
        <button
          onClick={() => setCreditsOpen(!creditsOpen)}
          className="w-full p-4 text-left flex items-center gap-2 hover:bg-gray-50"
        >
          <span>🔥</span>
          <span className="font-semibold text-gray-800">¿Cómo Adquirir Créditos?</span>
          <span className="ml-auto">{creditsOpen ? '▼' : '▶'}</span>
        </button>
        {creditsOpen && (
          <div className="p-4 pt-0 text-gray-700">
            <p>Contacta al administrador para adquirir más créditos.</p>
          </div>
        )}
      </div>
    </div>
  )
}
