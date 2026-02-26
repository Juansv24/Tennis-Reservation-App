-- ABOUTME: Migration adding player profile fields, match posts, comments, and direct messages.
-- ABOUTME: Adds RLS policies for all new tables and new columns on users table.

-- Extend users table with profile fields
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS gender TEXT,
  ADD COLUMN IF NOT EXISTS age INTEGER,
  ADD COLUMN IF NOT EXISTS level_tier TEXT,
  ADD COLUMN IF NOT EXISTS categoria TEXT,
  ADD COLUMN IF NOT EXISTS availability JSONB,
  ADD COLUMN IF NOT EXISTS profile_completed BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS last_profile_visit TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS notify_suggestions BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS notify_match_posts BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS notify_messages BOOLEAN NOT NULL DEFAULT TRUE;

-- Match posts
CREATE TABLE IF NOT EXISTS match_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('specific', 'standing')),
  date DATE,
  hour INTEGER CHECK (hour >= 6 AND hour <= 20),
  desired_level_tier TEXT,
  desired_categoria TEXT,
  note TEXT CHECK (char_length(note) <= 280),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Match post comments
CREATE TABLE IF NOT EXISTS match_post_comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id UUID NOT NULL REFERENCES match_posts(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Direct messages
CREATE TABLE IF NOT EXISTS direct_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  read_at TIMESTAMPTZ
);

-- RLS: match_posts
ALTER TABLE match_posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "match_posts_select" ON match_posts
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "match_posts_insert" ON match_posts
  FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "match_posts_delete" ON match_posts
  FOR DELETE TO authenticated
  USING (auth.uid() = user_id);

-- RLS: match_post_comments
ALTER TABLE match_post_comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "comments_select" ON match_post_comments
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "comments_insert" ON match_post_comments
  FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "comments_delete" ON match_post_comments
  FOR DELETE TO authenticated
  USING (auth.uid() = user_id);

-- RLS: direct_messages (critical — only sender or recipient can read)
ALTER TABLE direct_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "messages_select" ON direct_messages
  FOR SELECT TO authenticated
  USING (auth.uid() = sender_id OR auth.uid() = recipient_id);

CREATE POLICY "messages_insert" ON direct_messages
  FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = sender_id);
