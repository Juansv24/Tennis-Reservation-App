// ABOUTME: Form component for the Mi Perfil tab — personal info, availability grid, and email preferences.
// ABOUTME: Submits to PUT /api/profile. Calls onSaved() callback on successful save.
'use client'

import { useState } from 'react'
import type { User, Availability } from '@/types/database.types'
import AvailabilityGrid from './AvailabilityGrid'

interface Props {
  user: User
  onSaved: () => void
}

const LEVEL_TIERS = ['Principiante', 'Intermedio', 'Avanzado']
const CATEGORIAS = ['Primera', 'Segunda', 'Tercera', 'Cuarta', 'Quinta', 'No sé']
const GENDERS = [
  { value: 'masculino', label: 'Masculino' },
  { value: 'femenino',  label: 'Femenino' },
  { value: 'otro',      label: 'Otro' },
]

export default function ProfileForm({ user, onSaved }: Props) {
  const [gender, setGender] = useState(user.gender ?? '')
  const [age, setAge] = useState<string>(user.age?.toString() ?? '')
  const [levelTier, setLevelTier] = useState(user.level_tier ?? '')
  const [categoria, setCategoria] = useState(user.categoria ?? '')
  const [availability, setAvailability] = useState<Availability | null>(user.availability)
  const [notifySuggestions, setNotifySuggestions] = useState(user.notify_suggestions)
  const [notifyMatchPosts, setNotifyMatchPosts] = useState(user.notify_match_posts)
  const [notifyMessages, setNotifyMessages] = useState(user.notify_messages)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSaved(false)

    const res = await fetch('/api/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        gender: gender || null,
        age: age ? parseInt(age) : null,
        level_tier: levelTier || null,
        categoria: categoria || null,
        availability,
        notify_suggestions: notifySuggestions,
        notify_match_posts: notifyMatchPosts,
        notify_messages: notifyMessages,
      }),
    })

    setSaving(false)
    if (res.ok) {
      setSaved(true)
      onSaved()
    } else {
      const data = await res.json()
      setError(data.error || 'Error al guardar')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Personal Info */}
      <section className="space-y-4">
        <h3 className="text-lg font-semibold text-us-open-blue">Información personal</h3>

        {/* Nombre (read-only) */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-1">Nombre</p>
          <p className="text-gray-900 font-medium">{user.full_name}</p>
        </div>

        {/* Género */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Género</p>
          <div className="flex gap-6">
            {GENDERS.map(g => (
              <label key={g.value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="gender"
                  value={g.value}
                  checked={gender === g.value}
                  onChange={e => setGender(e.target.value)}
                  className="accent-us-open-light-blue"
                />
                <span className="text-sm">{g.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Edad */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="age">
            Edad
          </label>
          <input
            id="age"
            type="number"
            min={1}
            max={120}
            value={age}
            onChange={e => setAge(e.target.value)}
            placeholder="Tu edad"
            className="w-24 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue"
          />
        </div>

        {/* Nivel */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="level-tier">
            Nivel de juego
          </label>
          <select
            id="level-tier"
            value={levelTier}
            onChange={e => setLevelTier(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue"
          >
            <option value="">Seleccionar...</option>
            {LEVEL_TIERS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        {/* Categoría */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="categoria">
            Categoría
          </label>
          <select
            id="categoria"
            value={categoria}
            onChange={e => setCategoria(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue"
          >
            <option value="">Seleccionar...</option>
            {CATEGORIAS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </section>

      {/* Availability Grid */}
      <section className="space-y-2">
        <h3 className="text-lg font-semibold text-us-open-blue">Disponibilidad habitual</h3>
        <p className="text-sm text-gray-500">Selecciona los horarios en que usualmente juegas</p>
        <AvailabilityGrid value={availability} onChange={setAvailability} />
      </section>

      {/* Email Preferences */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold text-us-open-blue">Notificaciones por email</h3>
        {[
          { label: 'Recibir emails de compañeros sugeridos', value: notifySuggestions, setter: setNotifySuggestions },
          { label: 'Recibir emails de nuevas publicaciones', value: notifyMatchPosts, setter: setNotifyMatchPosts },
          { label: 'Recibir emails de mensajes directos', value: notifyMessages, setter: setNotifyMessages },
        ].map(({ label, value, setter }) => (
          <label key={label} className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={value}
              onChange={e => setter(e.target.checked)}
              className="accent-us-open-light-blue w-4 h-4"
            />
            <span className="text-sm text-gray-700">{label}</span>
          </label>
        ))}
      </section>

      {error && (
        <p className="text-red-600 text-sm">{error}</p>
      )}
      {saved && (
        <p className="text-green-600 text-sm">✓ Perfil guardado</p>
      )}

      <button
        type="submit"
        disabled={saving}
        className="w-full py-3 bg-us-open-blue text-white font-semibold rounded-lg hover:bg-us-open-light-blue transition-colors disabled:opacity-50"
      >
        {saving ? 'Guardando...' : 'Guardar perfil'}
      </button>
    </form>
  )
}
