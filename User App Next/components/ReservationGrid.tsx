'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import { COURT_HOURS, getTodayDate, getTomorrowDate, formatDateFull, formatDateShort } from '@/lib/constants'
import TimeSlot from './TimeSlot'
import ConfirmationModal from './ConfirmationModal'
import SuccessModal from './SuccessModal'
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
  const [reservations, setReservations] = useState(initialReservations)
  const [maintenance, setMaintenance] = useState(initialMaintenance)
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedHours, setSelectedHours] = useState<Array<{hour: number, date: string}>>([])
  const [todayReservations, setTodayReservations] = useState<Reservation[]>([])
  const [tomorrowReservations, setTomorrowReservations] = useState<Reservation[]>([])
  const [todayMaintenance, setTodayMaintenance] = useState<MaintenanceSlot[]>([])
  const [tomorrowMaintenance, setTomorrowMaintenance] = useState<MaintenanceSlot[]>([])
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [successData, setSuccessData] = useState<{date: string, hours: number[], creditsUsed: number} | null>(null)

  const supabase = createClient()
  const today = getTodayDate()
  const tomorrow = getTomorrowDate()

  // Fetch both days' data on mount
  useEffect(() => {
    async function fetchAllData() {
      setLoading(true)

      const [todayResData, tomorrowResData, todayMainData, tomorrowMainData] = await Promise.all([
        supabase.from('reservations').select('*, users(full_name)').eq('date', today).order('hour'),
        supabase.from('reservations').select('*, users(full_name)').eq('date', tomorrow).order('hour'),
        supabase.from('maintenance_slots').select('*').eq('date', today),
        supabase.from('maintenance_slots').select('*').eq('date', tomorrow),
      ])

      if (todayResData.data) setTodayReservations(todayResData.data)
      if (tomorrowResData.data) setTomorrowReservations(tomorrowResData.data)
      if (todayMainData.data) setTodayMaintenance(todayMainData.data)
      if (tomorrowMainData.data) setTomorrowMaintenance(tomorrowMainData.data)

      setLoading(false)
    }

    fetchAllData()
  }, [supabase, today, tomorrow])

  // Real-time subscription for today
  useEffect(() => {
    const channelToday = supabase
      .channel('reservations-today')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'reservations',
          filter: `date=eq.${today}`,
        },
        async (payload) => {
          if (payload.eventType === 'INSERT') {
            const { data } = await supabase
              .from('reservations')
              .select('*, users(full_name)')
              .eq('id', payload.new.id)
              .single()
            if (data) {
              setTodayReservations((prev) => [...prev, data])
            }
          } else if (payload.eventType === 'DELETE') {
            setTodayReservations((prev) => prev.filter((r) => r.id !== payload.old.id))
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channelToday)
    }
  }, [today, supabase])

  // Real-time subscription for tomorrow
  useEffect(() => {
    const channelTomorrow = supabase
      .channel('reservations-tomorrow')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'reservations',
          filter: `date=eq.${tomorrow}`,
        },
        async (payload) => {
          if (payload.eventType === 'INSERT') {
            const { data } = await supabase
              .from('reservations')
              .select('*, users(full_name)')
              .eq('id', payload.new.id)
              .single()
            if (data) {
              setTomorrowReservations((prev) => [...prev, data])
            }
          } else if (payload.eventType === 'DELETE') {
            setTomorrowReservations((prev) => prev.filter((r) => r.id !== payload.old.id))
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channelTomorrow)
    }
  }, [tomorrow, supabase])

  function getSlotStatus(
    hour: number,
    date: string,
    reservationsList: Reservation[],
    maintenanceList: MaintenanceSlot[]
  ): { status: SlotStatus; ownerName?: string } {
    // Check if selected
    if (selectedHours.some(s => s.hour === hour && s.date === date)) {
      return { status: 'selected' }
    }

    // Check if in maintenance
    const inMaintenance = maintenanceList.some((m) => m.hour === hour)
    if (inMaintenance) {
      return { status: 'maintenance' }
    }

    // Check if past
    const now = new Date()
    const slotDate = new Date(date + 'T00:00:00')
    const currentHour = now.getHours()

    if (slotDate.toDateString() === now.toDateString() && hour < currentHour) {
      return { status: 'past' }
    }

    // Check if reserved
    const reservation = reservationsList.find((r) => r.hour === hour)
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

  function handleSlotClick(hour: number, date: string) {
    const reservationsList = date === today ? todayReservations : tomorrowReservations
    const maintenanceList = date === today ? todayMaintenance : tomorrowMaintenance
    const { status } = getSlotStatus(hour, date, reservationsList, maintenanceList)

    // Only allow clicking on available slots
    if (status !== 'available' && status !== 'selected') return

    const isAlreadySelected = selectedHours.some(s => s.hour === hour && s.date === date)

    if (isAlreadySelected) {
      // Deselect
      setSelectedHours(selectedHours.filter((s) => !(s.hour === hour && s.date === date)))
      return
    }

    // Get user's existing reservations for both days
    const userTodayReservations = todayReservations.filter(r => r.user_id === user.id).map(r => r.hour)
    const userTomorrowReservations = tomorrowReservations.filter(r => r.user_id === user.id).map(r => r.hour)

    // RULE 1: Check if trying to book same hour on consecutive days
    if (date === today && userTomorrowReservations.includes(hour)) {
      const formattedHour = `${hour.toString().padStart(2, '0')}:00`
      alert(`No puedes reservar a las ${formattedHour} hoy porque ya lo tienes reservado mañana. No se permite reservar el mismo horario dos días seguidos.`)
      return
    }
    if (date === tomorrow && userTodayReservations.includes(hour)) {
      const formattedHour = `${hour.toString().padStart(2, '0')}:00`
      alert(`No puedes reservar a las ${formattedHour} mañana porque ya lo tienes reservado hoy. No se permite reservar el mismo horario dos días seguidos.`)
      return
    }

    // RULE 2: Check daily limit (max 2 hours per day)
    const userExistingHoursForDate = date === today ? userTodayReservations : userTomorrowReservations
    const selectedHoursForDate = selectedHours.filter(s => s.date === date).length
    const totalHoursAfterSelection = userExistingHoursForDate.length + selectedHoursForDate + 1

    if (totalHoursAfterSelection > 2) {
      alert(`Máximo 2 horas por día. Ya tienes ${userExistingHoursForDate.length} hora(s) reservada(s) para este día.`)
      return
    }

    // RULE 3: Check if already have 2 selections
    if (selectedHours.length >= 2) {
      alert('Máximo 2 horas por selección')
      return
    }

    if (selectedHours.length === 0) {
      // First selection
      setSelectedHours([{hour, date}])
    } else if (selectedHours.length === 1) {
      const existing = selectedHours[0]

      // RULE 4: Must be same date
      if (existing.date !== date) {
        alert('Las horas seleccionadas deben ser del mismo día')
        setSelectedHours([{hour, date}])
        return
      }

      // RULE 5: Must be consecutive hours
      if (Math.abs(hour - existing.hour) !== 1) {
        alert('Las horas seleccionadas deben ser consecutivas')
        setSelectedHours([{hour, date}])
        return
      }

      // Add consecutive hour on same date
      const sorted = [existing, {hour, date}].sort((a, b) => a.hour - b.hour)
      setSelectedHours(sorted)
    }
  }

  function handleOpenModal() {
    if (selectedHours.length > 0) {
      setIsModalOpen(true)
    }
  }

  async function handleConfirmReservation() {
    if (selectedHours.length === 0) return

    try {
      // Create reservations for all selected hours with their dates
      const promises = selectedHours.map((slot) =>
        fetch('/api/reservations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ date: slot.date, hour: slot.hour }),
        })
      )

      const responses = await Promise.all(promises)
      const results = await Promise.all(responses.map((r) => r.json()))

      // Check if any failed
      const errors = results.filter((r) => r.error)
      if (errors.length > 0) {
        alert(errors[0].error || 'Error al crear reserva')
        setIsModalOpen(false)
        setSelectedHours([])
        return
      }

      // Group hours by date for sending emails
      const hoursByDate = selectedHours.reduce((acc, slot) => {
        if (!acc[slot.date]) {
          acc[slot.date] = []
        }
        acc[slot.date].push(slot.hour)
        return acc
      }, {} as Record<string, number[]>)

      // Send confirmation email for each date
      const emailPromises = Object.entries(hoursByDate).map(([date, hours]) =>
        fetch('/api/send-confirmation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            date,
            hours,
            userName: user.full_name,
            userEmail: user.email,
          }),
        })
      )

      await Promise.all(emailPromises)

      // Calculate credits used
      const creditsUsed = user.is_vip ? 0 : selectedHours.length

      // Close confirmation modal and show success modal
      setIsModalOpen(false)
      setSuccessData({
        date: selectedHours[0].date,
        hours: selectedHours.map(s => s.hour),
        creditsUsed
      })
      setShowSuccessModal(true)
      setSelectedHours([])
    } catch (error) {
      alert('Error al crear reserva')
      setIsModalOpen(false)
      setSelectedHours([])
    }
  }

  function handleCloseModal() {
    setIsModalOpen(false)
  }

  return (
    <div className="space-y-6">
      {/* Big Blue Date Buttons */}
      <div className="grid grid-cols-2 gap-4">
        <button
          className="bg-us-open-light-blue text-white py-6 px-4 rounded-xl font-bold text-lg hover:bg-us-open-blue transition-colors shadow-lg"
        >
          <div className="text-xl">{formatDateShort(today)}</div>
          <div className="text-sm font-normal mt-1">HOY</div>
        </button>
        <button
          className="bg-us-open-light-blue text-white py-6 px-4 rounded-xl font-bold text-lg hover:bg-us-open-blue transition-colors shadow-lg"
        >
          <div className="text-xl">{formatDateShort(tomorrow)}</div>
          <div className="text-sm font-normal mt-1">MAÑANA</div>
        </button>
      </div>

      {/* Two Column Layout - Today and Tomorrow */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Cargando...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Today Column */}
          <div>
            <h3 className="text-lg font-bold text-us-open-blue mb-4 text-center">
              HOY - {formatDateFull(today)}
            </h3>
            <div className="space-y-3">
              {COURT_HOURS.map((hour) => {
                const { status, ownerName } = getSlotStatus(hour, today, todayReservations, todayMaintenance)
                return (
                  <TimeSlot
                    key={`today-${hour}`}
                    hour={hour}
                    status={status}
                    ownerName={ownerName}
                    onClick={() => handleSlotClick(hour, today)}
                  />
                )
              })}
            </div>
          </div>

          {/* Tomorrow Column */}
          <div>
            <h3 className="text-lg font-bold text-us-open-blue mb-4 text-center">
              MAÑANA - {formatDateFull(tomorrow)}
            </h3>
            <div className="space-y-3">
              {COURT_HOURS.map((hour) => {
                const { status, ownerName } = getSlotStatus(hour, tomorrow, tomorrowReservations, tomorrowMaintenance)
                return (
                  <TimeSlot
                    key={`tomorrow-${hour}`}
                    hour={hour}
                    status={status}
                    ownerName={ownerName}
                    onClick={() => handleSlotClick(hour, tomorrow)}
                  />
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Continue Button - Only show when hours are selected */}
      {selectedHours.length > 0 && (
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40">
          <button
            onClick={handleOpenModal}
            className="bg-white border-2 border-us-open-light-blue text-us-open-blue px-8 py-4 rounded-full font-bold text-lg shadow-2xl hover:bg-blue-50 transition-all"
          >
            Continuar ({selectedHours.length} hora{selectedHours.length > 1 ? 's' : ''})
          </button>
        </div>
      )}

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onConfirm={handleConfirmReservation}
        date={selectedHours.length > 0 ? selectedHours[0].date : today}
        hours={selectedHours.map(s => s.hour)}
        credits={user.credits}
        isVip={user.is_vip}
      />

      {/* Success Modal */}
      {successData && (
        <SuccessModal
          isOpen={showSuccessModal}
          userName={user.full_name}
          date={successData.date}
          hours={successData.hours}
          creditsUsed={successData.creditsUsed}
          creditsRemaining={user.is_vip ? user.credits : user.credits - successData.creditsUsed}
          onMakeAnotherReservation={() => {
            setShowSuccessModal(false)
            setSuccessData(null)
            window.location.reload()
          }}
        />
      )}
    </div>
  )
}
