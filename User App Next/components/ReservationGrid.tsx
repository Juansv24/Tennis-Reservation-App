'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import { COURT_HOURS, getTodayDate, getTomorrowDate, formatDateFull } from '@/lib/constants'
import TimeSlot from './TimeSlot'
import type { Reservation, SlotStatus, User, MaintenanceSlot } from '@/types/database.types'

interface ReservationGridProps {
  initialReservations: Reservation[]
  initialMaintenance: MaintenanceSlot[]
  user: User
  initialDate: string
}

export default function ReservationGrid({
  initialReservations,
  initialMaintenance,
  user,
  initialDate,
}: ReservationGridProps) {
  const [selectedDate, setSelectedDate] = useState(initialDate)
  const [reservations, setReservations] = useState(initialReservations)
  const [maintenance, setMaintenance] = useState(initialMaintenance)
  const [loading, setLoading] = useState(false)

  const supabase = createClient()
  const today = getTodayDate()
  const tomorrow = getTomorrowDate()

  // Real-time subscription
  useEffect(() => {
    const channel = supabase
      .channel('reservations-realtime')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'reservations',
          filter: `date=eq.${selectedDate}`,
        },
        async (payload) => {
          if (payload.eventType === 'INSERT') {
            // Fetch full reservation with user data
            const { data } = await supabase
              .from('reservations')
              .select('*, users(full_name)')
              .eq('id', payload.new.id)
              .single()

            if (data) {
              setReservations((prev) => [...prev, data])
            }
          } else if (payload.eventType === 'DELETE') {
            setReservations((prev) =>
              prev.filter((r) => r.id !== payload.old.id)
            )
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [selectedDate, supabase])

  // Fetch reservations when date changes
  useEffect(() => {
    async function fetchReservations() {
      setLoading(true)
      const { data: newReservations } = await supabase
        .from('reservations')
        .select('*, users(full_name)')
        .eq('date', selectedDate)
        .order('hour')

      const { data: newMaintenance } = await supabase
        .from('maintenance_slots')
        .select('*')
        .eq('date', selectedDate)

      if (newReservations) setReservations(newReservations)
      if (newMaintenance) setMaintenance(newMaintenance)
      setLoading(false)
    }

    fetchReservations()
  }, [selectedDate, supabase])

  function getSlotStatus(hour: number): { status: SlotStatus; ownerName?: string } {
    // Check if in maintenance
    const inMaintenance = maintenance.some((m) => m.hour === hour)
    if (inMaintenance) {
      return { status: 'maintenance' }
    }

    // Check if past
    const now = new Date()
    const slotDate = new Date(selectedDate + 'T00:00:00')
    const currentHour = now.getHours()

    if (
      slotDate.toDateString() === now.toDateString() &&
      hour < currentHour
    ) {
      return { status: 'past' }
    }

    // Check if reserved
    const reservation = reservations.find((r) => r.hour === hour)
    if (reservation) {
      if (reservation.user_id === user.id) {
        return { status: 'my-reservation' }
      }
      return {
        status: 'taken',
        ownerName: reservation.users?.full_name,
      }
    }

    return { status: 'available' }
  }

  async function handleSlotClick(hour: number) {
    // TODO: Show confirmation modal
    // For now, directly create reservation
    const response = await fetch('/api/reservations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date: selectedDate, hour }),
    })

    const data = await response.json()

    if (!response.ok) {
      alert(data.error || 'Error al crear reserva')
      return
    }

    // Optimistically update UI
    alert('¡Reserva confirmada!')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-us-open-blue to-us-open-light-blue text-white p-6 rounded-lg shadow-lg text-center">
        <h1 className="text-3xl font-bold mb-2">
          Reservas de Cancha de Tenis
        </h1>
        <p className="text-lg">{process.env.NEXT_PUBLIC_COURT_NAME}</p>
      </div>

      {/* Date selector */}
      <div className="flex gap-4 justify-center">
        <button
          onClick={() => setSelectedDate(today)}
          className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
            selectedDate === today
              ? 'bg-us-open-light-blue text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Hoy
        </button>
        <button
          onClick={() => setSelectedDate(tomorrow)}
          className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
            selectedDate === tomorrow
              ? 'bg-us-open-light-blue text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Mañana
        </button>
      </div>

      {/* Selected date display */}
      <div className="text-center text-lg text-gray-700 font-medium">
        {formatDateFull(selectedDate)}
      </div>

      {/* Time slots grid */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          Cargando...
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {COURT_HOURS.map((hour) => {
            const { status, ownerName } = getSlotStatus(hour)
            return (
              <TimeSlot
                key={hour}
                hour={hour}
                status={status}
                ownerName={ownerName}
                onClick={() => status === 'available' && handleSlotClick(hour)}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
