// ABOUTME: TypeScript interfaces for all Supabase database tables.
// ABOUTME: Keep in sync with the database schema after every migration.

export interface User {
  id: string
  email: string
  full_name: string
  credits: number
  is_vip: boolean
  first_login_completed: boolean
  created_at: string
  gender: string | null
  age: number | null
  level_tier: string | null
  categoria: string | null
  profile_completed: boolean
  last_profile_visit: string | null
  notify_suggestions: boolean
  notify_match_posts: boolean
  notify_messages: boolean
}

export interface SuggestedPartner {
  user: Pick<User, 'id' | 'full_name' | 'level_tier' | 'categoria'>
  badge: 'nivel+horario' | 'solo-nivel'
  overlapMessage: string | null
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

export interface MatchPost {
  id: string
  user_id: string
  type: 'specific' | 'standing'
  date: string | null
  hour: number | null
  desired_level_tier: string | null
  desired_categoria: string | null
  note: string | null
  is_active: boolean
  created_at: string
  users?: { full_name: string; level_tier: string | null; categoria: string | null }
}

export interface MatchPostWithCount extends MatchPost {
  comment_count: number
}

export interface MatchPostComment {
  id: string
  post_id: string
  user_id: string
  content: string
  created_at: string
  users?: { full_name: string }
}

export interface DirectMessage {
  id: string
  sender_id: string
  recipient_id: string
  content: string
  created_at: string
  read_at: string | null
}
