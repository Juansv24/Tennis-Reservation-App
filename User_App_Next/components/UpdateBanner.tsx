'use client'

import { useState, useEffect } from 'react'

export default function UpdateBanner() {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false)
    }, 30000) // Hide after 30 seconds

    return () => clearTimeout(timer)
  }, [])

  if (!isVisible) return null

  return (
    <div className="bg-orange-100 border-l-4 border-orange-400 text-orange-900 p-4 rounded-lg shadow-sm animate-in fade-in duration-300">
      <p className="font-semibold mb-2">Actualización de la app (Beta)</p>
      <p className="text-sm mb-2">Se han añadido dos nuevas pestañas en la parte inferior del encabezado:</p>
      <ul className="text-sm space-y-2 list-none">
        <li>
          <span className="font-semibold">Mi Perfil</span> — Completa tu perfil con tu información (nivel, categoría, edad) para recibir sugerencias de jugadores compatibles con tu disponibilidad y nivel de juego.
        </li>
        <li>
          <span className="font-semibold">Comunidad</span> — Consulta y comenta sobre publicaciones de jugadores que buscan partidos a determinados días, horarios y niveles de juego y publica tus propios posts para conectar con otros jugadores registrados.
        </li>
      </ul>
    </div>
  )
}
