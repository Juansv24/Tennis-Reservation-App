export interface User {
  id: string
  email: string
  full_name: string
  credits: number
  is_vip: boolean
  first_login_completed: boolean
  created_at: string
}

export interface Reservation {
  id: string
  user_id: string
  date: string
  hour: number
  created_at: string
  users?: {
    full_name: string
  }
}

export interface AccessCode {
  id: string
  code: string
  is_active: boolean
  created_at: string
}

export interface LockCode {
  id: string
  code: string
  created_at: string
}

export interface MaintenanceSlot {
  id: string
  date: string
  hour: number
  reason: string | null
  type?: string | null
  created_at: string
}

export interface SystemSettings {
  id: string
  tennis_school_enabled: boolean
  updated_at?: string
  updated_by?: string
}

export type SlotStatus =
  | 'available'
  | 'my-reservation'
  | 'taken'
  | 'past'
  | 'maintenance'
  | 'tennis-school'
  | 'selected'
