-- Create user_activity_logs table to track all user interactions
CREATE TABLE IF NOT EXISTS public.user_activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,  -- 'login', 'reservation_create', 'reservation_cancel', 'view_page', etc.
    activity_description TEXT,
    metadata JSONB,  -- Store additional context (page_name, reservation_id, etc.)
    ip_address INET,
    user_agent TEXT,
    session_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON public.user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON public.user_activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_logs_activity_type ON public.user_activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_activity_logs_session_id ON public.user_activity_logs(session_id);

-- Composite index for common queries (user activity over time)
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_time ON public.user_activity_logs(user_id, created_at DESC);

-- Enable RLS
ALTER TABLE public.user_activity_logs ENABLE ROW LEVEL SECURITY;

-- Policy to allow service_role to manage all logs
CREATE POLICY "Service role can manage activity logs"
    ON public.user_activity_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy to allow authenticated users to view only their own logs
CREATE POLICY "Users can view their own activity logs"
    ON public.user_activity_logs
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Function to clean up old activity logs (older than 6 months)
CREATE OR REPLACE FUNCTION clean_old_activity_logs()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    DELETE FROM public.user_activity_logs
    WHERE created_at < NOW() - INTERVAL '6 months';
END;
$$;

-- Create a view for analytics (aggregated data)
CREATE OR REPLACE VIEW public.activity_analytics AS
SELECT
    DATE_TRUNC('hour', created_at) as hour_bucket,
    DATE_TRUNC('day', created_at) as day_bucket,
    activity_type,
    COUNT(*) as activity_count,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as unique_sessions
FROM public.user_activity_logs
GROUP BY DATE_TRUNC('hour', created_at), DATE_TRUNC('day', created_at), activity_type;

COMMENT ON TABLE public.user_activity_logs IS 'Tracks all user interactions for analytics and monitoring';
COMMENT ON COLUMN public.user_activity_logs.activity_type IS 'Type of activity: login, reservation_create, reservation_cancel, view_page, etc.';
COMMENT ON COLUMN public.user_activity_logs.metadata IS 'Additional context stored as JSON (page_name, reservation_id, etc.)';
