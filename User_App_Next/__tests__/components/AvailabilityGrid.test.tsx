// ABOUTME: Unit tests for the 7x15 availability hour grid component.
// ABOUTME: Verifies toggle behavior and correct Availability format on output.
import { render, screen, fireEvent } from '@testing-library/react'
import AvailabilityGrid from '@/components/profile/AvailabilityGrid'
import type { Availability } from '@/types/database.types'

describe('AvailabilityGrid', () => {
  it('renders 7 day column headers', () => {
    render(<AvailabilityGrid value={null} onChange={() => {}} />)
    expect(screen.getByText('Lun')).toBeInTheDocument()
    expect(screen.getByText('Dom')).toBeInTheDocument()
  })

  it('renders hour labels from 06:00 to 20:00', () => {
    render(<AvailabilityGrid value={null} onChange={() => {}} />)
    expect(screen.getByText('06:00')).toBeInTheDocument()
    expect(screen.getByText('20:00')).toBeInTheDocument()
  })

  it('calls onChange with the toggled-on hour when a cell is clicked', () => {
    const handleChange = jest.fn()
    render(<AvailabilityGrid value={null} onChange={handleChange} />)
    // First button = Monday 06:00
    const buttons = screen.getAllByRole('button')
    fireEvent.click(buttons[0])
    expect(handleChange).toHaveBeenCalledWith(
      expect.objectContaining({ monday: expect.arrayContaining([6]) })
    )
  })

  it('removes the hour when a selected cell is clicked again', () => {
    const initial: Availability = { monday: [6] }
    const handleChange = jest.fn()
    render(<AvailabilityGrid value={initial} onChange={handleChange} />)
    const buttons = screen.getAllByRole('button')
    fireEvent.click(buttons[0]) // toggle Monday 06:00 OFF
    const result = handleChange.mock.calls[0][0]
    expect(result.monday).not.toContain(6)
  })

  it('marks pre-selected cells as aria-pressed=true', () => {
    const initial: Availability = { monday: [6] }
    render(<AvailabilityGrid value={initial} onChange={() => {}} />)
    const buttons = screen.getAllByRole('button')
    expect(buttons[0]).toHaveAttribute('aria-pressed', 'true')
    expect(buttons[1]).toHaveAttribute('aria-pressed', 'false') // Monday 07:00
  })
})
