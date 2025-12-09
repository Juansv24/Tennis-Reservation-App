'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import { COURT_HOURS, getTodayDate, getTomorrowDate, formatDateFull, formatDateShort } from '@/lib/constants'
import { canMakeReservationNow, getColombiaTime, getColombiaHour } from '@/lib/timezone'
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
  const [expandedDay, setExpandedDay] = useState<'today' | 'tomorrow' | null>(null) // For mobile accordion
  const [canReserve, setCanReserve] = useState(true)
  const [reservationError, setReservationError] = useState<string>('')

  const supabase = createClient()
  const today = getTodayDate()
  const tomorrow = getTomorrowDate()

  // Check if user can make reservations based on current time
  useEffect(() => {
    const [allowed, errorMsg] = canMakeReservationNow(user.is_vip)
    setCanReserve(allowed)
    setReservationError(errorMsg)
  }, [user.is_vip])

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

    // Check if past (using Colombian timezone)
    const colombiaTime = getColombiaTime()
    const slotDate = new Date(date + 'T00:00:00')
    const currentHour = getColombiaHour()

    if (slotDate.toDateString() === colombiaTime.toDateString() && hour < currentHour) {
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
    // Check if user is allowed to make reservations at this time
    if (!canReserve) {
      alert(reservationError)
      return
    }

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
      // Create all reservations in a single batch request
      const response = await fetch('/api/reservations/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reservations: selectedHours.map(slot => ({
            date: slot.date,
            hour: slot.hour
          }))
        }),
      })

      const result = await response.json()

      // Check if failed
      if (result.error) {
        alert(result.error || 'Error al crear reserva')
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

      // Use credits used from API response
      const creditsUsed = result.credits_used || 0

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
      console.error('Reservation error:', error)
      alert('Error al crear reserva')
      setIsModalOpen(false)
      setSelectedHours([])
    }
  }

  function handleCloseModal() {
    setIsModalOpen(false)
  }

  // Calculate available slots for each day (using Colombian timezone)
  function getAvailableSlotsCount(date: string, reservationsList: Reservation[], maintenanceList: MaintenanceSlot[]) {
    const colombiaTime = getColombiaTime()
    const currentHour = getColombiaHour()
    const slotDate = new Date(date + 'T00:00:00')
    const isToday = slotDate.toDateString() === colombiaTime.toDateString()

    return COURT_HOURS.filter(hour => {
      // Check if past
      if (isToday && hour < currentHour) return false

      // Check if in maintenance
      if (maintenanceList.some(m => m.hour === hour)) return false

      // Check if reserved
      if (reservationsList.some(r => r.hour === hour)) return false

      return true
    }).length
  }

  return (
    <div className="space-y-6">
      {/* View-Only Mode Warning Banner */}
      {!canReserve && (
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-3">
            <span className="text-3xl">⏰</span>
            <div>
              <h3 className="font-bold text-red-800 text-lg">Modo Solo Lectura</h3>
              <p className="text-red-700">{reservationError}</p>
              <p className="text-red-600 text-sm mt-1">
                Puedes ver las reservas existentes pero no puedes hacer nuevas reservas en este momento.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Desktop: Two Column Layout - Side by Side */}
      <div className="hidden lg:block">
        {/* Big Blue Date Buttons - Desktop (non-clickable, just visual) */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-us-open-light-blue text-white py-6 px-4 rounded-xl font-bold text-lg shadow-lg text-center">
            <div className="text-xl">{formatDateShort(today)}</div>
            <div className="text-sm font-normal mt-1">HOY</div>
          </div>
          <div className="bg-us-open-light-blue text-white py-6 px-4 rounded-xl font-bold text-lg shadow-lg text-center">
            <div className="text-xl">{formatDateShort(tomorrow)}</div>
            <div className="text-sm font-normal mt-1">MAÑANA</div>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500">Cargando...</div>
        ) : (
          <div className="grid grid-cols-2 gap-8">
            {/* Today Column */}
            <div>
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
      </div>

      {/* Mobile: Accordion Layout - Toggle Between Days */}
      <div className="lg:hidden space-y-4">
        {loading ? (
          <div className="text-center py-12 text-gray-500">Cargando...</div>
        ) : (
          <>
            {/* Today Accordion */}
            <div>
              <button
                onClick={() => setExpandedDay(expandedDay === 'today' ? null : 'today')}
                className="w-full bg-us-open-light-blue text-white py-6 px-6 rounded-xl font-bold hover:bg-us-open-blue transition-all duration-300 shadow-lg text-center"
              >
                <div className="text-xl">{formatDateShort(today)}</div>
                <div className="text-sm font-normal mt-1 opacity-90">HOY</div>
                <div className="text-sm font-normal mt-2 opacity-80">
                  {getAvailableSlotsCount(today, todayReservations, todayMaintenance)} turnos disponibles
                </div>
              </button>

              {expandedDay === 'today' && (
                <div className="mt-4 animate-in slide-in-from-top-2 duration-300">
                  <div className="grid grid-cols-2 gap-3">
                    {(() => {
                      const colombiaTime = getColombiaTime()
                      const currentHour = getColombiaHour()
                      const slotDate = new Date(today + 'T00:00:00')
                      const isToday = slotDate.toDateString() === colombiaTime.toDateString()

                      const availableHours = COURT_HOURS.filter(hour => {
                        if (isToday && hour < currentHour) return false
                        return true
                      })

                      const midpoint = Math.ceil(availableHours.length / 2)
                      const firstColumn = availableHours.slice(0, midpoint)
                      const secondColumn = availableHours.slice(midpoint)

                      return (
                        <>
                          <div className="space-y-3">
                            {firstColumn.map((hour) => {
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
                          <div className="space-y-3">
                            {secondColumn.map((hour) => {
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
                        </>
                      )
                    })()}
                  </div>
                </div>
              )}
            </div>

            {/* Tomorrow Accordion */}
            <div>
              <button
                onClick={() => setExpandedDay(expandedDay === 'tomorrow' ? null : 'tomorrow')}
                className="w-full bg-us-open-light-blue text-white py-6 px-6 rounded-xl font-bold hover:bg-us-open-blue transition-all duration-300 shadow-lg text-center"
              >
                <div className="text-xl">{formatDateShort(tomorrow)}</div>
                <div className="text-sm font-normal mt-1 opacity-90">MAÑANA</div>
                <div className="text-sm font-normal mt-2 opacity-80">
                  {getAvailableSlotsCount(tomorrow, tomorrowReservations, tomorrowMaintenance)} turnos disponibles
                </div>
              </button>

              {expandedDay === 'tomorrow' && (
                <div className="mt-4 animate-in slide-in-from-top-2 duration-300">
                  <div className="grid grid-cols-2 gap-3">
                    {(() => {
                      const midpoint = Math.ceil(COURT_HOURS.length / 2)
                      const firstColumn = COURT_HOURS.slice(0, midpoint)
                      const secondColumn = COURT_HOURS.slice(midpoint)

                      return (
                        <>
                          <div className="space-y-3">
                            {firstColumn.map((hour) => {
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
                          <div className="space-y-3">
                            {secondColumn.map((hour) => {
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
                        </>
                      )
                    })()}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Continue Button - Only show when hours are selected and user can make reservations */}
      {canReserve && selectedHours.length > 0 && (
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
      />

      {/* Success Modal */}
      {successData && (
        <SuccessModal
          isOpen={showSuccessModal}
          userName={user.full_name}
          date={successData.date}
          hours={successData.hours}
          creditsUsed={successData.creditsUsed}
          creditsRemaining={user.credits - successData.creditsUsed}
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
