// ABOUTME: Displays a single suggested partner card with level badge and schedule overlap message.
// ABOUTME: Shows player name, level/category, compatibility badge, overlap message, and message button.
'use client'

import { useState } from 'react'
import type { SuggestedPartner } from '@/types/database.types'
import MessageCompose from './MessageCompose'

interface Props {
  partner: SuggestedPartner
}

export default function PartnerCard({ partner }: Props) {
  const { user, badge, overlapMessage } = partner
  const [composing, setComposing] = useState(false)
  const [sent, setSent] = useState(false)

  function handleSent() {
    setComposing(false)
    setSent(true)
  }

  return (
    <>
      <div className="p-4 border border-gray-200 rounded-lg bg-white space-y-2">
        <p className="font-medium text-gray-900">{user.full_name}</p>
        <p className="text-sm text-gray-500">
          {user.level_tier ?? '—'}{user.categoria ? ` / ${user.categoria}` : ''}
        </p>
        <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${
          badge === 'nivel+horario'
            ? 'bg-green-100 text-green-700'
            : 'bg-blue-100 text-blue-700'
        }`}>
          {badge === 'nivel+horario' ? 'Nivel + horario' : 'Coincidencia en nivel'}
        </span>
        {overlapMessage && (
          <p className="text-xs text-gray-500 italic">{overlapMessage}</p>
        )}
        <div className="pt-1">
          {sent ? (
            <p className="text-xs text-green-600 font-medium">Mensaje enviado</p>
          ) : (
            <button
              onClick={() => setComposing(true)}
              className="text-xs font-medium text-us-open-light-blue hover:underline"
            >
              Enviar mensaje
            </button>
          )}
        </div>
      </div>

      {composing && (
        <MessageCompose
          recipientId={user.id}
          recipientName={user.full_name}
          onClose={() => setComposing(false)}
          onSent={handleSent}
        />
      )}
    </>
  )
}
