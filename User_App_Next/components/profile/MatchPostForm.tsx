// ABOUTME: Form for creating a new match post (specific date/time or standing availability).
// ABOUTME: Supports optional desired level/category filters and a note field with char counter.
'use client'

import { useState } from 'react'
import type { MatchPostWithCount } from '@/types/database.types'

interface Props {
  onCreated: (post: MatchPostWithCount) => void
}

const LEVEL_TIERS = ['Principiante', 'Intermedio', 'Avanzado']
const CATEGORIAS = ['Primera', 'Segunda', 'Tercera', 'Cuarta', 'Quinta', 'No sé']
const HOURS = Array.from({ length: 15 }, (_, i) => i + 6)

export default function MatchPostForm({ onCreated }: Props) {
  const [type, setType] = useState<'specific' | 'standing'>('specific')
  const [date, setDate] = useState('')
  const [hour, setHour] = useState('')
  const [desiredLevel, setDesiredLevel] = useState('')
  const [desiredCategoria, setDesiredCategoria] = useState('')
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError('')

    const body: Record<string, unknown> = {
      type,
      desired_level_tier: desiredLevel || null,
      desired_categoria: desiredCategoria || null,
      note: note || null,
    }
    if (type === 'specific') {
      body.date = date
      body.hour = parseInt(hour)
    }

    const res = await fetch('/api/match-posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    setSubmitting(false)
    if (res.ok) {
      const data = await res.json()
      onCreated({ ...data.post, comment_count: 0 })
      setDate('')
      setHour('')
      setDesiredLevel('')
      setDesiredCategoria('')
      setNote('')
    } else {
      const data = await res.json()
      setError(data.error || 'Error al publicar')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
      {/* Type toggle */}
      <div>
        <p className="text-sm font-medium text-gray-700 mb-2">Tipo de búsqueda</p>
        <div className="flex gap-2">
          {(['specific', 'standing'] as const).map(t => (
            <button
              key={t}
              type="button"
              onClick={() => setType(t)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                type === t ? 'bg-us-open-blue text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {t === 'specific' ? 'Partido específico' : 'Disponibilidad general'}
            </button>
          ))}
        </div>
      </div>

      {type === 'specific' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
            <input
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
              required
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Hora</label>
            <select
              value={hour}
              onChange={e => setHour(e.target.value)}
              required
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue"
            >
              <option value="">Seleccionar...</option>
              {HOURS.map(h => (
                <option key={h} value={h}>{h}:00 {h < 12 ? 'AM' : 'PM'}</option>
              ))}
            </select>
          </div>
        </>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Nivel buscado (opcional)</label>
        <select
          value={desiredLevel}
          onChange={e => setDesiredLevel(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue"
        >
          <option value="">Cualquier nivel</option>
          {LEVEL_TIERS.map(l => <option key={l} value={l}>{l}</option>)}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Categoría buscada (opcional)</label>
        <select
          value={desiredCategoria}
          onChange={e => setDesiredCategoria(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue"
        >
          <option value="">Cualquier categoría</option>
          {CATEGORIAS.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Nota (opcional)</label>
        <textarea
          value={note}
          onChange={e => setNote(e.target.value.slice(0, 280))}
          rows={3}
          placeholder="Cuéntale algo a los otros jugadores..."
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue"
        />
        <p className="text-xs text-gray-400 text-right">{note.length}/280</p>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full py-3 bg-us-open-blue text-white font-semibold rounded-lg hover:bg-us-open-light-blue transition-colors disabled:opacity-50"
      >
        {submitting ? 'Publicando...' : 'Publicar'}
      </button>
    </form>
  )
}
