'use client'

import { useState } from 'react'
import type { User } from '@/types/database.types'

interface CollapsibleSectionsProps {
  user: User
}

export default function CollapsibleSections({ user }: CollapsibleSectionsProps) {
  const [rulesOpen, setRulesOpen] = useState(false)
  const [creditsOpen, setCreditsOpen] = useState(false)
  const [cancelOpen, setCancelOpen] = useState(false)

  // Determine reservation hours based on user type
  const reservationHours = user.is_vip ? '8:00 AM - 11:00 PM' : '8:00 AM - 5:00 PM'

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
          className="w-full p-4 text-left flex items-center gap-2 hover:bg-gray-50 transition-colors"
        >
          <span>📋</span>
          <span className="font-semibold text-gray-800">Reglas de Reserva</span>
          <span className="ml-auto text-gray-400 text-xl font-light">
            {rulesOpen ? '−' : '+'}
          </span>
        </button>
        {rulesOpen && (
          <div className="p-4 pt-0 text-gray-700">
            <ul className="space-y-2">
              <li>• <strong>Puedes reservar para hoy y para mañana, pero solo un día a la vez</strong></li>
              <li>• <strong>Máximo 2 horas</strong> por persona por día</li>
              <li>• <strong>Horas consecutivas</strong> requeridas si se reservan 2 horas</li>
              <li>• No se permite reservar la cancha en <strong>los mismos horarios dos días consecutivos</strong></li>
              <li>• <strong>Horario para hacer reservas:</strong> {reservationHours}</li>
            </ul>
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 mt-3">
              <p className="text-sm text-yellow-800">
                <strong>⏰ Importante:</strong> Solo puedes hacer reservas dentro del horario permitido
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Cómo Adquirir Créditos - Expandable */}
      <div className="bg-white rounded-lg border border-gray-300">
        <button
          onClick={() => setCreditsOpen(!creditsOpen)}
          className="w-full p-4 text-left flex items-center gap-2 hover:bg-gray-50 transition-colors"
        >
          <span>🪙</span>
          <span className="font-semibold text-gray-800">¿Cómo Adquirir Créditos?</span>
          <span className="ml-auto text-gray-400 text-xl font-light">
            {creditsOpen ? '−' : '+'}
          </span>
        </button>
        {creditsOpen && (
          <div className="p-4 pt-0 text-gray-700 space-y-3">
            <div>
              <p className="font-semibold text-gray-900 mb-1">💳 Costo de Créditos:</p>
              <ul className="space-y-1 ml-4">
                <li>• Cada crédito = 1 hora de cancha</li>
                <li>• Precio por crédito: <strong>$15.000 COP</strong></li>
              </ul>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-1">📞 Contacto para Recargar:</p>
              <p className="ml-4"><strong>Orlando Rios</strong></p>
              <p className="ml-4">
                <strong>WhatsApp:</strong>{' '}
                <a
                  href="https://wa.me/573193368749"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-us-open-light-blue hover:underline"
                >
                  3193368749
                </a>
              </p>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-1">⏰ Horarios de Atención:</p>
              <ul className="space-y-1 ml-4">
                <li>• <strong>Lunes a Sábado:</strong> 9:00 AM - 11:00 AM</li>
                <li>• <strong>Domingos y Festivos:</strong> 5:00 PM - 7:00 PM</li>
              </ul>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-1">💡 Recomendaciones:</p>
              <ul className="space-y-1 ml-4">
                <li>• Planifica tu recarga con anticipación para evitar quedarte sin créditos</li>
                <li>• Contacta únicamente en los horarios establecidos para una respuesta rápida</li>
                <li>• Puedes recargar múltiples créditos en una sola transacción</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Cancelar Reservas - Expandable */}
      <div className="bg-white rounded-lg border border-gray-300">
        <button
          onClick={() => setCancelOpen(!cancelOpen)}
          className="w-full p-4 text-left flex items-center gap-2 hover:bg-gray-50 transition-colors"
        >
          <span>❌</span>
          <span className="font-semibold text-gray-800">¿Cómo Cancelar una Reserva?</span>
          <span className="ml-auto text-gray-400 text-xl font-light">
            {cancelOpen ? '−' : '+'}
          </span>
        </button>
        {cancelOpen && (
          <div className="p-4 pt-0 text-gray-700 space-y-3">
            <p>Para cancelar una reserva, sigue estos pasos:</p>

            <div>
              <p className="font-semibold text-gray-900 mb-2">📞 Contacta al Administrador:</p>
              <ul className="space-y-1 ml-4">
                <li>• Comunícate con el administrador para solicitar la cancelación</li>
                <li>• Explica el motivo de la cancelación</li>
              </ul>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-2">✅ Validación y Procesamiento:</p>
              <ul className="space-y-1 ml-4">
                <li>• El administrador revisará tu solicitud</li>
                <li>• Una vez validada, el administrador procederá con la cancelación</li>
              </ul>
            </div>

            <div>
              <p className="font-semibold text-gray-900 mb-2">🪙 Devolución de Créditos:</p>
              <ul className="space-y-1 ml-4">
                <li>• Los créditos correspondientes serán devueltos a tu cuenta automáticamente</li>
                <li>• Podrás utilizar estos créditos para futuras reservas</li>
              </ul>
            </div>

            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 mt-3">
              <p className="text-sm text-yellow-800">
                <strong>⚠️ Nota:</strong> Las cancelaciones están sujetas a aprobación del administrador.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
