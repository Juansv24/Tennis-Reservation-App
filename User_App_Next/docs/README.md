# Tennis Reservation App - Next.js

A modern, real-time tennis court reservation system built with Next.js 16, TypeScript, Tailwind CSS, and Supabase. This application provides an intuitive interface for users to book tennis court time slots with real-time availability updates, credit management, and VIP user support.

## Features

- **Authentication System**
  - User registration and login with email verification
  - Password reset functionality
  - Access code system for new user registration
  - Secure session management with Supabase Auth

- **Real-Time Reservations**
  - Interactive time slot grid showing availability
  - Live updates when reservations are made or cancelled
  - Date navigation (today/tomorrow)
  - Visual status indicators (available, taken, your reservations, past, maintenance)

- **Credit System**
  - Users consume credits when making reservations
  - VIP users have unlimited reservations
  - Credit balance displayed in the dashboard

- **Lock Code Display**
  - Authenticated users can view the current court lock code
  - Essential for accessing the physical tennis court

- **Maintenance Slots**
  - Admin-configurable maintenance periods
  - Blocks time slots for court maintenance
  - Clearly marked in the reservation grid

- **Responsive Design**
  - US Open-themed color palette
  - Mobile-friendly interface
  - Tailwind CSS for modern styling

## Tech Stack

- **Frontend**: Next.js 16.0.7 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Real-time**: Supabase Realtime
- **Date Handling**: date-fns 4.1.0
- **Utilities**: clsx for conditional classnames

## Project Structure

```
User App Next/
├── app/                          # Next.js App Router
│   ├── (auth)/                  # Authentication routes
│   │   ├── access-code/        # Access code validation
│   │   ├── login/              # Login page
│   │   ├── register/           # Registration page
│   │   └── verify-email/       # Email verification
│   ├── (dashboard)/            # Protected dashboard routes
│   │   ├── page.tsx            # Main reservation grid
│   │   └── layout.tsx          # Dashboard layout with header
│   ├── api/                    # API routes
│   │   ├── auth/              # Auth callbacks and validation
│   │   ├── lock-code/         # Lock code retrieval
│   │   └── reservations/      # Reservation CRUD operations
│   ├── globals.css            # Global styles
│   ├── layout.tsx             # Root layout
│   └── page.tsx               # Landing page
├── components/                 # React components
│   ├── ConfirmationModal.tsx  # Reservation confirmation dialog
│   ├── Header.tsx             # Navigation header with credits
│   ├── ReservationGrid.tsx    # Main grid component with real-time
│   └── TimeSlot.tsx           # Individual time slot button
├── lib/                       # Utility libraries
│   ├── constants.ts          # Court hours, colors, date helpers
│   └── supabase/            # Supabase client configuration
│       ├── client.ts        # Browser client
│       ├── server.ts        # Server client
│       └── middleware.ts    # Auth middleware
├── types/                    # TypeScript type definitions
│   └── database.types.ts    # Database schema types
├── .env.example             # Environment variables template
├── middleware.ts            # Next.js middleware for auth
├── tailwind.config.ts      # Tailwind configuration
└── package.json            # Dependencies
```

## Prerequisites

- **Node.js** 20.x or higher
- **npm** or **pnpm**
- **Supabase Account** (free tier works)
- **Git** (for version control)

## Local Development Setup

### 1. Clone the Repository

```bash
cd "User App Next"
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env.local
```

Edit `.env.local` and add your Supabase credentials:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your-project-url.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# App Configuration
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_COURT_NAME="Cancha Pública Colina Campestre"
```

**Environment Variables Explained:**

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous (public) API key | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (server-side only) | Yes |
| `NEXT_PUBLIC_APP_URL` | Application URL (for redirects) | Yes |
| `NEXT_PUBLIC_COURT_NAME` | Display name of the tennis court | No |

### 4. Set Up Supabase Database

See the [DEPLOYMENT.md](./DEPLOYMENT.md) file for detailed database setup instructions.

At minimum, you need to create the following tables in Supabase:
- `users` - User profiles with credits and VIP status
- `reservations` - Court reservations by date/hour
- `access_codes` - Registration access codes
- `lock_code` - Current court lock code
- `blocked_slots` - Maintenance periods

### 5. Start Development Server

```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000)

## Database Schema

