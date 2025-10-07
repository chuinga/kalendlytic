import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WorkingHoursForm } from '@/components/preferences/WorkingHoursForm'
import { WorkingHours } from '@/types/preferences'

const mockWorkingHours: WorkingHours = {
  monday: { start: '09:00', end: '17:00' },
  tuesday: { start: '09:00', end: '17:00' },
  wednesday: { start: '09:00', end: '17:00' },
  thursday: { start: '09:00', end: '17:00' },
  friday: { start: '09:00', end: '17:00' },
  saturday: { start: '10:00', end: '14:00' },
  sunday: { start: '10:00', end: '14:00' }
}

describe('WorkingHoursForm', () => {
  const mockProps = {
    workingHours: mockWorkingHours,
    timezone: 'America/New_York',
    onUpdate: jest.fn()
  }
  
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders working hours form correctly', () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    expect(screen.getByText('Working Hours')).toBeInTheDocument()
    expect(screen.getByText('Set your available hours for each day of the week')).toBeInTheDocument()
    
    // Check all days are rendered
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    days.forEach(day => {
      expect(screen.getByText(day)).toBeInTheDocument()
    })
  })

  it('displays current working hours correctly', () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    // Check Monday's working hours
    const mondayStartInput = screen.getByDisplayValue('09:00')
    const mondayEndInput = screen.getByDisplayValue('17:00')
    
    expect(mondayStartInput).toBeInTheDocument()
    expect(mondayEndInput).toBeInTheDocument()
  })

  it('allows editing working hours', async () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    // Find Monday's start time input (first occurrence of 09:00)
    const startInputs = screen.getAllByDisplayValue('09:00')
    const mondayStartInput = startInputs[0]
    
    await user.clear(mondayStartInput)
    await user.type(mondayStartInput, '08:00')
    
    expect(mondayStartInput).toHaveValue('08:00')
  })

  it('validates that end time is after start time', async () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    // Find Monday's inputs
    const startInputs = screen.getAllByDisplayValue('09:00')
    const endInputs = screen.getAllByDisplayValue('17:00')
    const mondayStartInput = startInputs[0]
    const mondayEndInput = endInputs[0]
    
    // Set end time before start time
    await user.clear(mondayEndInput)
    await user.type(mondayEndInput, '08:00')
    
    const saveButton = screen.getByText('Save Working Hours')
    await user.click(saveButton)
    
    await waitFor(() => {
      expect(screen.getByText('End time must be after start time')).toBeInTheDocument()
    })
  })

  it('allows toggling days on/off', async () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    // Find Sunday's toggle (assuming it has a checkbox or toggle)
    const sundayToggle = screen.getByRole('checkbox', { name: /sunday/i })
    
    await user.click(sundayToggle)
    
    // Sunday should now be disabled
    expect(sundayToggle).not.toBeChecked()
  })

  it('saves working hours when form is submitted', async () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    const saveButton = screen.getByText('Save Working Hours')
    await user.click(saveButton)
    
    expect(mockProps.onUpdate).toHaveBeenCalledWith({ workingHours: mockWorkingHours })
  })

  it('shows save button', () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    const saveButton = screen.getByText('Save Changes')
    expect(saveButton).toBeInTheDocument()
  })

  it('provides quick preset options', async () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    // Look for preset buttons
    const standardButton = screen.getByText('Standard (9-5)')
    await user.click(standardButton)
    
    // Should update all weekday hours to 9-5
    const startInputs = screen.getAllByDisplayValue('09:00')
    const endInputs = screen.getAllByDisplayValue('17:00')
    
    expect(startInputs.length).toBeGreaterThan(0)
    expect(endInputs.length).toBeGreaterThan(0)
  })

  it('handles early bird preset', async () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    const earlyBirdButton = screen.getByText('Early Bird (7-3)')
    await user.click(earlyBirdButton)
    
    // Should update weekday hours to 7-3
    await waitFor(() => {
      expect(screen.getAllByDisplayValue('07:00').length).toBeGreaterThan(0)
      expect(screen.getAllByDisplayValue('15:00').length).toBeGreaterThan(0)
    })
  })

  it('handles night owl preset', async () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    const nightOwlButton = screen.getByText('Night Owl (11-7)')
    await user.click(nightOwlButton)
    
    // Should update weekday hours to 11-7
    await waitFor(() => {
      expect(screen.getAllByDisplayValue('11:00').length).toBeGreaterThan(0)
      expect(screen.getAllByDisplayValue('19:00').length).toBeGreaterThan(0)
    })
  })

  it('allows copying hours to all days', async () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    // Modify Monday's hours first
    const startInputs = screen.getAllByDisplayValue('09:00')
    const mondayStartInput = startInputs[0]
    
    await user.clear(mondayStartInput)
    await user.type(mondayStartInput, '08:30')
    
    // Click copy to all days button
    const copyButton = screen.getByText('Copy to All Days')
    await user.click(copyButton)
    
    // All days should now have the same hours as Monday
    await waitFor(() => {
      expect(screen.getAllByDisplayValue('08:30').length).toBe(7) // All 7 days
    })
  })

  it('shows timezone information', () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    expect(screen.getByText(/times are in your local timezone/i)).toBeInTheDocument()
  })

  it('validates time format', async () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    const startInputs = screen.getAllByDisplayValue('09:00')
    const mondayStartInput = startInputs[0]
    
    await user.clear(mondayStartInput)
    await user.type(mondayStartInput, 'invalid')
    
    const saveButton = screen.getByText('Save Working Hours')
    await user.click(saveButton)
    
    await waitFor(() => {
      expect(screen.getByText('Invalid time format')).toBeInTheDocument()
    })
  })

  it('handles weekend-only work schedule', async () => {
    const weekendOnlyHours = {
      ...mockWorkingHours,
      monday: { start: '', end: '' },
      tuesday: { start: '', end: '' },
      wednesday: { start: '', end: '' },
      thursday: { start: '', end: '' },
      friday: { start: '', end: '' }
    }
    
    render(<WorkingHoursForm {...mockProps} workingHours={weekendOnlyHours} />)
    
    // Should show weekend hours only
    expect(screen.getByDisplayValue('10:00')).toBeInTheDocument()
    expect(screen.getByDisplayValue('14:00')).toBeInTheDocument()
  })

  it('resets form when reset button is clicked', async () => {
    render(<WorkingHoursForm {...mockProps} />)
    
    // Modify some hours
    const startInputs = screen.getAllByDisplayValue('09:00')
    const mondayStartInput = startInputs[0]
    
    await user.clear(mondayStartInput)
    await user.type(mondayStartInput, '08:00')
    
    // Click reset button
    const resetButton = screen.getByText('Reset')
    await user.click(resetButton)
    
    // Should revert to original values
    await waitFor(() => {
      expect(screen.getByDisplayValue('09:00')).toBeInTheDocument()
    })
  })
})