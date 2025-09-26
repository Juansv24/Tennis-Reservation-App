"""
Smart Wake-Up Service for Streamlit App
Two daily pings: 6:00-6:30 AM and 5:00-5:30 PM (randomized times)
"""

import requests
import threading
import time
import random
from datetime import datetime, timedelta
from timezone_utils import get_colombia_now


class SmartWakeUpService:
    """Service with two daily randomized wake-up pings"""

    def __init__(self, app_url: str = None):
        self.app_url = app_url or "https://reservas-tenis-colina.streamlit.app"
        self.is_running = False
        self.thread = None

        # Ping windows (will be randomized within these ranges)
        self.morning_window = (6, 6.5)  # 6:00-6:30 AM
        self.afternoon_window = (17, 17.5)  # 5:00-5:30 PM

        # Track pings for today
        self.today_pings = {
            'morning': {'done': False, 'scheduled_time': None},
            'afternoon': {'done': False, 'scheduled_time': None}
        }
        self.last_ping_date = None

    def reset_daily_schedule(self):
        """Reset and generate new random times for today"""
        current_date = get_colombia_now().date()

        if self.last_ping_date != current_date:
            # New day - generate random times
            morning_minutes = random.randint(0, 30)  # 0-30 minutes after 6 AM
            afternoon_minutes = random.randint(0, 30)  # 0-30 minutes after 5 PM

            self.today_pings = {
                'morning': {
                    'done': False,
                    'scheduled_time': f"6:{morning_minutes:02d} AM"
                },
                'afternoon': {
                    'done': False,
                    'scheduled_time': f"5:{afternoon_minutes:02d} PM"
                }
            }
            self.last_ping_date = current_date

            print(f"📅 Daily schedule for {current_date}:")
            print(f"   🌅 Morning ping: {self.today_pings['morning']['scheduled_time']}")
            print(f"   🌆 Afternoon ping: {self.today_pings['afternoon']['scheduled_time']}")

    def should_ping_now(self) -> str:
        """Check if we should ping now, return ping type or None"""
        current_time = get_colombia_now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_total_minutes = current_hour * 60 + current_minute

        # Morning window: 6:00-6:30 AM (360-390 minutes from midnight)
        morning_start = 6 * 60  # 360 minutes
        morning_end = 6 * 60 + 30  # 390 minutes

        # Afternoon window: 5:00-5:30 PM (1020-1050 minutes from midnight)
        afternoon_start = 17 * 60  # 1020 minutes
        afternoon_end = 17 * 60 + 30  # 1050 minutes

        # Check morning ping
        if (morning_start <= current_total_minutes <= morning_end and
                not self.today_pings['morning']['done']):
            return 'morning'

        # Check afternoon ping
        if (afternoon_start <= current_total_minutes <= afternoon_end and
                not self.today_pings['afternoon']['done']):
            return 'afternoon'

        return None

    def send_wake_up_ping(self, ping_type: str) -> bool:
        """Send wake-up ping to the app"""
        try:
            ping_emoji = "🌅" if ping_type == "morning" else "🌆"
            ping_name = "Morning" if ping_type == "morning" else "Afternoon"

            print(f"{ping_emoji} Sending {ping_name.lower()} wake-up ping at {get_colombia_now().strftime('%H:%M:%S')}")

            response = requests.get(
                self.app_url,
                timeout=30,
                headers={
                    'User-Agent': f'WakeUp-Service/{ping_name}/1.0',
                    'X-Ping-Type': ping_type
                }
            )

            success = response.status_code == 200
            if success:
                self.today_pings[ping_type]['done'] = True
                print(f"✅ {ping_name} ping successful - app is ready!")
            else:
                print(f"⚠️ {ping_name} ping returned status {response.status_code}")

            return success

        except Exception as e:
            print(f"❌ {ping_type} ping failed: {str(e)}")
            return False

    def wake_up_loop(self):
        """Main service loop"""
        print("🚀 Smart wake-up service started")

        while self.is_running:
            try:
                # Reset schedule if new day
                self.reset_daily_schedule()

                # Check if we should ping now
                ping_type = self.should_ping_now()
                if ping_type:
                    self.send_wake_up_ping(ping_type)

                # Check every 5 minutes during ping windows, otherwise every hour
                current_time = get_colombia_now()
                current_hour = current_time.hour

                if current_hour in [6, 17]:  # During ping hours
                    time.sleep(300)  # Check every 5 minutes
                else:
                    time.sleep(3600)  # Check every hour

            except Exception as e:
                print(f"❌ Wake-up service error: {str(e)}")
                time.sleep(1800)  # Wait 30 minutes on error

    def start(self):
        """Start the wake-up service"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self.wake_up_loop, daemon=True)
            self.thread.start()
            print("✅ Smart wake-up service started")
            print("📋 Schedule: 6:00-6:30 AM and 5:00-5:30 PM (randomized daily)")
        else:
            print("⚠️ Wake-up service already running")

    def stop(self):
        """Stop the wake-up service"""
        if self.is_running:
            self.is_running = False
            print("🛑 Smart wake-up service stopped")

    def get_status(self) -> dict:
        """Get current service status"""
        self.reset_daily_schedule()  # Ensure current schedule
        current_time = get_colombia_now()

        # Calculate next pending ping
        next_ping = None
        if not self.today_pings['morning']['done']:
            next_ping = f"Morning: {self.today_pings['morning']['scheduled_time']}"
        elif not self.today_pings['afternoon']['done']:
            next_ping = f"Afternoon: {self.today_pings['afternoon']['scheduled_time']}"
        else:
            next_ping = "Tomorrow morning (new random time)"

        return {
            'is_running': self.is_running,
            'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'today_morning': {
                'scheduled': self.today_pings['morning']['scheduled_time'],
                'completed': '✅' if self.today_pings['morning']['done'] else '⏳'
            },
            'today_afternoon': {
                'scheduled': self.today_pings['afternoon']['scheduled_time'],
                'completed': '✅' if self.today_pings['afternoon']['done'] else '⏳'
            },
            'next_ping': next_ping,
            'last_reset_date': str(self.last_ping_date)
        }


# Global instance
smart_wake_up_service = SmartWakeUpService()