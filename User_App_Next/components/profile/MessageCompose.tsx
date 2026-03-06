// ABOUTME: Modal for composing and sending a direct message to a specific user.
// ABOUTME: Calls POST /api/messages. Calls onSent() on success, onClose() on cancel.
'use client'

import { useState } from 'react'

interface Props {
  recipientId: string
  recipientName: string
  onClose: () => void
  onSent: () => void
}

export default function MessageCompose({ recipientId, recipientName, onClose, onSent }: Props) {
  const [content, setContent] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!content.trim()) return
    setSending(true)
    setError('')

    const res = await fetch('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient_id: recipientId, content }),
    })

    setSending(false)
    if (res.ok) {
      onSent()
    } else {
      const data = await res.json()
      setError(data.error || 'Error al enviar')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-us-open-blue">
            Mensaje a {recipientName}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            aria-label="Cerrar"
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            maxLength={1000}
            rows={4}
            placeholder="Escribe tu mensaje..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue resize-none"
            autoFocus
          />
          <p className="text-xs text-gray-400 text-right">{content.length}/1000</p>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={sending || !content.trim()}
              className="flex-1 py-2 bg-us-open-blue text-white rounded-lg text-sm font-semibold hover:bg-us-open-light-blue transition-colors disabled:opacity-50"
            >
              {sending ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
