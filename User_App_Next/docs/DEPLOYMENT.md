# Deployment Guide - Tennis Reservation App

This guide provides step-by-step instructions for deploying the Tennis Reservation App to production using Supabase (backend) and Vercel (frontend hosting).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Supabase Setup](#supabase-setup)
3. [Database Schema Setup](#database-schema-setup)
4. [Supabase Configuration](#supabase-configuration)
5. [Vercel Deployment](#vercel-deployment)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Testing the Deployment](#testing-the-deployment)
8. [Troubleshooting](#troubleshooting)
9. [Free Tier Limits](#free-tier-limits)

## Prerequisites

Before starting deployment, ensure you have:

- **GitHub Account** - For connecting to Vercel
- **Vercel Account** - Sign up at [vercel.com](https://vercel.com) (free tier available)
- **Supabase Account** - Sign up at [supabase.com](https://supabase.com) (free tier available)
- **Code Repository** - Project pushed to GitHub
- **Domain Name** (optional) - For custom domain setup

## Supabase Setup

### Step 1: Create a New Supabase Project

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Click **"New Project"**
3. Fill in project details:
   - **Organization**: Select or create an organization
   - **Project Name**: `tennis-reservation-app` (or your preferred name)
   - **Database Password**: Choose a strong password (save this securely)
   - **Region**: Select the region closest to your users
   - **Pricing Plan**: Free tier is sufficient for getting started
4. Click **"Create new project"**
5. Wait 2-3 minutes for the project to be provisioned

### Step 2: Get Your API Credentials

1. In your Supabase project dashboard, go to **Settings** (gear icon) > **API**
2. Copy the following values (you'll need these later):
   - **Project URL**: `https://xxxxxxxxxxxxx.supabase.co`
   - **anon public key**: Starts with `eyJhbGc...` (safe to expose in frontend)
   - **service_role key**: Starts with `eyJhbGc...` (keep this secret, server-side only)

## Database Schema Setup

### Step 3: Create Database Tables

1. In Supabase dashboard, go to **SQL Editor**
2. Click **"New Query"**
3. Copy and paste the following SQL schema:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT NOT NULL,
  credits INTEGER DEFAULT 5 NOT NULL,
  is_vip BOOLEAN DEFAULT false NOT NULL,
  first_login_completed BOOLEAN DEFAULT false NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users RLS Policies
CREATE POLICY "Users can view their own profile"
  ON public.users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON public.users FOR UPDATE
  USING (auth.uid() = id);

-- Reservations table
CREATE TABLE public.reservations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  hour INTEGER NOT NULL CHECK (hour >= 6 AND hour <= 21),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  UNIQUE(date, hour)
);

-- Enable Row Level Security
ALTER TABLE public.reservations ENABLE ROW LEVEL SECURITY;

-- Reservations RLS Policies
CREATE POLICY "Anyone can view reservations"
  ON public.reservations FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can create reservations"
  ON public.reservations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own reservations"
  ON public.reservations FOR DELETE
  USING (auth.uid() = user_id);

-- Create index for faster queries
CREATE INDEX idx_reservations_date ON public.reservations(date);
CREATE INDEX idx_reservations_user_id ON public.reservations(user_id);

-- Access codes table
CREATE TABLE public.access_codes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT NOT NULL UNIQUE,
  is_active BOOLEAN DEFAULT true NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.access_codes ENABLE ROW LEVEL SECURITY;

-- Access codes RLS Policies
CREATE POLICY "Anyone can view active access codes"
  ON public.access_codes FOR SELECT
  USING (is_active = true);

-- Lock code table
CREATE TABLE public.lock_code (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.lock_code ENABLE ROW LEVEL SECURITY;

-- Lock code RLS Policies
CREATE POLICY "Authenticated users can view lock code"
  ON public.lock_code FOR SELECT
  USING (auth.uid() IS NOT NULL);

-- Maintenance slots table
CREATE TABLE public.blocked_slots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  date DATE NOT NULL,
  hour INTEGER NOT NULL CHECK (hour >= 6 AND hour <= 21),
  reason TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  UNIQUE(date, hour)
);

-- Enable Row Level Security
ALTER TABLE public.blocked_slots ENABLE ROW LEVEL SECURITY;

-- Maintenance slots RLS Policies
CREATE POLICY "Anyone can view maintenance slots"
  ON public.blocked_slots FOR SELECT
  USING (true);

-- Create index for faster queries
CREATE INDEX idx_blocked_slots_date ON public.blocked_slots(date);

-- Function to create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
    0,  -- Start with 0 credits
    false,
    false
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to automatically create user profile
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

4. Click **"Run"** to execute the SQL
5. Verify all tables were created by checking the **Table Editor** section

### Step 4: Insert Seed Data

1. In the SQL Editor, create a new query
2. Insert initial data:

```sql
-- Insert an initial access code
INSERT INTO public.access_codes (code, is_active)
VALUES ('TENNIS2024', true);

-- Insert initial lock code
INSERT INTO public.lock_code (code)
VALUES ('1234');

-- Optional: Create a test VIP user (replace with your email)
-- First, create the auth user through the Supabase Auth UI, then update:
-- UPDATE public.users SET is_vip = true, credits = 999 WHERE email = 'your-email@example.com';
```

3. Click **"Run"** to execute

## Supabase Configuration

### Step 5: Enable Realtime

1. Go to **Database** > **Replication**
2. Find the `reservations` table in the list
3. Enable replication by toggling the switch to **ON**
4. Find the `blocked_slots` table
5. Enable replication for this table as well

### Step 6: Configure Authentication

1. Go to **Authentication** > **Providers**
2. Ensure **Email** provider is enabled
3. Configure email settings:
   - Go to **Authentication** > **Email Templates**
   - Customize the **Confirm signup** template (optional)
   - Customize the **Reset password** template (optional)

### Step 7: Configure Site URL (Important!)

1. Go to **Authentication** > **URL Configuration**
2. Add your URLs:
   - **Site URL**: `http://localhost:3000` (for local development)
   - **Redirect URLs**: Add the following (one per line):
     ```
     http://localhost:3000/auth/callback
     https://your-app-name.vercel.app/auth/callback
     ```
   - Replace `your-app-name` with your actual Vercel app name
   - Add your custom domain URL if you have one

## Vercel Deployment

### Step 8: Connect GitHub Repository

1. Go to [https://vercel.com](https://vercel.com)
2. Click **"Add New..."** > **"Project"**
3. Click **"Import Git Repository"**
4. Select your GitHub repository
5. If not listed, click **"Adjust GitHub App Permissions"** to grant access

### Step 9: Configure Build Settings

1. **Framework Preset**: Next.js (should auto-detect)
2. **Root Directory**: `User App Next` (if repository contains multiple folders)
   - Click **"Edit"** next to Root Directory
   - Enter `User App Next`
3. **Build Command**: `npm run build` (default)
4. **Output Directory**: `.next` (default)
5. **Install Command**: `npm install` (default)

### Step 10: Add Environment Variables

1. Expand **"Environment Variables"** section
2. Add the following variables:

| Name | Value | Notes |
|------|-------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL | From Step 2 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anon key | From Step 2 |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service role key | From Step 2 - Keep secret! |
| `NEXT_PUBLIC_APP_URL` | `https://your-app.vercel.app` | Your Vercel app URL (see below) |
| `NEXT_PUBLIC_COURT_NAME` | `"Cancha Pública Colina Campestre"` | Your court name |

**Note**: For `NEXT_PUBLIC_APP_URL`, Vercel will provide the URL after deployment. You can:
- Use a placeholder initially, then update it after deployment
- Or skip this initially and add it in Step 12

3. Click **"Deploy"**

### Step 11: Wait for Deployment

1. Vercel will build and deploy your app (takes 2-5 minutes)
2. Monitor the build logs for any errors
3. Once complete, you'll see **"Congratulations!"** with your app URL

## Post-Deployment Configuration

### Step 12: Update Environment Variables (if needed)

1. Go to your Vercel project dashboard
2. Click **"Settings"** > **"Environment Variables"**
3. Update `NEXT_PUBLIC_APP_URL` with your actual Vercel URL
4. Click **"Save"**
5. Go to **"Deployments"**
6. Click the three dots on the latest deployment
7. Click **"Redeploy"** to apply the changes

### Step 13: Update Supabase Redirect URLs

1. Go back to Supabase dashboard
2. Navigate to **Authentication** > **URL Configuration**
3. Update the **Redirect URLs** to include your production URL:
   ```
   https://your-actual-app-name.vercel.app/auth/callback
   ```
4. Click **"Save"**

### Step 14: Configure Custom Domain (Optional)

1. In Vercel project, go to **"Settings"** > **"Domains"**
2. Click **"Add"**
3. Enter your custom domain name
4. Follow Vercel's instructions to update DNS records
5. Wait for DNS propagation (can take up to 48 hours)
6. Once verified, add the custom domain to Supabase redirect URLs

## Testing the Deployment

### Step 15: Test Authentication Flow

1. Visit your deployed app URL
2. Click **"Register"** or **"Sign Up"**
3. Enter the access code: `TENNIS2024`
4. Complete registration with your email
5. Check your email for verification link
6. Click the verification link
7. You should be redirected to the app and logged in

### Step 16: Test Reservation Creation

1. Once logged in, you should see the reservation grid
2. Click on an available time slot (green)
3. Confirm the reservation
4. Verify:
   - The slot turns blue (your reservation)
   - Your credit count decreases by 1
   - The reservation persists after page refresh

### Step 17: Test Real-Time Updates

1. Open your app in two different browsers (or incognito window)
2. Log in as different users in each browser
3. Make a reservation in one browser
4. Verify the other browser updates in real-time (slot turns gray)

### Step 18: Test Lock Code Display

1. While logged in, look for the lock code display
2. Verify it shows the code you inserted in Step 4 (`1234`)
3. If not visible, check the browser console for errors

## Troubleshooting

### Build Fails on Vercel

**Error**: "Module not found" or "Cannot find package"
**Solution**:
- Check that `package.json` and `package-lock.json` are committed
- Verify `Root Directory` is set correctly in Vercel settings
- Clear Vercel build cache: Settings > General > Clear Build Cache

**Error**: TypeScript errors during build
**Solution**:
- Run `npm run build` locally to identify the errors
- Fix TypeScript errors in the code
- Commit and push changes

### Authentication Not Working

**Error**: "Invalid redirect URL" or redirect fails
**Solution**:
- Verify `NEXT_PUBLIC_APP_URL` is set correctly in Vercel
- Check Supabase redirect URLs include your exact Vercel URL
- Ensure URLs include `/auth/callback` path
- Clear browser cookies and try again

### Real-Time Updates Not Working

**Error**: Reservations don't update automatically
**Solution**:
- Verify Realtime is enabled for `reservations` table in Supabase
- Check browser console for WebSocket errors
- Ensure RLS policies allow reading reservations
- Verify Supabase project is not paused (free tier pauses after 7 days of inactivity)

### Database Connection Errors

**Error**: "Invalid API key" or "Unauthorized"
**Solution**:
- Double-check `NEXT_PUBLIC_SUPABASE_URL` is correct
- Verify `NEXT_PUBLIC_SUPABASE_ANON_KEY` is the anon key, not service role key
- Ensure environment variables are saved in Vercel
- Redeploy after updating environment variables

### Row Level Security Issues

**Error**: "Row level security policy violation"
**Solution**:
- Check that all RLS policies were created correctly (Step 3)
- Verify user is authenticated before making requests
- Test policies in Supabase SQL Editor:
  ```sql
  SELECT auth.uid(); -- Should return user ID when authenticated
  ```

## Free Tier Limits

### Supabase Free Tier

- **Database**: 500 MB storage
- **Bandwidth**: 5 GB per month
- **Realtime**: 2 GB per month
- **Pauses after**: 7 days of inactivity (wake on next request)
- **Projects**: 2 active projects

**Monitoring**:
- Go to **Settings** > **Billing** to check usage
- Enable email alerts for usage thresholds

### Vercel Free Tier

- **Bandwidth**: 100 GB per month
- **Build Time**: 100 hours per month
- **Deployments**: Unlimited
- **Team Members**: 1 (Hobby plan)

**Monitoring**:
- Go to **Settings** > **Usage** to check limits
- View build logs in **Deployments** section

### Recommendations for Free Tier

1. **Optimize Images**: Use Next.js Image component for automatic optimization
2. **Enable Caching**: Leverage Vercel's edge caching for static assets
3. **Monitor Usage**: Check Supabase and Vercel dashboards regularly
4. **Database Indexes**: Ensure indexes exist for frequently queried columns
5. **Inactive Projects**: Supabase pauses projects after 7 days - first request wakes it up

## Production Checklist

Before going live, verify:

- [ ] All environment variables are set correctly in Vercel
- [ ] Supabase redirect URLs include production domain
- [ ] Email verification is working
- [ ] Real-time updates are functioning
- [ ] Lock code displays correctly for authenticated users
- [ ] Credit system deducts properly on reservations
- [ ] VIP users can make unlimited reservations
- [ ] Access code system prevents unauthorized registration
- [ ] Responsive design works on mobile devices
- [ ] Error handling displays user-friendly messages
- [ ] HTTPS is enabled (automatic with Vercel)
- [ ] Database backups are configured in Supabase (Settings > Database)

## Scaling Beyond Free Tier

When you outgrow free tier limits:

### Supabase Pro ($25/month)
- 8 GB database
- 50 GB bandwidth
- No project pausing
- Daily backups
- Email support

### Vercel Pro ($20/month)
- Unlimited bandwidth
- Advanced analytics
- Team collaboration
- Priority support

## Support and Resources

- **Vercel Documentation**: [https://vercel.com/docs](https://vercel.com/docs)
- **Supabase Documentation**: [https://supabase.com/docs](https://supabase.com/docs)
- **Next.js Documentation**: [https://nextjs.org/docs](https://nextjs.org/docs)
- **Vercel Support**: [https://vercel.com/support](https://vercel.com/support)
- **Supabase Support**: [https://supabase.com/support](https://supabase.com/support)

## Next Steps

After successful deployment:

1. **Monitor Performance**: Use Vercel Analytics to track page load times
2. **Set Up Alerts**: Configure Supabase email alerts for usage thresholds
3. **Backup Database**: Download database backups regularly from Supabase
4. **Update Documentation**: Keep README updated with any configuration changes
5. **Add Admin Panel**: Consider deploying the Admin App for managing users and reservations
6. **Custom Email Templates**: Customize Supabase auth email templates with your branding
7. **Error Tracking**: Integrate Sentry or similar for production error monitoring

Congratulations! Your Tennis Reservation App is now live in production.