### Users Table (`users`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key (matches Supabase auth.users.id) |
| `email` | TEXT | User email address |
| `full_name` | TEXT | User's full name |
| `credits` | INTEGER | Available reservation credits |
| `is_vip` | BOOLEAN | VIP status (unlimited reservations) |
| `first_login_completed` | BOOLEAN | First login flag |
| `created_at` | TIMESTAMP | Registration timestamp |

### Reservations Table (`reservations`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Foreign key to users |
| `date` | DATE | Reservation date (YYYY-MM-DD) |
| `hour` | INTEGER | Hour (6-21, representing 6 AM - 9 PM) |
| `created_at` | TIMESTAMP | Reservation creation time |

**Unique constraint:** (`date`, `hour`) - prevents double booking

### Access Codes Table (`access_codes`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `code` | TEXT | Access code for registration |
| `is_active` | BOOLEAN | Whether code is currently valid |
| `created_at` | TIMESTAMP | Code creation time |

### Lock Code Table (`lock_code`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `code` | TEXT | Current lock code |
| `created_at` | TIMESTAMP | When code was set |

### Maintenance Slots Table (`blocked_slots`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `date` | DATE | Maintenance date |
| `hour` | INTEGER | Hour (6-21) |
| `reason` | TEXT | Optional maintenance reason |
| `created_at` | TIMESTAMP | Slot creation time |

## Available Scripts

```bash
# Development
npm run dev          # Start development server on port 3000

# Production
npm run build        # Build for production
npm run start        # Start production server

# Code Quality
npm run lint         # Run ESLint
```

## US Open Theme Colors

The app uses the official US Open color palette:

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| US Open Blue | `#001854` | Primary brand color, headers |
| US Open Light Blue | `#2478CC` | Buttons, links |
| US Open Yellow | `#FFD400` | Accents, highlights |
| Available Green | `#4CAF50` | Available time slots |
| Taken Gray | `#9E9E9E` | Reserved slots |
| Maintenance Orange | `#FF9800` | Maintenance slots |

These colors are defined in `tailwind.config.ts` and `lib/constants.ts`.

## Key Features Explained

### Real-Time Updates

The application uses Supabase Realtime to subscribe to database changes. When any user makes or cancels a reservation, all connected clients receive the update instantly via WebSocket connection.

**Implementation**: See `ReservationGrid.tsx` for the real-time subscription setup.

### Credit System

- **Standard Users**: Start with a set number of credits (configurable)
- Each reservation consumes 1 credit
- No credits = cannot make new reservations
- **VIP Users**: Unlimited reservations, credits never deducted

### Time Slots

- Court operates from **6:00 AM to 9:00 PM** (6-21 hours)
- Each slot represents a 1-hour reservation
- Slots are color-coded by status:
  - **Green**: Available to book
  - **Blue**: Your reservation
  - **Gray**: Taken by another user
  - **Light gray**: Past time (cannot book)
  - **Orange**: Maintenance (cannot book)

### Access Code System

New users must enter a valid access code during registration. This prevents unauthorized registrations and allows controlled access to the system.

## Deployment

For detailed deployment instructions to Vercel and Supabase, see [DEPLOYMENT.md](./DEPLOYMENT.md).

Quick steps:
1. Create Supabase project and run migrations
2. Deploy to Vercel
3. Configure environment variables
4. Set up Supabase redirect URLs
5. Test the application

## Troubleshooting

### Authentication Issues

**Problem**: "User not authenticated" errors
**Solution**:
- Check `.env.local` has correct Supabase credentials
- Verify Supabase URL redirect settings include your app URL
- Clear browser cookies and try logging in again

### Real-Time Not Working

**Problem**: Reservations don't update in real-time
**Solution**:
- Verify Supabase Realtime is enabled for the `reservations` table
- Check browser console for WebSocket connection errors
- Ensure Row Level Security (RLS) policies allow reading reservations

### Reservation Fails with "Slot already taken"

**Problem**: Concurrent booking attempts
**Solution**:
- This is expected behavior with the unique constraint
- The first user to complete the transaction gets the slot
- Implement optimistic UI updates if needed

### Build Errors

**Problem**: TypeScript compilation errors
**Solution**:
- Run `npm install` to ensure all dependencies are current
- Check `types/database.types.ts` matches your Supabase schema
- Regenerate types with Supabase CLI if schema changed

## Contributing

When making changes:
1. Follow existing code style (TypeScript + ESLint)
2. Test authentication flows thoroughly
3. Verify real-time updates work correctly
4. Update documentation if adding features
5. Follow commit message conventions

## License

Private project - All rights reserved.

## Support

For issues or questions, contact the development team.
