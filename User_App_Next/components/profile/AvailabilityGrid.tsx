// ABOUTME: Interactive 7x15 grid for selecting typical playing hours per day of the week.
// ABOUTME: Columns are Mon-Sun, rows are 6AM-8PM. Each cell is an accessible toggle button.
'use client'

import type { Availability } from '@/types/database.types'

const DAYS = [
  { key: 'monday',    label: 'Lun' },
  { key: 'tuesday',   label: 'Mar' },
  { key: 'wednesday', label: 'Mié' },
  { key: 'thursday',  label: 'Jue' },
  { key: 'friday',    label: 'Vie' },
  { key: 'saturday',  label: 'Sáb' },
  { key: 'sunday',    label: 'Dom' },
]

const HOURS = Array.from({ length: 15 }, (_, i) => i + 6)

interface Props {
  value: Availability | null
  onChange: (availability: Availability) => void
}

export default function AvailabilityGrid({ value, onChange }: Props) {
  function isSelected(day: string, hour: number): boolean {
    return value?.[day]?.includes(hour) ?? false
  }

  function toggle(day: string, hour: number) {
    const current = value ?? {}
    const dayHours = current[day] ?? []
    const updated = isSelected(day, hour)
      ? dayHours.filter(h => h !== hour)
      : [...dayHours, hour].sort((a, b) => a - b)
    onChange({ ...current, [day]: updated })
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse text-xs">
        <thead>
          <tr>
            <th className="w-12" />
            {DAYS.map(d => (
              <th key={d.key} className="text-center py-1 px-1 text-us-open-blue font-semibold">
                {d.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {HOURS.map(hour => (
            <tr key={hour}>
              <td className="text-right pr-2 text-gray-500 font-mono text-xs">
                {`${hour.toString().padStart(2, '0')}:00`}
              </td>
              {DAYS.map(d => {
                const selected = isSelected(d.key, hour)
                return (
                  <td key={d.key} className="p-0.5">
                    <button
                      type="button"
                      onClick={() => toggle(d.key, hour)}
                      className={`w-full h-6 rounded transition-colors ${
                        selected
                          ? 'bg-us-open-light-blue'
                          : 'bg-gray-100 hover:bg-gray-200'
                      }`}
                      aria-pressed={selected}
                      aria-label={`${d.label} ${hour}:00`}
                    />
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
