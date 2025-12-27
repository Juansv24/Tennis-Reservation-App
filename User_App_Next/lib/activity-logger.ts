import { SupabaseClient } from '@supabase/supabase-js'

/**
 * Activity type - RESERVATION CREATION ONLY
 */
export type ActivityType = 'reservation_create'

/**
 * Log reservation creation
 * Database handles created_at automatically with Colombian timezone
 */
export async function logActivity(
  supabase: SupabaseClient,
  userId: string,
  activityType: ActivityType,
  description?: string,
  metadata?: Record<string, any>
): Promise<boolean> {
  try {
    const { error } = await supabase
      .from('user_activity_logs')
      .insert({
        user_id: userId,
        activity_type: activityType,
        activity_description: description || null,
        metadata: metadata || {}
      })

    if (error) {
      console.error('Failed to log activity:', error)
      return false
    }

    return true
  } catch (error) {
    console.error('Exception while logging activity:', error)
    return false
  }
}
